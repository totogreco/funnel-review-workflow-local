# -*- coding: utf-8 -*-
"""Opt-in real Chromium regression fixtures: RUN_BROWSER_TESTS=1 python -m unittest ..."""
import asyncio
import io
import json
import os
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from PIL import Image
from tools.capture_packet import capture_many, reusable, sticky_states
from tools.locate_evidence import candidates, locate
from tools.annotate_screenshot import annotate_batch
from tools.review_io import file_hash
from tools.checkout_review import CHECKOUT_REVIEW_CHECKS

PAGE = '''<!doctype html><meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{margin:20px;font:18px/1.5 Arial}p{margin:24px 0}.space{height:1100px}.answer{display:none}.faq.active .answer{display:block}
@keyframes drift{from{transform:translateX(0)}to{transform:translateX(40px)}}.logo{animation:drift 2s linear infinite}</style>
<h1>Fixture funnel</h1><p id="state"></p>
<p class="logo">Animated logo fixture</p>
<input type="radio" name="offer" id="one" checked><label for="one">One bottle</label>
<input type="radio" name="offer" id="three"><label for="three">Three bottles</label>
<div><div><p>Unique nested paragraph.</p></div></div>
<p>Repeated sentence.</p><p>Repeated sentence.</p>
<p>🙂 It’s&nbsp; €177–€399 per jaar; <b>bold promise</b> and text that wraps onto another line.</p>
<div style="background:rgb(170,240,180);padding:12px;border-radius:14px">
<p style="font-size:24px;text-align:center"><em><u>Styled editorial heading</u></em></p>
<img alt="Review portrait fixture" width="48" height="48" style="border-radius:50%;object-fit:cover" src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='60' height='80'%3E%3C/svg%3E">
</div>
<div class="space"></div><div id="trigger">Lazy region</div><div id="late"></div>
<details><summary>Native question one</summary><p>First full answer.</p></details>
<details><summary>Native question two</summary><p>Second full answer.</p></details>
<div class="faq"><button aria-expanded="false">Accordion one</button><div class="answer"><p>Custom answer one.</p></div></div>
<div class="faq"><button aria-expanded="false">Accordion two</button><div class="answer"><p>Custom answer two.</p></div></div>
<p id="bottom">Final footer marker.</p>
<script>
document.querySelector('#state').textContent=document.cookie.includes('seen=1')?'Leaked cookie':'Fresh context';
document.cookie='seen=1';
new IntersectionObserver((entries,observer)=>{if(entries.some(e=>e.isIntersecting)){observer.disconnect();setTimeout(()=>{
document.querySelector('#late').innerHTML='<div>Loaded late content</div><img src="/slow.png" style="width:100%" alt="Late loaded image">';
},90)}}).observe(document.querySelector('#trigger'));
document.querySelectorAll('.faq button').forEach(b=>b.onclick=()=>{const open=b.getAttribute('aria-expanded')==='true';
document.querySelectorAll('.faq').forEach(r=>{r.classList.remove('active');r.querySelector('button').setAttribute('aria-expanded','false')});
if(!open)setTimeout(()=>{b.parentElement.classList.add('active');b.setAttribute('aria-expanded','true')},60)});
</script>'''


COUNTDOWN = '''<!doctype html><body><h1>Countdown offer</h1><div class="countdown"><span id="timer">0</span></div>
<p>Offer text below the timer.</p><div style="height:1500px"></div><p>Footer.</p>
<script>setInterval(()=>{const t=document.getElementById('timer');if(!t)return;t.textContent=Date.now();
t.style.display='block';t.style.paddingBottom=(Date.now()%40)+'px'},30)</script>'''
FAQ_TOP = '''<!doctype html><body><h1>FAQ first</h1>
<div class="faq"><button>Question one</button><div class="answer" hidden>Answer one.</div></div>
<div style="height:3000px"></div><p>Footer.</p>
<script>document.querySelectorAll('.faq button').forEach(b=>b.onclick=()=>setTimeout(()=>{
b.parentElement.classList.toggle('open');b.nextElementSibling.hidden=!b.parentElement.classList.contains('open')},60));</script>'''

