"""New capture packets cannot turn incomplete checks into a finished report."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from tools.review_coverage import validate_packet, validate_cross_page, validate_sticky_cta
from tools.review_io import file_hash, write_json


class PacketCoverageTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        (self.root/'image.png').write_bytes(b'fixture')
        self.capture={'schema_version':2,'status':'complete','files':{'image.png':file_hash(self.root/'image.png')},
            'required_checks':[{'id':i} for i in ('content_and_visuals','faq:1','control:1')]}
        self.capture.update({k:'image.png' for k in ('full_page','text_file','index','faq_file')})
        self.path=self.root/'manifest.json';write_json(self.path,self.capture)
        self.checks={'manifest_sha256':file_hash(self.path),'checks':[
            {'id':c['id'],'status':'pass','reason':'Compared fixture evidence'} for c in self.capture['required_checks']]}
        self.check_path=self.root/'checks.json';write_json(self.check_path,self.checks)
        self.entry={'checks_file':str(self.check_path)}
    def validate(self):
        write_json(self.check_path,self.checks)
        validate_packet(self.entry,self.capture,self.path,{'T1','D1'})
    def test_complete_checks_allowed(self): self.validate()
    def test_unhashed_artifact_reference_rejected(self):
        self.capture['index']='other.json'
        with self.assertRaisesRegex(ValueError,'Every referenced'):self.validate()
    def test_pending_blocked_and_missing_faq_rejected(self):
        for status in ('pending','blocked'):
            self.checks['checks'][1]['status']=status
            with self.assertRaisesRegex(ValueError,'pending, blocked'):self.validate()
        self.checks['checks'].pop(1)
        with self.assertRaisesRegex(ValueError,'exactly once'):self.validate()
    def test_exclusions_allowed_only_for_controls_with_reason(self):
        self.checks['checks'][2]['status']='not_applicable';self.validate()
        self.checks['checks'][2]['reason']=''
        with self.assertRaisesRegex(ValueError,'reason'):self.validate()
        self.checks['checks'][0]['status']='not_applicable'
        with self.assertRaisesRegex(ValueError,'invalid'):self.validate()
    def test_issue_must_point_to_real_finding_or_decision(self):
        check=self.checks['checks'][1];check['status']='issue';check['finding_ids']=['unknown']
        with self.assertRaisesRegex(ValueError,'existing finding'):self.validate()
        check['finding_ids']=['T1','D1'];self.validate()
    def test_capture_or_review_changes_invalidate_completion(self):
        self.checks['manifest_sha256']='old'
        with self.assertRaisesRegex(ValueError,'different capture'):self.validate()
        self.checks['manifest_sha256']=file_hash(self.path)
        (self.root/'image.png').write_bytes(b'changed')
        with self.assertRaises(ValueError):self.validate()
        self.capture['status']='incomplete'
        with self.assertRaisesRegex(ValueError,'incomplete'):self.validate()
    def test_cross_page_checks_required(self):
        with self.assertRaisesRegex(ValueError,'cross_page_checks'):validate_cross_page({},set())
        meta={'cross_page_checks':{name:{'status':'pass','reason':'Compared all occurrences'} for name in ('guarantee','pricing')}}
        validate_cross_page(meta,set())
        meta['cross_page_checks']['pricing']['status']='blocked'
        with self.assertRaisesRegex(ValueError,'blocked'):validate_cross_page(meta,set())

    def test_sticky_presence_cannot_be_hidden_in_generic_pass(self):
        states=[{'state':s,'image':s+'.png'} for s in
                ('top','after_hero','middle','bottom','up_middle','up_top')]
        capture={'sticky_states':states}
        check={'status':'pass','present':False,'evidence_files':[s['image'] for s in states]}
        with self.assertRaisesRegex(ValueError,'must be an issue'):
            validate_sticky_cta(check,{'side':'ours'},capture)
        # Missing source CTA is an observation, not a requirement on the competitor.
        validate_sticky_cta(check,{'side':'competitor'},capture)
        check.update(status='issue')
        validate_sticky_cta(check,{'side':'ours'},capture)
        check.update(status='pass',present=True,placement='bottom',
                     scroll_behavior='Visible through body; hides at main CTA',
                     click_result='Opened correct product',actual_destination='https://example.test/product')
        validate_sticky_cta(check,{'side':'ours'},capture)
        check['placement']='top'
        with self.assertRaisesRegex(ValueError,'viewport bottom'):
            validate_sticky_cta(check,{'side':'ours'},capture)
        check['placement']='bottom';check['actual_destination']=''
        with self.assertRaisesRegex(ValueError,'click destination'):
            validate_sticky_cta(check,{'side':'ours'},capture)
        capture['sticky_states']=states[:1]
        with self.assertRaisesRegex(ValueError,'down/up'):
            validate_sticky_cta(check,{'side':'ours'},capture)


if __name__=='__main__': unittest.main()
