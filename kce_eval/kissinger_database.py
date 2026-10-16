"""Create a source-free, work-scoped Kissinger retrieval database.

Contract: preserve scoped analytical IDs and required graph neighbors; exclude
operational history, generated transfer lessons, source text and document locators.
"""
import argparse
import hashlib
import json
import re
import sqlite3
from pathlib import Path

SCOPED = '''works concept_basins style_operator_findings operator_edges
writing_style_features compatibility_edges attractor_routes sentence_style_vectors
expression_pages expression_page_links expression_object_concept_links
expression_invariant_links fiction_narrative_units fiction_storycraft_annotations
fiction_author_engines fiction_thought_vectors fiction_surface_profiles
fiction_surface_observations fiction_surface_lexicon_terms fiction_domain_evidence'''.split()
SHARED = '''expression_concept_units expression_concept_edges universal_invariant_basins
universal_regime_slots universal_regime_families fiction_delivery_domains'''.split()
DROP = {'source_file','source_schema_path','source_locator_json','source_span',
        'evidence_json','source_field','source_run_key','extraction_run_key',
        'short_excerpt','context_before','context_after','source_hash'}
BAD_KEY = re.compile(r'(?:source_(?:span|text|file|path|url|uri|locator|document|schema|pointer|ref|title|key|note)|(?:^|_)(?:quote|quotation|excerpt|artifact_dir|report_path|document_path|document_pointer|span_text)(?:$|_))',re.I)
POINTER = re.compile(r'(?:https?://|gdrive://|file://|/Users/|(?:^|\s)(?:Expressions|sources|reports)/|[^\s]+\.(?:pdf|docx?|epub)(?:\b|$))',re.I)

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def clean(value):
    if isinstance(value,dict):return {k:clean(v) for k,v in value.items() if not BAD_KEY.search(k)}
    if isinstance(value,list):return [clean(v) for v in value]
    if isinstance(value,str) and POINTER.search(value):return ''
    return value

def rows(c,t):return [dict(r) for r in c.execute('SELECT * FROM "'+t+'"')]

def validate_route_sequences(routes, operators):
    """Resolve source-native operator labels in each work's own namespace."""
    operator_ids={(r['work_key'],r['operator_id']) for r in operators}
    for route in routes:
        if any((route['work_key'],label) not in operator_ids for label in json.loads(route['operator_sequence_json'])):
            raise ValueError('Unresolved route operator label')

