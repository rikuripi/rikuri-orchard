'use strict';
// Optional browser regression tooling; every request is synthetic or aborted.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('playwright');
const root = path.resolve(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const id = '12345678-1234-4234-9234-123456789abc';
const task = {id, status:'DONE', application_status:'APPLIED',
  request:'Review the synthetic heading update. <img src=x onerror="window.hostileExecuted=true">',
  evidence:'Synthetic execution report', receipt:{started:true}};
const base = {schema_version:1,kind:'orchard_legacy_snapshot_observation',legacy_task_id:id,
  metadata_sha256:'a'.repeat(64),reported_status:'DONE',reported_execution:'completed',
  reported_application:'APPLIED',execution:'unverified',acceptance:'unverified',
  application:'unverified',authority:'none',freshness:'snapshot_only',runtime_compatible:false,
  missing_runtime_seams:['prepare','start_ack_binding','observe_cursor','confirmed_cancel','trusted_capture','independent_gate']};
(async()=>{
 const browser = await chromium.launch({headless:true,
   ...(process.env.ORCHARD_TEST_BROWSER?{executablePath:process.env.ORCHARD_TEST_BROWSER}:{})});
 try {
  const context = await browser.newContext({viewport:{width:1280,height:1100},reducedMotion:'reduce',serviceWorkers:'block'});
  let mode='success', requests=[], unexpected=[], errors=[];
  await context.route('**/*',async route=>{
   const req=route.request(), url=new URL(req.url());requests.push([req.method(),url.pathname]);
   if(req.method()!=='GET'||url.origin!=='http://orchard.test'){
    unexpected.push([req.method(),req.url()]);return route.abort();
   }
   if(url.pathname==='/')return route.fulfill({contentType:'text/html',body:html});
   if(url.pathname==='/api/seeds')return route.fulfill({json:{seeds:[]}});
   if(url.pathname==='/api/tasks')return route.fulfill({json:{enabled:true,tasks:[task]}});
   if(url.pathname==='/api/tasks/'+id+'/observation'){
    if(mode==='http-error')return route.fulfill({status:409,json:{error:'PRIVATE-SERVER-SENTINEL'}});
    if(mode==='malformed')return route.fulfill({contentType:'text/html',body:'not json'});
    const observation=structuredClone(base);
    if(mode==='wrong-id')observation.legacy_task_id='22345678-1234-4234-9234-123456789abc';
    if(mode==='bad-authority')observation.acceptance='passed';
    if(mode==='unknown-version')observation.schema_version=2;
    if(mode==='hostile-app')observation.reported_application='<img src=x onerror="window.hostileExecuted=true">';
    if(mode==='running'){observation.reported_status='RUNNING';observation.reported_execution='running';observation.reported_application=null;}
    return route.fulfill({json:{observation}});
   }
   unexpected.push([req.method(),req.url()]);return route.abort();
  });
  const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
  async function open(){
   await page.goto('http://orchard.test/');
   await page.getByRole('button',{name:'Orchard Crew',exact:false}).click();
   await page.getByRole('button',{name:'Load status details',exact:true}).waitFor();
  }
  const fields=key=>page.locator('[data-observation-field="'+key+'"]');
  async function load(){
   await page.getByRole('button',{name:'Load status details',exact:true}).click();
   await page.getByRole('button',{name:'Refresh status details',exact:true}).waitFor();
   await page.waitForFunction(()=>!document.querySelector('.task-observation button').disabled);
  }
  await open();
  assert.equal(await fields('acceptance').textContent(),'Unverified');
  assert.equal(requests.filter(x=>x[1].endsWith('/observation')).length,0);
  await load();
  assert.equal(await fields('execution').textContent(),'Completed (reported)');
  assert.equal(await fields('application').textContent(),'Unverified · Reported: Applied');
  assert.equal(await fields('acceptance').textContent(),'Unverified');
  assert.equal(await page.locator('.task-observation').getByRole('button').count(),1);
  assert.match(await page.locator('article > strong').textContent(),/^Reported task status:/);
  assert.equal(await page.locator('article img').count(),0);
  assert.equal(await page.evaluate(()=>window.hostileExecuted),undefined);
  console.log('PASS: success, on-demand GET, separate unverified states and task-text safety');
  if(process.env.ORCHARD_UI_OUTPUT){
   fs.mkdirSync(process.env.ORCHARD_UI_OUTPUT,{recursive:true});
   await page.screenshot({path:path.join(process.env.ORCHARD_UI_OUTPUT,'desktop.png'),fullPage:true});
  }
  mode='http-error';
  await page.getByRole('button',{name:'Refresh status details',exact:true}).click();
  await page.getByRole('status').filter({hasText:'Status details unavailable'}).waitFor();
  assert.equal(await fields('execution').textContent(),'Not loaded');
  assert.equal(await fields('application').textContent(),'Unverified');
  assert.ok(!(await page.locator('body').textContent()).includes('PRIVATE-SERVER-SENTINEL'));
  console.log('PASS: failed refresh clears stale claims and withholds server text');
  for(mode of ['wrong-id','bad-authority','unknown-version','hostile-app','malformed']){
   await open();await load();
   assert.match(await page.locator('.task-observation [role=status]').textContent(),/Status details unavailable/);
   assert.equal(await fields('execution').textContent(),'Not loaded');
   assert.equal(await fields('acceptance').textContent(),'Unverified');
   assert.equal(await page.locator('article img').count(),0);
   console.log('PASS: refused '+mode);
  }
  mode='running';await open();await load();
  assert.equal(await fields('execution').textContent(),'Running (reported)');
  assert.equal(await fields('application').textContent(),'Unverified — no saved report');
  console.log('PASS: running report with no application evidence');
  mode='success';await page.setViewportSize({width:390,height:1000});await open();await load();
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth));
  const boxes=await page.locator('.observation-fields > div').evaluateAll(nodes=>nodes.map(n=>({top:n.getBoundingClientRect().top,left:n.getBoundingClientRect().left})));
  assert.ok(boxes[0].top<boxes[1].top&&boxes[1].top<boxes[2].top);
  if(process.env.ORCHARD_UI_OUTPUT)await page.screenshot({path:path.join(process.env.ORCHARD_UI_OUTPUT,'mobile.png'),fullPage:true});
  console.log('PASS: mobile stacked fields without horizontal overflow');
  assert.deepEqual(unexpected,[]);assert.deepEqual(errors,[]);
  assert.ok(requests.every(([method])=>method==='GET'));
  console.log('PASS: all page requests intercepted; no POST, unknown destination or page errors');
  await context.close();
 } finally { await browser.close(); }
})().catch(error=>{console.error(error);process.exitCode=1});
