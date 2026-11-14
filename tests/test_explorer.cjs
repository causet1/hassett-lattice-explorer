/** Behavioral tests of the actual browser script, without a browser renderer.
 * The small DOM double models disabled controls, DOM replacement, focus and
 * async event handlers. It cannot establish layout or native browser behavior.
 */
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path'),nativeAssert=require('node:assert');
const {webcrypto,createHash}=require('node:crypto');
const {gzipSync}=require('node:zlib');
const root=path.resolve(__dirname,'..');
let assertions=0;
function assert(value,message){assertions++;nativeAssert(value,message);}
for(const method of ['strictEqual','deepStrictEqual','match','throws'])assert[method]=(...args)=>{assertions++;return nativeAssert[method](...args);};
const html=fs.readFileSync(path.join(root,'web/explorer.html'),'utf8');
const js=html.match(/<script>\s*([\s\S]*?)<\/script>/)[1];
const embedded=html.match(/<script id="catalogue-data"[^>]*>([\s\S]*?)<\/script>/)[1];
const catalogue=JSON.parse(fs.readFileSync(path.join(root,'web/catalogue.json'),'utf8'));
assert.deepStrictEqual(JSON.parse(embedded),catalogue);
assert.match(html,/Interactive controls have not started/);
assert.match(html,/https:\/\/hassett-lattice-explorer\.causetpatrick\.chatgpt\.site/);
assert.strictEqual((html.match(/data-static-component="/g)||[]).length,5);
assert.match(html,/66 precomputed intersections/);
assert.match(html,/id="component-count">5<\/strong>/);
new vm.Script(js); // Check the actual application script before constructing a DOM.

function harness(options={}){
  const ids=new Map(),downloads=[],createdUrls=new Map(),timers=new Map(),windowEvents={},requests=[];
  let all=[],serial=0,document;
  function matches(el,sel){
    if(sel.startsWith('.'))return el.className.split(/\s+/).includes(sel.slice(1));
    if(sel.startsWith('[')){const m=sel.match(/^\[([^=\]]+)(?:="([^"]+)")?\]$/);return Boolean(m&&el.attrs[m[1]]!==undefined&&(m[2]===undefined||el.attrs[m[1]]===m[2]));}
    return el.tagName===sel;
  }
  class El{
    constructor(tag='div',attrs={}){
      this.tagName=tag;this.attrs={...attrs};this.dataset={};Object.keys(attrs).filter(k=>k.startsWith('data-')).forEach(k=>this.dataset[k.slice(5)]=attrs[k]);
      this.events={};this.className=attrs.class||'';this.style={};this.children=[];this._text='';this._html='';this.value=attrs.value||'';this.disabled='disabled' in attrs;this.hidden='hidden' in attrs;this.parent=null;
      this.classList={add:c=>{if(!this.classList.contains(c))this.className+=' '+c;},remove:c=>{this.className=this.className.split(/\s+/).filter(x=>x!==c).join(' ');},toggle:(c,on)=>{this.classList.remove(c);if(on)this.classList.add(c);},contains:c=>this.className.split(/\s+/).includes(c)};
    }
    clearChildren(){if(document&&this.children.includes(document.activeElement))document.activeElement=document.body;this.children.forEach(e=>{e.parent=null;if(e.attrs.id&&ids.get(e.attrs.id)===e)ids.delete(e.attrs.id);});this.children=[];}
    set textContent(t){this.clearChildren();this._text=String(t);this._html=String(t);}
    get textContent(){return this._text||this._html.replace(/<[^>]*>/g,'');}
    set innerHTML(s){this.clearChildren();this._html=String(s);this._text='';this.children=parse(this._html);this.children.forEach(e=>e.parent=this);}
    get innerHTML(){return this._html;}
    setAttribute(k,v){this.attrs[k]=String(v);if(k==='class')this.className=String(v);}
    addEventListener(k,fn){(this.events[k]??=[]).push(fn);}
    querySelectorAll(sel){return this.children.filter(e=>matches(e,sel));}
    fire(type,fields={}){const event={target:this,defaultPrevented:false,preventDefault(){this.defaultPrevented=true;},...fields};const results=(this.events[type]||[]).map(fn=>fn(event));return Promise.all(results);}
    click(){if(this.disabled)return Promise.resolve();this.focus();if(this.tagName==='a'&&this.download)downloads.push({name:this.download,url:this.href,blob:createdUrls.get(this.href)});return this.fire('click');}
    closest(sel){return matches(this,sel)?this:this.parent?.closest(sel)||null;}
    appendChild(e){e.parent=this;this.children.push(e);}
    remove(){if(this.parent){this.parent.children=this.parent.children.filter(e=>e!==this);this.parent=null;}if(document.activeElement===this)document.activeElement=document.body;}
    focus(){if(!this.disabled)document.activeElement=this;}
    select(){this.selectionStart=0;this.selectionEnd=String(this.value).length;}
  }
  function parse(text){const out=[];for(const m of text.matchAll(/<([a-z][\w-]*)\b([^>]*?)>/gi)){const attrs={};for(const a of m[2].matchAll(/([\w-]+)(?:="([^"]*)")?/g))attrs[a[1]]=a[2]??'';const el=new El(m[1],attrs);out.push(el);if(attrs.id)ids.set(attrs.id,el);}return out;}
  all=parse(html.split('<script id="catalogue-data"')[0]);all.filter(e=>e.attrs.id).forEach(e=>ids.set(e.attrs.id,e));
  const data=new El('script');data.textContent=options.embedded??embedded;ids.set('catalogue-data',data);
  document={getElementById:id=>ids.get(id)||null,querySelectorAll:sel=>[...new Set(all.concat([...ids.values()].flatMap(e=>e.children)))].filter(e=>matches(e,sel)),createElement:tag=>new El(tag),body:new El('body'),execCommand:()=>options.execCopyResult??false};document.activeElement=document.body;
  const location=new URL(options.href||'file:///offline/explorer.html');
  const window={location,crypto:options.noCrypto?undefined:webcrypto,isSecureContext:options.secure??location.protocol==='https:',addEventListener:(name,fn)=>{(windowEvents[name]??=[]).push(fn);}};
  const navigator=options.clipboard?{clipboard:{writeText:options.clipboard}}:{};
  class urlApi extends URL{static createObjectURL(blob){if(options.failDownload)throw Error('Downloads blocked');const u='blob:test-'+(++serial);createdUrls.set(u,blob);return u;}static revokeObjectURL(u){createdUrls.delete(u);}}
  const context={window,document,navigator,console,Blob,URL:urlApi,AbortController,TextDecoder,DecompressionStream:options.decompression===false?undefined:DecompressionStream,fetch:options.fetch?((url,init)=>{requests.push({url,init});return options.fetch(url,init);}):undefined,setTimeout:fn=>{const id=++serial;timers.set(id,fn);return id;},clearTimeout:id=>timers.delete(id)};
  vm.runInNewContext(js,context,{timeout:5000});
  return {api:window.HassettAtlas,ids,document,windowEvents,downloads,createdUrls,window,requests,timers,fireWindow:(name,event)=>{for(const f of windowEvents[name]||[])f(event);}};
}

// Exact representative Gram matrices from the Python engine for two pairs beyond
// the embedded range. Stream tests omit origins/candidates already tested above.
const onlineFixtures=[{"schema_version":"1.0","d1":8,"d2":50,"component_count":12,"complete":true,"algorithm":"Yang\u2013Yu Algorithm 7.6","components":[{"id":"8-50-c01","gram":[[3,1,1],[1,3,-5],[1,-5,17]],"determinant":48,"tau":-5,"index":1,"h":[1,0,0],"origins":[],"k3_association":{"admissible":true}},{"id":"8-50-c02","gram":[[3,1,1],[1,3,-4],[1,-4,17]],"determinant":77,"tau":-4,"index":1,"h":[1,0,0],"origins":[],"k3_association":{"admissible":true}},{"id":"8-50-c03","gram":[[3,1,1],[1,3,-3],[1,-3,17]],"determinant":100,"tau":-3,"index":1,"h":[1,0,0],"origins":[],"k3_association":{"admissible":true}},{"id":"8-50-c04","gram":[[3,1,1],[1,3,-2],[1,-2,17]],"determinant":117,"tau":-2,"index":1,"h":[1,0,0],"origins":[],"k3_association":{"admissible":true}},{"id":"8-50-c05","gram":[[3,1,1],[1,3,-1],[1,-1,17]],"determinant":128,"tau":-1,"index":1,"h":[1,0,0],"origins":[],"k3_association":{"admissible":true}},{"id":"8-50-c06","gram":[[3,1,1],[1,3,0],[1,0,17]],"determinant":133,"tau":0,"index":1,"h":[1,0,0],"origins":[],"k3_association":{"admissible":true}},{"id":"8-50-c07","gram":[[3,1,1],[1,3,1],[1,1,17]],"determinant":132,"tau":1,"index":1,"h":[1,0,0],"origins":[],"k3_association":{"admissible":true}},{"id":"8-50-c08","gram":[[3,1,1],[1,3,2],[1,2,17]],"determinant":125,"tau":2,"index":1,"h":[1,0,0],"origins":[],"k3_association":{"admissible":true}},{"id":"8-50-c09","gram":[[3,1,1],[1,3,3],[1,3,17]],"determinant":112,"tau":3,"index":1,"h":[1,0,0],"origins":[],"k3_association":{"admissible":true}},{"id":"8-50-c10","gram":[[3,1,1],[1,3,4],[1,4,17]],"determinant":93,"tau":4,"index":1,"h":[1,0,0],"origins":[],"k3_association":{"admissible":true}},{"id":"8-50-c11","gram":[[3,1,1],[1,3,5],[1,5,17]],"determinant":68,"tau":5,"index":1,"h":[1,0,0],"origins":[],"k3_association":{"admissible":true}},{"id":"8-50-c12","gram":[[3,1,1],[1,3,6],[1,6,17]],"determinant":37,"tau":6,"index":1,"h":[1,0,0],"origins":[],"k3_association":{"admissible":true}}],"candidates":[]},{"schema_version":"1.0","d1":8,"d2":54,"component_count":7,"complete":true,"algorithm":"Yang\u2013Yu Algorithm 7.6","components":[{"id":"8-54-c01","gram":[[3,1,0],[1,3,0],[0,0,18]],"determinant":144,"tau":0,"index":1,"h":[1,0,0],"origins":[],"k3_association":{"admissible":true}},{"id":"8-54-c02","gram":[[3,1,0],[1,3,1],[0,1,18]],"determinant":141,"tau":1,"index":1,"h":[1,0,0],"origins":[],"k3_association":{"admissible":true}},{"id":"8-54-c03","gram":[[3,1,0],[1,3,2],[0,2,18]],"determinant":132,"tau":2,"index":1,"h":[1,0,0],"origins":[],"k3_association":{"admissible":true}},{"id":"8-54-c04","gram":[[3,1,0],[1,3,3],[0,3,18]],"determinant":117,"tau":3,"index":1,"h":[1,0,0],"origins":[],"k3_association":{"admissible":true}},{"id":"8-54-c05","gram":[[3,1,0],[1,3,4],[0,4,18]],"determinant":96,"tau":4,"index":1,"h":[1,0,0],"origins":[],"k3_association":{"admissible":true}},{"id":"8-54-c06","gram":[[3,1,0],[1,3,5],[0,5,18]],"determinant":69,"tau":5,"index":1,"h":[1,0,0],"origins":[],"k3_association":{"admissible":true}},{"id":"8-54-c07","gram":[[3,1,0],[1,3,6],[0,6,18]],"determinant":36,"tau":6,"index":1,"h":[1,0,0],"origins":[],"k3_association":{"admissible":true}}],"candidates":[]}];
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
function assetFor(result,compression='gzip'){
  const key=[result.d1,result.d2].sort((a,b)=>a-b).join('-'),raw=Buffer.from(JSON.stringify(result)+'\n'),stored=compression==='gzip'?gzipSync(raw,{mtime:0}):raw;
  return {raw,stored,row:{key,d1:result.d1,d2:result.d2,component_count:result.component_count,path:'pairs/'+key+'.json'+(compression==='gzip'?'.gz':''),compression,bytes:stored.length,uncompressed_bytes:raw.length,sha256:sha(stored),uncompressed_sha256:sha(raw)}};
}
function indexFor(assets,maximum=54,complete=false){
  const discriminants=[];for(let d=8;d<=maximum;d++)if(d%6===0||d%6===2)discriminants.push(d);
  const expected=discriminants.length*(discriminants.length-1)/2;
  return {schema_version:'1.1',max_discriminant:maximum,discriminants,expected_pair_count:expected,pair_count:assets.length,component_count:assets.reduce((n,a)=>n+a.row.component_count,0),complete,failed_pair_count:0,pending_pair_count:complete?0:expected-assets.length,pairs:assets.map(a=>a.row)};
}
const responseFor=(body,status=200)=>new Response(body,{status,headers:{'content-type':'application/octet-stream','content-length':String(Buffer.byteLength(body))}});
const jsonResponse=value=>responseFor(JSON.stringify(value));
function deferred(){let resolve,reject;const promise=new Promise((yes,no)=>{resolve=yes;reject=no;});return {promise,resolve,reject};}
function fetcher(index,assets,override){return async(url,init)=>{
  const pathname=new URL(url).pathname;
  if(pathname.endsWith('/catalogue-index.json'))return jsonResponse(index);
  const asset=assets.find(a=>pathname.endsWith('/'+a.row.path));
  if(!asset)return responseFor('missing',404);
  return override?override(asset,url,init):responseFor(asset.stored);
};}

(async()=>{
const h=harness(),{api,ids,document}=h;
assert(api);assert.strictEqual(api.getState().ready,true);assert.strictEqual(api.getState().componentCount,5);assert.strictEqual(api.getState().catalogueSize,66);assert.strictEqual(ids.get('startup-notice').hidden,true);
for(const control of document.querySelectorAll('[data-requires-js]'))assert.strictEqual(control.disabled,false);
assert.match(ids.get('proof-status').innerHTML,/Published case verified/);assert.match(ids.get('proof-status').innerHTML,/Auel et al/);

// Exercise actual button handlers, not just the optional public integration API.
for(const [a,b,n] of [[8,14,5],[8,26,8],[8,38,10],[12,20,6],[20,38,17]]){
 const preset=document.querySelectorAll('.preset').find(e=>e.dataset.pair===a+','+b);await preset.click();
 assert.strictEqual(api.getState().componentCount,n);assert.strictEqual(ids.get('component-count').textContent,String(n));assert.strictEqual(ids.get('components').querySelectorAll('[data-component]').length,n);assert(ids.get('inspector-body').innerHTML.includes('Higher-rank specializations'));
}
ids.get('d1').value='12';ids.get('d2').value='20';await ids.get('pair-form').fire('submit');assert.strictEqual(ids.get('saturation-count').textContent,'1');
const tau=ids.get('tau-strip').querySelectorAll('[data-tau]').find(e=>e.dataset.tau==='0');await tau.click();assert.match(ids.get('scan-detail').textContent,/2 distinct final components/);assert.strictEqual(document.activeElement,tau);assert.strictEqual(tau.attrs['aria-pressed'],'true');
const card=ids.get('components').querySelectorAll('[data-component]')[3];await card.click();assert.strictEqual(api.getState().selected,3);assert.strictEqual(document.activeElement,card);assert.strictEqual(card.attrs['aria-pressed'],'true');assert.match(ids.get('inspector-heading').textContent,/Component 04/);
await ids.get('table-view').click();assert.strictEqual(api.getState().mode,'table');assert(ids.get('components').innerHTML.includes('<table'));
const tableButton=ids.get('components').querySelectorAll('[data-component]')[1];await tableButton.click();assert.strictEqual(document.activeElement,tableButton);assert.strictEqual(api.getState().selected,1);
await ids.get('grid-view').click();assert.strictEqual(api.getState().mode,'grid');
ids.get('d1').value='8';ids.get('d2').value='8';await ids.get('pair-form').fire('submit');assert.match(ids.get('status').textContent,/distinct/);assert.strictEqual(ids.get('status').attrs.role,'alert');
ids.get('d1').value='10';ids.get('d2').value='14';await ids.get('pair-form').fire('submit');assert.match(ids.get('status').textContent,/modulo 6/);
ids.get('d1').value='8';ids.get('d2').value='50';await ids.get('pair-form').fire('submit');assert.strictEqual(api.getState().componentCount,null);assert.match(ids.get('components').innerHTML,/not in the bundled catalogue/);assert.match(ids.get('components').innerHTML,/intersect 8 50/);assert.strictEqual(ids.get('export-button').disabled,true);
assert.strictEqual(api.admissible(14).valid,true);assert.strictEqual(api.admissible(8).valid,false);assert.strictEqual(api.admissible(26).valid,true);assert.strictEqual(api.admissible(18).valid,false);assert.strictEqual(api.admissible(50).valid,false);
assert.throws(()=>api.loadData(null),/Expected a JSON result/);
const example=catalogue.pairs.find(r=>[r.d1,r.d2].sort((a,b)=>a-b).join('-')==='8-14');
const corrupt=JSON.parse(JSON.stringify(example));corrupt.components[0].determinant=999;assert.throws(()=>api.loadData(corrupt),/determinant disagrees/);
const nonsym=JSON.parse(JSON.stringify(example));nonsym.components[0].gram[1][0]+=1;assert.throws(()=>api.loadData(nonsym),/symmetric|determinant/);
// Async JSON input event: valid import, failed import, oversize input, and reset.
const fileInput=ids.get('json-file');fileInput.files=[{size:100,text:async()=>JSON.stringify(example)}];fileInput.value='chosen-file';await fileInput.fire('change');assert.strictEqual(api.getState().componentCount,5);assert.strictEqual(fileInput.value,'');
fileInput.files=[{size:3,text:async()=>'{x'}];await fileInput.fire('change');assert.match(ids.get('status').textContent,/Import failed/);assert.strictEqual(api.getState().componentCount,5);
fileInput.files=[{size:21*1024*1024,text:async()=>JSON.stringify(example)}];await fileInput.fire('change');assert.match(ids.get('status').textContent,/20 MB/);
// Export route verifies generated bytes and filename; no native save-dialog claim.
await ids.get('export-button').click();assert.strictEqual(h.downloads.length,1);assert.strictEqual(h.downloads[0].name,'hassett-8-14.json');const exported=JSON.parse(await h.downloads[0].blob.text());assert.strictEqual(exported.component_count,5);assert.deepStrictEqual(exported.components[0].gram,example.components[0].gram);
const xss=JSON.parse(JSON.stringify(example));xss.components[0].id='<img src=x onerror=alert(1)>';xss.components[0].k3_association.criterion='<script>alert(1)</script>';api.loadData(xss);api.choosePair(8,14);assert(!ids.get('inspector-body').innerHTML.includes('<script>'));assert(!ids.get('inspector-body').innerHTML.includes('<img'));
const incomplete=JSON.parse(JSON.stringify(example));incomplete.complete=false;api.loadData(incomplete);api.choosePair(8,14);assert.strictEqual(api.getState().componentCount,null);assert.strictEqual(ids.get('component-count').textContent,'—');assert.match(ids.get('proof-status').innerHTML,/Incomplete imported result/);
api.loadData(catalogue);api.choosePair(8,14);
let node=ids.get('network').querySelectorAll('[data-d]').find(e=>e.dataset.d==='8');node.focus();await node.fire('keydown',{key:'Enter'});node=ids.get('network').querySelectorAll('[data-d]').find(e=>e.dataset.d==='8');assert.strictEqual(document.activeElement,node);
node=ids.get('network').querySelectorAll('[data-d]').find(e=>e.dataset.d==='26');await node.fire('keydown',{key:' '});assert.strictEqual(api.getState().componentCount,8);assert.strictEqual(document.activeElement.dataset.d,'26');
assert.strictEqual(api.determinant([[3,1,1],[1,3,0],[1,0,5]]),'37');
// Clipboard failures must keep the matrix accessible and must not leak a hidden textarea.
await ids.get('copy-matrix').click();assert.strictEqual(ids.get('copy-fallback').hidden,false);assert.strictEqual(document.activeElement,ids.get('copy-fallback-value'));assert.strictEqual(document.body.children.length,0);assert.match(ids.get('copy-fallback-value').value,/^\[\[3,/);
const clipboardDenied=harness({secure:true,clipboard:async()=>{throw Error('Denied');},execCopyResult:true});await clipboardDenied.ids.get('copy-matrix').click();assert.match(clipboardDenied.ids.get('toast').textContent,/matrix copied/);assert.strictEqual(clipboardDenied.document.body.children.length,0);
let clipboardText='';const clipboardAllowed=harness({secure:true,clipboard:async text=>{clipboardText=text;}});await clipboardAllowed.ids.get('copy-matrix').click();assert.match(clipboardText,/^\[\[3,/);assert.strictEqual(clipboardAllowed.document.activeElement,clipboardAllowed.ids.get('copy-matrix'));
const blockedExport=harness({failDownload:true});await blockedExport.ids.get('export-button').click();assert.match(blockedExport.ids.get('status').textContent,/browser could not save/);
// Startup failure remains legible and can recover from a valid imported catalogue.
const failed=harness({embedded:'{broken'});assert.strictEqual(failed.api.getState().ready,false);assert.strictEqual(failed.ids.get('startup-notice').hidden,false);assert.match(failed.ids.get('startup-title').textContent,/could not start/);assert.strictEqual(failed.ids.get('d1').disabled,true);assert.strictEqual(failed.ids.get('import-button').disabled,false);assert.match(failed.ids.get('components').innerHTML||html,/data-static-component/);
failed.ids.get('json-file').files=[{size:100,text:async()=>JSON.stringify(catalogue)}];await failed.ids.get('json-file').fire('change');assert.strictEqual(failed.api.getState().ready,true);assert.strictEqual(failed.ids.get('startup-notice').hidden,true);assert.strictEqual(failed.api.getState().componentCount,3); // first bundled pair C8∩C12
h.fireWindow('error',{message:'synthetic runtime error'});assert.match(ids.get('status').textContent,/synthetic runtime error/);assert.strictEqual(api.getState().lastError,'synthetic runtime error');
// HTTPS catalogue loading and real Web Streams/gzip/hash execution.
const assets=onlineFixtures.map(r=>assetFor(r)),partialIndex=indexFor(assets);
const remote=harness({href:'https://atlas.test/explorer.html',fetch:fetcher(partialIndex,assets)});
assert.strictEqual(remote.api.getState().indexState,'loading');assert.strictEqual(remote.api.getState().componentCount,5);
await remote.api.whenIdle();assert.strictEqual(remote.api.getState().indexState,'ready');assert.strictEqual(remote.api.getState().availableBound,54);assert.strictEqual(remote.api.getState().availablePairs,2);assert.strictEqual(remote.api.getState().coverageComplete,false);assert.match(remote.ids.get('catalogue-scope').textContent,/incomplete/);assert.strictEqual(remote.requests.length,1);
remote.api.choosePair(8,50);assert.strictEqual(remote.api.getState().loadPhase,'loading');assert.strictEqual(remote.api.getState().componentCount,null);assert.strictEqual(remote.ids.get('results').attrs['aria-busy'],'true');
await remote.api.whenIdle();assert.strictEqual(remote.api.getState().componentCount,12);assert.strictEqual(remote.api.getState().loadPhase,'ready');assert.strictEqual(remote.ids.get('results').attrs['aria-busy'],'false');assert.strictEqual(remote.requests.length,2);assert(remote.requests[1].url.includes('.json.gz?v='));
remote.api.choosePair(8,50);await remote.api.whenIdle();assert.strictEqual(remote.requests.length,2); // downloaded pair is reused
remote.api.choosePair(8,26);assert.strictEqual(remote.api.getState().componentCount,8);assert.strictEqual(remote.requests.length,2); // embedded pair never needs a shard fetch
assert(remote.ids.get('network').querySelectorAll('[data-d]').length<=12);assert.match(remote.ids.get('network-caption').textContent,/Showing 12 of/);
// Complete range coverage is verified, not merely trusted from a boolean.
const completeAssets=catalogue.pairs.map(r=>assetFor(r,'none'));
const complete=harness({href:'https://atlas.test/',fetch:fetcher(indexFor(completeAssets,42,true),completeAssets)});await complete.api.whenIdle();assert.strictEqual(complete.api.getState().coverageComplete,true);assert.match(complete.ids.get('catalogue-scope').textContent,/66 computed intersections/);
const falseComplete=indexFor(assets);falseComplete.complete=true;falseComplete.pending_pair_count=0;
const inconsistent=harness({href:'https://atlas.test/',fetch:fetcher(falseComplete,assets)});await inconsistent.api.whenIdle();assert.strictEqual(inconsistent.api.getState().indexState,'error');assert.match(inconsistent.ids.get('catalogue-scope').textContent,/missing pairs/);
// A desired pair selected before the large index arrives is loaded automatically.
const indexGate=deferred();const duringIndex=harness({href:'https://atlas.test/',fetch:(url,init)=>new URL(url).pathname.endsWith('/catalogue-index.json')?indexGate.promise:fetcher(partialIndex,assets)(url,init)});
duringIndex.api.choosePair(8,50);assert.strictEqual(duringIndex.api.getState().loadPhase,'waiting-index');assert.match(duringIndex.ids.get('status').textContent,/Checking/);indexGate.resolve(jsonResponse(partialIndex));await duringIndex.api.whenIdle();assert.strictEqual(duringIndex.api.getState().componentCount,12);assert.strictEqual(duringIndex.requests.length,2);
const indexGate2=deferred();const backToEmbedded=harness({href:'https://atlas.test/',fetch:(url,init)=>new URL(url).pathname.endsWith('/catalogue-index.json')?indexGate2.promise:fetcher(partialIndex,assets)(url,init)});
backToEmbedded.api.choosePair(8,50);backToEmbedded.api.choosePair(8,26);indexGate2.resolve(jsonResponse(partialIndex));await backToEmbedded.api.whenIdle();assert.strictEqual(backToEmbedded.api.getState().componentCount,8);assert.strictEqual(backToEmbedded.requests.length,1);
// Recovering from corrupt embedded data must also start the hosted index.
const hostedRecovery=harness({href:'https://atlas.test/',embedded:'{broken',fetch:fetcher(partialIndex,assets)});assert.strictEqual(hostedRecovery.requests.length,0);hostedRecovery.ids.get('json-file').files=[{size:100,text:async()=>JSON.stringify(example)}];await hostedRecovery.ids.get('json-file').fire('change');await hostedRecovery.api.whenIdle();assert.strictEqual(hostedRecovery.api.getState().ready,true);assert.strictEqual(hostedRecovery.api.getState().indexState,'ready');assert.strictEqual(hostedRecovery.requests.length,1);
// Rapid navigation: old responses cannot replace the new selection or its cache.
const gateA=deferred(),gateB=deferred();let callsA=0;
const race=harness({href:'https://atlas.test/',fetch:fetcher(partialIndex,assets,asset=>asset.row.key==='8-50'?(++callsA===1?gateA.promise:responseFor(asset.stored)):gateB.promise)});await race.api.whenIdle();
race.api.choosePair(8,50);const oldWork=race.api.whenIdle();await Promise.resolve();race.api.choosePair(8,54);assert.strictEqual(race.requests[1].init.signal.aborted,true);
gateB.resolve(responseFor(assets[1].stored));await race.api.whenIdle();assert.strictEqual(race.api.getState().componentCount,7);
gateA.resolve(responseFor(assets[0].stored));await oldWork;assert.strictEqual(race.api.getState().componentCount,7);assert.strictEqual(race.api.getState().catalogueSize,67);
race.api.choosePair(8,50);await race.api.whenIdle();assert.strictEqual(race.api.getState().componentCount,12);assert.strictEqual(callsA,2);
// Plain JSON is still supported, and gzip capability is guarded after integrity checks.
const plain=assetFor(onlineFixtures[0],'none');const noGzipPlain=harness({href:'https://atlas.test/',decompression:false,fetch:fetcher(indexFor([plain]),[plain])});await noGzipPlain.api.whenIdle();noGzipPlain.api.choosePair(8,50);await noGzipPlain.api.whenIdle();assert.strictEqual(noGzipPlain.api.getState().componentCount,12);
const noGzip=harness({href:'https://atlas.test/',decompression:false,fetch:fetcher(partialIndex,assets)});await noGzip.api.whenIdle();noGzip.api.choosePair(8,50);await noGzip.api.whenIdle();assert.strictEqual(noGzip.api.getState().loadPhase,'error');assert.match(noGzip.ids.get('status').textContent,/cannot decompress/);noGzip.api.choosePair(8,14);assert.strictEqual(noGzip.api.getState().componentCount,5);
// CDN decompression is accepted only if the exact raw digest AND size match.
const decoded=harness({href:'https://atlas.test/',decompression:false,fetch:fetcher(partialIndex,assets,asset=>responseFor(asset.raw))});await decoded.api.whenIdle();decoded.api.choosePair(8,50);await decoded.api.whenIdle();assert.strictEqual(decoded.api.getState().componentCount,12);
const noRawHash=JSON.parse(JSON.stringify(partialIndex));delete noRawHash.pairs[0].uncompressed_sha256;
const unverifiedDecode=harness({href:'https://atlas.test/',fetch:fetcher(noRawHash,assets,asset=>responseFor(asset.raw))});await unverifiedDecode.api.whenIdle();unverifiedDecode.api.choosePair(8,50);await unverifiedDecode.api.whenIdle();assert.strictEqual(unverifiedDecode.api.getState().loadPhase,'error');assert.match(unverifiedDecode.ids.get('status').textContent,/SHA-256/);
// Corruption, incorrect result identity/count and unsafe index paths are rejected.
const corrupted=harness({href:'https://atlas.test/',fetch:fetcher(partialIndex,assets,asset=>{const b=Buffer.from(asset.stored);b[b.length-1]^=1;return responseFor(b);})});await corrupted.api.whenIdle();corrupted.api.choosePair(8,50);await corrupted.api.whenIdle();assert.strictEqual(corrupted.api.getState().componentCount,null);assert.match(corrupted.ids.get('status').textContent,/SHA-256/);
const wrongCount=JSON.parse(JSON.stringify(partialIndex));wrongCount.pairs[0].component_count++;wrongCount.component_count++;
const wrong=harness({href:'https://atlas.test/',fetch:fetcher(wrongCount,assets)});await wrong.api.whenIdle();wrong.api.choosePair(8,50);await wrong.api.whenIdle();assert.strictEqual(wrong.api.getState().loadPhase,'error');assert.match(wrong.ids.get('status').textContent,/disagrees/);
for(const badPath of ['../pairs/8-50.json.gz','https://elsewhere.test/data.json','pairs/8-50.json.gz?redirect=x']){
 const unsafe=JSON.parse(JSON.stringify(partialIndex));unsafe.pairs[0].path=badPath;const blocked=harness({href:'https://atlas.test/',fetch:fetcher(unsafe,assets)});await blocked.api.whenIdle();assert.strictEqual(blocked.api.getState().indexState,'error');assert.strictEqual(blocked.requests.length,1);assert.match(blocked.ids.get('catalogue-scope').textContent,/safe relative/);
}
const tooLarge=JSON.parse(JSON.stringify(partialIndex));tooLarge.pairs[0].uncompressed_bytes=20*1024*1024+1;
const bounded=harness({href:'https://atlas.test/',fetch:fetcher(tooLarge,assets)});await bounded.api.whenIdle();assert.strictEqual(bounded.api.getState().indexState,'error');assert.match(bounded.ids.get('catalogue-scope').textContent,/size limits/);
// A gzip stream cannot bypass the decompressed byte cap by lying in its index.
const hugeRaw=Buffer.alloc(20*1024*1024+1,32),hugeStored=gzipSync(hugeRaw,{mtime:0}),huge={raw:hugeRaw,stored:hugeStored,row:{...assets[0].row,bytes:hugeStored.length,uncompressed_bytes:20*1024*1024,sha256:sha(hugeStored),uncompressed_sha256:sha(hugeRaw)}};
const expansion=harness({href:'https://atlas.test/',fetch:fetcher(indexFor([huge]),[huge])});await expansion.api.whenIdle();expansion.api.choosePair(8,50);await expansion.api.whenIdle();assert.strictEqual(expansion.api.getState().loadPhase,'error');assert.match(expansion.ids.get('status').textContent,/exceeds the browser size limit/);
// Failed downloads are retryable without disabling the embedded app.
let failIndex=true;const retry=harness({href:'https://atlas.test/',fetch:(url,init)=>{if(failIndex&&new URL(url).pathname.endsWith('/catalogue-index.json'))return Promise.resolve(responseFor('unavailable',503));return fetcher(partialIndex,assets)(url,init);}});await retry.api.whenIdle();assert.strictEqual(retry.api.getState().indexState,'error');assert.strictEqual(retry.api.getState().componentCount,5);assert.strictEqual(retry.ids.get('retry-catalogue').hidden,false);failIndex=false;await retry.ids.get('retry-catalogue').click();await retry.api.whenIdle();assert.strictEqual(retry.api.getState().indexState,'ready');assert.strictEqual(retry.ids.get('retry-catalogue').hidden,true);
let failPair=true;const retryPair=harness({href:'https://atlas.test/',fetch:fetcher(partialIndex,assets,asset=>responseFor(failPair?'unavailable':asset.stored,failPair?503:200))});await retryPair.api.whenIdle();retryPair.api.choosePair(8,50);await retryPair.api.whenIdle();assert.strictEqual(retryPair.api.getState().loadPhase,'error');assert(retryPair.ids.get('retry-pair'));failPair=false;await retryPair.ids.get('retry-pair').click();await retryPair.api.whenIdle();assert.strictEqual(retryPair.api.getState().componentCount,12);
// File and unsupported protocols never request the hosted index.
for(const href of ['file:///offline/explorer.html','http://local.test/explorer.html']){const offline=harness({href,fetch:()=>{throw Error('Unexpected network request');}});await offline.api.whenIdle();assert.strictEqual(offline.requests.length,0);assert.strictEqual(offline.api.getState().hostedMode,false);assert.strictEqual(offline.api.getState().componentCount,5);}
// Optional integration against the runner's real (complete or checkpoint) output.
const dataFlag=process.argv.indexOf('--hosted-data');
let realHosted=null;
if(dataFlag!==-1){
 const directory=path.resolve(process.argv[dataFlag+1]||''),indexBytes=fs.readFileSync(path.join(directory,'catalogue-index.json')),realIndex=JSON.parse(indexBytes);
 const integration=harness({href:'https://atlas.test/',fetch:async url=>{
  const pathname=new URL(url).pathname;
  if(pathname.endsWith('/catalogue-index.json'))return responseFor(indexBytes);
  const relative=pathname.replace(/^\/data\//,'');
  if(!/^pairs\/[0-9]+-[0-9]+\.json(?:\.gz)?$/.test(relative))return responseFor('invalid path',400);
  try{return responseFor(fs.readFileSync(path.join(directory,relative)));}catch(err){return responseFor('missing',404);}
 }});
 await integration.api.whenIdle();assert.strictEqual(integration.api.getState().indexState,'ready');assert.strictEqual(integration.api.getState().availablePairs,realIndex.pair_count);assert.strictEqual(integration.api.getState().availableBound,realIndex.max_discriminant);assert.strictEqual(integration.api.getState().coverageComplete,realIndex.complete);
 const choices=realIndex.pairs.filter(r=>Math.max(r.d1,r.d2)>42),sample=[choices[0],choices[Math.floor(choices.length/2)],choices[choices.length-1]].filter(Boolean);
 for(const row of sample){integration.api.choosePair(row.d1,row.d2);await integration.api.whenIdle();assert.strictEqual(integration.api.getState().loadPhase,'ready');assert.strictEqual(integration.api.getState().componentCount,row.component_count);assert.strictEqual(integration.ids.get('components').querySelectorAll('[data-component]').length,row.component_count);assert(integration.ids.get('network').querySelectorAll('[data-d]').length<=12);}
 realHosted={max_discriminant:realIndex.max_discriminant,pair_count:realIndex.pair_count,complete:realIndex.complete,verified_shards:sample.map(r=>r.key)};
}
const report={passed:true,checks:assertions,catalogue_pairs:catalogue.pairs.length,real_hosted_data:realHosted,method:'Actual embedded JavaScript executed in Node VM with a DOM test double; focus, disabled controls and async event routes modeled. Native Web Streams, gzip and WebCrypto execute against mocked same-origin HTTP responses. No browser layout, native clipboard, or actual network/download verification.',componentCounts:{'8,14':5,'8,26':8,'8,38':10,'12,20':6,'20,38':17},features:['automatic startup','static preview fallback','startup error and import recovery','form submission','preset clicks','component and tau focus preservation','matrix/table controls','keyboard network selection','JSON import success/error/size limit','export JSON bytes','clipboard success/denial/manual-copy fallback','published validation metadata','missing-pair state','incomplete-result state','K3 arithmetic','HTML escaping','runtime error diagnostics','HTTPS index and per-pair lazy loading','complete and partial range metadata','selection-before-index race','rapid-selection cancellation and stale-response protection','real gzip decompression and SHA-256 validation','verified CDN decompression fallback','safe paths and compressed/decompressed size caps','network retry states','offline no-network behavior']};
console.log(JSON.stringify(report,null,2));
if(process.argv.includes('--write-report')){fs.mkdirSync(path.join(root,'docs'),{recursive:true});fs.writeFileSync(path.join(root,'docs/web_validation.json'),JSON.stringify(report,null,2)+'\n');}
})().catch(err=>{console.error(err);process.exitCode=1;});
