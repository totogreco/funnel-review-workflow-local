#!/usr/bin/env python3
"""Settled, indexed capture packets; isolated jobs, bounded concurrency and resume."""
import asyncio
import importlib.metadata
import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image
from playwright.async_api import async_playwright
try:
    from .review_io import digest, file_hash, utc_now, verify_files, write_json
    from .checkout_review import REVIEW_POLICY_VERSION, DUTCH_CHECKOUT_SCOPE, CHECKOUT_REVIEW_CHECKS, check_template_fields
except ImportError:
    from review_io import digest, file_hash, utc_now, verify_files, write_json
    from checkout_review import REVIEW_POLICY_VERSION, DUTCH_CHECKOUT_SCOPE, CHECKOUT_REVIEW_CHECKS, check_template_fields

INDEX_SCRIPT = Path(__file__).with_name('capture_index.js').read_text(encoding='utf-8')
USER_AGENT = ('Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) '
              'AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1')
READINESS = """() => {
 const h=Math.max(document.body.scrollHeight,document.documentElement.scrollHeight);
 const visible=[...document.images].filter(i=>{const r=i.getBoundingClientRect(),s=getComputedStyle(i);return r.bottom>=0&&r.top<=innerHeight&&r.right>0&&r.left<innerWidth&&i.getClientRects().length&&s.display!=='none'&&s.visibility!=='hidden'&&(!i.checkVisibility||i.checkVisibility())});
 const geometry=[...document.querySelectorAll('h1,h2,h3,p,img,button,summary')].filter(e=>{const r=e.getBoundingClientRect();return r.bottom>=0&&r.top<=innerHeight}).map(e=>{const r=e.getBoundingClientRect();return [Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)]});
 return {height:h,scroll:scrollY,pending:visible.filter(i=>!i.complete).length,
 fonts:!document.fonts||document.fonts.status==='loaded',geometry};
}"""
PAUSE_MOTION = """() => {
 const paused=[];
 for(const a of document.getAnimations()) {
  if(a.playState==='running' && a.effect && a.effect.getComputedTiming().iterations===Infinity) {
   const e=a.effect.target;
   paused.push({name:a.animationName||a.constructor.name,tag:e?.tagName,
     class_name:e?.getAttribute('class'),time_ms:a.currentTime});
   a.pause();
  }
 }
 return paused;
}"""


def layout_key(value):
    """An index for comparing two states. Coordinates rounded to 0.1 CSS px: a finishing transform transition
    (an FAQ icon rotating to ×, SE 265 Milvino) moves glyph rects by 0.00002 px, which is no layout change."""
    if isinstance(value,float):
        return round(value,1)
    if isinstance(value,dict):
        return {k:layout_key(v) for k,v in value.items()}
    if isinstance(value,list):
        return [layout_key(v) for v in value]
    return value


def navigation_in_progress(error):
    """A same-tab navigation replaced the document mid-poll: retry, not a failure."""
    message=str(error)
    return any(text in message for text in ('Execution context was destroyed','Cannot find context with specified id',
                                            'because of a navigation'))


async def settle(page, deadline, quiet_ms=200):
    """Polling interval measures stability; it is not proof that a timer elapsed."""
    previous, since = None, time.monotonic()
    while time.monotonic() < deadline:
        try:
            # Freeze observed countdowns before measuring: a layout-changing timer
            # would otherwise keep the geometry from ever settling.
            await freeze_pending(page)
            # Keep an actual frame stable. Screenshot animation disabling would rewind
            # an infinite marquee and detach image coordinates from the DOM index.
            paused=await page.evaluate(PAUSE_MOTION)
            if paused:
                page.capture_paused_motion=getattr(page,'capture_paused_motion',[])+paused
            current = await page.evaluate(READINESS)
        except Exception as error:
            if not navigation_in_progress(error):
                raise
            previous, since = None, time.monotonic()
            await asyncio.sleep(.1)
            continue
        if current == previous and not current['pending'] and current['fonts']:
            if (time.monotonic()-since)*1000 >= quiet_ms:
                return current
        else:
            previous, since = current, time.monotonic()
        await asyncio.sleep(.05)
    detail={k:previous[k] for k in ('height','scroll','pending','fonts')} if previous else {}
    raise TimeoutError('Page geometry, images or fonts did not settle within the capture budget: '+json.dumps(detail))


