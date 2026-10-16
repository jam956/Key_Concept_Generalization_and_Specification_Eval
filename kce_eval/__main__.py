import argparse
import json
from pathlib import Path
import sys
from .engine import canonical, require, status_counts, load, validate_fixture, prompt, run, review_template, score, summarize, atomic_new


def main(argv=None):
    parser = argparse.ArgumentParser(description='Source-bounded KCE and generation evaluation; semantic scores require human review.')
    commands = parser.add_subparsers(dest='action', required=True)
    p = commands.add_parser('validate'); p.add_argument('fixtures')
    p = commands.add_parser('prompt'); p.add_argument('fixture')
    p = commands.add_parser('run'); p.add_argument('fixture'); p.add_argument('--backend', choices=['command','ollama'], required=True); p.add_argument('--command-json'); p.add_argument('--model', required=True); p.add_argument('--out', required=True); p.add_argument('--url', default='http://127.0.0.1:11434/api/chat'); p.add_argument('--think', choices=['true','false'], default='false'); p.add_argument('--timeout', type=float, default=120)
    p = commands.add_parser('review-template'); p.add_argument('result'); p.add_argument('--output', required=True)
    p = commands.add_parser('score'); p.add_argument('result'); p.add_argument('review')
    p = commands.add_parser('summarize'); p.add_argument('results'); p.add_argument('reviews')
    args = parser.parse_args(argv)
    try:
        if args.action == 'validate':
            path = Path(args.fixtures)
            files = sorted(path.rglob('*.json')) if path.is_dir() else [path]
            ids = set()
            for file in files:
                f = validate_fixture(load(file))
                if f['id'] in ids: raise ValueError('duplicate fixture ID: ' + f['id'])
                ids.add(f['id'])
            if not files: raise ValueError('no fixture files')
            value = {'valid':True, 'fixtures':len(files)}
        elif args.action == 'prompt':
            value = {'messages':prompt(load(args.fixture))}
        elif args.action == 'run':
            path, result = run(load(args.fixture), backend=args.backend, model=args.model, out=args.out, command=json.loads(args.command_json) if args.command_json else None, url=args.url, think=args.think == 'true', timeout=args.timeout)
            print(json.dumps({'result':str(path), 'status':result['status']}))
            return 0 if result['status'] == 'success' else 1
        elif args.action == 'review-template':
            atomic_new(args.output, review_template(load(args.result)))
            value = {'output':args.output}
        elif args.action == 'score':
            value = score(load(args.result), load(args.review))
        else:
            runs = [load(p) for p in sorted(Path(args.results).rglob('run.json'))]
            require(len({canonical(r['model_config']) for r in runs}) <= 1, 'mixed model configurations: summarize separate directories per model and condition')
            by_id = {r['run_id']:r for r in runs}
            reviews = [load(p) for p in sorted(Path(args.reviews).rglob('*.json'))]
            seen = set(); scores = []
            for review in reviews:
                key = review.get('run_id')
                if key not in by_id: raise ValueError('review references unknown run')
                if key in seen: raise ValueError('duplicate review for run')
                seen.add(key); scores.append(score(by_id[key],review))
            value = summarize(scores)
            value['runs_without_review'] = len(runs) - len(seen)
            value['all_run_status_counts'] = status_counts(runs)
            value['unreviewed_run_status_counts'] = status_counts([r for r in runs if r['run_id'] not in seen])
        print(json.dumps(value, indent=2, ensure_ascii=False))
        return 0
    except (ValueError, KeyError, OSError, TypeError) as error:
        print(json.dumps({'error':str(error)}), file=sys.stderr)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
