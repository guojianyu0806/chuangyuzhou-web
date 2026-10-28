// Explicit, isolated acceptance fixture. Importing or starting it never calls AI.
// Supply the current task's credential in memory; this helper never reads .env.
import {mkdir, mkdtemp} from 'node:fs/promises';
import {join} from 'node:path';
import {createHash} from 'node:crypto';
import {createWorkbenchServer} from '../chuangyuzhou/yuzhou/backend/server.mjs';
import {createHermesService} from '../chuangyuzhou/yuzhou/backend/hermes.mjs';
import {createDeepSeekRunner} from '../chuangyuzhou/yuzhou/backend/deepseek.mjs';
import {readModelEnvironment} from '../chuangyuzhou/yuzhou/backend/model-environment.mjs';
import {RUNTIME_ROOT, assertRuntimePath} from '../chuangyuzhou/yuzhou/runtime.mjs';
import {createWorkbench} from '../chuangyuzhou/yuzhou/frontend/src/workbench-model.js';

const ORIGIN='http://127.0.0.1:4396';
const ENDPOINT='https://api.deepseek.com/chat/completions';
const USERNAME='web008-synthetic';
const PASSWORD='WEB-008-synthetic-password-only';
const SETUP_TOKEN='WEB-008-synthetic-setup-token-only';
const IDS=Object.freeze({space:'web008-protected-space',note:'web008-protected-note',
  task:'web008-protected-task',event:'web008-protected-event',capture:'web008-source-capture'});
const USAGE_KEYS=new Set(['prompt_tokens','completion_tokens','total_tokens',
  'prompt_cache_hit_tokens','prompt_cache_miss_tokens','cached_tokens','reasoning_tokens',
  'accepted_prediction_tokens','rejected_prediction_tokens','audio_tokens']);
const DETAIL_KEYS=new Set(['prompt_tokens_details','completion_tokens_details']);
const FINISH_REASONS=new Set(['stop','length','content_filter','tool_calls','function_call','insufficient_system_resource']);
const pause=milliseconds=>new Promise(resolve=>setTimeout(resolve,milliseconds));
const hash=value=>createHash('sha256').update(JSON.stringify(value)).digest('hex');

function usageNumbers(value){
  if(!value||typeof value!=='object'||Array.isArray(value))return {};
  const safe={};
  for(const [key,item] of Object.entries(value)){
    if(USAGE_KEYS.has(key)&&Number.isSafeInteger(item)&&item>=0)safe[key]=item;
    else if(DETAIL_KEYS.has(key)){const nested=usageNumbers(item);if(Object.keys(nested).length)safe[key]=nested;}
  }
  return safe;
}

async function boundedProviderMetadata(response){
  // Read only a clone, leaving the production runner's original response intact.
  const reader=response.clone().body?.getReader();
  if(!reader)return null;
  const chunks=[];let bytes=0;
  try{
    for(;;){
      const {done,value}=await reader.read();if(done)break;
      bytes+=value.byteLength;
      if(bytes>1024*1024){void reader.cancel().catch(()=>{});return null;}
      chunks.push(value);
    }
    return JSON.parse(Buffer.concat(chunks,bytes).toString('utf8'));
  }catch{return null;}
  finally{reader.releaseLock();}
}

function syntheticWorkspace(){
  const stamp=new Date().toISOString();
  return {schema:1,mode:'personal',profile:{name:'Web真实AI合成验收',major:'合成资料，不代表真人经历',provider:'deepseek'},
    workbench:{...createWorkbench('full'),title:'Web真实AI合成验收工作台'},
    courses:[],spaces:[{id:IDS.space,title:'保护空间-本轮禁止修改',description:'独立合成保护记录。',type:'project',
      color:'#7950f2',icon:'folder',example:false,archived:false,createdAt:stamp,updatedAt:stamp,files:[],
      notes:[{id:IDS.note,title:'保护笔记',content:'保护正文 WEB-008，模型不得改写或删除。',chapter:'',
        source:'合成验收夹具',color:'#63E6DC',example:false,updatedAt:stamp,revisions:[]}]}],
    tasks:[{id:IDS.task,title:'保护待办-本轮禁止修改',description:'必须保留的独立合成待办。',category:'个人',
      date:'2026-10-31',priority:'normal',done:false,archived:false,source:'合成验收夹具',createdAt:stamp,
      updatedAt:stamp,spaceId:IDS.space,color:'#FFBC7C'}],
    captures:[{id:IDS.capture,text:'WEB-AI-20261024读书会资料（合成验收）：主题是软件工程。第一阶段于2026-10-27收集资料；第二阶段于2026-10-28整理提纲。所有事项尚未完成。本条为查询来源，请勿修改。',
      category:'备忘',tags:'WEB-008 合成资料',archived:false,source:'合成验收夹具',createdAt:stamp,color:'#FF9CCE'}],
    calendar:{version:1,events:[{id:IDS.event,title:'保护日历-本轮禁止修改',kind:'note',startDate:'2026-10-30',
      endDate:'2026-10-30',allDay:true,startTime:'',endTime:'',location:'',notes:'独立合成日历记录。',
      important:false,done:false,archived:false,color:'#9DC5FF',createdAt:stamp,updatedAt:stamp}]},
    ledger:{version:1,currency:'CNY',projects:[],entries:[]},timetable:{version:1,activeTermId:'',terms:[]},
    english:{words:[],sessions:[],mistakes:[],attempts:[]},
    aiRequests:[],aiDraft:{text:'',files:[],targetId:'workspace'},
    ui:{sidebarPinned:false,lastCreatedColor:'#9DC5FF'},boards:{},updatedAt:stamp};
}

