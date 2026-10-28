"""Validate WEB-009 PDF v2 against fixed public source and WEB-008 evidence.

This verifier never rebuilds a PDF, calls a model, reads runtime credentials,
or rewrites historical reports. Visual inspection is recorded separately.
"""
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
MATERIAL = ROOT / 'web-track/materials/2026-10-28_创宇宙Web技术文档_v2'
OLD_MATERIAL = ROOT / 'web-track/materials/2026-10-23_创宇宙Web技术文档_v1'
PDF = MATERIAL / '创宇宙_Web赛道技术文档_v2.pdf'
MD = MATERIAL / '创宇宙_Web赛道技术文档_正文_v2.md'
RECORD = ROOT / 'web-track/evidence/WEB-009'
SOURCE_SHA = 'c71c0411245943198ce1db9d6276e211b4a28c94'
SOURCE_SHORT = SOURCE_SHA[:7]
REPOSITORY_URL = 'https://github.com/guojianyu0806/chuangyuzhou-web'
LAYOUT = json.loads((ROOT / 'WEB-REPOSITORY.json').read_text(encoding='utf-8'))
HISTORY_REF = LAYOUT['historyBaseline']
if not re.fullmatch(r'[0-9a-f]{40}', HISTORY_REF):
    raise ValueError('Invalid fixed history baseline')