# Computed styles are inlined first so the frozen frame looks identical; class
# names are prefixed and ids moved to data-frozen-id so selector- and
# getElementById-based tick scripts no longer match the clone. Elements already
# frozen (or inside a frozen clone) are skipped, so repeated calls only catch
# widgets that rendered later.
FREEZE_SCRIPT='''(selectors)=>{const out=[];for(const s of selectors){for(const e of document.querySelectorAll(s)){
  if(e.closest('[data-capture-frozen]'))continue;
  for(const n of [e,...e.querySelectorAll('*')]){const cs=getComputedStyle(n);let t='';for(const p of cs)t+=p+':'+cs.getPropertyValue(p)+';';n.setAttribute('style',t);}
  const c=e.cloneNode(true);c.setAttribute('data-capture-frozen','');
  for(const n of [c,...c.querySelectorAll('[class]')]){n.className=[...n.classList].map(x=>'frozen-'+x).join(' ')||n.className;}
  for(const n of [c,...c.querySelectorAll('[id]')]){if(n.id){n.setAttribute('data-frozen-id',n.id);n.removeAttribute('id');}}
  e.replaceWith(c);out.push({selector:s,text:c.innerText.trim().replace(/\\s+/g,' ')});}}return out}'''


def freeze_selectors(job):
    selectors=job.get('freeze_selectors') or []
    if not isinstance(selectors,list) or any(not isinstance(s,str) or not s for s in selectors):
        raise ValueError('freeze_selectors must be a list of observed CSS selectors')
    return selectors


async def freeze_pending(page):
    """Freeze any newly rendered observed widget; every settle() poll calls this."""
    selectors=getattr(page,'capture_freeze_selectors',None)
    if not selectors:
        return []
    frozen=await page.evaluate(FREEZE_SCRIPT,selectors)
    if frozen:
        log=getattr(page,'capture_frozen_elements',None)
        if log is None:
            log=page.capture_frozen_elements=[]
        log.extend(frozen)
    return frozen


async def freeze_volatile(page, job, log=None):
    """Replace observed ticking widgets (e.g. countdowns) with a static clone.

    The clone keeps the current frame visually but drops the element/class hooks
    the page script updates. Record what was frozen; this is static evidence and
    never proves the widget's live behavior. Once registered, settle() keeps
    freezing matches that render later, before measuring layout stability.
    """
    page.capture_freeze_selectors=freeze_selectors(job)
    page.capture_frozen_elements=[] if log is None else log
    return await freeze_pending(page)


async def warm_page(page, deadline, max_steps=300):
    """Visit intermediate regions, re-read height, and verify the final bottom."""
    await page.evaluate('scrollTo({top:0,behavior:"instant"})')
    for _ in range(max_steps):
        state = await settle(page, deadline)
        viewport = await page.evaluate('innerHeight')
        bottom = max(0,state['height']-viewport)
        if state['scroll'] >= bottom-2:
            state = await settle(page, deadline, quiet_ms=500)
            if state['scroll'] >= state['height']-viewport-2:
                await page.evaluate('scrollTo({top:0,behavior:"instant"})')
                await settle(page, deadline, quiet_ms=300)
                return
        y = min(bottom, state['scroll']+int(viewport*.85))
        await page.evaluate('(y)=>scrollTo({top:y,behavior:"instant"})', y)
    raise TimeoutError('Progressive scrolling exceeded its step budget; page may be infinite')


