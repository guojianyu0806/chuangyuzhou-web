// Verify captured evidence offline. This script has no model transport or credentials.
import assert from 'node:assert/strict';
import {readFile,writeFile} from 'node:fs/promises';
import {resolve,dirname,join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {verifySource} from '../chuangyuzhou/tools/verify-source.mjs';

const root=resolve(dirname(fileURLToPath(import.meta.url)),'../..');
const folder=join(root,'web-track/evidence/WEB-008');
const names=['01-before-ai','02-first-proposal','03-revised-proposal','04-corrected-proposal','05-confirmed','06-duplicate-confirm','07-refreshed-and-linked','08-undone','09-undone-after-refresh','10-replay-before-undo','11-replay-undone','12-replay-undone-after-refresh'];
const rows=await Promise.all(names.map(async name=>JSON.parse(await readFile(join(folder,name+'.json'),'utf8'))));
const [base,first,missed,corrected,confirmed,duplicate,linked,oldUndo,oldReload,replay,fixed,fixedReload]=rows;
const state=row=>row.workspace.state,request=row=>state(row).aiRequests[0];
const checks={};
function check(name,fn){fn();checks[name]=true;}
const businessKeys=['spaces','courses','tasks','captures','calendar','ledger','english','timetable','fitness','competitions','customBlocks'];
const business=row=>Object.fromEntries(businessKeys.map(key=>[key,state(row)[key]]));
const protectedRecords=row=>({space:state(row).spaces.find(v=>v.id==='web008-protected-space'),task:state(row).tasks.find(v=>v.id==='web008-protected-task'),event:state(row).calendar.events.find(v=>v.id==='web008-protected-event'),capture:state(row).captures.find(v=>v.id==='web008-source-capture')});
check('baseline_is_synthetic_and_has_no_ai_request',()=>{assert.equal(state(base).spaces.length,1);assert.equal(state(base).tasks.length,1);assert.equal(state(base).aiRequests.length,0);});
for(const [name,row] of [['first',first],['missed_revision',missed],['corrected',corrected]]){
  check(name+'_awaits_review_without_business_write',()=>{assert.deepEqual(business(row),business(base));assert.equal(request(row).status,'waiting_model');assert.equal(request(row).conversation.proposal.actions.length,4);});
}
check('queries_were_really_returned_to_the_model',()=>{const kinds=first.metrics.calls[1].queryKinds;assert.equal(first.metrics.calls[1].queryResultCount,2);assert.deepEqual(kinds,[{kind:'search',entity:'capture'},{kind:'search',entity:'space'}]);});
check('first_proposal_keeps_original_dates',()=>assert.deepEqual(request(first).conversation.proposal.actions.filter(a=>a.entity==='task').map(a=>a.data.date),['2026-10-27','2026-10-28']));
check('original_revision_date_miss_is_preserved',()=>{const actions=request(missed).conversation.proposal.actions;assert.equal(actions.find(a=>a.entity==='task'&&a.data.title==='整理提纲').data.date,'2026-10-28');assert.match(actions.find(a=>a.entity==='note').data.content,/2026-10-29/);});
check('clarified_proposal_has_consistent_revised_date',()=>{const actions=request(corrected).conversation.proposal.actions;assert.ok(actions.every(a=>a.operation==='create'));assert.match(actions.find(a=>a.entity==='space').data.description,/2026-10-29/);assert.match(actions.find(a=>a.entity==='note').data.content,/2026-10-29/);assert.match(actions.find(a=>a.entity==='note').data.content,/验收注意事项/);assert.deepEqual(actions.filter(a=>a.entity==='task').map(a=>a.data.date),['2026-10-27','2026-10-29']);});
check('previous_proposal_is_replaced',()=>{assert.notEqual(request(first).conversation.pendingJobId,request(missed).conversation.pendingJobId);assert.notEqual(request(missed).conversation.pendingJobId,request(corrected).conversation.pendingJobId);});
const newSpace=state(confirmed).spaces.find(v=>v.id!=='web008-protected-space');
check('confirmation_creates_linked_space_note_and_two_tasks',()=>{assert.ok(newSpace);assert.equal(newSpace.notes.length,1);assert.match(newSpace.notes[0].content,/验收注意事项/);const tasks=state(confirmed).tasks.filter(v=>v.spaceId===newSpace.id);assert.equal(tasks.length,2);assert.ok(tasks.every(v=>!v.done));assert.equal(tasks.find(v=>v.title==='整理提纲').date,'2026-10-29');assert.equal(state(confirmed).calendar.events.length,1);});
check('confirmation_receipt_matches_latest_job',()=>{assert.equal(request(confirmed).status,'filed');assert.equal(request(confirmed).conversation.confirmedJobId,request(corrected).conversation.pendingJobId);assert.equal(request(confirmed).receipt.items.length,4);assert.ok(request(confirmed).receipt.items.every(item=>item.collection==='actions'));assert.equal(request(confirmed).conversation.proposal,undefined);});
check('duplicate_confirmation_does_not_duplicate_or_change_records',()=>assert.deepEqual(duplicate.workspace,confirmed.workspace));
check('refresh_and_navigation_preserve_records_and_receipt',()=>{assert.deepEqual(business(linked),business(confirmed));assert.deepEqual(request(linked),request(confirmed));});
check('original_undo_defect_is_preserved',()=>{assert.equal(state(oldUndo).spaces.length,2);assert.equal(state(oldUndo).tasks.length,1);assert.equal(state(oldUndo).spaces.find(v=>v.id===newSpace.id).notes.length,0);assert.deepEqual(oldReload.workspace,oldUndo.workspace);});
check('offline_replay_uses_exact_saved_business_and_boards',()=>{assert.equal(replay.execution,'captured-live-state-offline-replay');assert.deepEqual(state(replay),state(linked));});
for(const [name,row] of [['fixed',fixed],['fixed_after_refresh',fixedReload]]){
  check(name+'_undo_clears_all_four_records_and_auto_boards',()=>{assert.deepEqual(business(row),business(base));assert.equal(Object.keys(state(row).boards||{}).length,0);assert.equal(request(row).status,'waiting_model');assert.equal(request(row).receipt,undefined);for(const key of ['proposal','pendingJobId','confirmedJobId'])assert.equal(request(row).conversation[key],undefined);assert.equal(request(row).conversation.messages.length,6);assert.equal(row.providerCalls,0);});
}
check('offline_undo_survives_refresh',()=>assert.deepEqual(fixed.workspace,fixedReload.workspace));
for(let index=0;index<rows.length;index++)check(names[index]+'_protects_unrelated_records',()=>assert.deepEqual(protectedRecords(rows[index]),protectedRecords(base)));
const usage=JSON.parse(await readFile(join(folder,'provider-usage.json'),'utf8'));
check('usage_accounts_for_every_actual_request',()=>{assert.equal(usage.metrics.totals.requests,4);assert.equal(usage.metrics.calls.length,4);assert.ok(usage.metrics.calls.every(c=>c.httpStatus===200&&c.finishReason==='stop'));assert.equal(usage.metrics.totals.totalTokens,48730);assert.equal(usage.metrics.calls.reduce((n,c)=>n+c.usage.total_tokens,0),48730);assert.ok(usage.metrics.calls.every(c=>!c.formatCorrection));});
const pdf=await readFile(join(root,'web-track/materials/2026-10-23_创宇宙Web技术文档_v1/创宇宙_Web赛道技术文档_v1.pdf'));
check('existing_pdf_unchanged',()=>assert.equal(createHash('sha256').update(pdf).digest('hex'),usage.before.pdfSha256));
const report={recordId:'WEB-008',checkedAt:new Date().toISOString(),checks,passed:Object.keys(checks).length,
  liveSourceCommit:'e5925b3b622977b6b70797ec249251983bdbba70',currentSource:verifySource(),
  liveResult:'query-generation-clarified-revision-confirmation-refresh-and-links-passed; original-undo-defect-recorded',
  postFixResult:'captured-live-state-offline-browser-replay-passed; no-additional-provider-call',
  totals:usage.metrics.totals,firstRevisionRequiredClarification:true,cleanEnvironmentReproduction:false,publicTLS:false,
  knownLimitations:{globalCanvasRetainsHiddenGeometryForRemovedSpace:!!state(fixedReload).canvas?.cards?.some(card=>card.id===newSpace.id),
    note:'Space-scoped automatic boards are removed. The existing global canvas retains a hidden geometry cache entry; this is not a remaining business space or visible card.'}};
const output=join(folder,'acceptance-check.json');
try{
  const existing=JSON.parse(await readFile(output,'utf8'));
  assert.deepEqual({...existing,checkedAt:report.checkedAt},report);
}catch(error){
  if(error.code!=='ENOENT')throw error;
  await writeFile(output,JSON.stringify(report,null,2)+'\n',{flag:'wx'});
}
console.log(JSON.stringify({passed:report.passed,totals:report.totals,postFixResult:report.postFixResult}));