SOURCES = {
    'E01': ['README.md', 'SOURCE-MANIFEST.json', 'RELEASE-CHANGES.json'],
    'E02': ['@web-track/evidence/WEB-007.md', '@web-track/evidence/WEB-008.md',
            '@web-track/evidence/WEB-008/isolation-check.json'],
    'E03': ['evidence/engineering/WEB-008-tests-2026-10-24T10-05-53-648Z.tap'],
    'E04': ['@web-track/evidence/WEB-008/09-linked-tasks.png',
            '@web-track/evidence/WEB-008/12-replay-undo-after-refresh.png'],
    'E05': ['yuzhou/frontend/src/' + p for p in
            ['workbench-model.js', 'canvas.js', 'space-workbench-model.js', 'calendar-links.js']],
    'E06': ['yuzhou/backend/' + p for p in ['server.mjs', 'store.mjs', 'extractor.mjs', 'extract.py']],
    'E07': ['yuzhou/backend/hermes.mjs', 'yuzhou/backend/workspace-queries.mjs',
            'yuzhou/frontend/src/workspace-actions.js', 'yuzhou/frontend/src/workspace-actions-core.js'],
    'E08': ['yuzhou/backend/deepseek.mjs', 'yuzhou/backend/model-environment.mjs', 'tools/start.mjs'],
    'E09': ['yuzhou/frontend/src/' + p for p in
            ['custom-blocks.js', 'miniapp-runtime.js', 'miniapp-frame.js']]
           + ['yuzhou/frontend/miniapp-runtime.html'],
    'E10': ['yuzhou/frontend/src/cloud.js', 'yuzhou/frontend/src/workspace-storage.js',
            'yuzhou/backend/store.mjs'],
    'E11': ['web-deployment/' + p for p in
            ['README.md', 'Caddyfile.example', 'environment.example', 'chuangyuzhou.service.example']]
           + ['yuzhou/web-access.mjs', 'yuzhou/backend/tests/web-deployment.test.mjs'],
    'E12': ['@evidence/dev/DEV-027.md', '@evidence/dev/DEV-028.md', '@evidence/prompt-chains/README.md'],
    'E13': ['@web-track/evidence/WEB-008.md', '@web-track/evidence/WEB-008/acceptance-check.json',
            '@web-track/evidence/WEB-008/provider-usage.json'],
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git_bytes(ref, relative):
    return subprocess.run(['git', 'show', ref + ':' + relative], cwd=ROOT,
                          check=True, stdout=subprocess.PIPE).stdout


def source_bytes(path, historical=False):
    if not historical and path.is_file():
        return path.read_bytes(), 'working-tree'
    return git_bytes(HISTORY_REF, path.relative_to(ROOT).as_posix()), HISTORY_REF


def main():
    checks = {}

    def require(name, condition):
        checks[name] = bool(condition)
        if not condition:
            raise AssertionError(name)

    require('source_commit_is_present', subprocess.run(
        ['git', 'cat-file', '-e', SOURCE_SHA + '^{commit}'], cwd=ROOT,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0)
    reader = PdfReader(PDF)
    pages = [page.extract_text() or '' for page in reader.pages]
    text = '\n'.join(pages)
    flat = re.sub(r'\s+', '', text)
    markdown = MD.read_text(encoding='utf-8')
    require('15_pages_within_30_page_limit', len(pages) == 15)
    require('unencrypted_static_pdf', not reader.is_encrypted and '/AcroForm' not in reader.trailer['/Root'])
    require('A4_pages', all(abs(float(p.mediabox.width) - 595.276) < 1
                            and abs(float(p.mediabox.height) - 841.89) < 1 for p in reader.pages))
    require('all_pages_have_body_and_correct_footer', all(
        len(value) > 300 and f'{index:02d}/15' in re.sub(r'\s+', '', value)
        for index, value in enumerate(pages, 1)))
    names = ['郭剑宇', '单汝巨', '栾健']
    require('team_member_order', all(name in pages[0] for name in names)
            and [pages[0].index(name) for name in names] == sorted(pages[0].index(name) for name in names))
    cover = re.sub(r'\s+', '', pages[0])
    require('official_team_name_number_school_and_group', all(value in cover for value in
            ['我不是软蛋', '42988', '云南大学', 'A组', '211']))
    require('current_source_commit_release_and_port', SOURCE_SHORT in text
            and '2026-10-24-web-dev-008' in flat and '127.0.0.1:4396' in flat)
    require('version_and_document_date', '技术文档v2' in flat and '2026-10-28' in text)
    require('no_wrong_runtime_ports', all(port not in flat for port in ['4397', '4398', '4399']))
    require('all_6_environment_fields', all(value in flat for value in
            ['CZB_YUZHOU_HOST', 'CZB_YUZHOU_PORT', 'CZB_YUZHOU_MODE',
             'CZB_YUZHOU_PUBLIC_ORIGIN', 'DEEPSEEK_API_KEY', 'DEEPSEEK_MODEL']))
    require('no_key_like_literal', not re.search(r'\bsk-[A-Za-z0-9_-]{12,}', text + markdown))
    require('no_replacement_or_square_glyph', all(c not in text for c in ['\ufffd', '\u25a0', '\u25a1']))

    tap = (APP / SOURCES['E03'][0]).read_text(encoding='utf-8')
    metrics = {key: int(re.search(r'^# ' + key + r' (\d+)$', tap, re.M).group(1))
               for key in ['tests', 'pass', 'fail', 'skipped']}
    require('TAP_metrics_match_document', metrics == {'tests': 920, 'pass': 917, 'fail': 0, 'skipped': 3}
            and all(value in flat for value in ['920项', '917通过', '0失败', '3跳过']))
    acceptance = json.loads((ROOT / 'web-track/evidence/WEB-008/acceptance-check.json').read_text(encoding='utf-8'))
    usage = json.loads((ROOT / 'web-track/evidence/WEB-008/provider-usage.json').read_text(encoding='utf-8'))
    totals = usage['metrics']['totals']
    require('live_usage_evidence_is_complete', totals == {
        'requests': 4, 'promptTokens': 46802, 'completionTokens': 1928,
        'totalTokens': 48730, 'usageResponses': 4}
        and len(usage['metrics']['calls']) == 4
        and all(call['httpStatus'] == 200 for call in usage['metrics']['calls']))
    require('live_usage_matches_document', 'deepseek-flash' in flat and '4次' in flat
            and bool(re.search(r'48[,，]?730', flat)))
    require('acceptance_checks_are_separate_from_engineering_tests', acceptance['passed'] == 32
            and all(acceptance['checks'].values()) and '32项' in flat)
    require('revision_failure_is_not_hidden', acceptance['firstRevisionRequiredClarification']
            and '漏改' in text and '修订' in text)
    require('offline_replay_boundary_is_explicit', '离线回放' in flat
            and bool(re.search(r'(?:0次|0新增|新增.{0,4}0|未新增|没有新增|未追加|无新增).{0,12}(?:模型|请求|调用)'
                               r'|(?:模型|请求|调用).{0,8}(?:0次|0新增)', flat)))
    require('hidden_geometry_cache_limit_is_disclosed', '隐藏' in text and ('几何缓存' in text or '布局缓存' in text))
    require('no_clean_reproduction_or_TLS_claim', acceptance['cleanEnvironmentReproduction'] is False
            and acceptance['publicTLS'] is False and 'TLS' in text)

    positions = []
    with pdfplumber.open(PDF) as pdf:
        for index, page in enumerate(pdf.pages, 1):
            chars = [c for c in page.chars if c['text'].strip()]
            punctuation = '，。、；：！？）》】”’'
            bad = [c for c in chars if c['x0'] < 45
                   or c['x1'] > page.width - (36 if c['text'] in punctuation else 45)
                   or c['top'] < 8 or c['bottom'] > page.height - 20]
            require(f'page_{index:02d}_text_inside_print_area', not bad)
            positions.append({'page': index, 'characters': len(chars),
                              'left': round(min(c['x0'] for c in chars), 2),
                              'right': round(max(c['x1'] for c in chars), 2)})
    fonts = set()
    for page in reader.pages:
        for ref in page['/Resources']['/Font'].values():
            font = ref.get_object()
            descriptor = font.get('/FontDescriptor')
            if descriptor and '/FontFile2' in descriptor.get_object():
                fonts.add(str(font.get('/BaseFont')))
    require('Chinese_body_and_heading_fonts_embedded', len(fonts) >= 2)
    links = []
    for page in reader.pages:
        for ref in page.get('/Annots', []):
            action = ref.get_object().get('/A')
            if action and action.get('/URI'):
                links.append(str(action['/URI']))
    require('new_repository_and_fixed_source_links', any(link.rstrip('/') == REPOSITORY_URL for link in links)
            and any(REPOSITORY_URL + '/tree/' + SOURCE_SHA in link for link in links))
    require('official_track_link_retained', any('boxuegu.com/matchTrack/detail/?id=10037' in link for link in links))
    require('no_old_repository_links', not any(re.search(
        r'https://github\.com/guojianyu0806/chuangyuzhou(?:/|$)', link) for link in links))
    require('new_builder_is_valid_python', bool(ast.parse((MATERIAL / 'build_pdf.py').read_text(encoding='utf-8'))))

    resolved = []
    for evidence_id, paths in SOURCES.items():
        for value in paths:
            path = ROOT / value[1:] if value.startswith('@') else APP / value
            data, source = source_bytes(path, historical=evidence_id == 'E12')
            require('source_exists_' + path.relative_to(ROOT).as_posix(), bool(data))
            resolved.append({'id': evidence_id, 'path': path.relative_to(ROOT).as_posix(),
                             'sha256': sha(data), 'source': source})
    preserved_v1 = []
    protected = json.loads((RECORD / 'protected-v1-files.json').read_text(encoding='utf-8-sig'))
    require('v1_protection_manifest_has_all_6_files', len(protected) == 6
            and {entry['path'] for entry in protected} == {p.name for p in OLD_MATERIAL.iterdir() if p.is_file()})
    for entry in protected:
        path = OLD_MATERIAL / entry['path']
        data = path.read_bytes()
        require('v1_file_unchanged_' + entry['path'], len(data) == entry['bytes'] and sha(data) == entry['sha256'])
        preserved_v1.append({'path': path.relative_to(ROOT).as_posix(),
                             'bytes': len(data), 'sha256': sha(data)})
    old_materials = []
    for value in ['delivery/2026-10-19_创宇宙正式提交_v2/创宇宙_作品介绍文档_正式提交版_v1.pdf',
                  'delivery/DEV-045/技术文档-正式提交版-v1.md',
                  'delivery/DEV-051/作品介绍文档-正文-v1.txt']:
        data = git_bytes(HISTORY_REF, value)
        require('old_material_preserved_in_history_' + value, bool(data))
        old_materials.append({'path': value, 'sha256': sha(data), 'preservedInHistory': HISTORY_REF})
    result = {'recordId': 'WEB-009', 'checkedAt': datetime.now(timezone.utc).isoformat(),
              'pdf': PDF.relative_to(ROOT).as_posix(), 'pdfSha256': sha(PDF.read_bytes()),
              'bytes': PDF.stat().st_size, 'pages': len(pages), 'sourceCommit': SOURCE_SHA,
              'metricsFromExistingTAP': metrics, 'liveUsageFromExistingEvidence': totals,
              'checks': checks, 'textBounds': positions, 'embeddedFonts': sorted(fonts),
              'links': links, 'sourceEvidence': resolved, 'protectedV1Files': preserved_v1,
              'protectedOldMaterials': old_materials,
              'visualReview': {'performedThisRun': False,
                               'separateRecord': 'web-track/evidence/WEB-009/visual-check.json'},
              'applicationTestsRerun': False, 'realModelCalled': False}
    RECORD.mkdir(parents=True, exist_ok=True)
    (RECORD / 'pdf-check.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'ok': True, 'pages': len(pages), 'bytes': PDF.stat().st_size,
                      'passedChecks': len(checks), 'pdfSha256': result['pdfSha256']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