async def sticky_states(page, folder, deadline):
    """Capture real viewport states; candidate discovery never decides CTA presence."""
    states=[]
    for name, position in [('top',0),('after_hero',1),('middle',.5),
                           ('bottom',1),('up_middle',.5),('up_top',0)]:
        size=await page.evaluate('({height:document.documentElement.scrollHeight,viewport:innerHeight})')
        bottom=max(0,size['height']-size['viewport'])
        y=min(bottom,size['viewport']) if name=='after_hero' else round(bottom*position)
        await page.evaluate('(y)=>scrollTo({top:y,behavior:"instant"})',y)
        await settle(page,deadline,quiet_ms=500)
        candidates=await page.evaluate('''()=>[...document.querySelectorAll('body *')].filter(e=>{
          const s=getComputedStyle(e),r=e.getBoundingClientRect();
          return ['fixed','sticky'].includes(s.position)&&s.display!=='none'&&s.visibility!=='hidden'
            &&Number(s.opacity)>0&&r.width>0&&r.height>0&&r.bottom>0&&r.top<innerHeight;
        }).map(e=>{const r=e.getBoundingClientRect();return {tag:e.tagName,id:e.id,
          class_name:e.getAttribute('class'),position:getComputedStyle(e).position,
          text:e.innerText,rect:{x:r.x,y:r.y,w:r.width,h:r.height},
          controls:[...e.querySelectorAll('a,button,[role="button"],.btn')].map(a=>({
            text:a.innerText,href:a.getAttribute('href'),target:a.getAttribute('data-goto-element')}))};})''')
        filename='sticky_'+name+'.png'
        await page.screenshot(path=str(folder/filename),full_page=False,timeout=max(1,(deadline-time.monotonic())*1000))
        states.append({'state':name,'scroll_y':await page.evaluate('scrollY'),
                       'image':filename,'candidates':candidates})
    write_json(folder/'sticky_states.json',states)
    return states


def fingerprint(job, desktop, browser_version=None):
    return digest({'job':job,'desktop':desktop,'schema':2,'review_policy_version':REVIEW_POLICY_VERSION,
        'checkout_checks':CHECKOUT_REVIEW_CHECKS,
        'capture_code':file_hash(__file__),'index_code':digest(INDEX_SCRIPT),
        'playwright':importlib.metadata.version('playwright'),
        'pillow':importlib.metadata.version('Pillow'),'browser_version':browser_version})


def reusable(folder, key, max_age):
    path=folder/'manifest.json'
    if not path.exists():
        return None
    try:
        m=json.loads(path.read_text(encoding='utf-8'))
        age=(datetime.now(timezone.utc)-datetime.fromisoformat(m['captured_at'])).total_seconds()
        if m.get('status')!='complete' or m.get('input_fingerprint')!=key or not 0<=age<=max_age:
            return None
        verify_files(folder,m['files'])
        return m
    except (ValueError,KeyError,OSError,TypeError):
        return None


async def snapshot(page, root, folder, state_id, deadline, clip_row=False):
    """The index and image belong to the same state; layout drift triggers retry."""
    for attempt in range(3):
        await settle(page,deadline)
        before=await root.evaluate(INDEX_SCRIPT)
        clip=None
        if clip_row:
            bbox=await root.bounding_box()
            if not bbox:
                raise ValueError('FAQ row has no visible bounds')
            top=max(0,bbox['y']+await page.evaluate('scrollY')-120)
            height=min(before['document_height']-top,max(before['viewport']['height'],bbox['height']+240))
            clip={'x':0,'y':top,'width':before['viewport']['width'],'height':height}
        image=folder/(state_id+'.png')
        await page.screenshot(path=str(image),full_page=True,clip=clip,animations='allow')
        after=await root.evaluate(INDEX_SCRIPT)
        if digest(layout_key(before))==digest(layout_key(after)):
            break
        if time.monotonic()>=deadline:
            raise TimeoutError('Capture changed during screenshot')
    else:
        raise ValueError('Capture changed during screenshot on three attempts; inspect dynamic content')
    with Image.open(image) as im:
        size=list(im.size)
    before.update(schema_version=2,state_id=state_id,url=page.url,image=image.name,
        image_size=size,origin={'x':clip['x'] if clip else 0,'y':clip['y'] if clip else 0},
        files={image.name:file_hash(image)},captured_at=utc_now())
    for block in before['blocks']:
        block['id']=digest([state_id,block['path'],block['text']])[:24]
    before['snapshot_id']=digest({k:v for k,v in before.items() if k!='captured_at'})
    index=folder/(state_id+'.index.json');write_json(index,before)
    return {'state_id':state_id,'image':image.name,'index':index.name,'snapshot_id':before['snapshot_id'],
            'blocks':len(before['blocks'])},before