# NLBE 247 (2026-10-08): the engine names no FAQ selector. Our Gezondbenelux page uses the site builder's div.faq rows
# (no <details>, no aria-expanded); the competitor's Shopify theme has a <details> menu drawer in the header first.
BUILDER_FAQ = '''<!doctype html><body><h1>Product</h1><style>.faq-content-wrapper{display:none}.faq.active .faq-content-wrapper{display:block}</style>
<div class="faq-wrapper"><div class="faq el-1 faq_icon"><div class="faq-header"><div class="faq-title">Hoe werkt het?</div></div>
<div class="faq-content-wrapper"><div class="faq-content"><p>Antwoord een.</p></div></div></div>
<div class="faq el-1 faq_icon"><div class="faq-header"><div class="faq-title">Doet het pijn?</div></div>
<div class="faq-content-wrapper"><div class="faq-content"><p>Antwoord twee.</p></div></div></div></div>
<div style="height:1500px"></div><p>Footer.</p>
<script>document.querySelectorAll('.faq-header').forEach(h=>h.onclick=()=>h.parentElement.classList.toggle('active'))</script>'''
SHOPIFY_FAQ = '''<!doctype html><body><header><details class="menu-drawer-container"><summary aria-label="Menu">=</summary>
<nav>Menu links</nav></details><div style="position:fixed;top:0;left:0;width:100%;height:60px;background:#fff">Cookies</div></header>
<h1>Product</h1><details class="accordion__details"><summary>How It Works</summary><p>Answer one.</p></details>
<details class="accordion__details"><summary>Shipping</summary><p>Answer two.</p></details>
<div style="height:1500px"></div><p>Footer.</p>'''


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ('/builder-faq','/shopify-faq'):
            self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.end_headers()
            self.wfile.write((BUILDER_FAQ if self.path=='/builder-faq' else SHOPIFY_FAQ).encode());return
        if self.path.startswith('/countdown') or self.path.startswith('/faq-top'):
            self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.end_headers()
            self.wfile.write((COUNTDOWN if self.path.startswith('/countdown') else FAQ_TOP).encode());return
        if self.path.startswith('/slow-checkout'):
            time.sleep(3.6)  # Same-tab navigation commits after the 3 s popup window.
            self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.end_headers()
            self.wfile.write(b'<html><body><h1>Checkout</h1><p>Selected 6 bottles</p></body></html>');return
        if self.path.startswith('/offer-source') or self.path.startswith('/offer-checkout'):
            self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.end_headers()
            if self.path.startswith('/offer-source'):
                body='''<html><body><h1>Choose your offer</h1>
                <a id="three" href="/offer-checkout?quantity=3">Three bottles — 599 kr</a>
                <a id="one" href="/offer-checkout?quantity=1" target="_blank">One bottle — 299 kr</a>
                <button id="delayed" onclick="setTimeout(()=>window.open('/offer-checkout?quantity=2','_blank'),1200)">Delayed checkout</button>
                <button id="too-late" onclick="setTimeout(()=>window.open('/offer-checkout?quantity=4','_blank'),4500)">Late checkout</button>
                <button id="slow" onclick="setTimeout(()=>location.href='/slow-checkout?quantity=6',200)">Six bottles — slow checkout</button>
                <input type="radio" id="five" name="offer" onclick="document.getElementById('buy').href='/offer-checkout?quantity=5'">
                <label for="five">Five bottles — 899 kr</label><a id="buy" href="/offer-checkout?quantity=1">Checkout</a></body></html>'''
            else:
                body='<html><body><h1>Checkout</h1><p>Selected '+self.path.split('=')[-1]+' bottles</p></body></html>'
            self.wfile.write(body.encode());return
        if self.path=='/slow.png':
            time.sleep(.9)
            stream=io.BytesIO();Image.new('RGB',(350,700),'lightblue').save(stream,format='PNG')
            self.send_response(200);self.send_header('Content-Type','image/png');self.end_headers();self.wfile.write(stream.getvalue());return
        if self.path=='/never.png':
            time.sleep(20);self.send_response(404);self.end_headers();return
        self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.end_headers()
        content=PAGE
        if self.path=='/closed-faq-image':
            content='<p>Top</p><details><summary>Question</summary><p>Answer<img src="/never.png" style="width:300px"></p></details>'
        if self.path=='/moving':
            content += '<script>setInterval(()=>document.body.style.paddingBottom=(parseInt(document.body.style.paddingBottom||0)+10)+"px",30)</script>'
        self.wfile.write(content.encode('utf-8'))
    def log_message(self,*args): pass


