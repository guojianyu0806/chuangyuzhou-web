"""Verify WEB-010 PDF v3 and its unchanged business implementation offline.

Only this stage's pdf-check.json is written. No model call, credential loading,
PDF rebuilding, old-report mutation, or claimed visual inspection occurs here.
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
MATERIAL = ROOT / 'web-track/materials/2026-10-28_创宇宙Web技术文档_v3'
PDF = MATERIAL / '创宇宙_Web赛道技术文档_v3.pdf'
MD = MATERIAL / '创宇宙_Web赛道技术文档_正文_v3.md'
RECORD = ROOT / 'web-track/evidence/WEB-010'
REPOSITORY_URL = 'https://github.com/guojianyu0806/chuangyuzhou-web'
IMPLEMENTATION_SHA = 'c71c0411245943198ce1db9d6276e211b4a28c94'
HISTORY_REF = json.loads((ROOT / 'WEB-REPOSITORY.json').read_text(encoding='utf-8'))['historyBaseline']
if not re.fullmatch(r'[0-9a-f]{40}', HISTORY_REF):
    raise ValueError('Invalid fixed history baseline')

SOURCES = {
    'E01': ['README.md', 'SOURCE-MANIFEST.json', 'RELEASE-CHANGES.json'],
    'E02': ['@web-track/evidence/WEB-007.md', '@web-track/evidence/WEB-008.md',
            '@web-track/evidence/WEB-008/isolation-check.json'],
    'E03': ['evidence/engineering/WEB-008-tests-2026-10-24T10-05-53-648Z.tap'],
    'E04': ['@web-track/evidence/WEB-008/09-linked-tasks.png',
            '@web-track/evidence/WEB-008/12-replay-undo-after-refresh.png'],
    'E05': ['yuzhou/frontend/src/' + name for name in
            ['workbench-model.js', 'canvas.js', 'space-workbench-model.js', 'calendar-links.js']],
    'E06': ['yuzhou/backend/' + name for name in ['server.mjs', 'store.mjs', 'extractor.mjs', 'extract.py']],
    'E07': ['yuzhou/backend/hermes.mjs', 'yuzhou/backend/workspace-queries.mjs',
            'yuzhou/frontend/src/workspace-actions.js', 'yuzhou/frontend/src/workspace-actions-core.js'],
    'E08': ['yuzhou/backend/deepseek.mjs', 'yuzhou/backend/model-environment.mjs', 'tools/start.mjs'],
    'E09': ['yuzhou/frontend/src/' + name for name in
            ['custom-blocks.js', 'miniapp-runtime.js', 'miniapp-frame.js']]
           + ['yuzhou/frontend/miniapp-runtime.html'],
    'E10': ['yuzhou/frontend/src/cloud.js', 'yuzhou/frontend/src/workspace-storage.js',
            'yuzhou/backend/store.mjs'],
    'E11': ['web-deployment/' + name for name in
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


def public_bytes(path, historical=False):
    if not historical and path.is_file():
        return path.read_bytes(), 'working-tree'
    return git_bytes(HISTORY_REF, path.relative_to(ROOT).as_posix()), HISTORY_REF


def main():
    checks = {}

    def require(name, condition):
        checks[name] = bool(condition)
        if not condition:
            raise AssertionError(name)

    markdown = MD.read_text(encoding='utf-8')
    source_link = re.search(
        r'\[本报告对应的固定Web源码\]\(https://github\.com/guojianyu0806/chuangyuzhou-web/tree/'
        r'([0-9a-f]{40})/web-track/chuangyuzhou\)', markdown)
    require('one_exact_fixed_source_link', source_link is not None)
    source_sha = source_link.group(1)
    require('fixed_source_commit_is_present', subprocess.run(
        ['git', 'cat-file', '-e', source_sha + '^{commit}'], cwd=ROOT,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0)
    require('business_implementation_commit_is_present', subprocess.run(
        ['git', 'cat-file', '-e', IMPLEMENTATION_SHA + '^{commit}'], cwd=ROOT,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0)
    expected_pages = markdown.count('<!-- PAGE -->') + 1
    reader = PdfReader(PDF)
    pages = [page.extract_text() or '' for page in reader.pages]
    text = '\n'.join(pages)
    flat = re.sub(r'\s+', '', text)
    require('explicit_page_count_within_30_page_limit', 1 <= len(pages) == expected_pages <= 30)
    require('unencrypted_static_pdf', not reader.is_encrypted and '/AcroForm' not in reader.trailer['/Root'])
    require('A4_pages', all(abs(float(page.mediabox.width) - 595.276) < 1
                            and abs(float(page.mediabox.height) - 841.89) < 1 for page in reader.pages))
    require('all_pages_have_body_and_correct_footer', all(
        len(value) > 300 and f'{index:02d}/{expected_pages}' in re.sub(r'\s+', '', value)
        for index, value in enumerate(pages, 1)))
    names = ['郭剑宇', '单汝巨', '栾健']
    require('team_member_order', all(name in pages[0] for name in names)
            and [pages[0].index(name) for name in names] == sorted(pages[0].index(name) for name in names))
    cover = re.sub(r'\s+', '', pages[0])
    require('team_name_number_school_and_group', all(value in cover for value in
            ['我不是软蛋', '42988', '云南大学', 'A组', '211']))
    require('current_source_release_and_port', source_sha[:7] in text
            and '2026-10-28-web-dev-010' in flat and '127.0.0.1:4396' in flat)
    require('v3_version_and_document_date', '技术文档v3' in flat and '2026-10-28' in text)
    require('no_wrong_runtime_ports', all(port not in flat for port in ['4397', '4398', '4399']))
    require('all_environment_fields', all(value in flat for value in
            ['CZB_YUZHOU_HOST', 'CZB_YUZHOU_PORT', 'CZB_YUZHOU_MODE',
             'CZB_YUZHOU_PUBLIC_ORIGIN', 'DEEPSEEK_API_KEY', 'DEEPSEEK_MODEL']))
    require('no_key_like_literal', not re.search(r'\bsk-[A-Za-z0-9_-]{12,}', text + markdown))
    require('no_replacement_or_square_glyph', all(char not in text for char in ['\ufffd', '\u25a0', '\u25a1']))

    tap = (APP / SOURCES['E03'][0]).read_text(encoding='utf-8')
    metrics = {key: int(re.search(r'^# ' + key + r' (\d+)$', tap, re.M).group(1))
               for key in ['tests', 'pass', 'fail', 'skipped']}
    require('existing_TAP_metrics_match', metrics == {'tests': 920, 'pass': 917, 'fail': 0, 'skipped': 3}
            and all(value in flat for value in ['920项', '917通过', '0失败', '3跳过']))
    acceptance = json.loads((ROOT / 'web-track/evidence/WEB-008/acceptance-check.json').read_text(encoding='utf-8'))
    usage = json.loads((ROOT / 'web-track/evidence/WEB-008/provider-usage.json').read_text(encoding='utf-8'))
    totals = usage['metrics']['totals']
    require('all_four_actual_calls_are_counted', totals == {
        'requests': 4, 'promptTokens': 46802, 'completionTokens': 1928,
        'totalTokens': 48730, 'usageResponses': 4}
        and len(usage['metrics']['calls']) == 4
        and all(call['httpStatus'] == 200 for call in usage['metrics']['calls']))
    require('actual_usage_matches_document', 'deepseek-flash' in flat and '4次' in flat
            and bool(re.search(r'48[,，]?730', flat)))
    require('separate_targeted_and_evidence_checks', acceptance['passed'] == 32
            and all(acceptance['checks'].values()) and '32项' in flat and '27项' in flat)
    require('original_revision_failure_is_preserved', acceptance['firstRevisionRequiredClarification']
            and '漏改' in text and '修订' in text)
    require('offline_replay_boundary_is_explicit', '离线回放' in flat
            and bool(re.search(r'(?:0次|0新增|新增.{0,4}0|未新增|没有新增|未追加|无新增).{0,12}(?:模型|请求|调用)'
                               r'|(?:模型|请求|调用).{0,8}(?:0次|0新增)', flat)))
    require('hidden_geometry_cache_limit_is_disclosed', '隐藏' in text and ('几何缓存' in text or '布局缓存' in text))
    require('unverified_environment_boundaries_remain', acceptance['cleanEnvironmentReproduction'] is False
            and acceptance['publicTLS'] is False and 'TLS' in text
            and bool(re.search(r'(?:未|尚无|没有).{0,16}(?:独立|真人|收益|对照)', flat)))

    require('AI_selection_reasons_and_tradeoffs_are_explicit', bool(re.search(r'选型|选择', text))
            and bool(re.search(r'取舍|原因|依据|理由', text)) and 'DeepSeek' in text)
    require('optimization_purpose_and_evidence_are_explicit', '优化' in text
            and bool(re.search(r'目的|目标|取舍', text)) and bool(re.search(r'证据|验证|实测', text)))
    require('technical_and_application_innovation_are_separate', '技术创新' in text and '应用创新' in text)
    require('case_matrix_has_expected_actual_and_protection', all(value in text for value in ['预期', '实际', '保护']))
    require('primary_user_or_scenario_is_defined', bool(re.search(r'首要|目标用户|首批用户|优先服务', text)))
    require('no_claimed_model_benchmark_superiority', bool(re.search(
        r'(?:未|没有|尚未).{0,16}(?:横向|对比|对照|比较)|(?:横向|对比|对照|比较).{0,16}(?:未|没有|尚无)', flat)))
    require('no_internal_user_instruction_in_formal_boundary', '按用户本轮要求' not in text)

    guide = (APP / 'README.md').read_text(encoding='utf-8')
    guide_flat = re.sub(r'\s+', '', guide)
    require('current_guide_uses_WEB010', 'WEB-010' in guide and '开发版 WEB-004' not in guide)
    require('current_guide_uses_independent_repository', REPOSITORY_URL in guide
            and not re.search(r'https://github\.com/guojianyu0806/chuangyuzhou(?:/|\s|$)', guide))
    require('current_guide_has_review_route', '评审' in guide and '路线' in guide)
    require('current_guide_has_no_unmeasured_time_or_optional_AI_heading',
            '十分钟基础复现' not in guide and '可选AI体验' not in guide)
    require('current_guide_does_not_mark_completed_AI_as_pending', not re.search(
        r'真实AI流程与材料定稿另按|真实AI.{0,8}待完成|没有为你填写或读取真实Key', guide))
    require('current_guide_retains_existing_metrics_and_boundaries', all(value in guide_flat for value in
            ['920', '917', '27', '32', '离线回放']) and bool(re.search(r'48[,，]?730', guide_flat)))

    positions = []
    with pdfplumber.open(PDF) as pdf:
        for index, page in enumerate(pdf.pages, 1):
            chars = [char for char in page.chars if char['text'].strip()]
            punctuation = '，。、；：！？）》】”’'
            bad = [char for char in chars if char['x0'] < 45
                   or char['x1'] > page.width - (36 if char['text'] in punctuation else 45)
                   or char['top'] < 8 or char['bottom'] > page.height - 20]
            require(f'page_{index:02d}_text_inside_print_area', not bad)
            positions.append({'page': index, 'characters': len(chars),
                              'left': round(min(char['x0'] for char in chars), 2),
                              'right': round(max(char['x1'] for char in chars), 2)})
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
            and any(REPOSITORY_URL + '/tree/' + source_sha in link for link in links))
    require('official_track_link_retained', any('boxuegu.com/matchTrack/detail/?id=10037' in link for link in links))
    require('no_old_repository_links', not any(re.search(
        r'https://github\.com/guojianyu0806/chuangyuzhou(?:/|$)', link) for link in links))
    require('v3_builder_has_valid_syntax', bool(ast.parse((MATERIAL / 'build_pdf.py').read_text(encoding='utf-8'))))

    resolved = []
    for evidence_id, paths in SOURCES.items():
        for value in paths:
            path = ROOT / value[1:] if value.startswith('@') else APP / value
            data, source = public_bytes(path, historical=evidence_id == 'E12')
            require('source_exists_' + path.relative_to(ROOT).as_posix(), bool(data))
            resolved.append({'id': evidence_id, 'path': path.relative_to(ROOT).as_posix(),
                             'sha256': sha(data), 'source': source})

    preserved_versions = []
    protected = json.loads((RECORD / 'protected-pdf-versions.json').read_text(encoding='utf-8-sig'))
    require('two_old_pdf_packages_have_twelve_files', len(protected) == 12
            and len({entry['version'] for entry in protected}) == 2)
    for entry in protected:
        path = ROOT / 'web-track/materials' / entry['version'] / entry['path']
        data = path.read_bytes()
        require('old_version_file_unchanged_' + entry['version'] + '/' + entry['path'],
                len(data) == entry['bytes'] and sha(data) == entry['sha256'])
        preserved_versions.append({'path': path.relative_to(ROOT).as_posix(),
                                   'bytes': len(data), 'sha256': sha(data)})
    application = json.loads((RECORD / 'protected-application-files.json').read_text(encoding='utf-8-sig'))
    require('only_expected_application_doc_paths_are_permitted', set(application['permittedApplicationChanges'])
            == {'README.md', 'SOURCE-MANIFEST.json', 'RELEASE-CHANGES.json'})
    require('business_protection_manifest_has_310_files', len(application['files']) == 310)
    for entry in application['files']:
        data = (APP / entry['path']).read_bytes()
        require('business_file_unchanged_' + entry['path'],
                len(data) == entry['bytes'] and sha(data) == entry['sha256'])

    result = {'recordId': 'WEB-010', 'checkedAt': datetime.now(timezone.utc).isoformat(),
              'pdf': PDF.relative_to(ROOT).as_posix(), 'pdfSha256': sha(PDF.read_bytes()),
              'bytes': PDF.stat().st_size, 'pages': len(pages), 'expectedPages': expected_pages,
              'sourceCommit': source_sha, 'businessImplementationCommit': IMPLEMENTATION_SHA,
              'metricsFromExistingTAP': metrics, 'liveUsageFromExistingEvidence': totals,
              'checks': checks, 'textBounds': positions, 'embeddedFonts': sorted(fonts),
              'links': links, 'sourceEvidence': resolved, 'protectedPDFVersions': preserved_versions,
              'protectedApplicationFiles': len(application['files']),
              'visualReview': {'performedThisRun': False,
                               'separateRecord': 'web-track/evidence/WEB-010/visual-check.json'},
              'applicationTestsRerun': False, 'realModelCalled': False}
    RECORD.mkdir(parents=True, exist_ok=True)
    (RECORD / 'pdf-check.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'ok': True, 'pages': len(pages), 'bytes': PDF.stat().st_size,
                      'passedChecks': len(checks), 'pdfSha256': result['pdfSha256']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