# FAQ templates tried in order when a job names no faq_selector (the review engine never does). The first one with
# visible rows outside the site header/menu is used.
FAQ_TEMPLATES=(
    {},  # native <details> (Shopify themes and most others)
    # Site builder of Gezondbenelux/Halsoland pages: div.faq rows, the .faq-header toggles, "active" marks an open row.
    {'faq_selector':'.faq:has(> .faq-header)','faq_toggle_selector':':scope > .faq-header','faq_open_class':'active'},
)
IN_SITE_MENU='(e)=>!!e.closest("header,nav,[role=navigation]")'


async def faq_rows(page, job):
    """The job's FAQ settings and its visible FAQ rows. A <details> menu drawer in the site header is no FAQ
    (xeviola.com, NLBE 247: clicking it timed out and failed the capture)."""
    for template in ([job] if job.get('faq_selector') else [{**job,**t} for t in FAQ_TEMPLATES]):
        rows=page.locator(template.get('faq_selector','details'))
        found=[]
        for i in range(await rows.count()):
            row=rows.nth(i)
            if await row.is_visible() and not await row.evaluate(IN_SITE_MENU):
                found.append(row)
        if found:
            return template,found
    return job,[]


async def faq_states(page, job, folder, deadline):
    """Capture answers separately, including accordions allowing only one open row."""
    job,rows=await faq_rows(page,job)
    results=[]
    for i,row in enumerate(rows):
        is_details=await row.evaluate('(e)=>e.tagName==="DETAILS"')
        toggle=row.locator('summary' if is_details else job.get('faq_toggle_selector','[aria-expanded]'))
        if await toggle.count()!=1:
            raise ValueError(f'FAQ {i+1}: no unique toggle; provide the observed template selector')
        await toggle.scroll_into_view_if_needed()
        if is_details:
            opened=await row.evaluate('(e)=>e.open')
        elif job.get('faq_open_class'):
            opened=job['faq_open_class'] in (await row.get_attribute('class') or '').split()
        elif job.get('faq_answer_selector'):
            # Widgets that toggle only the answer's inline display: the answer's visibility is the state.
            answer=row.locator(job['faq_answer_selector'])
            if await answer.count()!=1:
                raise ValueError(f'FAQ {i+1}: no unique answer for faq_answer_selector')
            opened=await answer.is_visible()
        else:
            expanded=await toggle.get_attribute('aria-expanded')
            if expanded not in ('true','false'):
                raise ValueError(f'FAQ {i+1}: no explicit expanded state; provide faq_open_class')
            opened=expanded=='true'
        if not opened:
            await toggle.click(timeout=max(1,int((deadline-time.monotonic())*1000)))
        # A successful click is insufficient: verify expansion before taking evidence.
        if is_details:
            await row.evaluate("e=>{if(!e.open) throw Error('FAQ did not open')}")
        elif job.get('faq_open_class'):
            # The row selector may be Playwright-only (text=, :has-text, >>), so
            # poll the located element itself rather than re-querying the DOM.
            await page.wait_for_function('(a)=>a.row.classList.contains(a.cls)',
                arg={'row':await row.element_handle(),'cls':job['faq_open_class']},timeout=5000)
        elif job.get('faq_answer_selector'):
            await row.locator(job['faq_answer_selector']).wait_for(state='visible',timeout=5000)
        else:
            await page.wait_for_function('(e)=>e.getAttribute("aria-expanded")==="true"',
                arg=await toggle.element_handle(),timeout=5000)
        state,index=await snapshot(page,row,folder,f'faq_{i+1:02}',deadline,clip_row=True)
        state['question']=await toggle.inner_text();state['expanded_text']='\n'.join(b['text'] for b in index['blocks'])
        results.append(state)
        # Isolated browser context is discarded after the capture, so no cart state leaks.
        if not opened:
            await toggle.click(timeout=5000)
    return results


