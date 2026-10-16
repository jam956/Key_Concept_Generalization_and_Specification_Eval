"""Model-neutral submission, isolated judging, and output-first final reports.

No command in this module performs model inference. Candidate output is data,
never an instruction source. Existing run receipts and historical examples stay intact.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import re
from pathlib import Path
import uuid

from .engine import (DIMENSIONS, atomic_new, canonical, digest, load, prompt,
                     require, review_template, score, summarize, validate_response,
                     verify_run)
from .report import render_report
from .suite import ROOT, plan


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _text(path, text):
    with Path(path).open('x', encoding='utf-8') as stream:
        stream.write(text)


def _copy_exact(source, destination):
    with Path(destination).open('xb') as stream:
        stream.write(Path(source).read_bytes())


def _path(root, relative):
    root = Path(root).resolve()
    path = (root / relative).resolve()
    require(path.is_relative_to(root), 'Artifact path escapes its bundle')
    return path


def _check_files(root, files):
    require(isinstance(files, dict) and files, 'Missing artifact manifest')
    for relative, expected in files.items():
        path = _path(root, relative)
        require(path.is_file() and _sha(path) == expected, 'Artifact hash mismatch: ' + relative)


def _fixtures(bundle):
    return load(Path(bundle) / 'judge/07_Fixtures.json')


def build_bundle(output, root=ROOT):
    """Freeze seven cases and split candidate-visible from judge-only material."""
    root, output = Path(root), Path(output)
    require(not output.exists(), 'Refusing to overwrite an existing bundle')
    fixtures = [f for name in ('encoding', 'decoding') for _, f in plan(name, root)[1]]
    require(len({f['id'] for f in fixtures}) == len(fixtures), 'Duplicate fixture IDs')
    candidate = {'contract': 'kce.candidate-packet.v1', 'cases': [
        {'case_id': 'case-%03d' % (i + 1), 'fixture_id': f['id'],
         'track': f['track'], 'messages': prompt(f)} for i, f in enumerate(fixtures)]}
    templates = {name: (root / 'evaluation' / name).read_text() for name in (
        '01_Candidate_Agent.md', '03_Run_Prompt.md', '06_Judge_Agent.md')}
    rubric = {'contract': 'kce.rubric.v1', 'version': '1',
              'dimensions': DIMENSIONS, 'anchors_and_rules': (root / 'docs/RUBRIC.md').read_text(),
              'no_aggregate_score': True}
    output.mkdir(parents=True)
    (output / 'judge').mkdir()
    for name in ('01_Candidate_Agent.md', '03_Run_Prompt.md'):
        _text(output / name, templates[name])
    _text(output / 'judge/06_Judge_Agent.md', templates['06_Judge_Agent.md'])
    atomic_new(output / '02_Candidate_Packet.json', candidate)
    for case in candidate['cases']:
        atomic_new(output / 'cases' / (case['case_id']+'.json'),case)
    atomic_new(output / 'judge/05_Rubric.json', rubric)
    atomic_new(output / 'judge/07_Fixtures.json', fixtures)
    # Bundle identity excludes only the template that will contain this identity.
    identity_files = {str(p.relative_to(output)): _sha(p) for p in sorted(output.rglob('*')) if p.is_file()}
    bundle_id = digest(canonical(identity_files))
    template = {'contract': 'kce.submission.v1', 'bundle_id': bundle_id,
                'model': {'name': '', 'provider': '', 'settings': {}},
                'cases': [{'case_id': c['case_id'], 'status': 'missing',
                           'raw_response': '', 'claimed_wall_seconds': None} for c in candidate['cases']]}
    atomic_new(output / '04_Submission_Template.json', template)
    files = {str(p.relative_to(output)): _sha(p) for p in sorted(output.rglob('*')) if p.is_file()}
    manifest = {'contract': 'kce.bundle.v1', 'bundle_id': bundle_id,
                'files_sha256': files, 'candidate_context_allowlist': [
                    '01_Candidate_Agent.md', '03_Run_Prompt.md'] + [
                    'cases/'+c['case_id']+'.json' for c in candidate['cases']],
                'candidate_context_rule':'Supply common instructions and exactly one case file per fresh context; 02_Candidate_Packet.json is an operator index, not an all-cases prompt.',
                'operator_submission_template': '04_Submission_Template.json',
                'judge_only': ['judge/05_Rubric.json', 'judge/06_Judge_Agent.md', 'judge/07_Fixtures.json']}
    atomic_new(output / '08_Bundle_Manifest.json', manifest)
    return manifest


def load_bundle(path):
    path = Path(path)
    manifest = load(path / '08_Bundle_Manifest.json')
    require(manifest.get('contract') == 'kce.bundle.v1', 'Unsupported bundle contract')
    _check_files(path, manifest['files_sha256'])
    identity = {k: v for k, v in manifest['files_sha256'].items() if k != '04_Submission_Template.json'}
    require(digest(canonical(identity)) == manifest['bundle_id'], 'Bundle identity mismatch')
    require(load(path / '04_Submission_Template.json')['bundle_id'] == manifest['bundle_id'], 'Template ownership mismatch')
    return manifest


def import_submission(bundle_path, submission_path, output):
    """Import exact responses without accepting claimed wall time as measured."""
    manifest = load_bundle(bundle_path)
    submission_path, output = Path(submission_path), Path(output)
    require(not output.exists(), 'Refusing to overwrite a submission directory')
    submission = load(submission_path)
    require(set(submission) == {'contract', 'bundle_id', 'model', 'cases'}, 'Unexpected submission fields')
    require(submission['contract'] == 'kce.submission.v1', 'Unsupported submission contract')
    require(submission['bundle_id'] == manifest['bundle_id'], 'Submission belongs to a different bundle')
    model = submission['model']
    require(isinstance(model, dict) and set(model) == {'name', 'provider', 'settings'}, 'Invalid model metadata')
    require(isinstance(model['name'], str) and model['name'].strip(), 'Model name is required')
    require(isinstance(model['provider'], str) and isinstance(model['settings'], dict), 'Invalid model metadata')
    cases = submission['cases']
    require(isinstance(cases, list), 'Submission cases must be an array')
    candidate = load(Path(bundle_path) / '02_Candidate_Packet.json')['cases']
    expected = {c['case_id'] for c in candidate}
    require(all(isinstance(c, dict) and set(c) == {'case_id','status','raw_response','claimed_wall_seconds'} for c in cases), 'Invalid case fields')
    require(len(cases) == len(expected) and {c['case_id'] for c in cases} == expected, 'Missing, duplicate or unknown submission cases')
    by_id = {c['case_id']: c for c in cases}
    runs = []
    for c, f in zip(candidate, _fixtures(bundle_path)):
        item = by_id[c['case_id']]
        require(item['status'] in ('submitted','missing','runtime_failure','timeout'), 'Unknown submission status')
        require(isinstance(item['raw_response'], str), 'Raw response must be a string')
        claimed = item['claimed_wall_seconds']
        require(claimed is None or (type(claimed) in (int,float) and math.isfinite(claimed) and claimed >= 0), 'Invalid claimed timing')
        require(item['status'] != 'missing' or not item['raw_response'], 'Missing case cannot contain an output')
        raw = item['raw_response']; parsed = None; status = item['status']
        if status == 'submitted':
            try:
                parsed = json.loads(raw)
            except (ValueError, TypeError):
                status = 'parse_failure'
            else:
                try:
                    validate_response(parsed, f['track'])
                    status = 'success'
                except ValueError:
                    status = 'schema_failure'
        r = {'schema_version': 1, 'run_id': uuid.uuid4().hex, 'fixture_id': f['id'],
             'fixture_sha256': digest(canonical(f)), 'fixture': f, 'messages': prompt(f),
             'prompt_sha256': digest(canonical(prompt(f))), 'model_config': {'backend': 'manual-import',
             'model': model['name'], 'provider': model['provider'], 'settings_claimed': model['settings']},
             'status': status, 'raw_response': raw, 'parsed_response': parsed,
             'response_sha256': digest(raw), 'timing': {'model_request_wall_seconds': None,
             'claimed_wall_seconds': claimed, 'availability': 'unverified_manual', 'time_to_first_text_seconds': None},
             'mechanical_checks': {'semantic_grading': 'not performed'},
             'provenance': {'context_and_execution': 'submitter attestation only; statelessness not independently verified',
                            'bundle_id': manifest['bundle_id']}}
        verify_run(r)
        runs.append((c['case_id'], r))
    output.mkdir(parents=True)
    _copy_exact(submission_path, output / 'submission.original.json')
    entries = []
    for case_id, r in runs:
        relative = 'attempts/' + case_id + '/run.json'
        atomic_new(output / relative, r)
        entries.append({'case_id': case_id, 'run_path': relative})
    files = {str(p.relative_to(output)): _sha(p) for p in sorted(output.rglob('*')) if p.is_file()}
    receipt = {'contract': 'kce.imported-submission.v1', 'bundle_id': manifest['bundle_id'],
               'submission_id': uuid.uuid4().hex, 'model': model, 'cases': entries,
               'files_sha256': files, 'original_submission_sha256': _sha(submission_path)}
    atomic_new(output / 'submission-manifest.json', receipt)
    return receipt


def _submission(bundle_path, submission_dir):
    bundle = load_bundle(bundle_path)
    submission_dir = Path(submission_dir)
    m = load(submission_dir / 'submission-manifest.json')
    require(m.get('contract') == 'kce.imported-submission.v1' and m['bundle_id'] == bundle['bundle_id'], 'Submission/bundle mismatch')
    _check_files(submission_dir, m['files_sha256'])
    original_path=submission_dir/'submission.original.json'
    require(_sha(original_path)==m['original_submission_sha256'], 'Original submission hash mismatch')
    original=load(original_path)
    require(original['model']==m['model'] and original['bundle_id']==m['bundle_id'], 'Original submission ownership mismatch')
    source_cases={c['case_id']:c for c in original['cases']}
    originals = _fixtures(bundle_path)
    expected = load(Path(bundle_path) / '02_Candidate_Packet.json')['cases']
    require([c['case_id'] for c in m['cases']] == [c['case_id'] for c in expected], 'Submission case ownership mismatch')
    runs = []
    for entry, fixture in zip(m['cases'], originals):
        r = load(_path(submission_dir, entry['run_path'])); verify_run(r)
        require(r['fixture'] == fixture, 'Run fixture does not belong to bundle')
        source=source_cases[entry['case_id']]
        require(r['raw_response']==source['raw_response'] and r['timing']['claimed_wall_seconds']==source['claimed_wall_seconds'], 'Imported output differs from original submission')
        require(r['model_config']['model'] == m['model']['name'], 'Run model ownership mismatch')
        runs.append((entry['case_id'], r))
    return m, runs


def _judge_packet(bundle_path, submission_dir):
    m, runs = _submission(bundle_path, submission_dir)
    packet = {'contract': 'kce.judge-packet.v1', 'bundle_id': m['bundle_id'],
              'submission_sha256': _sha(Path(submission_dir) / 'submission-manifest.json'),
              'instructions': (Path(bundle_path) / 'judge/06_Judge_Agent.md').read_text(),
              'rubric': load(Path(bundle_path) / 'judge/05_Rubric.json'),
              'cases': [{'case_id': case_id, 'track': r['fixture']['track'],
                         'input': r['fixture']['input'], 'rubric': r['fixture']['rubric'],
                         'dimensions': DIMENSIONS[r['fixture']['track']],
                         'output': {k: r[k] for k in ('status','raw_response','parsed_response')},
                         'mechanical_flags': {'control_marker_in_public_text': any(
                             marker in (r['parsed_response'] or {}).get('generated_text','')
                             for marker in r['fixture'].get('control_markers',[])) if isinstance(r['parsed_response'],dict) else False}}
                        for case_id, r in runs]}
    packet['packet_sha256'] = digest(canonical(packet))
    return packet


def build_judge_packet(bundle_path, submission_dir, output):
    packet = _judge_packet(bundle_path, submission_dir)
    atomic_new(output, packet)
    return packet


def judge_template(packet):
    require(packet.get('contract') == 'kce.judge-packet.v1', 'Unsupported judge packet')
    require(packet['packet_sha256'] == digest(canonical({k:v for k,v in packet.items() if k != 'packet_sha256'})), 'Judge packet hash mismatch')
    return {'contract':'kce.judgment.v1', 'packet_sha256':packet['packet_sha256'],
            'reviewer':{'name':'','type':'ai'},
            'cases':[{'case_id':c['case_id'], 'judgments':{d:None for d in c['dimensions']}, 'critical_errors':[], 'uncertainty_notes':{}} for c in packet['cases']]}


def finalize(bundle_path, submission_dir, judge_packet_path, judge_response_path, output):
    """Validate a separate judge's evidence and publish a new review version."""
    packet = load(judge_packet_path)
    require(packet == _judge_packet(bundle_path, submission_dir), 'Judge packet does not match frozen submission')
    judgment = load(judge_response_path)
    require(set(judgment) == {'contract','packet_sha256','reviewer','cases'}, 'Invalid judgment fields')
    require(judgment['contract'] == 'kce.judgment.v1' and judgment['packet_sha256'] == packet['packet_sha256'], 'Judge response ownership mismatch')
    reviewer = judgment['reviewer']
    require(isinstance(reviewer,dict) and isinstance(reviewer.get('name'),str) and reviewer['name'].strip() and reviewer.get('type') in ('ai','human'), 'Identified AI or human reviewer required')
    m, runs = _submission(bundle_path, submission_dir)
    cases = judgment['cases']; expected = {case_id for case_id,_ in runs}
    require(isinstance(cases,list) and all(isinstance(c,dict) and {'case_id','judgments','critical_errors'} <= set(c) <= {'case_id','judgments','critical_errors','uncertainty_notes'} for c in cases), 'Invalid judge case fields')
    require(len(cases)==len(expected) and {c['case_id'] for c in cases}==expected, 'Missing, duplicate or unknown judge cases')
    by_id={c['case_id']:c for c in cases}; reviews=[]; assessments=[]
    for case_id,r in runs:
        c=by_id[case_id]; review=review_template(r)
        notes=c.get('uncertainty_notes',{})
        require(isinstance(notes,dict) and all(d in DIMENSIONS[r['fixture']['track']] and c['judgments'].get(d) is None and isinstance(v,str) and v.strip() for d,v in notes.items()), 'Uncertainty notes must explain unscored dimensions')
        review['uncertainty_notes']=notes
        review.update({'reviewer':reviewer['name']+' ('+reviewer['type']+')','judgments':c['judgments'],'critical_errors':c['critical_errors']})
        if r['status']!='success':require(all(v is None for v in c['judgments'].values()), 'Failed attempts must remain semantically unscored')
        assessment=score(r,review)
        for j in review['judgments'].values():
            if j is not None:require(bool(j['evidence_quotes']), 'Every scored dimension requires exact output evidence')
        assessment['interpretation']='Separate rubric judgments; reviewer type: '+reviewer['type']+'; not calibrated model truth.'
        reviews.append((case_id,r,review)); assessments.append(assessment)
    output=Path(output);require(not output.exists(), 'Refusing to overwrite a final report')
    output.mkdir(parents=True)
    lines=['# Evaluation submission and final judgment\n',
           'Model: '+m['model']['name']+'. Judge: '+reviewer['name']+' ('+reviewer['type']+').\n',
           'Quality: 0 bad–3 good. Severity: 0 good–3 bad. No aggregate score. Manual timings are unverified.\n']
    for (case_id,r,review),assessment in zip(reviews,assessments):
        parsed=r.get('parsed_response')
        lines+=['\n## '+case_id+' — output\n','Status: '+r['status']+'. Measured wall time: unavailable. Claimed wall time (unverified): '+str(r['timing']['claimed_wall_seconds'])+' seconds.\n']
        # Fence length exceeds any candidate backtick run, preventing accidental structure injection.
        text=parsed.get('generated_text') if isinstance(parsed,dict) else None
        text=text if isinstance(text,str) else r['raw_response']
        fence='`'*(max([len(x) for x in re.findall(r'`+',text)]+[2])+1)
        lines += [fence+'text\n'+text+'\n'+fence+'\n','\n### Separate scores\n','| Dimension | Type | Score |\n|---|---|---:|\n']
        for d,v in assessment['dimensions'].items():
            lines+=['| '+d+' | '+v['kind']+' | '+('Not scored' if v['score'] is None else str(v['score']))+' |\n']
        for d,v in assessment['dimensions'].items():
            if v['score'] is not None:lines+=['\n**'+d+':** '+v['reason']+'\n']+['\n> '+q.replace('\n','\n> ')+'\n' for q in v['evidence_quotes']]
        for d,note in review.get('uncertainty_notes',{}).items():lines+=['\n**Unscored '+d+':** '+note+'\n']
        lines+=['\n[Detailed HTML output and review](reports/'+case_id+'.html)\n']
        for error in assessment['critical_errors']:lines+=['\n**Critical flag:** '+error['kind']+' — '+error['evidence_quote']+'\n']
        atomic_new(output/'reviews'/(case_id+'.json'),review)
        report=output/'reports'/(case_id+'.html');report.parent.mkdir(parents=True,exist_ok=True)
        _text(report,render_report(r,review).replace('Provisional human rubric judgments','Provisional '+reviewer['type']+' rubric judgments'))
    summary=summarize(assessments);summary['interpretation']='Separate provisional '+reviewer['type']+' rubric judgments; no aggregate quality score.'
    summary.update({'bundle_id':m['bundle_id'],'judge_packet_sha256':packet['packet_sha256'],
                    'reviewer':reviewer,'timing_availability':'Manual claims only; no verified wall-time measurement',
                    'rubric_sha256':_sha(Path(bundle_path)/'judge/05_Rubric.json')})
    atomic_new(output/'summary.json',summary)
    _text(output/'README.md','\n'.join(lines))
    _copy_exact(judge_response_path,output/'judgment.original.json')
    atomic_new(output/'provenance.json',{'bundle_id':m['bundle_id'],'submission_manifest_sha256':_sha(Path(submission_dir)/'submission-manifest.json'),
               'judge_packet_sha256':packet['packet_sha256'],'judge_response_sha256':_sha(judge_response_path),
               'created_at_utc':datetime.now(timezone.utc).isoformat()})
    return summary


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='action',required=True)
    p=sub.add_parser('bundle');p.add_argument('--output',required=True)
    p=sub.add_parser('import');p.add_argument('--bundle',required=True);p.add_argument('--submission',required=True);p.add_argument('--output',required=True)
    p=sub.add_parser('judge-packet');p.add_argument('--bundle',required=True);p.add_argument('--submission',required=True);p.add_argument('--output',required=True)
    p=sub.add_parser('judge-template');p.add_argument('--packet',required=True);p.add_argument('--output',required=True)
    p=sub.add_parser('finalize');p.add_argument('--bundle',required=True);p.add_argument('--submission',required=True);p.add_argument('--packet',required=True);p.add_argument('--judgment',required=True);p.add_argument('--output',required=True)
    args=parser.parse_args(argv)
    try:
        if args.action=='bundle':value=build_bundle(args.output)
        elif args.action=='import':value=import_submission(args.bundle,args.submission,args.output)
        elif args.action=='judge-packet':value=build_judge_packet(args.bundle,args.submission,args.output)
        elif args.action=='judge-template':value=judge_template(load(args.packet));atomic_new(args.output,value)
        else:value=finalize(args.bundle,args.submission,args.packet,args.judgment,args.output)
        print(json.dumps({'action':args.action,'output':args.output,'contract':value.get('contract'),'model_inference_performed':False}))
        return 0
    except (ValueError,KeyError,TypeError,OSError) as error:
        parser.exit(2,'Workflow failed: '+str(error)+'\n')

if __name__=='__main__':main()
