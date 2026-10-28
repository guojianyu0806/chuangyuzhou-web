// Manual, opt-in live acceptance controller. No key is accepted through argv or files.
// Run in a terminal with echo disabled by raw mode; the first stdin JSON is start.
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import {resolve,dirname,join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {verifySource} from '../chuangyuzhou/tools/verify-source.mjs';
import {startFixture} from './web-live-acceptance-fixture.mjs';

const root=resolve(dirname(fileURLToPath(import.meta.url)),'../..');
const evidence=join(root,'web-track/evidence/WEB-008');
const pdf=join(root,'web-track/materials/2026-10-23_创宇宙Web技术文档_v1/创宇宙_Web赛道技术文档_v1.pdf');
let fixture=null,secret='',buffer='',queue=Promise.resolve(),before=null;
const captures=[];
const safe=value=>JSON.stringify(value,(_key,value)=>typeof value==='string'?value.replace(/sk-[A-Za-z0-9_-]{12,}/g,'[REDACTED_SECRET]'):value);
const emit=value=>process.stdout.write(safe(value)+'\n');
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
async function save(name,value){
  const text=safe(value)+'\n';
  if(secret&&text.includes(secret))throw Error('secret_export_forbidden');
  await mkdir(evidence,{recursive:true});
  await writeFile(join(evidence,name),text,{flag:'wx'});
}
function summary(value){
  const state=value.state||value;
  return {revision:value.revision,spaces:state.spaces?.length,tasks:state.tasks?.length,captures:state.captures?.length,
    requests:state.aiRequests?.map(r=>({id:r.id,status:r.status,messages:r.conversation?.messages?.length,pendingJobId:r.conversation?.pendingJobId,confirmedJobId:r.conversation?.confirmedJobId,proposal:r.conversation?.proposal,receipt:r.receipt}))};
}
async function dispatch(command){
  if(command.action==='start'){
    if(fixture)throw Error('already_started');
    secret=command.apiKey;command.apiKey=undefined;
    if(typeof secret!=='string'||!secret)throw Error('missing_key');
    before={source:verifySource(),pdfSha256:hash(await readFile(pdf)),startedAt:new Date().toISOString(),node:process.version};
    fixture=await startFixture({apiKey:secret,model:command.model||'deepseek-flash'});
    emit({event:'started',origin:fixture.origin,username:fixture.username,password:fixture.password,...before,metrics:fixture.metrics()});return;
  }
  if(!fixture)throw Error('not_started');
  if(command.action==='metrics'){emit({event:'metrics',value:fixture.metrics()});return;}
  if(command.action==='snapshot'){emit({event:'snapshot',value:summary(await fixture.snapshot())});return;}
  if(command.action==='capture'){
    if(!/^[a-z0-9-]{1,60}$/.test(command.label))throw Error('invalid_label');
    const value={capturedAt:new Date().toISOString(),workspace:await fixture.snapshot(),protected:await fixture.protectedSnapshot(),metrics:fixture.metrics()};
    await save(command.label+'.json',value);captures.push(command.label);emit({event:'captured',label:command.label,value:summary(value.workspace),metrics:value.metrics});return;
  }
  if(command.action==='api'){emit({event:'api',path:command.path,value:await fixture.api(command.path,{method:command.method||'GET',body:command.body})});return;}
  if(command.action==='export'){
    const after={source:verifySource(),pdfSha256:hash(await readFile(pdf))};
    await save('provider-usage.json',{recordId:'WEB-008',before,after,captures,metrics:fixture.metrics(),cleanEnvironmentReproduction:false,publicTLS:false});
    emit({event:'exported',captures,after,metrics:fixture.metrics()});return;
  }
  if(command.action==='close'){
    await fixture.close();fixture=null;secret='';emit({event:'closed'});process.exit(0);
  }
  throw Error('unknown_command');
}
if(!process.stdin.isTTY)throw Error('Use a dedicated interactive terminal; no secret on command line.');
process.stdin.setRawMode(true);
process.stdin.setEncoding('utf8');
process.stdin.on('data',chunk=>{
  if(chunk.includes('\u0003')){queue=queue.then(async()=>{await fixture?.close();secret='';process.exit(0);});return;}
  buffer+=chunk;
  for(;;){
    const end=buffer.search(/[\r\n]/);if(end<0)break;
    let line=buffer.slice(0,end).trim();buffer=buffer.slice(end+1);
    if(!line)continue;
    queue=queue.then(async()=>{let command;try{command=JSON.parse(line);line='';await dispatch(command);}catch{emit({event:'command_failed',code:'CONTROLLER_COMMAND_FAILED'});}finally{if(command)command.apiKey=undefined;line='';}});
  }
});
emit({event:'ready',secretInputEcho:false,modelRequests:0});