async def capture_job(browser,job,run_id,output_root,desktop=False,resume=False,max_age=1800,budget=120):
    folder=Path(output_root)/run_id/job['name'];folder.mkdir(parents=True,exist_ok=True)
    key=fingerprint(job,desktop,browser.version);started=utc_now();start=time.monotonic()
    if resume:
        cached=reusable(folder,key,max_age)
        if cached:
            return {'name':job['name'],'status':'complete','reused':True,'manifest':str(folder/'manifest.json'),
                    'captured_at':cached['captured_at'],'duration_seconds':time.monotonic()-start}
    attempt=folder/'attempts'/uuid.uuid4().hex[:12];attempt.mkdir(parents=True)
    prefix=attempt.relative_to(folder).as_posix()+'/'
    manifest={'schema_version':2,'review_policy_version':REVIEW_POLICY_VERSION,
        'page':job.get('page'),'scope':job.get('scope'),
        'name':job['name'],'run_id':run_id,'url':job['url'],
        'input_fingerprint':key,'status':'capturing','started_at':started,'review_status':'pending',
        'phase':'initializing','phase_timings':[]}
    write_json(folder/'manifest.json',manifest)
    phase_start=time.monotonic()
    def phase(name):
        nonlocal phase_start
        now=time.monotonic()
        manifest['phase_timings'].append({'phase':manifest['phase'],'duration_seconds':now-phase_start,'ended_at':utc_now()})
        manifest['phase']=name;phase_start=now
        write_json(folder/'manifest.json',manifest)
    context=None
    try:
        vw,vh=(1440,900) if desktop else (390,844)
        context=await browser.new_context(viewport={'width':vw,'height':vh},device_scale_factor=2,
            is_mobile=not desktop,has_touch=not desktop,user_agent=None if desktop else USER_AGENT,
            reduced_motion='reduce')
        page=await context.new_page();page.set_default_timeout(min(30000,budget*1000))
        page.capture_paused_motion=[]
        frozen_log=[]
        # Registered before navigation: settle() freezes countdowns before it
        # measures stability, including during the first progressive scroll.
        await freeze_volatile(page,job,frozen_log)
        deadline=start+budget
        phase('navigation')
        handoff=job.get('offer_handoff')
        if handoff and (job.get('page') != 'checkout' or not handoff.get('source_url') or not (handoff.get('selector') or handoff.get('selectors'))):
            raise ValueError('Offer handoff requires a checkout job, source_url and observed unique selector')
        if handoff and job.get('radio_selections'):
            raise ValueError('Do not override the selected checkout offer after testing its source button')
        response=await page.goto(handoff['source_url'] if handoff else job['url'],wait_until='domcontentloaded',timeout=min(60000,budget*1000))
        if response and response.status>=400:
            raise ValueError(f'Page returned HTTP {response.status}')
        if not (await page.locator('body').inner_text()).strip():
            await page.wait_for_function('document.body.innerText.trim().length>0',timeout=10000)
        if handoff:
            phase('offer_handoff')
            await freeze_pending(page)
            await warm_page(page,deadline)
            await snapshot(page,page.locator('body'),attempt,'offer_source',deadline)
            selectors=handoff.get('selectors') or [handoff['selector']]
            if not isinstance(selectors,list) or not 1<=len(selectors)<=5 or any(not isinstance(s,str) or not s for s in selectors):
                raise ValueError('Offer handoff requires one to five observed click selectors')
            for selector in selectors:
                button=page.locator(selector)
                # Later controls in a sequence may belong to a destination that
                # is still rendering after navigation (e.g. order-summary toggle).
                await button.first.wait_for(state='attached',timeout=min(10000,max(1,(deadline-time.monotonic())*1000)))
                if await button.count()!=1:
                    raise ValueError('Offer handoff must identify exactly one source button')
                # Subscribe before clicking: target=_blank/window.open can arrive
                # after click() returns. Looking at context.pages immediately
                # could silently capture the source page instead of checkout.
                popup=asyncio.create_task(page.wait_for_event('popup',timeout=0))
                started,committed=asyncio.Event(),asyncio.Event()
                main_frame=page.main_frame
                def on_request(request):
                    if request.is_navigation_request() and request.frame==main_frame:
                        started.set()
                def on_navigated(frame):
                    if frame==main_frame:
                        committed.set()
                source_page=page
                source_page.on('request',on_request);source_page.on('framenavigated',on_navigated)
                try:
                    url_before=page.url
                    await button.click(timeout=min(10000,max(1,(deadline-time.monotonic())*1000)))
                    # A target=_blank cart link can take >1s to open its tab (observed
                    # 1.2s on a Shopify cart permalink). Wait for the popup until the
                    # same tab navigates instead, bounded by the owner's 3s wait
                    # and the remaining capture budget. A same-tab navigation that
                    # has started (request sent / frame navigated) within those 3s
                    # is followed to its committed page even when the server is slow.
                    destination=None
                    wait_until=min(deadline,time.monotonic()+3)
                    while time.monotonic()<wait_until:
                        try:
                            destination=await asyncio.wait_for(asyncio.shield(popup),timeout=.25)
                            break
                        except asyncio.TimeoutError:
                            if page.url!=url_before or started.is_set() or committed.is_set():
                                break
                    remaining=lambda:max(1,(deadline-time.monotonic())*1000)
                    if destination:
                        page=destination
                        page.capture_paused_motion=[]
                        page.capture_freeze_selectors=freeze_selectors(job)
                        page.capture_frozen_elements=frozen_log
                        await page.wait_for_load_state('domcontentloaded',timeout=min(10000,remaining()))
                        await page.wait_for_load_state('load',timeout=remaining())
                    elif started.is_set() or committed.is_set() or page.url!=url_before:
                        if not committed.is_set() and page.url==url_before:
                            try:
                                await asyncio.wait_for(committed.wait(),timeout=remaining()/1000)
                            except asyncio.TimeoutError:
                                raise TimeoutError('Offer click started a navigation that did not commit within the capture budget')
                        await page.wait_for_load_state('load',timeout=remaining())
                finally:
                    source_page.remove_listener('request',on_request)
                    source_page.remove_listener('framenavigated',on_navigated)
                    if not popup.done():
                        popup.cancel()
            if page.url.split('#')[0].rstrip('/')==handoff['source_url'].split('#')[0].rstrip('/'):
                # Never save the source page as the clicked checkout state.
                raise ValueError('Offer handoff stayed on the source page; record a dead button or retest the click')
            manifest['offer_handoff']={**handoff,'selectors':selectors,'source_image':prefix+'offer_source.png',
                'source_index':prefix+'offer_source.index.json','action':'click'}
        # Only native radio selection is supported; arbitrary click scripts are not executed.
        for selection in job.get('radio_selections',[]):
            radio=page.locator(selection['selector'])
            if await radio.count()!=1 or await radio.get_attribute('type')!='radio':
                raise ValueError('Offer selection must identify exactly one native radio input')
            await radio.check()
            if not await radio.is_checked():
                raise ValueError('Offer selection did not persist')
        phase('settle_and_scroll')
        # Freeze before the first settle (warm_page settles at every step) so a
        # layout-changing countdown cannot exhaust the budget before it is frozen.
        await freeze_pending(page)
        await warm_page(page,deadline)
        if job.get('page') in ('advertorial','product'):
            phase('sticky_scroll_states')
            sticky=await sticky_states(page,attempt,deadline)
            manifest['sticky_states']=[dict(s,image=prefix+s['image']) for s in sticky]
            manifest['sticky_states_file']=prefix+'sticky_states.json'
        phase('base_snapshot')
        base,index=await snapshot(page,page.locator('body'),attempt,'full_page',deadline)
        text='\n\n'.join(b['text'] for b in index['blocks'])
        (attempt/'text_content.txt').write_text(text,encoding='utf-8')
        phase('section_tiles')
        sections=[]
        with Image.open(attempt/'full_page.png') as image:
            scale=index['device_scale_factor'];step=round(index['viewport']['height']*scale)
            for n,y in enumerate(range(0,image.height,step),1):
                name=f'section_{n:03}.png';image.crop((0,y,image.width,min(y+step,image.height))).save(attempt/name)
                sections.append({'index':n,'file':prefix+name,'scroll_y':y/scale,'kind':'static_full_page_tile'})
        phase('expanded_faqs')
        faqs=await faq_states(page,job,attempt,deadline)
        write_json(attempt/'faqs.json',faqs)
        required=[{'id':'content_and_visuals','label':'Full text, section mapping, layout and emphasis'},
                  {'id':'page_role','label':'Verify actual funnel stage and destination'},
                  {'id':'image_text_and_branding','label':'Inspect all unique images, labels and branding'},
                  {'id':'faq_inventory','label':'Confirm all FAQ questions and full answers are captured and paired, including custom widgets'},
                  {'id':'interaction_inventory','label':'Complete location/state inventory including sticky controls, image CTAs, tabs and selectors missed by DOM discovery'}]
        if job.get('page') in ('advertorial','product'):
            required.append({'id':'sticky_cta','label':'Explicit bottom sticky CTA presence, scroll behavior and actual click destination'})
        if job.get('page') == 'product':
            required.extend({'id':'product:'+name,'label':name.replace('_',' ')} for name in (
                'headline','subheadline','every_bullet','first_testimonial','age_and_name',
                'bold_emphasis','price_and_discount','offer_presentation'))
        if job.get('page') == 'checkout' and job.get('scope') == DUTCH_CHECKOUT_SCOPE:
            required.extend({'id':name,'label':label} for name,label in CHECKOUT_REVIEW_CHECKS.items())
        required.extend({'id':'faq:'+s['state_id'],'label':s['question']} for s in faqs)
        required.extend({'id':'control:'+digest(c['id'])[:24],
                         'label':c['label'] or c['type'] or c['tag'], 'control':c}
                        for c in index['controls'])
        # Inventory does not grant a pass: the reviewer must classify actual controls,
        # exclusions and non-submission boundaries, and compare every expanded answer.
        manifest['required_checks']=required
        phase('finalize')
        if frozen_log or job.get('freeze_selectors'):
            manifest['frozen_elements']=list(frozen_log)
        if handoff:
            manifest['offer_handoff']['destination_url']=page.url
        manifest.update(status='complete',captured_at=utc_now(),resolved_url=page.url,
            viewport=index['viewport'],device_scale_factor=index['device_scale_factor'],
            browser_version=browser.version,full_page=prefix+'full_page.png',text_file=prefix+'text_content.txt',
            motion_policy='pause_infinite_animations_at_current_frame',paused_animations=page.capture_paused_motion,
            index=prefix+'full_page.index.json',total_height=index['document_height'],sections=sections,
            faq_file=prefix+'faqs.json',faq_states=[dict(s,image=prefix+s['image'],index=prefix+s['index']) for s in faqs],
            control_count=len(index['controls']),controls_status='inventory_only_not_tested',
            emulation={'is_mobile':not desktop,'has_touch':not desktop,'user_agent':USER_AGENT if not desktop else None},
            duration_seconds=time.monotonic()-start,
            files={prefix+p.name:file_hash(p) for p in attempt.iterdir() if p.is_file()})
        phase('complete')
        manifest['duration_seconds']=time.monotonic()-start
        write_json(folder/'manifest.json',manifest)
        write_json(folder/'review-checks.template.json',{
            'manifest_sha256':file_hash(folder/'manifest.json'),
            'checks':[dict(r,status='pending',**check_template_fields(r['id'])) for r in required]})
        return {'name':job['name'],'status':'complete','reused':False,'manifest':str(folder/'manifest.json'),
                'captured_at':manifest['captured_at'],'duration_seconds':manifest['duration_seconds']}
    except Exception as error:
        failed_phase=manifest['phase'];phase('failed')
        manifest['failed_phase']=failed_phase
        manifest.update(status='incomplete',error=str(error),completed_at=utc_now(),duration_seconds=time.monotonic()-start)
        write_json(folder/'manifest.json',manifest)
        return {'name':job['name'],'status':'incomplete','error':str(error),'manifest':str(folder/'manifest.json'),
                'duration_seconds':manifest['duration_seconds']}
    finally:
        if context:
            await context.close()


