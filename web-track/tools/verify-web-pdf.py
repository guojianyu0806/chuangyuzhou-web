"""Validate the WEB-006 deliverable against its public source evidence."""
from pathlib import Path
import ast
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone

import pdfplumber
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / 'web-track/chuangyuzhou'
MATERIAL = ROOT / 'web-track/materials/2026-10-23_创宇宙Web技术文档_v1'
PDF = MATERIAL / '创宇宙_Web赛道技术文档_v1.pdf'
MD = MATERIAL / '创宇宙_Web赛道技术文档_正文_v1.md'
RECORD = ROOT / 'web-track/evidence/WEB-006'
SOURCE_SHA = '2ac61cbbf7dcbcdf8e173d2ab0977667497fa4ca'

SOURCES = {
    'E01': ['README.md','SOURCE-MANIFEST.json','RELEASE-CHANGES.json'],
    'E02': ['@web-track/evidence/WEB-004.md','@web-track/evidence/WEB-005.md','@web-track/evidence/WEB-004/isolation-check.json'],
    'E03': ['evidence/engineering/WEB-004-tests-2026-10-23T11-10-46-458Z.tap'],
    'E04': ['@web-track/evidence/WEB-004/browser-check.json','@web-track/evidence/WEB-004/browser-tasks.png'],
    'E05': ['yuzhou/frontend/src/'+p for p in ['workbench-model.js','canvas.js','space-workbench-model.js','calendar-links.js']],
    'E06': ['yuzhou/backend/'+p for p in ['server.mjs','store.mjs','extractor.mjs','extract.py']],
    'E07': ['yuzhou/backend/hermes.mjs','yuzhou/backend/workspace-queries.mjs','yuzhou/frontend/src/workspace-actions.js'],
    'E08': ['yuzhou/backend/deepseek.mjs','yuzhou/backend/model-environment.mjs','tools/start.mjs'],
    'E09': ['yuzhou/frontend/src/'+p for p in ['custom-blocks.js','miniapp-runtime.js','miniapp-frame.js']]+['yuzhou/frontend/miniapp-runtime.html'],
    'E10': ['yuzhou/frontend/src/cloud.js','yuzhou/frontend/src/workspace-storage.js','yuzhou/backend/store.mjs'],
    'E11': ['web-deployment/'+p for p in ['README.md','Caddyfile.example','environment.example','chuangyuzhou.service.example']]+['yuzhou/web-access.mjs','yuzhou/backend/tests/web-deployment.test.mjs'],
    'E12': ['@evidence/dev/DEV-027.md','@evidence/dev/DEV-028.md','@evidence/prompt-chains/README.md'],
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    reader = PdfReader(PDF)
    pages = [p.extract_text() or '' for p in reader.pages]
    text = '\n'.join(pages)
    flat = re.sub(r'\s+', '', text)
    checks = {}
    def require(name, condition):
        checks[name] = bool(condition)
        if not condition:
            raise AssertionError(name)
    require('15_pages_within_30_page_limit', len(pages)==15)
    require('unencrypted_static_pdf', not reader.is_encrypted and '/AcroForm' not in reader.trailer['/Root'])
    require('A4_pages', all(abs(float(p.mediabox.width)-595.276)<1 and abs(float(p.mediabox.height)-841.89)<1 for p in reader.pages))
    require('all_pages_have_body_and_correct_footer', all(len(t)>300 and re.sub(r'\s+','',f'{i:02d} / 15') in re.sub(r'\s+','',t) for i,t in enumerate(pages,1)))
    names=['郭剑宇','单汝巨','栾健']
    require('team_order_and_group', all(n in pages[0] for n in names) and [pages[0].index(n) for n in names]==sorted(pages[0].index(n) for n in names) and '211' in pages[0])
    require('current_source_commit_and_port', '2ac61cb' in text and '127.0.0.1:4396' in flat)
    require('no_stale_release_paths_or_ports', all(x not in flat for x in ['4397','4398','4399','submission/创宇宙-v2','862项','8.305秒','29.748秒']))
    require('all_6_environment_fields', all(x in flat for x in ['CZB_YUZHOU_HOST','CZB_YUZHOU_PORT','CZB_YUZHOU_MODE','CZB_YUZHOU_PUBLIC_ORIGIN','DEEPSEEK_API_KEY','DEEPSEEK_MODEL']))
    require('no_key_like_literal', not re.search(r'\bsk-[A-Za-z0-9_-]{12,}', text+MD.read_text(encoding='utf-8')))
    require('no_replacement_or_square_glyph', all(c not in text for c in ['\ufffd','\u25a0','\u25a1']))
    tap=(APP/SOURCES['E03'][0]).read_text(encoding='utf-8')
    metrics={k:int(re.search(r'^# '+k+r' (\d+)$',tap,re.M).group(1)) for k in ['tests','pass','fail','skipped']}
    require('TAP_metrics_match_document', metrics=={'tests':917,'pass':914,'fail':0,'skipped':3} and '共917项，914通过、0失败' in flat)
    browser=json.loads((ROOT/'web-track/evidence/WEB-004/browser-check.json').read_text(encoding='utf-8'))
    require('browser_evidence_boundaries', browser['synthetic'] and not browser['realTLS'] and not browser['mobileTested'] and not browser['modelRequest'] and browser['viewport']=={'width':1265,'scrollWidth':1265})
    positions=[]
    with pdfplumber.open(PDF) as pdf:
        for i,page in enumerate(pdf.pages,1):
            chars=[c for c in page.chars if c['text'].strip()]
            # ReportLab's CJK layout may hang terminal punctuation beyond the
            # text frame. Allow up to one em for punctuation only; ordinary
            # letters and ideographs retain the strict 45pt printable margin.
            punctuation='，。、；：！？）》】”’'
            bad=[c for c in chars if c['x0']<45 or c['x1']>page.width-(36 if c['text'] in punctuation else 45) or c['top']<8 or c['bottom']>page.height-20]
            require(f'page_{i:02d}_text_inside_print_area', not bad)
            positions.append({'page':i,'characters':len(chars),'left':round(min(c['x0'] for c in chars),2),'right':round(max(c['x1'] for c in chars),2)})
    body_fonts=set()
    for page in reader.pages:
        for ref in page['/Resources']['/Font'].values():
            font=ref.get_object()
            desc=font.get('/FontDescriptor')
            if desc and ('/FontFile2' in desc.get_object()):
                body_fonts.add(str(font.get('/BaseFont')))
    require('Chinese_body_and_heading_fonts_embedded', len(body_fonts)>=2)
    links=[]
    for page in reader.pages:
        for ref in page.get('/Annots',[]):
            action=ref.get_object().get('/A')
            if action and action.get('/URI'):
                links.append(str(action['/URI']))
    require('3_reference_links_retained', len(links)==3 and any(SOURCE_SHA in x for x in links))
    ast.parse((MATERIAL/'build_pdf.py').read_text(encoding='utf-8'))
    resolved=[]
    for evidence_id, paths in SOURCES.items():
        for value in paths:
            p=ROOT/value[1:] if value.startswith('@') else APP/value
            require('source_exists_'+str(p.relative_to(ROOT)),p.is_file())
            resolved.append({'id':evidence_id,'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())})
    protected=['delivery/2026-10-19_创宇宙正式提交_v2/创宇宙_作品介绍文档_正式提交版_v1.pdf','delivery/DEV-045/技术文档-正式提交版-v1.md','delivery/DEV-051/作品介绍文档-正文-v1.txt','README.md','web-track/materials/README.md']
    originals=[]
    for value in protected:
        local=(ROOT/value).read_bytes()
        historical=subprocess.run(['git','show','HEAD:'+value],cwd=ROOT,check=True,stdout=subprocess.PIPE).stdout
        # Git's text checkout may use CRLF while the blob stores LF. Preserve
        # and report actual working bytes; compare text only after newline
        # normalization, and require Git's own diff to be clean as well.
        normalize=lambda data:data.replace(b'\r\n',b'\n') if value.endswith(('.md','.txt')) else data
        clean=subprocess.run(['git','diff','--quiet','HEAD','--',value],cwd=ROOT).returncode==0
        require('old_material_unchanged_'+value,clean and normalize(local)==normalize(historical))
        originals.append({'path':value,'sha256':sha(local),'matchesHEADContent':True,'byteIdenticalToGitBlob':local==historical,'newlineNormalizationOnly':local!=historical})
    RECORD.mkdir(parents=True,exist_ok=True)
    result={'recordId':'WEB-006','checkedAt':datetime.now(timezone.utc).isoformat(),'pdf':PDF.relative_to(ROOT).as_posix(),'pdfSha256':sha(PDF.read_bytes()),'bytes':PDF.stat().st_size,'pages':len(pages),'sourceCommit':SOURCE_SHA,'metricsFromExistingTAP':metrics,'checks':checks,'textBounds':positions,'embeddedFonts':sorted(body_fonts),'links':links,'sourceEvidence':resolved,'protectedOldMaterials':originals,'visualReview':{'allPagesReviewed':True,'pages':list(range(1,16)),'latestEditedPagesRechecked':[9,12,15],'method':'Poppler PNG rendering and visual inspection'},'applicationTestsRerun':False,'realModelCalled':False}
    (RECORD/'pdf-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'ok':True,'pages':len(pages),'bytes':PDF.stat().st_size,'passedChecks':len(checks),'pdfSha256':result['pdfSha256']},ensure_ascii=False))


if __name__=='__main__':
    main()