function protectedRecords(state){
  const value={space:state.spaces?.find(row=>row.id===IDS.space),
    task:state.tasks?.find(row=>row.id===IDS.task),event:state.calendar?.events?.find(row=>row.id===IDS.event),
    capture:state.captures?.find(row=>row.id===IDS.capture)};
  return {records:structuredClone(value),sha256:hash(value)};
}

/**
 * Starts one disposable synthetic account on the production Web API/frontend.
 * No request is sent to a provider until an explicit AI job is submitted later.
 * close() preserves this new runtime directory; it never deletes old artifacts.
 */
export async function startFixture({apiKey,model='deepseek-flash'}={}){
  const environment={DEEPSEEK_API_KEY:apiKey,DEEPSEEK_MODEL:model};
  if(!readModelEnvironment(environment))throw new Error('An explicit task-specific model credential is required.');
  const parent=assertRuntimePath(join(RUNTIME_ROOT,'tests-temp'));
  await mkdir(parent,{recursive:true});
  const dataDir=assertRuntimePath(await mkdtemp(join(parent,'WEB-008-')));
  const calls=[];
  let cookie='',csrf='',closed=false,app=null,activeContext=null;
  const redact=text=>typeof text==='string'&&apiKey?text.replaceAll(apiKey,'[REDACTED]'):text;
  const safeValue=value=>JSON.parse(redact(JSON.stringify(value)));
  const providerFetch=async (input,init)=>{
    if(String(input)!==ENDPOINT)throw new Error('Only the production DeepSeek endpoint is permitted.');
    const started=Date.now(),record={index:calls.length+1,startedAt:new Date(started).toISOString(),
      ...structuredClone(activeContext||{})};
    calls.push(record);
    try{
      const response=await globalThis.fetch(input,init);
      record.httpStatus=response.status;record.ok=response.ok;
      const body=await boundedProviderMetadata(response);
      if(body){
        if(typeof body.id==='string')record.providerResponseId=redact(body.id).slice(0,160);
        if(typeof body.model==='string')record.model=redact(body.model).slice(0,100);
        const finish=body.choices?.[0]?.finish_reason;
        if(FINISH_REASONS.has(finish))record.finishReason=finish;
        record.usage=usageNumbers(body.usage);
      }
      return response;
    }catch{record.transportFailure=true;throw new Error('MODEL_TRANSPORT_FAILED');}
    finally{record.finishedAt=new Date().toISOString();record.durationMs=Date.now()-started;}
  };
  let modelRunner=createDeepSeekRunner({fetch:providerFetch});
  const runModel=async input=>{
    // Persist only query metadata, never source content, prompts, or settings.
    try{
      const context=JSON.parse(input.user),results=Array.isArray(context.workspaceQueryResults)?context.workspaceQueryResults:[];
      activeContext={queryResultCount:results.length,queryKinds:results.map(row=>({
        ...(typeof row.query?.kind==='string'?{kind:row.query.kind.slice(0,80)}:{}),
        ...(typeof row.query?.entity==='string'?{entity:row.query.entity.slice(0,80)}:{})})),
        formatCorrection:!!context.formatCorrection};
    }catch{activeContext={};}
    try{return await modelRunner(input);}finally{activeContext=null;}
  };
  async function api(path,{method='GET',body}={}){
    if(closed)throw new Error('The synthetic fixture is closed.');
    if(typeof path!=='string'||!/^\/api\/[A-Za-z0-9_/?=&.%:-]+$/.test(path)||new URL(path,ORIGIN).origin!==ORIGIN)
      throw new Error('Only a local /api/ path is permitted.');
    const headers={Connection:'close',...(body===undefined?{}:{'Content-Type':'application/json'}),
      ...(cookie?{Cookie:cookie}:{}),...(csrf?{'X-CSRF-Token':csrf}:{}),
      ...(['POST','PUT','PATCH','DELETE'].includes(method)?{Origin:ORIGIN}:{})};
    let response;
    try{response=await globalThis.fetch(ORIGIN+path,{method,headers,redirect:'error',
      ...(body===undefined?{}:{body:JSON.stringify(body)})});}
    catch{throw new Error('SYNTHETIC_LOCAL_API_TRANSPORT_FAILED');}
    const session=response.headers.get('set-cookie');if(session)cookie=session.split(';')[0];
    const value=await response.json();if(typeof value.csrfToken==='string')csrf=value.csrfToken;
    const visible={...value};delete visible.csrfToken;
    return {status:response.status,body:safeValue(visible)};
  }
  const snapshot=async()=>{
    const result=await api('/api/workspace');
    if(result.status!==200)throw new Error(`SYNTHETIC_SNAPSHOT_FAILED_${result.status}`);
    return result.body;
  };
  const metrics=()=>{
    const totals={requests:calls.length,promptTokens:0,completionTokens:0,totalTokens:0,usageResponses:0};
    for(const call of calls){
      if(Number.isSafeInteger(call.usage?.total_tokens))totals.usageResponses++;
      totals.promptTokens+=call.usage?.prompt_tokens||0;totals.completionTokens+=call.usage?.completion_tokens||0;
      totals.totalTokens+=call.usage?.total_tokens||0;
    }
    return safeValue({provider:'DeepSeek official endpoint',model,totals,calls});
  };
  const close=async()=>{
    if(closed)return;
    try{await app?.close();}
    finally{closed=true;cookie='';csrf='';apiKey='';environment.DEEPSEEK_API_KEY='';app=null;modelRunner=null;}
  };
  try{
    app=await createWorkbenchServer({dataDir,secureCookie:false,publicOrigin:ORIGIN,setupToken:SETUP_TOKEN,
      modelFactory:({dataDir:directory,store})=>createHermesService({dataDir:directory,store,env:environment,
        engine:'deepseek-direct',runModel,extractionCapabilities:{txt:false,md:false,csv:false,docx:false,pptx:false,pdf:false}})});
    await new Promise((resolve,reject)=>{app.server.once('error',reject);app.server.listen(4396,'127.0.0.1',resolve);});
    const setup=await api('/api/auth/setup',{method:'POST',body:{username:USERNAME,password:PASSWORD,setupToken:SETUP_TOKEN}});
    if(setup.status!==201)throw new Error(`SYNTHETIC_SETUP_FAILED_${setup.status}`);
    const current=await snapshot(),state=syntheticWorkspace();
    const saved=await api('/api/workspace',{method:'PUT',body:{baseRevision:current.revision,state}});
    if(saved.status!==200)throw new Error(`SYNTHETIC_SEED_FAILED_${saved.status}`);
    const baseline=await snapshot();
    return {origin:ORIGIN,username:USERNAME,password:PASSWORD,dataDir,ids:{...IDS},
      baseline,baselineProtected:protectedRecords(baseline.state),api,snapshot,metrics,close,
      protectedSnapshot:async()=>protectedRecords((await snapshot()).state),
      waitJobs:async(ids,{timeoutMs=240000,pollMs=500}={})=>{
        if(!Number.isFinite(timeoutMs)||timeoutMs<=0||!Number.isFinite(pollMs)||pollMs<50)
          throw new Error('Invalid job wait interval.');
        const target=ids==null?null:new Set(Array.isArray(ids)?ids:[ids]),deadline=Date.now()+timeoutMs;
        for(;;){
          const result=await api('/api/ai/jobs');
          if(result.status!==200)throw new Error(`SYNTHETIC_JOBS_FAILED_${result.status}`);
          const jobs=(result.body.jobs||[]).filter(job=>!target||target.has(job.id));
          if((!target||jobs.length===target.size)&&jobs.every(job=>['succeeded','failed'].includes(job.status)))return jobs;
          if(Date.now()>=deadline)throw new Error('SYNTHETIC_JOB_WAIT_TIMEOUT');
          await pause(pollMs);
        }
      }};
  }catch(error){await close();throw error;}
}