async def capture_many(jobs,run_id,output_root='.tmp/captures',desktop=False,resume=False,concurrency=2,max_age=1800,budget=120):
    if concurrency not in (1,2):
        raise ValueError('Capture concurrency must be 1 or 2')
    names=[j['name'] for j in jobs]
    if not jobs or len(names)!=len(set(names)):
        raise ValueError('Capture job names must be unique')
    for name in [run_id]+names:
        if not isinstance(name,str) or not name or Path(name).name!=name or name in ('.','..'):
            raise ValueError('Run and job names must be safe directory names')
    if budget<=0 or max_age<0:
        raise ValueError('Invalid capture budget/resume age')
    for job in jobs:
        if not job.get('url','').startswith(('https://','http://')):
            raise ValueError('Capture URLs must use HTTP(S)')
    start=time.monotonic();started=utc_now();semaphore=asyncio.Semaphore(concurrency)
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        try:
            async def run(job):
                async with semaphore:
                    try:
                        return await asyncio.wait_for(
                            capture_job(browser,job,run_id,output_root,desktop,resume,max_age,budget),
                            timeout=budget+10)
                    except asyncio.TimeoutError:
                        path=Path(output_root)/run_id/job['name']/'manifest.json'
                        value=json.loads(path.read_text()) if path.exists() else {'schema_version':2}
                        value.update(status='incomplete',error='Capture exceeded budget plus cleanup grace',completed_at=utc_now())
                        write_json(path,value)
                        return {'name':job['name'],'status':'incomplete','manifest':str(path),'error':value['error']}
            results=await asyncio.gather(*(run(job) for job in jobs))
        finally:
            await browser.close()
    receipt={'schema_version':2,'started_at':started,'completed_at':utc_now(),'duration_seconds':time.monotonic()-start,
             'concurrency':concurrency,'jobs':results,'status':'complete' if all(j['status']=='complete' for j in results) else 'incomplete'}
    history=Path(output_root)/run_id/'capture-runs'/(uuid.uuid4().hex+'.json')
    receipt['history_file']=str(history)
    write_json(history,receipt)
    write_json(Path(output_root)/run_id/'capture-run.json',receipt)
    return receipt
