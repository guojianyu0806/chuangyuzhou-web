"""Create a local, versioned submission folder from public Git objects.

No model calls, credentials, working runtime data, network upload, or overwrite.
Requires reportlab, pypdf, ffprobe and the Windows Deng fonts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
from xml.sax.saxutils import escape
import zipfile

from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

ROOT = Path(__file__).resolve().parents[2]
BASELINE = 'c0ac0564c5e93ea0ba9a7af001dc5e12b685754e'
SNAPSHOTS = '8d3b22714badc7abc532f09e04f1fc02efdf4780'
VIDEO_SHA = 'ab2816d9bab7a6ce9196575b1d95619a094d8386761dfb235130eafba233ae81'
PDF_SHA = '531f3b7e97cc9bba1985feba23e122275424408becd1544cd689fdfd6236699c'
PDF_REL = 'web-track/materials/2026-10-28_创宇宙Web技术文档_v3/创宇宙_Web赛道技术文档_v3.pdf'
AI_TEXT = (
    '创宇宙采用“需求拆解、分阶段提示、运行核验、反馈修正”的人机协作流程。'
    '开发阶段使用Codex辅助生成和调整Web代码、测试与文档；提示词明确目标、现有功能、隔离范围和审核要求。'
    '人工确定产品方向，审阅交互效果，通过具体反馈推动拖入搭建、布局及AI流程修正。'
    '产品内接入DeepSeek，按“查询资料、生成结构化方案、多轮修订、人工确认、执行回执、有限撤销”组织操作，确认前不写业务数据。'
    '真实验收保留日期漏改和撤销问题及修复记录，区分在线模型结果、工程测试和离线回放。'
    '源码、Prompt链和Git记录可追溯。'
)


def git(*args: str) -> bytes:
    return subprocess.check_output(['git', *args], cwd=ROOT)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def committed_files(commit: str, selected: tuple[str, ...] = ()) -> tuple[dict, dict]:
    objects = {}
    for row in git('ls-tree', '-r', '-z', commit).split(b'\0'):
        if not row:
            continue
        meta, raw_path = row.split(b'\t', 1)
        mode, kind, object_id = meta.decode().split()
        path = raw_path.decode('utf-8')
        if selected and not any(path == prefix or path.startswith(prefix + '/') for prefix in selected):
            continue
        assert kind == 'blob' and mode in {'100644', '100755'}
        assert safe_public_path(path), path
        objects[path] = object_id
    object_ids = list(objects.values())
    process = subprocess.run(['git', 'cat-file', '--batch'], cwd=ROOT,
                             input=('\n'.join(object_ids) + '\n').encode(), capture_output=True, check=True)
    raw, offset, contents = process.stdout, 0, {}
    for path, expected in objects.items():
        end = raw.index(b'\n', offset)
        object_id, kind, size = raw[offset:end].split()
        assert object_id.decode() == expected and kind == b'blob'
        start = end + 1
        data = raw[start:start + int(size)]
        assert hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest() == expected
        contents[path] = data
        offset = start + int(size) + 1
    assert offset == len(raw)
    return objects, contents


def text_file(path: Path, value: str) -> None:
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(value)


def safe_public_path(value: str) -> bool:
    path = PurePosixPath(value)
    forbidden = {'.git', '.cu-runtime', '.runtime', '.private-cloud', 'node_modules', '__pycache__'}
    name = path.name
    return (not forbidden.intersection(path.parts)
            and not (name.startswith('.env') and name != '.env.example')
            and name not in {'setup-code.txt', 'model-config.json'}
            and path.suffix.lower() not in {'.db', '.sqlite', '.keystore', '.jks'})


def write_short_pdf(path: Path) -> dict:
    title = '创宇宙AI创作说明'
    footer = '云南大学 · A组 · 郭剑宇、单汝巨、栾健'
    assert len(AI_TEXT) <= 300
    assert len(title + AI_TEXT + footer) <= 300
    pdfmetrics.registerFont(TTFont('CBody', 'C:/Windows/Fonts/Deng.ttf'))
    pdfmetrics.registerFont(TTFont('CBold', 'C:/Windows/Fonts/Dengb.ttf'))
    ink, teal = colors.HexColor('#163443'), colors.HexColor('#087D78')
    body = ParagraphStyle('Body', fontName='CBody', fontSize=12, leading=24,
                          textColor=ink, wordWrap='CJK')
    heading = ParagraphStyle('Title', fontName='CBold', fontSize=23, leading=32, textColor=ink)

    def decorate(canvas, doc):
        width, height = A4
        canvas.setFillColor(teal)
        canvas.rect(56, height - 56, 42, 4, fill=1, stroke=0)
        canvas.setStrokeColor(colors.HexColor('#D9E6E7'))
        canvas.line(56, 86, width - 56, 86)
        canvas.setFont('CBody', 10)
        canvas.setFillColor(colors.HexColor('#52636D'))
        canvas.drawString(56, 65, footer)

    doc = SimpleDocTemplate(str(path), pagesize=A4, leftMargin=56, rightMargin=56,
                            topMargin=88, bottomMargin=110, title=title,
                            author='郭剑宇、单汝巨、栾健', subject='AI创作说明，正文300字以内')
    doc.build([Paragraph(title, heading), Spacer(1, 28), Paragraph(escape(AI_TEXT), body)],
              onFirstPage=decorate, onLaterPages=decorate)
    reader = PdfReader(path)
    extracted = ''.join((p.extract_text() or '') for p in reader.pages)
    visible = re.sub(r'\s+', '', extracted)
    assert len(reader.pages) == 1 and not reader.is_encrypted
    assert re.sub(r'\s+', '', AI_TEXT) in visible
    assert len(visible) <= 300
    assert path.stat().st_size < 100_000_000
    return {'pages': 1, 'bodyCharactersIncludingPunctuationAndLatinLetters': len(AI_TEXT),
            'allVisibleNonWhitespaceCharacters': len(visible), 'under100MB': True}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-commit', required=True)
    parser.add_argument('--video', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    commit = git('rev-parse', args.source_commit).decode().strip()
    assert commit == git('rev-parse', 'main').decode().strip(), 'Use the reviewed main baseline'
    assert git('rev-parse', 'codex/web-separation-baseline').decode().strip() == BASELINE
    assert git('rev-parse', 'codex/yuzhou-historical-snapshots').decode().strip() == SNAPSHOTS
    assert git('diff', '--name-only', '--', 'web-track/chuangyuzhou') == b''
    output = args.output.resolve()
    assert output.is_relative_to((ROOT / 'releases').resolve())
    if output.exists() and any(output.iterdir()):
        raise FileExistsError('Refusing to overwrite an existing delivery folder: ' + str(output))
    video = args.video.resolve(strict=True)
    assert file_sha(video) == VIDEO_SHA, 'Unexpected video original'
    pdf = ROOT / PDF_REL
    assert file_sha(pdf) == PDF_SHA
    media = json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_entries', 'format=duration:stream=codec_type,width,height',
        '-of', 'json', str(video)], text=True, encoding='utf-8'))
    video_stream = next(row for row in media['streams'] if row['codec_type'] == 'video')
    assert video_stream['width'] == 1920 and video_stream['height'] == 1080
    output.mkdir(parents=True, exist_ok=True)
    work = ROOT / 'web-track/.local/WEB-011'
    work.mkdir(parents=True, exist_ok=True)
    source = output / ('01_创宇宙Web源码_' + commit[:7] + '.zip')
    objects, committed = committed_files(commit)
    with zipfile.ZipFile(source, 'x', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path, data in committed.items():
            archive.writestr('chuangyuzhou-web/' + path, data)
    sensitive = re.compile(rb'sk-[0-9a-fA-F]{32,}|gh[pousr]_[A-Za-z0-9]{30,}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----')
    with zipfile.ZipFile(source) as archive:
        files = {i.filename[len('chuangyuzhou-web/'):]: i for i in archive.infolist() if not i.is_dir()}
        assert set(files) == set(objects)
        data_by_path = {}
        for path, info in files.items():
            data = archive.read(info)
            assert hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest() == objects[path]
            if b'\0' not in data and not path.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg', '.webp')):
                assert not sensitive.search(data), 'Review secret-like literal in ' + path
            data_by_path[path] = data
        manifest = json.loads(data_by_path['web-track/chuangyuzhou/SOURCE-MANIFEST.json'])
        manifest_files = manifest['files']
        assert len(manifest_files) == 312
        for item in manifest_files:
            data = data_by_path['web-track/chuangyuzhou/' + item['path']]
            assert sha(data) == item['sha256'], item['path']
    bundle = work / 'chuangyuzhou-web-complete-history.bundle'
    if bundle.exists():
        raise FileExistsError('Refusing to replace existing bundle: ' + str(bundle))
    subprocess.run(['git', 'bundle', 'create', str(bundle), 'main',
                    'codex/web-separation-baseline', 'codex/yuzhou-historical-snapshots'], cwd=ROOT, check=True)
    verified = subprocess.run(['git', 'bundle', 'verify', str(bundle)], cwd=ROOT,
                               capture_output=True, text=True, encoding='utf-8')
    assert verified.returncode == 0
    bundle_heads = git('bundle', 'list-heads', str(bundle)).decode().splitlines()
    assert len(bundle_heads) == 3
    _, historical = committed_files(BASELINE, ('evidence/prompt-chains',
                                               'evidence/dev/DEV-030.md',
                                               'docs/参赛提交核查-2026-10-16.md'))
    historical_files = 0
    evidence = output / '04_AI开发过程与验收证据.zip'
    with zipfile.ZipFile(evidence, 'x', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        archive.writestr('README.md', (
            '# 创宇宙Web开发过程与验收证据\n\n'
            f'Web固定版本：{commit}；历史基线：{BASELINE}。\n\n'
            '先读current-web/web-track/evidence/WEB-008.md，再看history-baseline/evidence/prompt-chains/README.md。\n'
            '历史摘编保留原名、日期、失败及限制；不把旧流程写成本次重新运行。\n'
            '三链共104条选定主题的公开文本，含专业说明、原文哈希、46条提交索引和10份diff；不是完整原生聊天或全部图片附件。\n'
            '产品内DeepSeek验收与Codex辅助开发分别阅读。WEB-008为4次真实请求；修复后撤销为离线回放。\n'
            'current-web保留当前Web证据；history-baseline为原字节历史摘编。个别跨目录历史链接可用完整Git恢复后查看。\n\n'
            'git-history/chuangyuzhou-web-complete-history.bundle包含main和两个固定历史分支的完整可达历史，无本地凭据或运行目录。\n'
            '需要完整历史时，在新的空目录旁执行：\n'
            'git clone git-history/chuangyuzhou-web-complete-history.bundle review-web\n'
            'git -C review-web log --all --oneline\n'
            f'git -C review-web switch --detach {BASELINE}\n'
            '以上为恢复说明，本轮没有执行独立环境应用复现。\n').encode('utf-8'))
        archive.write(bundle, 'git-history/' + bundle.name)
        for path, data in data_by_path.items():
            if path.startswith(('web-track/evidence/', 'web-track/chuangyuzhou/evidence/')):
                archive.writestr('current-web/' + path, data)
        for path, data in historical.items():
            assert not sensitive.search(data), 'Review historical literal in ' + path
            archive.writestr('history-baseline/' + path, data)
            historical_files += 1
    with zipfile.ZipFile(evidence) as archive:
        assert archive.testzip() is None
        assert archive.read('git-history/' + bundle.name) == bundle.read_bytes()
    shutil.copyfile(pdf, output / '02_创宇宙Web技术文档_v3.pdf')
    shutil.copyfile(video, output / '03_创宇宙演示视频.mp4')
    assert file_sha(video) == file_sha(output / '03_创宇宙演示视频.mp4') == VIDEO_SHA
    assert file_sha(pdf) == file_sha(output / '02_创宇宙Web技术文档_v3.pdf') == PDF_SHA
    short_pdf = output / '05_AI创作说明_300字以内_v1.pdf'
    pdf_check = write_short_pdf(short_pdf)
    text_file(output / '作品链接.txt', (
        '作品：创宇宙 - AI驱动的可搭建个人Web工作台\n'
        '云南大学；我不是软蛋；团队编号42988；A组（211组）。\n'
        '成员位次：1 郭剑宇；2 单汝巨；3 栾健。\n\n'
        '独立公开仓库：https://github.com/guojianyu0806/chuangyuzhou-web\n'
        f'本包固定版本：https://github.com/guojianyu0806/chuangyuzhou-web/tree/{commit}\n'
        '当前没有已部署的公网演示站点；仓库链接不是在线应用。\n'
        '网盘分享地址和提取码由上传者生成后填写到官网第5项；本文件不伪造分享链接。\n'))
    text_file(output / '00_材料说明与上传指引.txt', (
        '创宇宙Web预指导提交材料 | 2026-10-29 | v1\n\n'
        '第5项：将本文件夹整体上传百度网盘，生成有效分享链接，建议长期有效并附提取码，再填入官网。\n'
        '第6项：单独选择05_AI创作说明_300字以内_v1.pdf上传；正文251字符，连标题及署名仍少于300，文件小于100MB。\n'
        '不要把02技术长文档或03视频错选到第6项。100MB限制来自截图第6项，不是本文件夹或网盘视频的限制。\n\n'
        '文件清单：\n'
        '01：Web源码ZIP，固定公开Git版本，包含运行指南、配置模板和现有证据，无账号、Key或运行数据。\n'
        '02：最新18页技术PDF v3，原件字节保留。\n'
        '03：用户选定旧MP4的原字节副本，不重新剪辑。\n'
        '04：三条真实开发对话链、Web验收记录、工程报告及完整Git bundle。\n'
        '05：300字以内AI创作说明，供官网第6项单独上传。\n'
        '作品链接.txt：独立公开仓库及固定版本入口。SHA256SUMS.txt：其余7个文件的SHA-256。\n\n'
        '核对结果与边界：截图第5、6项需要的本地文件已经备齐；当前未上传网盘、未生成分享链接、未提交官网。\n'
        '本轮核验文件完整性、ZIP内容、PDF和视频参数；没有重新观看视频全片、重复模型调用或进行独立环境应用复现。\n'
        '截图未展示的其他表单项需要按实际页面另行核对；不据两项截图声称整张报名表已完成。\n'
        f'源码固定提交：{commit}\n'
        '源码运行：解压01后阅读根README；Node.js >=22.13，进入web-track/chuangyuzhou运行node tools/start.mjs。\n'
        '模型由体验者配置自己的Key，提交包不提供作者Key。\n\n'
        'AI创作说明正文（也便于复制）：\n' + AI_TEXT + '\n'))
    files = sorted(output.iterdir(), key=lambda p: p.name)
    assert len(files) == 7
    file_records = [{'name': p.name, 'bytes': p.stat().st_size, 'sha256': file_sha(p)} for p in files]
    text_file(output / 'SHA256SUMS.txt', ''.join(f"{r['sha256']}  {r['name']}\n" for r in file_records))
    report = {
        'recordId': 'WEB-011', 'date': '2026-10-29', 'output': output.relative_to(ROOT).as_posix(),
        'sourceCommit': commit, 'sourceFilesVerifiedAgainstGitBlobs': len(objects),
        'applicationManifestFilesVerified': len(manifest_files),
        'sourceZipContainsOnlyCommittedFiles': True, 'sourceTextSecretLikeLiterals': 0,
        'historicalExcerptFiles': historical_files, 'bundleHeads': bundle_heads,
        'bundleVerifyExitCode': verified.returncode, 'shortPDF': pdf_check,
        'video': {'sourcePath': str(video), 'sha256': VIDEO_SHA, 'copiedBytesUnchanged': True,
                  'width': video_stream['width'], 'height': video_stream['height'],
                  'durationSeconds': float(media['format']['duration']), 'fullViewingRepeated': False},
        'technicalPDF': {'source': PDF_REL, 'sha256': PDF_SHA, 'copiedBytesUnchanged': True,
                         'pages': len(PdfReader(pdf).pages)},
        'files': file_records, 'checksumFile': 'SHA256SUMS.txt',
        'totalBytes': sum(p.stat().st_size for p in output.iterdir()),
        'visualReview': {'completed': False, 'separateRecord': 'WEB-011/visual-check.json'},
        'newModelCalls': 0, 'applicationCleanEnvironmentReproduction': False,
        'uploadedToCloud': False, 'cloudShareLinkCreated': False, 'competitionSubmitted': False,
        'originalFilesOverwritten': False, 'originalRepositoryWrite': False,
    }
    record_path = ROOT / 'web-track/evidence/WEB-011/package-check.json'
    record_path.parent.mkdir(parents=True, exist_ok=True)
    text_file(record_path, json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'output': str(output), 'files': 8, 'totalBytes': report['totalBytes'],
                      'sourceFiles': len(objects), 'shortPDF': pdf_check}, ensure_ascii=False))


if __name__ == '__main__':
    main()
