// Replays the saved synthetic pre-undo state. No provider transport or key exists.
import {mkdir,mkdtemp,readFile,writeFile} from 'node:fs/promises';
import {resolve,dirname,join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createWorkbenchServer} from '../chuangyuzhou/yuzhou/backend/server.mjs';
import {createHermesService} from '../chuangyuzhou/yuzhou/backend/hermes.mjs';
import {RUNTIME_ROOT,assertRuntimePath} from '../chuangyuzhou/yuzhou/runtime.mjs';

const root=resolve(dirname(fileURLToPath(import.meta.url)),'../..');
const evidence=join(root,'web-track/evidence/WEB-008');
const captured=JSON.parse(await readFile(join(evidence,'07-refreshed-and-linked.json'),'utf8'));
const parent=assertRuntimePath(join(RUNTIME_ROOT,'tests-temp'));
await mkdir(parent,{recursive:true});
const directory=assertRuntimePath(await mkdtemp(join(parent,'WEB-008-replay-')));
const origin='http://127.0.0.1:4396';
let cookie='',csrf='',buffer='',queue=Promise.resolve();
const app=await createWorkbenchServer({dataDir:directory,secureCookie:false,publicOrigin:origin,
  setupToken:'WEB-008-offline-replay-setup-only',modelFactory:({dataDir,store})=>createHermesService({dataDir,store,
    env:{},engineAvailable:()=>false,runModel:async()=>{throw Error('No model may run during offline replay.');}})});
await new Promise((resolve,reject)=>{app.server.once('error',reject);app.server.listen(4396,'127.0.0.1',resolve);});
async function api(path,method='GET',body){
  const response=await fetch(origin+path,{method,headers:{Connection:'close',...(body?{'Content-Type':'application/json'}:{}),
    ...(cookie?{Cookie:cookie,'X-CSRF-Token':csrf}:{}),...(method!=='GET'?{Origin:origin}:{})},...(body?{body:JSON.stringify(body)}:{})});
  const setCookie=response.headers.get('set-cookie');if(setCookie)cookie=setCookie.split(';')[0];
  const value=await response.json();if(value.csrfToken)csrf=value.csrfToken;
  delete value.csrfToken;return {status:response.status,body:value};
}
const setup=await api('/api/auth/setup','POST',{username:'web008-synthetic',password:'WEB-008-synthetic-password-only',setupToken:'WEB-008-offline-replay-setup-only'});
if(setup.status!==201)throw Error('Offline replay setup failed.');
const current=await api('/api/workspace');
const seeded=await api('/api/workspace','PUT',{baseRevision:current.body.revision,state:captured.workspace.state});
if(seeded.status!==200)throw Error('Offline replay seed failed.');
const emit=value=>console.log(JSON.stringify(value));
async function command(input){
  if(input.action==='capture'){
    if(!/^[a-z0-9-]{1,60}$/.test(input.label))throw Error('invalid_label');
    const value={capturedAt:new Date().toISOString(),execution:'captured-live-state-offline-replay',providerCalls:0,workspace:(await api('/api/workspace')).body};
    await writeFile(join(evidence,input.label+'.json'),JSON.stringify(value)+'\n',{flag:'wx'});
    emit({event:'captured',label:input.label,revision:value.workspace.revision,spaces:value.workspace.state.spaces.length,tasks:value.workspace.state.tasks.length,boards:Object.keys(value.workspace.state.boards||{}),providerCalls:0});return;
  }
  if(input.action==='close'){await app.close();emit({event:'closed',providerCalls:0});process.exit(0);}
  throw Error('unknown_command');
}
if(!process.stdin.isTTY)throw Error('Use the manual interactive replay controller.');
process.stdin.setRawMode(true);process.stdin.setEncoding('utf8');
process.stdin.on('data',chunk=>{
  if(chunk.includes('\u0003')){queue=queue.then(async()=>{await app.close();process.exit(0);});return;}
  buffer+=chunk;
  for(;;){const end=buffer.search(/[\r\n]/);if(end<0)break;const line=buffer.slice(0,end).trim();buffer=buffer.slice(end+1);if(line)queue=queue.then(async()=>{try{await command(JSON.parse(line));}catch{emit({event:'command_failed'});}});}
});
emit({event:'ready',execution:'captured-live-state-offline-replay',origin,providerCalls:0});
