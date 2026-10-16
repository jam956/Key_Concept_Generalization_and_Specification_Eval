"""Read-only, work-scoped framework export; excludes drafts and historical scores."""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3

WORK='kissinger_strains_1963'
FIELDS={
    'style_operator_findings':['operator_key','operator_id','sequence_index','definition','transfer_boundary','status'],
    'operator_edges':['edge_key','source_operator_key','target_operator_key','relation'],
    'attractor_routes':['attractor_key','layer','route_type','operator_sequence_json','status','notes'],
    'writing_style_features':['feature_key','feature_type','feature_id','label','function','status'],
    'concept_basins':['basin_key','status'],
    'sentence_style_vectors':['vector_key','subject','actor_role','dynamical_vector_json','regime_field_json','transition_destination','rehydrated_statement','status'],
}

def file_hash(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for part in iter(lambda:stream.read(1048576),b''):h.update(part)
    return h.hexdigest()

def export_framework(database,work_key=WORK):
    database=Path(database).resolve()
    if not database.is_file():raise ValueError('Source database is missing')
    wal=Path(str(database)+'-wal')
    if wal.exists() and wal.stat().st_size:raise ValueError('Export requires a checkpointed source snapshot; do not checkpoint the original automatically')
    before=file_hash(database)
    with sqlite3.connect(database.as_uri()+'?mode=ro',uri=True) as conn:
        conn.row_factory=sqlite3.Row;conn.execute('PRAGMA query_only=ON');conn.execute('BEGIN')
        for table,columns in {'works':['work_key','author','title','year','pass_status'],**FIELDS}.items():
            schema={r[1] for r in conn.execute('PRAGMA table_info('+table+')')}
            if not set(columns).issubset(schema) or 'work_key' not in schema:raise ValueError('Unsupported source schema: '+table)
        work=conn.execute('SELECT work_key,author,title,year,pass_status FROM works WHERE work_key=?',(work_key,)).fetchone()
        if work is None:raise ValueError('Work not found')
        tables={}
        for table,columns in FIELDS.items():
            where='work_key=?'
            if table=='sentence_style_vectors':where+=" AND status='source_extracted_candidate'"
            query='SELECT '+','.join(columns)+' FROM '+table+' WHERE '+where+' ORDER BY '+columns[0]
            tables[table]=[dict(r) for r in conn.execute(query,(work_key,))]
    if file_hash(database)!=before:raise ValueError('Source changed during export')
    return {'contract':'kce.framework-snapshot.v1','work':dict(work),'source_database':{'filename':database.name,'bytes':database.stat().st_size,'sha256':before},'tables':tables,'limits':['Candidate extraction, not a validated answer key or a complete source article.','No original PDF, generated drafts, historical judge scores, credentials or personal machine paths are exported.','Only source_extracted_candidate sentence vectors are included; transfer-test-derived vectors are excluded.']}

def article_fixture(snapshot):
    if snapshot.get('contract')!='kce.framework-snapshot.v1':raise ValueError('Unsupported snapshot')
    if snapshot.get('work',{}).get('work_key')!=WORK:raise ValueError('This article fixture is scoped to Strains on the Alliance')
    framework={k:snapshot['tables'][k] for k in ['style_operator_findings','operator_edges','attractor_routes','sentence_style_vectors']}
    return {'id':'article-kissinger-river-alliance','track':'article','family':'optional-kissinger-framework','split':'dev','input':{
        'task':'Construct a new strategic article using the supplied analytical framework where the facts support it. Transfer relationships, not donor wording or historical facts. The subject is fictional.',
        'source_text':'[f1] Alder financed shared river-energy infrastructure for Bell and Rook. [f2] Bell can now fund its own upgrades but the old board still gives Alder approval over every project. [f3] Rook remains dependent on shared maintenance crews and fears service interruptions. [f4] A technically viable new grid plan does not settle how the three partners share approval authority. [f5] Bell requests more autonomy; Alder wants predictable joint operating standards. [f6] None of the partners has announced withdrawal. [f7] Future trust, investment and institutional outcomes are unknown.',
        'provided_framework':framework,'framework_provenance':{'work':snapshot['work'],'source_database_sha256':snapshot['source_database']['sha256'],'review_status':'candidate_annotations'},
        'target':'Write four to six paragraphs for a general reader. Preserve the different constraints of Alder, Bell and Rook. Diagnose before proposing conditional changes. Do not force an inevitability claim or guaranteed outcome. No internal operator IDs, scoring instructions or source-era actors belong in the public article.'},
        'rubric':{'required_relations':['Successful assistance enables Bell autonomy without establishing Rook independence.','Technical feasibility does not establish legitimacy of approval arrangements.','Proposals must be conditional and responsive to asymmetric interests.'],'overgeneralization_traps':['All recipients now independent','Withdrawal or trust restoration asserted as fact','Development declared irreversible without evidence'],'undergeneralization_traps':['Procurement-only summary misses governance/capacity mismatch'],'generation_checks':['An earned multi-paragraph argument, not an operator list','No imported source-era facts or unsupported real-world news'],'forbidden_source_carryover':['US-Soviet talks','Berlin Wall','de Gaulle'],'acceptable_alternatives':['Several conditional governance or consultation proposals can fit the bounded facts.'],'annotation_status':'provisional_needs_human_calibration'},
        'control_markers':['KCE_CONTROL_ONLY_RIVER_59D2']}

def write_new(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as stream:json.dump(value,stream,indent=2,ensure_ascii=False);stream.write('\n')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--database',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--work',default=WORK);p.add_argument('--article-fixture',type=Path)
    a=p.parse_args();snapshot=export_framework(a.database,a.work)
    if a.output.exists() or (a.article_fixture and a.article_fixture.exists()):p.error('Refusing to overwrite existing export')
    fixture=article_fixture(snapshot) if a.article_fixture else None
    write_new(a.output,snapshot)
    if a.article_fixture:write_new(a.article_fixture,fixture)
    print(json.dumps({'framework':str(a.output),'counts':{k:len(v) for k,v in snapshot['tables'].items()},'bytes':a.output.stat().st_size}))

if __name__=='__main__':main()