def export(source,destination,receipt):
    source=Path(source).resolve();destination=Path(destination);receipt=Path(receipt)
    if destination.exists() or receipt.exists():raise ValueError('Refusing to overwrite an export')
    if Path(str(source)+'-wal').exists() and Path(str(source)+'-wal').stat().st_size:raise ValueError('Source must be a checkpointed snapshot')
    before=digest(source)
    c=sqlite3.connect(source.as_uri()+'?mode=ro',uri=True);c.row_factory=sqlite3.Row
    c.execute('PRAGMA query_only=ON');c.execute('BEGIN')
    workkeys={r[0] for r in c.execute("SELECT work_key FROM works WHERE author IN ('Henry A. Kissinger','Henry A. Kissinger and Cyrus Vance')")}
    if len(workkeys)!=28:raise ValueError('Expected the reviewed 28-work corpus')
    marks=','.join('?' for _ in workkeys)
    selected={t:[dict(r) for r in c.execute('SELECT * FROM "'+t+'" WHERE work_key IN ('+marks+')',sorted(workkeys))] for t in SCOPED}
    excluded={r['vector_key'] for r in selected['sentence_style_vectors'] if r['status'] not in ('source_extracted_candidate','source_anchored_corpus_pass')}
    selected['sentence_style_vectors']=[r for r in selected['sentence_style_vectors'] if r['vector_key'] not in excluded]
    # Exclude the mirrored units/vectors and their dependent observations as well.
    excluded_units={'unit::sentence_style_vector::'+k for k in excluded}
    excluded_thoughts={'thought::'+k for k in excluded}
    for t in SCOPED:
        selected[t]=[r for r in selected[t] if r.get('unit_key') not in excluded_units and r.get('vector_key') not in excluded_thoughts]
    enginekeys={r['engine_key'] for r in selected['fiction_author_engines']}
    for t in ('fiction_engine_parameters','fiction_surface_bindings'):
        selected[t]=[dict(r) for r in c.execute('SELECT * FROM '+t+' WHERE engine_key IN ('+','.join('?' for _ in enginekeys)+')',sorted(enginekeys))] if t=='fiction_engine_parameters' else [dict(r) for r in c.execute('SELECT * FROM '+t+' WHERE surface_profile_key IN ('+','.join('?' for _ in selected['fiction_surface_profiles'])+')',[r['surface_profile_key'] for r in selected['fiction_surface_profiles']])]
        selected[t]=[r for r in selected[t] if r.get('vector_key') not in excluded_thoughts and not any(k in excluded_units for k in json.loads(r.get('evidence_unit_keys_json') or '[]'))]
    for r in selected['fiction_surface_lexicon_terms']:
        r['evidence_unit_keys_json']=json.dumps([k for k in json.loads(r['evidence_unit_keys_json']) if k not in excluded_units])
    selected['fiction_surface_lexicon_terms']=[r for r in selected['fiction_surface_lexicon_terms'] if json.loads(r['evidence_unit_keys_json'])]
    concepts={r['concept_id'] for r in selected['expression_object_concept_links'] if r['object_key'] not in excluded}
    edges=rows(c,'expression_concept_edges')
    # One-hop semantic neighborhood, then induced edges: preserve the shared hub
    # without traversing through it into unrelated work neighborhoods.
    adjacent=[r for r in edges if r['src_concept_id'] in concepts or r['dst_concept_id'] in concepts]
    concepts.update(r[k] for r in adjacent for k in ('src_concept_id','dst_concept_id'))
    selected['expression_concept_units']=[r for r in rows(c,'expression_concept_units') if r['concept_id'] in concepts]
    selected['expression_concept_edges']=[r for r in edges if r['src_concept_id'] in concepts and r['dst_concept_id'] in concepts]
    links=selected['expression_invariant_links']
    invariants={r['invariant_id'] for r in links};slots={r['slot_id'] for r in links if r['slot_id']}
    selected['universal_regime_slots']=[r for r in rows(c,'universal_regime_slots') if r['slot_id'] in slots]
    invariants.update(r['invariant_id'] for r in selected['universal_regime_slots'])
    selected['universal_invariant_basins']=[r for r in rows(c,'universal_invariant_basins') if r['invariant_id'] in invariants]
    families={r['regime_family'] for r in selected['universal_regime_slots']}
    selected['universal_regime_families']=[r for r in rows(c,'universal_regime_families') if r['regime_family'] in families]
    domains={r['domain_key'] for r in selected['fiction_domain_evidence']}
    selected['fiction_delivery_domains']=[r for r in rows(c,'fiction_delivery_domains') if r['domain_key'] in domains]
    # Every polymorphic edge must point to an exported analytical object.
    def object_ids():
        return {str(r[col[1]]) for t,rs in selected.items() for col in c.execute('PRAGMA table_info("'+t+'")') if col[5] for r in rs}
    ids=object_ids();pruned={}
    checks={'expression_object_concept_links':['object_key'], 'expression_invariant_links':['source_key'],
            'compatibility_edges':['source_key','target_key'],'expression_pages':['primary_subject_key'],'expression_page_links':['source_page_key','target_page_key']}
    for t,cols in checks.items():
        old=selected[t];selected[t]=[r for r in old if all(r[k] in ids for k in cols)]
        pruned[t]=len(old)-len(selected[t])
    # Keep analytical route member lists inside the exported identity set.
    for r in selected['attractor_routes']:
        for k in ('member_keys_json',):
            v=json.loads(r[k])
            if isinstance(v,list):r[k]=json.dumps([x for x in v if not isinstance(x,str) or x in ids])
    # Remove any page links targeting pages discarded by the ownership filter.
    ids=object_ids()
    selected['expression_page_links']=[r for r in selected['expression_page_links'] if r['source_page_key'] in ids and r['target_page_key'] in ids]
    columns={t:[r for r in c.execute('PRAGMA table_info("'+t+'")') if r[1] not in DROP and not (t=='sentence_style_vectors' and r[1]=='source_key')] for t in selected}
    # Keep only FK constraints whose tables and fields are exported.
    foreign={}
    for t in selected:
        foreign[t]=[r for r in c.execute('PRAGMA foreign_key_list("'+t+'")') if r[2] in columns and r[3] in {x[1] for x in columns[t]} and r[4] in {x[1] for x in columns[r[2]]}]
    destination.parent.mkdir(parents=True,exist_ok=True)
    out=sqlite3.connect(destination);out.execute('PRAGMA foreign_keys=OFF')
    for t,cs in columns.items():
        definitions=['"'+r[1]+'" '+r[2]+(' PRIMARY KEY' if r[5] else '') for r in cs]
        definitions+=['FOREIGN KEY("'+r[3]+'") REFERENCES "'+r[2]+'"("'+r[4]+'")' for r in foreign[t]]
        out.execute('CREATE TABLE "'+t+'" ('+','.join(definitions)+')')
    sanitized={}
    for t,rs in selected.items():
        names=[r[1] for r in columns[t]];sanitized[t]=[]
        for row in rs:
            new={}
            for k in names:
                v=row[k]
                if k.endswith('_json') and v:
                    v=json.dumps(clean(json.loads(v)),ensure_ascii=False,sort_keys=True)
                else:v=clean(v)
                new[k]=v
            sanitized[t].append(new)
        if rs:out.executemany('INSERT INTO "'+t+'" ('+','.join('"'+n+'"' for n in names)+') VALUES ('+','.join('?' for _ in names)+')',([r[n] for n in names] for r in sanitized[t]))
    for t,cs in columns.items():
        for r in cs:
            if r[1] in ('work_key','concept_id','src_concept_id','dst_concept_id','invariant_id','slot_id','object_key','source_operator_key','target_operator_key') and not r[5]:
                out.execute('CREATE INDEX "idx_'+t+'_'+r[1]+'" ON "'+t+'"("'+r[1]+'")')
    out.commit()
    fk=out.execute('PRAGMA foreign_key_check').fetchall()
    if fk:raise ValueError('Foreign key failures: '+str(fk[:10]))
    if out.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('Integrity failed')
    # Exact result comparison for every retained source-derived analytical row,
    # including JSON structures after declared sanitization.
    for t,expected in sanitized.items():
        out.row_factory=sqlite3.Row
        actual=[dict(r) for r in out.execute('SELECT * FROM "'+t+'"')]
        key=lambda r:json.dumps(r,sort_keys=True,ensure_ascii=False)
        if sorted(map(key,actual))!=sorted(map(key,expected)):raise ValueError('Retrieval mismatch '+t)
    # Validate internal graph addresses that SQLite cannot express as FKs.
    ids=object_ids()
    ref_fields={'sentence_style_vectors':['attractor_keys_json'], 'attractor_routes':['member_keys_json'], 'fiction_surface_lexicon_terms':['evidence_unit_keys_json'], 'fiction_engine_parameters':['evidence_unit_keys_json'], 'fiction_narrative_units':['parent_unit_key'], 'fiction_domain_evidence':['parameter_key','vector_key','unit_key'], 'fiction_surface_bindings':['vector_key','parameter_key','surface_profile_key','domain_key']}
    for t,fields in ref_fields.items():
        for row in selected[t]:
            for field in fields:
                v=row[field];vs=json.loads(v) if field.endswith('_json') and v else [v]
                if any(isinstance(x,str) and x and x not in ids for x in vs):raise ValueError('Unresolved graph address '+t+'.'+field)
    # Route sequences use per-work operator_id labels, not operator_key PKs.
    validate_route_sequences(selected['attractor_routes'],selected['style_operator_findings'])
    # Concrete consumer query: work -> operator -> operator neighbors.
    operator_query='''SELECT w.work_key,o.operator_key,e.target_operator_key FROM works w JOIN style_operator_findings o USING(work_key) JOIN operator_edges e ON e.source_operator_key=o.operator_key ORDER BY 1,2,3'''
    if [tuple(r) for r in out.execute(operator_query)]!=[tuple(r) for r in c.execute(operator_query.replace('ORDER BY',"WHERE w.author IN ('Henry A. Kissinger','Henry A. Kissinger and Cyrus Vance') ORDER BY"))]:raise ValueError('Operator traversal parity failed')
    route_query='SELECT work_key,attractor_key,operator_sequence_json,member_keys_json FROM attractor_routes'
    original_routes={tuple(r) for r in c.execute(route_query) if r['work_key'] in workkeys}
    # Compare decoded JSON: exporter canonicalizes whitespace only.
    normalize=lambda r:(r[0],r[1],json.dumps(json.loads(r[2]),sort_keys=True),json.dumps(json.loads(r[3]),sort_keys=True))
    if {normalize(r) for r in out.execute(route_query)}!={normalize(r) for r in original_routes}:raise ValueError('Route sequence parity failed')
    # Concept lookup and invariant traversal must resolve all retained references.
    for q in ["SELECT count(*) FROM expression_object_concept_links l LEFT JOIN expression_concept_units n USING(concept_id) WHERE n.concept_id IS NULL", "SELECT count(*) FROM expression_invariant_links l LEFT JOIN universal_invariant_basins n USING(invariant_id) WHERE n.invariant_id IS NULL"]:
        if out.execute(q).fetchone()[0]:raise ValueError('Unresolved shared node')
    pointer_hits=[]
    for t in sanitized:
        for r in out.execute('SELECT * FROM "'+t+'"'):
            for k in r.keys():
                if isinstance(r[k],str) and POINTER.search(r[k]):pointer_hits.append([t,k])
    if pointer_hits:raise ValueError('Document pointer scan failed '+str(pointer_hits[:5]))
    out.execute('VACUUM');out.close();c.close()
    if digest(source)!=before:raise ValueError('Original source changed')
    report={'contract':'kce.kissinger-database.v1','source_sha256':before,'database_sha256':digest(destination),'database_bytes':destination.stat().st_size,
            'counts':{t:len(rs) for t,rs in sanitized.items()},'excluded_transfer_vectors':sorted(excluded),'pruned_unexported_object_links':pruned,
            'verification':{'source_unchanged':True,'sqlite_integrity':'ok','foreign_key_violations':0,'all_retained_row_retrieval_parity':True,'operator_traversal_parity':True,'route_sequence_parity':True,'shared_node_orphans':0,'document_pointer_pattern_hits':0},
            'policy':{'excluded':['source spans, locators, evidence payloads and document pointers','historical drafts, scores and operational runs','transfer-test-derived lesson vectors','cross-corpus clusters and external system bridges'], 'shared_graph':'Scoped concept links plus one-hop concept neighbors and induced edges; linked invariant slots, families and delivery domains.', 'limits':['Candidate annotations are not validated gold.','Conceptual summaries and authored analytical expressions remain; this is not a guarantee of no phrase overlap with the original works.','No transitive traversal through shared hubs into unrelated work neighborhoods.']}}
    receipt.parent.mkdir(parents=True,exist_ok=True);receipt.write_text(json.dumps(report,indent=2)+'\n')
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',required=True);p.add_argument('--output',required=True);p.add_argument('--receipt',required=True)
    a=p.parse_args();print(json.dumps(export(a.source,a.output,a.receipt),indent=2))
if __name__=='__main__':main()