@unittest.skipUnless(os.environ.get('RUN_BROWSER_TESTS')=='1','Set RUN_BROWSER_TESTS=1 for local Chromium fixtures')
class CaptureBrowserTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        cls.url='http://127.0.0.1:'+str(cls.server.server_port)
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join()
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)

    async def test_sticky_viewports_find_fixed_parent_and_sticky_but_not_flow_button(self):
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser=await p.chromium.launch();page=await browser.new_page(viewport={'width':390,'height':844})
            await page.set_content('''<style>body{margin:0}.space{height:3000px}
              #bar{position:fixed;bottom:0;width:100%;display:none}
              #header{position:sticky;top:0}</style><div id="header">Header</div>
              <div class="space"></div><button id="flow">Normal footer button</button>
              <div id="bar"><a href="#flow">Buy</a></div><script>
              onscroll=()=>document.querySelector('#bar').style.display=scrollY>100?'block':'none';</script>''')
            states=await sticky_states(page,self.root,time.monotonic()+20)
            self.assertEqual(len(states),6)
            ids=lambda s:{c['id'] for c in s['candidates']}
            self.assertNotIn('bar',ids(states[0]));self.assertIn('bar',ids(states[2]))
            self.assertIn('header',ids(states[2]));self.assertNotIn('flow',ids(states[3]))
            self.assertNotIn('bar',ids(states[-1]))
            self.assertTrue(all((self.root/s['image']).is_file() for s in states))
            await browser.close()

    async def test_lazy_growth_faq_occurrences_isolation_and_resume(self):
        jobs=[{'name':'source','url':self.url,'radio_selections':[{'selector':'#three'}]},
              {'name':'target','url':self.url,'page':'product','faq_selector':'.faq','faq_toggle_selector':'button'}]
        receipt=await capture_many(jobs,'fixture',self.root,budget=30)
        self.assertEqual(receipt['status'],'complete',receipt)
        self.assertTrue(Path(receipt['history_file']).is_file())
        indexes=[]
        for job in receipt['jobs']:
            path=Path(job['manifest']);m=json.loads(path.read_text());folder=path.parent
            text=(folder/m['text_file']).read_text()
            self.assertIn('Loaded late content',text);self.assertIn('Final footer marker.',text)
            self.assertIn('Fresh context',text);self.assertNotIn('Leaked cookie',text)
            self.assertEqual(m['viewport']['width'],390);self.assertGreater(m['total_height'],2100)
            self.assertTrue(m['paused_animations'])
            if job['name']=='target':
                self.assertIn('sticky_cta',{c['id'] for c in m['required_checks']})
                self.assertEqual(len(m['sticky_states']),6)
                self.assertTrue(all(s['image'] in m['files'] for s in m['sticky_states']))
            index=json.loads((folder/m['index']).read_text());indexes.append(index)
            heading=next(b for b in index['blocks'] if b['text']=='Styled editorial heading')
            self.assertEqual(index['visual_schema_version'],1)
            self.assertEqual(index['styles'][heading['style_id']]['fontSize'],'24px')
            self.assertEqual(index['styles'][heading['tokens'][0]['style_id']]['fontStyle'],'italic')
            self.assertEqual(index['styles'][heading['tokens'][0]['style_id']]['textDecorationLine'],'underline')
            ancestor_styles=[index['styles'][index['containers'][p]['style_id']] for p in heading['container_paths']]
            self.assertTrue(any(s['backgroundColor']=='rgb(170, 240, 180)' and s['paddingTop']=='12px' for s in ancestor_styles))
            portrait=next(i for i in index['images'] if i['alt']=='Review portrait fixture')
            self.assertEqual(portrait['natural_height'],80)
            self.assertEqual(index['styles'][portrait['style_id']]['borderRadius'],'50%')
            self.assertTrue(all(img['complete'] and img['natural_width']>0 for img in index['images']))
            with Image.open(folder/m['full_page']) as im:
                self.assertEqual(im.height,round(m['total_height']*2));self.assertEqual(im.width,780)
            self.assertEqual(len(candidates(index,{'find':'Unique nested paragraph.'})),1)
            self.assertEqual(len(candidates(index,{'find':'Repeated sentence.'})),2)
            self.assertEqual(len(candidates(index,{'find':"🙂 It's €177-€399 per jaar"})),1)
            self.assertEqual(len(m['faq_states']),2)
            self.assertEqual(sum(c['id'].startswith('faq:') for c in m['required_checks']),2)
            template=json.loads((folder/'review-checks.template.json').read_text())
            self.assertTrue(all(c['status']=='pending' for c in template['checks']))
            for state in m['faq_states']:
                self.assertIn('answer',state['expanded_text'])
                faq_index=json.loads((folder/state['index']).read_text())
                answer=next(b['text'] for b in faq_index['blocks'] if 'answer' in b['text'])
                plan={'schema_version':2,'jobs':[locate(folder/state['index'],{'id':state['state_id'],'find':answer},folder/(state['state_id']+'-marked.png'))]}
                self.assertEqual(annotate_batch(plan,folder/'annotation-receipt.json')['status'],'complete')
            self.assertIsNotNone(reusable(folder,m['input_fingerprint'],1800))
            self.assertIsNone(reusable(folder,m['input_fingerprint'],0))
        checked=lambda idx:[c['id'] for c in idx['controls'] if c['type']=='radio' and c['checked']]
        self.assertNotEqual(checked(indexes[0]),checked(indexes[1]))
        cached=await capture_many(jobs,'fixture',self.root,budget=30,resume=True)
        self.assertTrue(all(j['reused'] for j in cached['jobs']))
        self.assertEqual(len(list((self.root/'fixture'/'capture-runs').glob('*.json'))),2)
        path=Path(cached['jobs'][0]['manifest']);m=json.loads(path.read_text())
        (path.parent/m['text_file']).write_text('tampered')
        self.assertIsNone(reusable(path.parent,m['input_fingerprint'],1800))

    async def test_incomplete_job_does_not_erase_successful_sibling(self):
        receipt=await capture_many([{'name':'good','url':self.url},
            {'name':'bad','url':self.url,'faq_selector':'.faq','faq_toggle_selector':'.does-not-exist'}],
            'partial',self.root,budget=30)
        self.assertEqual(receipt['status'],'incomplete')
        self.assertEqual(receipt['jobs'][0]['status'],'complete')
        self.assertIn('unique toggle',receipt['jobs'][1]['error'])
        self.assertFalse((Path(receipt['jobs'][1]['manifest']).parent/'review-checks.template.json').exists())

    async def test_never_settling_page_is_bounded_and_incomplete(self):
        receipt=await capture_many([{'name':'moving','url':self.url+'/moving'}],'timeout',self.root,budget=1)
        self.assertEqual(receipt['status'],'incomplete')
        self.assertLess(receipt['duration_seconds'],12)
        self.assertIn('budget',receipt['jobs'][0]['error'])

    async def test_unloaded_image_inside_closed_details_does_not_block_settling(self):
        receipt=await capture_many([{'name':'closed','url':self.url+'/closed-faq-image'}],'closed',self.root,budget=8)
        self.assertNotIn('did not settle',receipt['jobs'][0].get('error',''),receipt)

    async def test_dutch_checkout_packet_requires_all_seven_pending_checks(self):
        result=await capture_many([{'name':'ours_checkout','url':self.url,
            'page':'checkout','scope':'dutch_checkout'}],'checkout',self.root,budget=30)
        self.assertEqual(result['status'],'complete',result)
        path=Path(result['jobs'][0]['manifest']);manifest=json.loads(path.read_text())
        self.assertGreaterEqual(manifest['review_policy_version'],2)
        self.assertEqual(manifest['scope'],'dutch_checkout')
        template=json.loads((path.parent/'review-checks.template.json').read_text())
        rows={r['id']:r for r in template['checks']}
        self.assertTrue(CHECKOUT_REVIEW_CHECKS.keys() <= rows.keys())
        self.assertTrue(all(rows[name]['status']=='pending' for name in CHECKOUT_REVIEW_CHECKS))
        self.assertEqual(rows['checkout_review_dates']['reviews'],[])
        self.assertIsNone(rows['checkout_ideal']['loaded'])
        self.assertEqual(len(manifest['faq_states']),2)

    async def test_swedish_offer_handoff_preserves_clicked_bundle_and_new_tabs(self):
        jobs=[]
        for count,selectors in [(3,['#three']),(1,['#one']),(5,['#five','#buy'])]:
            jobs.append({'name':'offer'+str(count),'url':self.url+'/offer-checkout',
                'page':'checkout','scope':'price_and_offer','offer_handoff':{
                    'source_url':self.url+'/offer-source','selectors':selectors}})
        receipt=await capture_many(jobs,'swedish',self.root,budget=30)
        self.assertEqual(receipt['status'],'complete',receipt)
        for count,result in zip([3,1,5],receipt['jobs']):
            path=Path(result['manifest']);manifest=json.loads(path.read_text())
            self.assertEqual(manifest['review_policy_version'],3)
            self.assertTrue(manifest['resolved_url'].endswith('quantity='+str(count)),manifest['resolved_url'])
            self.assertIn('Selected '+str(count)+' bottles',(path.parent/manifest['text_file']).read_text())
            self.assertIn(manifest['offer_handoff']['source_image'],manifest['files'])
        forbidden={**jobs[0],'name':'override','radio_selections':[{'selector':'#other'}]}
        result=await capture_many([forbidden],'swedish',self.root,budget=10)
        self.assertEqual(result['status'],'incomplete')
        self.assertIn('Do not override',result['jobs'][0]['error'])

    async def test_checkout_popup_wait_accepts_1200ms_but_stops_before_4500ms(self):
        jobs=[{'name':name,'url':self.url+'/offer-checkout','page':'checkout',
               'scope':'price_and_offer','offer_handoff':{
                   'source_url':self.url+'/offer-source','selector':'#'+name}}
              for name in ('delayed','too-late')]
        receipt=await capture_many(jobs,'popup-wait',self.root,budget=30)
        good,bad=receipt['jobs']
        self.assertEqual(good['status'],'complete',good)
        path=Path(good['manifest']);manifest=json.loads(path.read_text())
        self.assertTrue(manifest['resolved_url'].endswith('quantity=2'))
        self.assertIn('Selected 2 bottles',(path.parent/manifest['text_file']).read_text())
        self.assertEqual(bad['status'],'incomplete',bad)
        self.assertIn('stayed on the source page',bad['error'])
        failed=json.loads(Path(bad['manifest']).read_text())
        self.assertNotIn('full_page',failed)
        self.assertFalse((Path(bad['manifest']).parent/'review-checks.template.json').exists())

    async def test_slow_same_tab_navigation_is_followed_not_a_dead_button(self):
        receipt=await capture_many([{'name':'slow','url':self.url+'/slow-checkout?quantity=6','page':'checkout',
            'scope':'price_and_offer','offer_handoff':{'source_url':self.url+'/offer-source','selector':'#slow'}}],
            'slow-nav',self.root,budget=30)
        self.assertEqual(receipt['status'],'complete',receipt)
        manifest=json.loads(Path(receipt['jobs'][0]['manifest']).read_text())
        self.assertTrue(manifest['resolved_url'].endswith('/slow-checkout?quantity=6'),manifest['resolved_url'])
        self.assertIn('Selected 6 bottles',(Path(receipt['jobs'][0]['manifest']).parent/manifest['text_file']).read_text())

    async def test_layout_changing_countdown_is_frozen_before_settling(self):
        receipt=await capture_many([{'name':'countdown','url':self.url+'/countdown','freeze_selectors':['.countdown']}],
            'countdown',self.root,budget=15)
        self.assertEqual(receipt['status'],'complete',receipt)
        manifest=json.loads(Path(receipt['jobs'][0]['manifest']).read_text())
        self.assertEqual([f['selector'] for f in manifest['frozen_elements']],['.countdown'])

    async def test_faq_open_class_with_playwright_selector_and_desktop_viewport_clip(self):
        receipt=await capture_many([{'name':'faq','url':self.url+'/faq-top','faq_selector':'div.faq:has-text("Question")',
            'faq_toggle_selector':'button','faq_open_class':'open'}],'faq-desktop',self.root,desktop=True,budget=30)
        self.assertEqual(receipt['status'],'complete',receipt)
        path=Path(receipt['jobs'][0]['manifest']);manifest=json.loads(path.read_text())
        [state]=manifest['faq_states']
        self.assertIn('Answer one.',state['expanded_text'])
        with Image.open(path.parent/state['image']) as im:
            self.assertEqual(im.height,900*2)  # Desktop viewport height, not the mobile 844 px.

    async def test_known_faq_templates_are_found_without_a_selector_and_the_header_menu_is_skipped(self):
        receipt=await capture_many([{'name':'builder','url':self.url+'/builder-faq','page':'product'},
                                    {'name':'shopify','url':self.url+'/shopify-faq','page':'product'}],'faq-auto',self.root,budget=40)
        self.assertEqual(receipt['status'],'complete',receipt)
        for job,answers in zip(receipt['jobs'],(['Antwoord een.','Antwoord twee.'],['Answer one.','Answer two.'])):
            states=json.loads(Path(job['manifest']).read_text())['faq_states']
            self.assertEqual([a in s['expanded_text'] for s,a in zip(states,answers)],[True,True],(job['name'],states))


class SettleRetryTests(unittest.IsolatedAsyncioTestCase):
    async def test_destroyed_execution_context_during_settle_is_retried(self):
        from tools.capture_packet import settle
        stable={'height':100,'scroll':0,'pending':0,'fonts':True,'geometry':[]}

        class Page:
            calls=0
            async def evaluate(self,script,*args):
                Page.calls+=1
                if Page.calls<=2:
                    raise Exception('Execution context was destroyed, most likely because of a navigation')
                return [] if 'getAnimations' in script else stable

        self.assertEqual(await settle(Page(),time.monotonic()+5,quiet_ms=50),stable)

    async def test_other_evaluation_errors_still_fail(self):
        from tools.capture_packet import settle

        class Page:
            async def evaluate(self,script,*args):
                raise Exception('ReferenceError: foo is not defined')

        with self.assertRaisesRegex(Exception,'ReferenceError'):
            await settle(Page(),time.monotonic()+5)


if __name__=='__main__': unittest.main()
