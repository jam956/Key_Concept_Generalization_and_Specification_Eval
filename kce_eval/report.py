"""Output-first, offline HTML review of one verified evaluation receipt."""
import argparse
from html import escape
import json
from pathlib import Path

from .engine import DIMENSIONS, load, score, verify_run


def _text(value):
    return escape(str(value), quote=True)


def _json(value):
    return _text(json.dumps(value, ensure_ascii=False, indent=2))


def render_report(receipt, review=None):
    """Return HTML only after validating receipt and any supplied review."""
    verify_run(receipt)
    assessment = score(receipt, review) if review is not None else None
    parsed = receipt.get('parsed_response')
    generated = parsed.get('generated_text') if isinstance(parsed, dict) else None
    parts = ['<!doctype html><html lang="en"><head><meta charset="utf-8">',
             '<meta name="viewport" content="width=device-width, initial-scale=1">',
             '<title>Evaluation output and review</title><style>',
             'body{max-width:960px;margin:2rem auto;padding:0 1rem;font:17px/1.6 system-ui;color:#17212b;background:#faf9f5}',
             'pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#fff;padding:1rem;border:1px solid #d8d8d0}',
             'article,details{margin:1rem 0}blockquote{border-left:3px solid #777;padding-left:1rem;white-space:pre-wrap}',
             'a{color:#145b8c}h2{margin-top:2rem}</style></head><body>',
             '<h1>Evaluation output and review</h1>',
             '<section id="model-output"><h2>Model output</h2>']
    if isinstance(generated, str):
        parts += ['<h3>Decoded generated_text</h3><pre id="decoded-output">', _text(generated), '</pre>']
    if receipt['fixture']['track'] == 'kce' and isinstance(parsed, dict):
        parts += ['<h3>Parsed KCE JSON</h3><pre>', _json(parsed), '</pre>']
    parts += ['<h3>Exact raw model response</h3><pre id="raw-output">', _text(receipt['raw_response']), '</pre></section>',
              '<section id="scores"><h2>Independent dimension scores</h2>',
              '<p>Severity: 0 good, 3 bad. Quality: 0 bad, 3 good. Dimensions stay separate; no aggregate score.</p>']
    if assessment is None:
        parts += ['<p><strong>Not scored</strong> — no review supplied. Critical gate: not assessed.</p>']
    else:
        parts += ['<p>Reviewer: ', _text(assessment['reviewer']), '. Review complete: ',
                  _text(assessment['complete']), '. Critical gate: ',
                  'pass' if assessment['critical_gate_pass'] else 'not passed', '.</p>']

    def evidence(quote):
        target = 'decoded-output' if isinstance(generated, str) and quote in generated else 'raw-output'
        source = generated if target == 'decoded-output' else receipt['raw_response']
        start = source.find(quote)
        context = source[max(0, start - 100):start + len(quote) + 100]
        return ('<blockquote>' + _text(quote) + '</blockquote><p><a href="#' + target +
                '">Exact quote in model output</a></p><details><summary>Surrounding output context</summary><pre>' +
                _text(context) + '</pre></details>')

    for name, kind in DIMENSIONS[receipt['fixture']['track']].items():
        judgment = assessment['dimensions'][name] if assessment else None
        parts += ['<article><h3>', _text(name), '</h3><p>', _text(kind), ': ']
        if judgment is None or judgment['score'] is None:
            parts += ['<strong>Not scored</strong> (null).</p>']
        else:
            parts += ['<strong>', str(judgment['score']), ' / 3</strong></p><p>', _text(judgment['reason']), '</p>']
            parts.extend(evidence(q) for q in judgment['evidence_quotes'])
        parts += ['</article>']
    parts += ['<h3>Critical errors</h3>']
    if assessment is None:
        parts += ['<p>Not assessed.</p>']
    elif not assessment['critical_errors']:
        parts += ['<p>None recorded in this review.</p>']
    else:
        for error in assessment['critical_errors']:
            parts += ['<article><h4>', _text(error['kind']), '</h4>', evidence(error['evidence_quote']),
                      '<details><summary>Full critical error annotation</summary><pre>', _json(error), '</pre></details></article>']
    parts += ['<p>Provisional human rubric judgments; not calibrated model truth.</p></section>',
              '<section><h2>Runtime</h2><p>Status: ', _text(receipt['status']),
              '</p><p>Model request wall time (seconds): ',
              _text(receipt.get('timing', {}).get('model_request_wall_seconds')), '</p></section>']
    for title, value in (
        ('Fixture and source context (includes reviewer-only annotations)', receipt['fixture']),
        ('Run metadata and mechanical checks', {k: v for k, v in receipt.items() if k not in ('fixture', 'messages', 'raw_response', 'parsed_response')}),
        ('Exact model messages', receipt['messages']),
        ('Review record', review),
    ):
        parts += ['<details><summary>', _text(title), '</summary><pre>', _json(value), '</pre></details>']
    parts += ['</body></html>\n']
    return ''.join(parts)


def write_report(result, output, review=None):
    """Verify inputs before exclusively creating a new UTF-8 HTML file."""
    html = render_report(load(result), load(review) if review is not None else None)
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('x', encoding='utf-8') as handle:
        handle.write(html)
    return destination


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('result', help='run.json receipt')
    parser.add_argument('--review', help='hash-bound review JSON')
    parser.add_argument('--output', required=True, help='new standalone HTML file')
    args = parser.parse_args(argv)
    try:
        write_report(args.result, args.output, args.review)
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.exit(2, f'Cannot create report: {error}\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
