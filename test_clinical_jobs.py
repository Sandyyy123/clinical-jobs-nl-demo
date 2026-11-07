import copy
import json
import unittest
from pathlib import Path
from clinical_jobs import LEIDEN, distance_km, canonical_url, process, render, csv_export

class DemoTests(unittest.TestCase):
    def setUp(self): self.rows=json.loads(Path(__file__).with_name('fixtures.json').read_text())
    def test_filter_and_duplicate_audit(self):
        r=process(self.rows)
        self.assertEqual([x['id'] for x in r['jobs']],['demo-01','demo-03','demo-04'])
        self.assertEqual({x['reason'] for x in r['excluded']},{'Duplicate requisition','Outside agreed Netherlands scope','Outside configured clinical-role terms'})
    def test_distance_units_and_validation(self):
        self.assertEqual(distance_km(*LEIDEN),0)
        self.assertTrue(30 < distance_km(52.34,4.88) < 40)
        self.assertIsNone(distance_km(None,None))
        for coords in [(91,0),(0,181),(float('nan'),0)]:
            with self.assertRaises(ValueError):distance_km(*coords)
    def test_identifying_query_preserved(self):
        self.assertNotEqual(canonical_url('https://jobs.example/?id=1'),canonical_url('https://jobs.example/?id=2'))
        self.assertEqual(canonical_url('https://jobs.example/x?utm_source=y&id=1'),'https://jobs.example/x?id=1')
    def test_missing_values_not_invented(self):
        r=process(self.rows)['jobs'];self.assertEqual(r[1]['benefits'],'Not stated');self.assertIsNone(r[2]['distance_km'])
    def test_source_script_rejected(self):
        with self.assertRaises(ValueError):canonical_url('javascript:alert(1)')
    def test_html_and_csv_injection(self):
        rows=copy.deepcopy(self.rows[:1]);rows[0]['company']='=1+2';rows[0]['benefits']='<script>alert(1)</script>'
        r=process(rows)
        self.assertIn("'=1+2",csv_export(r['jobs']))
        self.assertNotIn('<script>alert(1)</script>',render(r))
    def test_closed_record_is_excluded(self):
        self.rows[0]['status']='closed';self.assertIn('Not confirmed open',process(self.rows)['excluded'][0]['reason'])

if __name__=='__main__':unittest.main()
