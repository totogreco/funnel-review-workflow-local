# -*- coding: utf-8 -*-
"""Regression checks for exact occurrences, batches and evidence invalidation."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image, ImageChops
from tools.annotate_screenshot import annotate, annotate_batch
from tools.locate_evidence import candidates, locate, locate_many, load_index, normalized, text_regions
from tools.review_io import file_hash, write_json


class EvidencePipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.image = self.root/'full.png'; Image.new('RGB',(780,2400),'white').save(self.image)
        text = '🙂 Prijs €177–€399 per jaar. Prijs €177 per jaar.'
        tokens = []
        for pos, word in enumerate(text.split()):
            start = text.find(word, tokens[-1]['end'] if tokens else 0)
            tokens.append({'start':start,'end':start+len(word),'rects':[
                {'x':20+(pos%4)*70,'y':100+(pos//4)*30,'w':60,'h':20}]})
        block = {'id':'b1','text':text,'heading':'Costs','rect':{'x':20,'y':100,'w':300,'h':80},'tokens':tokens}
        self.index = {'schema_version':2,'snapshot_id':'snap','image':'full.png','image_size':[780,2400],
            'device_scale_factor':2,'origin':{'x':0,'y':0},'files':{'full.png':file_hash(self.image)},'blocks':[block]}
        self.path=self.root/'index.json';write_json(self.path,self.index)

    def job(self, name='one'):
        return locate(self.path,{'id':name,'find':'€177 per jaar'},self.root/(name+'.png'))

    def test_typography_normalization_preserves_unicode_offsets(self):
        text, offsets=normalized('🙂 It’s\u00a0  €177–€399\u200b')
        self.assertEqual(text,"🙂 It's €177-€399")
        self.assertEqual(offsets[-1],17)
        job=self.job();self.assertEqual(job['observed_text'],'€177 per jaar')
        self.assertEqual(job['review_status'],'pending_visual_review')

    def test_wrapped_passage_has_one_frame_and_no_strokes_between_lines(self):
        # Font range bounds may be taller than line spacing, as in the FAQ.
        block=self.index['blocks'][0]
        block['text']='First second third'
        block['tokens']=[{'start':a,'end':b,'rects':[{'x':30,'y':100+n*21.5,'w':140+n*10,'h':25}]}
                         for n,(a,b) in enumerate([(0,5),(6,12),(13,18)])]
        write_json(self.path,self.index)
        for color in ['red','green']:
            job=locate(self.path,{'id':color,'find':block['text'],'color':color},self.root/(color+'.png'))
            self.assertEqual(job['highlights'],[[50,190,340,156]])
            annotate_batch({'schema_version':2,'jobs':[job]},self.root/(color+'.json'))
            with Image.open(job['output_path']) as output:
                # Clear inside the entire paragraph, including every line boundary.
                self.assertEqual(output.crop((60,200,380,336)).getextrema(),((255,255),)*3)

    def test_separate_paragraphs_and_columns_do_not_become_one_frame(self):
        rects=[{'x':20,'y':100,'w':100,'h':20},{'x':200,'y':100,'w':100,'h':20},
               {'x':20,'y':128,'w':90,'h':20},{'x':200,'y':128,'w':90,'h':20},
               {'x':20,'y':210,'w':100,'h':20}]
        self.assertEqual(len(text_regions(rects)),3)

    def test_duplicate_occurrences_need_explicit_selection(self):
        with self.assertRaisesRegex(ValueError,'found 2'):
            locate(self.path,{'id':'a','find':'€177'},self.root/'a.png')
        matches=candidates(self.index,{'find':'€177'})
        job=locate(self.path,{'id':'a','find':'€177','occurrence_id':matches[1]['occurrence_id']},self.root/'a.png')
        self.assertEqual(job['occurrence_id'],matches[1]['occurrence_id'])
        # Repeated paragraphs are distinct, not silently first-matched.
        self.index['blocks'].append(dict(self.index['blocks'][0],id='b2'))
        self.assertEqual(len(candidates(self.index,{'find':'€177 per jaar'})),2)
        self.assertEqual(len(candidates(self.index,{'find':'€177 per jaar','block_id':'b2'})),1)

    def test_insertion_requires_entire_block_and_uses_bottom(self):
        with self.assertRaisesRegex(ValueError,'complete indexed block'):
            locate(self.path,{'id':'a','insert':'after','anchor':'€177 per jaar'},self.root/'a.png')
        job=locate(self.path,{'id':'a','insert':'after','anchor':self.index['blocks'][0]['text']},self.root/'a.png')
        self.assertEqual(job['insertion_lines'][0][1],368)

    def test_stale_image_and_invalid_dimensions_rejected(self):
        self.index['image_size']=[1,1];write_json(self.path,self.index)
        with self.assertRaisesRegex(ValueError,'dimensions'):
            self.job()
        self.index['image_size']=[780,2400];write_json(self.path,self.index)
        Image.new('RGB',(780,2400),'black').save(self.image)
        with self.assertRaises(ValueError): self.job()

    def test_query_batch_parses_and_verifies_index_once(self):
        queries=[{'id':name,'find':'€177 per jaar'} for name in ('a','b')]
        with patch('tools.locate_evidence.load_index',wraps=load_index) as loader:
            plan=locate_many(self.path,queries,self.root)
            self.assertEqual(loader.call_count,1)
            self.assertEqual(len(plan['jobs']),2)
        queries[1]['id']='../escape'
        with self.assertRaisesRegex(ValueError,'safe filenames'): locate_many(self.path,queries,self.root)

    def test_match_outside_clipped_image_rejected(self):
        self.index['origin']['y']=1000;write_json(self.path,self.index)
        with self.assertRaisesRegex(ValueError,'outside captured'): self.job()

    def test_batch_decodes_once_and_is_pixel_identical(self):
        jobs=[self.job('one'),self.job('two')]
        original_hash=file_hash(self.image)
        real_open=Image.open
        with patch('tools.annotate_screenshot.Image.open',wraps=real_open) as opened:
            result=annotate_batch({'schema_version':2,'jobs':jobs},self.root/'receipt.json')
            self.assertEqual(opened.call_count,1)
        self.assertEqual(result['status'],'complete')
        annotate(str(self.image),str(self.root/'legacy.png'),highlights=jobs[0]['highlights'])
        with Image.open(self.root/'one.png') as a,Image.open(self.root/'legacy.png') as b:
            self.assertIsNone(ImageChops.difference(a,b).getbbox())
        self.assertEqual(file_hash(self.image),original_hash)

    def test_batch_insertion_and_explicit_context_match_single_renderer(self):
        job=locate(self.path,{'id':'insert','insert':'after','anchor':self.index['blocks'][0]['text'],
            'region':[0,0,780,1200],'color':'green'},self.root/'insert.png')
        annotate_batch({'schema_version':2,'jobs':[job]},self.root/'receipt.json')
        annotate(str(self.image),str(self.root/'single.png'),color='green',region=job['region'],insertion_lines=job['insertion_lines'])
        with Image.open(self.root/'insert.png') as a, Image.open(self.root/'single.png') as b:
            self.assertIsNone(ImageChops.difference(a,b).getbbox())
            self.assertEqual(a.size,(780,1200))

    def test_resume_validates_output_decisions_geometry_and_index(self):
        job=self.job();plan={'schema_version':2,'jobs':[job]};receipt=self.root/'receipt.json'
        annotate_batch(plan,receipt)
        self.assertTrue(annotate_batch(plan,receipt,True)['jobs'][0]['reused'])
        Path(job['output_path']).write_bytes(b'corrupt')
        self.assertFalse(annotate_batch(plan,receipt,True)['jobs'][0]['reused'])
        job['decision_context']={'offer':'competitor approved'}
        self.assertFalse(annotate_batch(plan,receipt,True)['jobs'][0]['reused'])
        job['highlights'][0][0]+=1
        self.assertFalse(annotate_batch(plan,receipt,True)['jobs'][0]['reused'])
        self.path.write_text(self.path.read_text()+' ')
        with self.assertRaisesRegex(ValueError,'index changed'): annotate_batch(plan,receipt,True)

    def test_partial_failure_can_resume_and_cannot_overwrite_sources(self):
        jobs=[self.job('one'),self.job('two')];jobs[1]['highlights']=[[0,0,9999,30]]
        plan={'schema_version':2,'jobs':jobs};receipt=self.root/'receipt.json'
        with self.assertRaises(ValueError): annotate_batch(plan,receipt)
        self.assertEqual(json.loads(receipt.read_text())['status'],'failed')
        jobs[1]=self.job('two')
        result=annotate_batch(plan,receipt,True)
        self.assertTrue(result['jobs'][0]['reused']);self.assertFalse(result['jobs'][1]['reused'])
        with self.assertRaisesRegex(ValueError,'Receipt'): annotate_batch(plan,self.image)
        jobs[1]['output_path']=str(self.image)
        with self.assertRaisesRegex(ValueError,'source evidence'): annotate_batch(plan,receipt)


if __name__=='__main__': unittest.main()
