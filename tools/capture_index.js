// Evaluated against the document body or a specific FAQ row in its captured state.
(root) => {
  const box = r => ({x:r.x+scrollX,y:r.y+scrollY,w:r.width,h:r.height});
  const visible = e => {
    const s=getComputedStyle(e),r=e.getBoundingClientRect();
    return s.visibility!=='hidden' && s.display!=='none' && r.width>0 && r.height>0;
  };
  const paths=new WeakMap(), computed=new WeakMap(), styles={}, containers={};
  const properties=['fontFamily','fontSize','fontWeight','fontStyle','lineHeight','letterSpacing',
    'textAlign','textDecorationLine','textDecorationColor','color','backgroundColor','backgroundImage',
    'paddingTop','paddingRight','paddingBottom','paddingLeft','marginTop','marginBottom',
    'borderTopWidth','borderRightWidth','borderBottomWidth','borderLeftWidth','borderColor',
    'borderRadius','display','gap','objectFit','objectPosition'];
  const styleCache=new Map();
  const styleId=e=>{
    if(computed.has(e)) return computed.get(e);
    const s=getComputedStyle(e),value=Object.fromEntries(properties.map(p=>[p,s[p]]));
    const key=JSON.stringify(value);
    if(!styleCache.has(key)) {const id='s'+styleCache.size;styleCache.set(key,id);styles[id]=value;}
    const id=styleCache.get(key);computed.set(e,id);return id;
  };
  const path = e => {
    if(paths.has(e)) return paths.get(e);
    const original=e;
    const parts=[];
    while(e && e.nodeType===1) {
      const tag=e.tagName.toLowerCase();
      const siblings=e.parentElement ? [...e.parentElement.children].filter(s=>s.tagName===e.tagName) : [e];
      parts.unshift(tag+':nth-of-type('+(siblings.indexOf(e)+1)+')');
      if(e===document.body) break;
      e=e.parentElement;
    }
    const result=parts.join(' > ');paths.set(original,result);return result;
  };
  // Keep ancestor styling once, including inline highlights and outer cards.
  // Backgrounds/underlines are facts at each level, not inferred effective styles.
  const containerPaths=e=>{
    const result=[];
    while(e && e.nodeType===1) {
      const id=path(e);result.push(id);
      if(!containers[id]) containers[id]={path:id,tag:e.tagName.toLowerCase(),
        parent_path:e.parentElement ? path(e.parentElement) : null,
        rect:box(e.getBoundingClientRect()),style_id:styleId(e)};
      if(e===document.body) break;
      e=e.parentElement;
    }
    return result;
  };
  const semantic='p,li,h1,h2,h3,h4,h5,h6,button,a,summary,label,td,th,figcaption,blockquote,[role="heading"],[role="button"]';
  const groups=new Map();
  const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);
  let n;
  while(n=walker.nextNode()) {
    const parent=n.parentElement;
    if(!n.textContent || parent.closest('script,style,noscript,template,svg') || !visible(parent)) continue;
    const owner=parent.closest(semantic) || parent.closest('div,section,article,body') || parent;
    // Ownership, rather than ancestor substring searches, avoids duplicate paragraphs.
    if(!groups.has(owner)) groups.set(owner,{element:owner,text:'',tokens:[]});
    const group=groups.get(owner), raw=n.textContent, cpMap=[];
    let unit=0, cp=0;
    for(const char of raw) {for(let j=0;j<char.length;j++) cpMap[unit++]=cp;cp++;}
    cpMap[unit]=cp;
    const offset=Array.from(group.text).length;
    group.text+=raw;
    const tokenStyle=styleId(parent),inlinePath=containerPaths(parent)[0];
    for(const m of raw.matchAll(/\S+/gu)) {
      const range=document.createRange();range.setStart(n,m.index);range.setEnd(n,m.index+m[0].length);
      const rects=[...range.getClientRects()].filter(r=>r.width>0 && r.height>0).map(box);
      if(!rects.length) continue;
      const style=getComputedStyle(parent);
      group.tokens.push({start:offset+cpMap[m.index],end:offset+cpMap[m.index+m[0].length],rects,
        bold:Number(style.fontWeight)>=600 || style.fontWeight==='bold',
        style_id:tokenStyle,element_path:inlinePath});
    }
  }
  const headings=[...document.querySelectorAll('h1,h2,h3,h4,h5,h6,[role="heading"]')].filter(visible);
  const blocks=[];
  for(const g of groups.values()) {
    if(!g.text.trim() || !g.tokens.length) continue;
    const rs=g.tokens.flatMap(t=>t.rects),x=Math.min(...rs.map(r=>r.x)),y=Math.min(...rs.map(r=>r.y));
    const right=Math.max(...rs.map(r=>r.x+r.w)),bottom=Math.max(...rs.map(r=>r.y+r.h));
    const heading=[...headings].reverse().find(h=>h===g.element || (h.compareDocumentPosition(g.element)&Node.DOCUMENT_POSITION_FOLLOWING));
    blocks.push({path:path(g.element),tag:g.element.tagName.toLowerCase(),text:g.text,
      heading:heading ? heading.innerText : '',rect:{x,y,w:right-x,h:bottom-y},tokens:g.tokens,
      style_id:styleId(g.element),container_paths:containerPaths(g.element)});
  }
  const controls=[...root.querySelectorAll('a,button,input,select,textarea,summary,[role="button"],[role="radio"]')].filter(visible).map(e=>({
    id:path(e),tag:e.tagName.toLowerCase(),type:e.getAttribute('type'),role:e.getAttribute('role'),
    label:e.innerText || e.getAttribute('aria-label') || e.getAttribute('placeholder') || '',
    href:e.getAttribute('href'),expanded:e.getAttribute('aria-expanded'),checked:e.checked??null,rect:box(e.getBoundingClientRect())
  }));
  const images=[...root.querySelectorAll('img')].filter(visible).map(e=>({path:path(e),src:e.currentSrc || e.src,alt:e.alt,
    complete:e.complete,natural_width:e.naturalWidth,natural_height:e.naturalHeight,
    rect:box(e.getBoundingClientRect()),style_id:styleId(e),container_paths:containerPaths(e)}));
  return {visual_schema_version:1,styles,containers,blocks,controls,images,document_height:Math.max(document.body.scrollHeight,document.documentElement.scrollHeight),
    viewport:{width:innerWidth,height:innerHeight},device_scale_factor:devicePixelRatio};
}
