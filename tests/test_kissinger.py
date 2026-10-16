import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from kce_eval.kissinger import FIELDS,export_framework,article_fixture,file_hash

class ExportTests(unittest.TestCase):
    def test_work_scoped_readonly_export_excludes_model_judgments_and_machine_paths(self):
        with tempfile.TemporaryDirectory() as folder:
            db=Path(folder)/'source.sqlite';c=sqlite3.connect(db)
            c.execute('create table works(work_key text,author text,title text,year integer,pass_status text,source_file text)')
            c.execute("insert into works values('kissinger_strains_1963','Kissinger','Strains',1963,'candidate','/private/user/document.pdf')")
            for table,fields in FIELDS.items():
                c.execute('create table '+table+'(work_key text,'+','.join(x+' text' for x in fields)+')')
                values=['kissinger_strains_1963']+['source_extracted_candidate' if x=='status' else x for x in fields]
                c.execute('insert into '+table+' values('+','.join('?' for _ in values)+')',values)
                values[0]='other_work';c.execute('insert into '+table+' values('+','.join('?' for _ in values)+')',values)
            c.execute("insert into sentence_style_vectors(work_key,status,vector_key) values('kissinger_strains_1963','candidate_toolset','model-derived')")
            c.commit();c.close();before=file_hash(db)
            snapshot=export_framework(db)
            self.assertEqual(file_hash(db),before)
            self.assertTrue(all(len(rows)==1 for rows in snapshot['tables'].values()))
            self.assertNotIn('/private/user',json.dumps(snapshot))
            self.assertNotIn('model-derived',json.dumps(snapshot))
            fixture=article_fixture(snapshot)
            self.assertEqual(fixture['track'],'article');self.assertIn('provided_framework',fixture['input'])
            self.assertNotIn('score',snapshot['tables'])
    def test_missing_work_or_schema_does_not_create_or_modify_source(self):
        with tempfile.TemporaryDirectory() as folder:
            db=Path(folder)/'missing.sqlite'
            with self.assertRaises(ValueError):export_framework(db)
            self.assertFalse(db.exists())
            sqlite3.connect(db).close();before=file_hash(db)
            with self.assertRaises(ValueError):export_framework(db)
            self.assertEqual(before,file_hash(db))
    def test_article_fixture_cannot_silently_use_another_work(self):
        with self.assertRaisesRegex(ValueError,'scoped'):
            article_fixture({'contract':'kce.framework-snapshot.v1','work':{'work_key':'different_work'}})

if __name__=='__main__':unittest.main()
