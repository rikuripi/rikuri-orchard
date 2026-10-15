'use strict';
// Real loopback HTTP/SQLite test; no production server, database or worker.
const assert=require('node:assert/strict');
const path=require('node:path');
const crypto=require('node:crypto');
const {spawn}=require('node:child_process');
const readline=require('node:readline');
const os=require('node:os');
const http=require('node:http');
const fs=require('node:fs');
const {chromium}=require('playwright');
function bounded(promise,ms,label){
 let timer;
 return Promise.race([promise,new Promise((_,reject)=>{timer=setTimeout(()=>reject(Error(label+' timed out')),ms)})]).finally(()=>clearTimeout(timer));
}
(async()=>{
 const fixture=spawn(process.env.ORCHARD_TEST_PYTHON||'python3',
  ['-I','-B',path.join(__dirname,'observation_http_fixture.py')],
  {stdio:['pipe','pipe','pipe'],env:{PATH:process.env.PATH,TMPDIR:os.tmpdir()}});
 let stderr='';fixture.stderr.on('data',chunk=>stderr+=chunk);
 const exited=new Promise((resolve,reject)=>{fixture.once('error',reject);fixture.once('exit',(code,signal)=>resolve({code,signal}))});
 const lines=readline.createInterface({input:fixture.stdout})[Symbol.asyncIterator]();
 async function receive(expected){
  const item=await bounded(lines.next(),10000,'fixture '+expected);
  assert.ok(!item.done,'fixture exited early: '+stderr);
  const message=JSON.parse(item.value);assert.equal(message.event,expected);
  return message;
 }
 async function control(command){
  fixture.stdin.write(JSON.stringify({command})+'\n');
  const result=await receive(command);
  assert.equal(result.database_unchanged_by_reads,true);assert.equal(result.forbidden_actions,0);
  return result;
 }
 let browser,stopped=false;
 try{
  const ready=await receive('ready'),url=new URL(ready.origin);
  assert.equal(url.hostname,'127.0.0.1');assert.ok(Number(url.port)>0);
  const origin=url.origin,taskId=ready.task_id;
  assert.match(taskId,/^[0-9a-f-]{36}$/);
  const endpoint=origin+'/api/tasks/'+taskId+'/observation';
  async function get(url,headers={}){
   return fetch(url,{headers,signal:AbortSignal.timeout(5000)});
  }
  let response=await get(endpoint);assert.equal(response.status,200);
  assert.equal(response.headers.get('cache-control'),'no-store');
  assert.equal(response.headers.get('x-content-type-options'),'nosniff');
  assert.match(response.headers.get('content-type'),/^application\/json/);
  let payload=await response.text();assert.ok(!payload.includes('PRIVATE-SENTINEL'));
  const observation=JSON.parse(payload).observation;
  assert.equal(observation.acceptance,'unverified');assert.equal(observation.application,'unverified');
  const selected={application_status:'APPLIED',id:taskId,status:'DONE'};
  assert.equal(observation.metadata_sha256,crypto.createHash('sha256').update(JSON.stringify(selected)).digest('hex'));
  assert.equal((await get(endpoint,{Origin:'https://foreign.example'})).status,403);
  const hostStatus=await new Promise((resolve,reject)=>{
   const request=http.get(endpoint,{headers:{Host:'foreign.example'}},response=>{
    response.resume();response.once('end',()=>resolve(response.statusCode));
   });
   request.setTimeout(5000,()=>request.destroy(Error('Host check timed out')));
   request.once('error',reject);
  });
  assert.equal(hostStatus,403);
  assert.equal((await get(origin+'/api/tasks/12345678-1234-4234-9234-123456789abc/observation')).status,404);
  await control('check');
  console.log('PASS: real HTTP success, schema metadata digest, payload omission, no-store headers and host/origin/missing refusals');
  browser=await chromium.launch({headless:true,
    ...(process.env.ORCHARD_TEST_BROWSER?{executablePath:process.env.ORCHARD_TEST_BROWSER}:{})});
  const context=await browser.newContext({viewport:{width:1280,height:1100},reducedMotion:'reduce',serviceWorkers:'block'});
  const requests=[],rejected=[],errors=[];
  await context.route('**/*',route=>{
   const request=route.request();requests.push([request.method(),request.url()]);
   if(request.method()!=='GET'||new URL(request.url()).origin!==origin){
    rejected.push([request.method(),request.url()]);return route.abort();
   }
   return route.continue();
  });
  const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
  await page.goto(origin);
  await page.getByRole('button',{name:'Orchard Crew',exact:false}).click();
  await page.getByRole('button',{name:'Load status details',exact:true}).click();
  await page.locator('.task-observation [role=status]').filter({hasText:'Saved snapshot loaded'}).waitFor();
  const field=key=>page.locator('[data-observation-field="'+key+'"]');
  assert.equal(await field('execution').textContent(),'Completed (reported)');
  assert.equal(await field('acceptance').textContent(),'Unverified');
  assert.equal(await field('application').textContent(),'Unverified · Reported: Applied');
  await control('check');
  console.log('PASS: browser → real HTTP Handler → SQLite → validated unverified status panel; database bytes unchanged');
  if(process.env.ORCHARD_UI_OUTPUT){
   fs.mkdirSync(process.env.ORCHARD_UI_OUTPUT,{recursive:true});
   await page.screenshot({path:path.join(process.env.ORCHARD_UI_OUTPUT,'real-http.png'),fullPage:true});
  }
  await control('unsupported');
  await page.getByRole('button',{name:'Refresh status details',exact:true}).click();
  await page.locator('.task-observation [role=status]').filter({hasText:'Status details unavailable'}).waitFor();
  assert.equal(await field('execution').textContent(),'Not loaded');
  assert.equal(await field('acceptance').textContent(),'Unverified');
  assert.equal(await field('application').textContent(),'Unverified');
  response=await get(endpoint);assert.equal(response.status,409);
  assert.ok(!(await response.text()).includes('PRIVATE-SENTINEL'));
  await control('check');
  console.log('PASS: real unsupported database status returns409; failed browser refresh clears stale claims without changing storage');
  await control('restore');
  await page.getByRole('button',{name:'Refresh status details',exact:true}).click();
  await page.locator('.task-observation [role=status]').filter({hasText:'Saved snapshot loaded'}).waitFor();
  assert.equal(await field('execution').textContent(),'Completed (reported)');
  assert.equal(await field('acceptance').textContent(),'Unverified');
  await control('check');
  assert.deepEqual(rejected,[]);assert.deepEqual(errors,[]);
  assert.ok(requests.every(([method,address])=>method==='GET'&&new URL(address).origin===origin));
  console.log('PASS: restored fixture reloads; browser requests only real loopback GETs, no POST or page errors');
  await context.close();await browser.close();browser=null;
  await control('stop');
  const cleaned=await receive('cleaned');
  assert.equal(cleaned.server_stopped,true);assert.equal(cleaned.fixture_removed,true);
  const exit=await bounded(exited,5000,'fixture shutdown');assert.equal(exit.code,0,stderr);
  stopped=true;
  console.log('PASS: browser/server stopped and temporary SQLite/source/run directories removed');
 }finally{
  if(browser)await browser.close();
  if(!stopped){
   if(fixture.exitCode===null){
    fixture.stdin.end();
    const outcome=await bounded(exited,5000,'fixture emergency cleanup').catch(()=>null);
    if(!outcome){fixture.kill('SIGTERM');await bounded(exited,3000,'fixture termination').catch(()=>fixture.kill('SIGKILL'))}
   }
  }
 }
})().catch(error=>{console.error(error);process.exitCode=1});
