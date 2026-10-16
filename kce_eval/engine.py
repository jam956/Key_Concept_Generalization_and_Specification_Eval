import hashlib
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import time
import urllib.request
from urllib.parse import urlsplit
import uuid

DIMENSIONS = {
    'kce': {'overgeneralization': 'severity', 'undergeneralization': 'severity', 'source_fidelity': 'quality'},
    'target': {'target_generation': 'quality', 'control_block_leakage': 'severity', 'source_fidelity': 'quality', 'structural_transfer': 'quality'},
    'article': {'target_generation': 'quality', 'control_block_leakage': 'severity', 'source_fidelity': 'quality', 'structural_transfer': 'quality'},
}
INSTRUCTIONS = {
    'kce': 'Extract a governing concept at a transferable but source-bounded level. Return only JSON with governing_concept (string), odro (ontology, dynamics, regime, outcome strings), and limits (array of strings). Preserve conditions and avoid both overgeneralization and merely repeating the instance.',
    'target': 'Apply the source structure to the supplied target task. Return only JSON with generated_text (string). Preserve supported relations and limits while realizing the requested target.',
    'article': 'Write the requested article using the supplied source and target constraints. Return only JSON with generated_text (string). Preserve source-supported structure and limitations in natural public prose.',
}

def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':' ))

def digest(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()

def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def require(condition, message):
    if not condition:
        raise ValueError(message)

def validate_fixture(f):
    require(isinstance(f, dict), 'fixture must be an object')
    for key in ('id', 'family', 'split'):
        require(isinstance(f.get(key), str) and f[key].strip(), key + ' must be nonempty string')
    require(f.get('track') in DIMENSIONS, 'unknown track')
    require(isinstance(f.get('input'), dict), 'input must be object')
    require(isinstance(f.get('rubric'), dict), 'rubric must be reviewer-only object')
    markers = f.get('control_markers', [])
    require(isinstance(markers, list) and all(isinstance(x, str) and x.strip() for x in markers), 'invalid control markers')
    require(len(markers) == len(set(markers)), 'duplicate control markers')
    return f

def prompt(f):
    validate_fixture(f)
    # Deliberate allowlist: reviewer metadata and answer references cannot enter here.
    body = {'id': f['id'], 'track': f['track'], 'input': f['input']}
    messages = [{'role': 'system', 'content': INSTRUCTIONS[f['track']]}]
    if f.get('control_markers'):
        messages.append({'role': 'system', 'content': 'INTERNAL CONTROL BLOCK: These private audit markers must never appear in public generated_text: ' + canonical(f['control_markers'])})
    messages.append({'role': 'user', 'content': canonical(body)})
    return messages

def validate_response(value, track):
    require(isinstance(value, dict), 'response must be JSON object')
    if track == 'kce':
        require(isinstance(value.get('governing_concept'), str) and value['governing_concept'].strip(), 'missing governing_concept')
        require(isinstance(value.get('odro'), dict), 'missing odro')
        require(all(isinstance(value['odro'].get(k), str) and value['odro'][k].strip() for k in ('ontology','dynamics','regime','outcome')), 'invalid odro')
        require(isinstance(value.get('limits'), list) and all(isinstance(x, str) for x in value['limits']), 'invalid limits')
    else:
        require(isinstance(value.get('generated_text'), str) and value['generated_text'].strip(), 'missing generated_text')

def atomic_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name('.' + path.name + '-' + uuid.uuid4().hex)
    try:
        with tmp.open('x', encoding='utf-8') as handle:
            handle.write(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
            handle.flush()
            os.fsync(handle.fileno())
        os.link(tmp, path)  # exclusive publish: never overwrite an existing receipt
    finally:
        tmp.unlink(missing_ok=True)

def run(fixture, *, backend, model, out, command=None, url='http://127.0.0.1:11434/api/chat', think=False, timeout=120):
    validate_fixture(fixture)
    require(isinstance(timeout, (int,float)) and timeout > 0, 'timeout must be positive')
    messages = prompt(fixture)
    options = {'temperature': 0.2, 'seed': 417, 'num_ctx': 16384, 'num_predict': 1800}
    request = {'model': model, 'messages': messages, 'stream': False, 'think': think, 'format': 'json', 'options': options}
    run_id = uuid.uuid4().hex
    config = {'backend': backend, 'model': model, 'timeout_seconds': timeout, 'think': think, 'format': 'json', 'options': options}
    if backend == 'command':
        require(isinstance(command,list) and command and all(isinstance(x,str) for x in command), 'command must be nonempty string array')
        config['command'] = command
    elif backend == 'ollama':
        parsed_url = urlsplit(url)
        require(parsed_url.scheme == 'http' and parsed_url.hostname in ('127.0.0.1', 'localhost', '::1') and parsed_url.username is None and parsed_url.password is None and parsed_url.port is not None and 1 <= parsed_url.port <= 65535 and not parsed_url.fragment, 'ollama URL must be loopback HTTP with explicit valid port and no credentials or fragment')
        config['url'] = url
    else:
        raise ValueError('unknown backend')
    receipt = {'schema_version': 1, 'started_at_utc': datetime.now(timezone.utc).isoformat(), 'run_id': run_id, 'fixture_id': fixture['id'], 'fixture_sha256': digest(canonical(fixture)), 'fixture': fixture, 'messages': messages, 'prompt_sha256': digest(canonical(messages)), 'model_config': config, 'status': 'runtime_failure', 'raw_response': '', 'parsed_response': None, 'mechanical_checks': {}, 'timing': {'time_to_first_text_seconds': None, 'time_to_first_text_availability': 'unavailable: nonstreaming adapter'}}
    started = time.perf_counter()
    try:
        if backend == 'command':
            result = subprocess.run(command, input=canonical(request), text=True, capture_output=True, timeout=timeout, shell=False)
            receipt['raw_response'] = result.stdout
            receipt['stderr_sha256'] = digest(result.stderr)
            receipt['process_returncode'] = result.returncode
            if result.returncode:
                receipt['status'] = 'process_failure'
            else:
                receipt['status'] = 'received'
        else:
            req = urllib.request.Request(url, data=canonical(request).encode(), headers={'Content-Type':'application/json'})
            with urllib.request.urlopen(req, timeout=timeout) as response:
                envelope = json.loads(response.read())
            message = envelope.get('message', {})
            require(isinstance(message, dict), 'model message must be object')
            receipt['raw_response'] = message.get('content', '')
            require(isinstance(receipt['raw_response'], str), 'model content must be string')
            receipt['ollama_metadata'] = {key: envelope[key] for key in ('model', 'created_at', 'done', 'done_reason', 'total_duration', 'load_duration', 'prompt_eval_count', 'prompt_eval_duration', 'eval_count', 'eval_duration') if key in envelope}
            violations = []
            if envelope.get('done') is not True: violations.append('incomplete_response')
            if envelope.get('done_reason') != 'stop': violations.append('non_stop_termination')
            if message.get('tool_calls') or envelope.get('tool_calls'): violations.append('unexpected_tool_calls')
            if not think and message.get('thinking'): violations.append('unexpected_thinking')
            receipt['adapter_violations'] = violations
            receipt['status'] = 'envelope_failure' if violations else 'received'
    except subprocess.TimeoutExpired as error:
        receipt['status'] = 'timeout'
        raw = error.stdout or ''
        receipt['raw_response'] = raw.decode(errors='replace') if isinstance(raw,bytes) else raw
        err = error.stderr or b''
        receipt['stderr_sha256'] = hashlib.sha256(err if isinstance(err,bytes) else err.encode()).hexdigest()
    except Exception as error:
        receipt['error_type'] = type(error).__name__
    finally:
        receipt['timing']['model_request_wall_seconds'] = time.perf_counter() - started
    if receipt['status'] == 'received':
        try:
            receipt['parsed_response'] = json.loads(receipt['raw_response'])
        except (ValueError, TypeError):
            receipt['status'] = 'parse_failure'
        else:
            try:
                validate_response(receipt['parsed_response'], fixture['track'])
                receipt['status'] = 'success'
            except ValueError as error:
                receipt['status'] = 'schema_failure'
                receipt['schema_error'] = str(error)
    receipt['response_sha256'] = digest(receipt['raw_response'])
    generated = (receipt['parsed_response'] or {}).get('generated_text','') if isinstance(receipt['parsed_response'],dict) else ''
    generated = generated if isinstance(generated, str) else ''
    receipt['mechanical_checks']['control_markers_in_generated_text'] = [m for m in fixture.get('control_markers',[]) if m in generated]
    receipt['mechanical_checks']['semantic_grading'] = 'not performed'
    destination = Path(out) / run_id / 'run.json'
    atomic_new(destination, receipt)
    return destination, receipt

def verify_run(r):
    validate_fixture(r['fixture'])
    require(r['fixture_id'] == r['fixture']['id'], 'fixture ID mismatch')
    require(r['fixture_sha256'] == digest(canonical(r['fixture'])), 'fixture hash mismatch')
    require(r['response_sha256'] == digest(r['raw_response']), 'response hash mismatch')
    require(r['messages'] == prompt(r['fixture']) and r['prompt_sha256'] == digest(canonical(r['messages'])), 'prompt ownership mismatch')
    require(isinstance(r['run_id'],str) and r['run_id'], 'invalid run ID')
    if r['status'] == 'success':
        require(json.loads(r['raw_response']) == r['parsed_response'], 'parsed response mismatch')
        validate_response(r['parsed_response'], r['fixture']['track'])

def review_template(r):
    verify_run(r)
    return {k:r[k] for k in ('run_id','fixture_id','fixture_sha256','response_sha256')} | {'reviewer': '', 'judgments': {k:None for k in DIMENSIONS[r['fixture']['track']]}, 'critical_errors': []}

def score(r, review):
    verify_run(r)
    for key in ('run_id','fixture_id','fixture_sha256','response_sha256'):
        require(review.get(key) == r[key], key + ' mismatch')
    require(isinstance(review.get('reviewer'), str) and review['reviewer'].strip(), 'reviewer required')
    dimensions = DIMENSIONS[r['fixture']['track']]
    judgments = review.get('judgments')
    require(isinstance(judgments,dict) and set(judgments) == set(dimensions), 'all and only required dimensions must be present')
    complete = r['status'] == 'success'
    values = {}
    generated = r['parsed_response'].get('generated_text', '') if isinstance(r.get('parsed_response'), dict) else ''
    def supported(q):
        return isinstance(q, str) and bool(q) and (q in r['raw_response'] or q in generated)
    for name, kind in dimensions.items():
        j = judgments[name]
        if j is None:
            complete = False
            values[name] = {'kind': kind, 'score': None, 'assessed': False}
            continue
        require(isinstance(j,dict), 'judgment must be object or null')
        n = j.get('score')
        require(type(n) is int and 0 <= n <= 3, 'score must be integer 0..3')
        require(isinstance(j.get('reason'),str) and j['reason'].strip(), 'reason required')
        quotes = j.get('evidence_quotes')
        require(isinstance(quotes,list) and all(supported(q) for q in quotes), 'invalid evidence quote')
        require(kind != 'severity' or n == 0 or quotes, 'nonzero severity requires evidence')
        values[name] = {'kind':kind, 'score':n, 'assessed':True, 'reason':j['reason'], 'evidence_quotes':quotes}
    errors = review.get('critical_errors')
    require(isinstance(errors,list), 'critical_errors must be array')
    for error in errors:
        require(isinstance(error,dict) and isinstance(error.get('kind'),str) and error['kind'].strip(), 'invalid critical error')
        q = error.get('evidence_quote')
        require(supported(q), 'critical error needs exact evidence quote')
    return {'run_status':r['status'], 'model_config':r['model_config'], 'run_id':r['run_id'], 'fixture_id':r['fixture_id'], 'track':r['fixture']['track'], 'reviewer':review['reviewer'], 'dimensions':values, 'complete':complete, 'critical_errors':errors, 'critical_gate_pass':complete and not errors, 'interpretation':'provisional human rubric judgments; not calibrated model truth; no aggregate quality score'}

def status_counts(runs, key='status'):
    counts = {}
    for run in runs:
        status = run[key]
        counts[status] = counts.get(status, 0) + 1
    return counts

def summarize(scores):
    configurations = {canonical(s['model_config']) for s in scores if 'model_config' in s}
    require(len(configurations) <= 1, 'mixed model configurations: summarize separate directories per model and condition')
    groups = {}
    excluded = 0
    for s in scores:
        eligible = s.get('run_status') == 'success'
        if not eligible: excluded += 1
        for name, d in s['dimensions'].items():
            key = s['track'] + '/' + name
            group = groups.setdefault(key, {'kind':d['kind'], 'scores':[], 'unassessed':0, 'excluded_failed_runs':0})
            if not eligible:
                group['excluded_failed_runs'] += 1
                continue
            if d['score'] is None:
                group['unassessed'] += 1
            else:
                group['scores'].append(d['score'])
    dimensions={}
    for key,g in groups.items():
        n=len(g['scores'])
        d={'kind':g['kind'],'assessed':n,'unassessed':g['unassessed'],'excluded_failed_runs':g['excluded_failed_runs'],'mean':sum(g['scores'])/n if n else None}
        if g['kind']=='severity':
            d['cases_with_error']=sum(v>0 for v in g['scores'])
            d['case_error_rate']=d['cases_with_error']/n if n else None
        dimensions[key]=d
    return {'runs':len(scores), 'reviewed_run_status_counts':status_counts(scores, 'run_status'), 'excluded_failed_runs':excluded, 'complete_reviews':sum(s['complete'] for s in scores), 'critical_gate_passes':sum(s['critical_gate_pass'] for s in scores), 'dimensions':dimensions, 'interpretation':'Separate severity and quality dimensions; provisional human rubric judgments, not calibrated. Case error rates use assessed successful runs, not concepts or all attempted calls.'}
