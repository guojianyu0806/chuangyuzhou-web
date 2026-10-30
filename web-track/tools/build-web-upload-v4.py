"""Assemble a new v4 delivery from a fixed Git tree and verified media.

Preserves all existing packages. No application launch, model use or upload.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import zipfile
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
BASE = 'c0ac0564c5e93ea0ba9a7af001dc5e12b685754e'
SNAP = '8d3b22714badc7abc532f09e04f1fc02efdf4780'
APP = 'web-track/chuangyuzhou/'
PDF_REL = 'web-track/materials/2026-10-30_创宇宙Web技术文档_v4/创宇宙_Web赛道技术文档_v4.pdf'
INTRO_REL = 'web-track/materials/2026-10-30_创宇宙Web作品介绍文档_v1/创宇宙_Web赛道作品介绍文档_v1.pdf'
VIDEO_REL = 'releases/2026-10-30_创宇宙Web视频修订_v2/创宇宙_Web赛道演示视频_v2.mp4'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def put(path, text):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(text)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-commit', required=True)
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location('prior_package_helpers', ROOT/'web-track/tools/build-preguidance-package.py')
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    commit = helper.git('rev-parse', args.source_commit).decode().strip()
    assert commit == helper.git('rev-parse', 'HEAD').decode().strip()
    assert not helper.git('diff', '--name-only', '--', 'web-track/chuangyuzhou')
    out = ROOT/'releases/2026-10-30_创宇宙Web网盘直接上传_v4'
    if out.exists():
        raise FileExistsError('Preserve existing output: '+str(out))
    objects, contents = helper.committed_files(commit)
    _, app_snapshot = helper.committed_files('3982e5753b45638e236b897f0f21abbdf1c9f250', (APP.rstrip('/'),))
    assert {n:d for n,d in contents.items() if n.startswith(APP)} == app_snapshot
    manifest = json.loads(contents[APP+'SOURCE-MANIFEST.json'])
    assert len(manifest['files']) == 312
    for row in manifest['files']:
        data = contents[APP+row['path']]
        assert len(data) == row['bytes'] and digest(data) == row['sha256'], row['path']
    pattern = re.compile(rb'sk-[A-Za-z0-9]{20,}|gh[pousr]_[A-Za-z0-9]{30,}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----')
    for name, data in contents.items():
        assert helper.safe_public_path(name), name
        if b'\0' not in data:
            assert not pattern.search(data), 'Secret-like literal in '+name
    assert contents[PDF_REL] == (ROOT/PDF_REL).read_bytes()
    assert contents[INTRO_REL] == (ROOT/INTRO_REL).read_bytes()
    video = ROOT/VIDEO_REL
    video_report_path = 'web-track/evidence/WEB-019/video-check.json'
    assert contents[video_report_path] == (ROOT/video_report_path).read_bytes()
    report = json.loads(contents[video_report_path])
    # Exact identity is bound to the independently reviewed video report.
    expected_video = report.get('renderSha256') or report.get('outputSha256') or report.get('sha256')
    assert expected_video and helper.file_sha(video) == expected_video
    media = json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration:stream=codec_type,width,height','-of','json',str(video)]))
    stream = next(s for s in media['streams'] if s['codec_type']=='video')
    assert 300 <= float(media['format']['duration']) <= 480
    assert stream['width'] >= 1920 and stream['height'] >= 1080
    work = ROOT/'web-track/.local/WEB-019-package'
    bundle = work/'chuangyuzhou-web-complete-history.bundle'
    if bundle.exists():
        raise FileExistsError('Preserve previous bundle')
    out.mkdir()
    source_name = '01_创宇宙Web源码_'+commit[:7]+'.zip'
    with zipfile.ZipFile(out/source_name,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for name, data in contents.items():
            archive.writestr('chuangyuzhou-web/'+name, data)
    work.mkdir(parents=True, exist_ok=True)
    subprocess.run(['git','bundle','create',str(bundle),'main','codex/web-separation-baseline','codex/yuzhou-historical-snapshots'],cwd=ROOT,check=True)
    subprocess.run(['git','bundle','verify',str(bundle)],cwd=ROOT,check=True,capture_output=True)
    heads = helper.git('bundle','list-heads',str(bundle)).decode().splitlines()
    assert {line.split()[0] for line in heads} == {commit,BASE,SNAP}
    _, historic = helper.committed_files(BASE,('evidence/prompt-chains','evidence/dev/DEV-030.md','docs/参赛提交核查-2026-10-16.md'))
    with zipfile.ZipFile(out/'04_AI开发过程与验收证据.zip','x',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        archive.writestr('README.md', ('# 创宇宙Web开发过程与验收证据\n\n'
            f'打包快照：{commit}。本包含该时点main及两条历史分支的完整Git历史；后续归集回执可在独立公开仓库查看。\n\n'
            '先读current-web/web-track/evidence/WEB-008.md及WEB-019.md，再读history-baseline/evidence/prompt-chains/README.md。\n'
            '三条主题链共104条公开文本，保留原文、日期、失败修正与逐条哈希；原生会话和全部图片附件不包含在此摘编中。\n'
            'WEB-008的4次真实模型请求与修复后离线撤销回放分别记录。本轮更新说明及视频，不增加模型测试结论。\n\n'
            '在新的空目录恢复完整历史：\n'
            'git clone git-history/chuangyuzhou-web-complete-history.bundle review-web\n'
            'git -C review-web log --all --oneline\n').encode('utf-8'))
        archive.write(bundle,'git-history/'+bundle.name)
        for name,data in contents.items():
            if name.startswith(('web-track/evidence/','web-track/chuangyuzhou/evidence/')):
                archive.writestr('current-web/'+name,data)
        for name,data in historic.items():
            assert not pattern.search(data), name
            archive.writestr('history-baseline/'+name,data)
    shutil.copyfile(ROOT/PDF_REL,out/'02_创宇宙Web技术文档_v4.pdf')
    shutil.copyfile(video,out/'03_创宇宙Web演示视频_v2.mp4')
    shutil.copyfile(ROOT/INTRO_REL,out/'05_创宇宙Web作品介绍文档_v1.pdf')
    for original,name in [(ROOT/PDF_REL,'02_创宇宙Web技术文档_v4.pdf'),(video,'03_创宇宙Web演示视频_v2.mp4'),(ROOT/INTRO_REL,'05_创宇宙Web作品介绍文档_v1.pdf')]:
        assert helper.file_sha(original) == helper.file_sha(out/name), name
    put(out/'00_作品材料说明.txt',f'''创宇宙 - AI驱动的可搭建个人Web工作台
云南大学；团队“我不是软蛋”；编号42988；A组（211组）。
成员位次：郭剑宇、单汝巨、栾健。

第5项：将本目录全部8个文件上传同一网盘目录，生成有效分享链接及提取码，填写到官网。
第6项：单独选择05_创宇宙Web作品介绍文档_v1.pdf，8页，覆盖表单七项要求。

阅读顺序：05作品介绍 → 02技术PDF v4 → 03演示视频v2 → 01源码 → 04开发与验收证据。
源码ZIP：{source_name}，从固定Git快照{commit}生成。
本次源码包包含部署说明更新，业务实现仍为WEB-008。技术PDF应用快照3982e57与本包应用目录一致；作品介绍引用4946975的功能与验收，后续只更新文档。
证据ZIP保留打包时点完整历史；新增归集回执以公开仓库为准。
视频v2另存整理后的历史反馈说明画面，保留原音轨、字幕、时长与功能演示。
SHA256SUMS.txt校验本目录其他7个文件。

账号由体验者自行创建，模型Key自行配置；本包不提供作者凭据或业务数据库。
当前尚无公网演示站点。实际网盘分享与官网提交在上传完成后办理。
''')
    put(out/'作品链接.txt',f'''作品：创宇宙
云南大学；我不是软蛋；42988；A组（211组）。成员位次：郭剑宇、单汝巨、栾健。
独立公开仓库：https://github.com/guojianyu0806/chuangyuzhou-web
本包固定快照：https://github.com/guojianyu0806/chuangyuzhou-web/tree/{commit}
介绍与技术PDF入口：https://github.com/guojianyu0806/chuangyuzhou-web/blob/main/web-track/materials/README.md
网盘分享地址及提取码由上传者生成后填写第5项；第6项上传05作品介绍PDF。
''')
    records=[{'name':p.name,'bytes':p.stat().st_size,'sha256':helper.file_sha(p)} for p in sorted(out.iterdir())]
    assert len(records)==7
    put(out/'SHA256SUMS.txt',''.join(f"{x['sha256']}  {x['name']}\n" for x in records))
    for name in [source_name,'04_AI开发过程与验收证据.zip']:
        with zipfile.ZipFile(out/name) as z:
            assert z.testzip() is None
    with zipfile.ZipFile(out/source_name) as z:
        for name,data in contents.items():
            assert z.read('chuangyuzhou-web/'+name)==data
    pages={name:len(PdfReader(out/name).pages) for name in ['02_创宇宙Web技术文档_v4.pdf','05_创宇宙Web作品介绍文档_v1.pdf']}
    assert pages['02_创宇宙Web技术文档_v4.pdf']==18 and pages['05_创宇宙Web作品介绍文档_v1.pdf']==8
    result={'date':'2026-10-30','folder':out.relative_to(ROOT).as_posix(),'sourceCommit':commit,'fileCount':8,'files':records,'totalBytes':sum(p.stat().st_size for p in out.iterdir()),'applicationManifestFilesVerified':312,'sourceFilesVerified':len(contents),'zipCrcPassed':True,'bundleHeads':heads,'bundleVerified':True,'pdfPages':pages,'modelCalls':0,'applicationCleanEnvironmentReproduction':False,'uploadedToCloud':False,'competitionSubmitted':False}
    put(ROOT/'web-track/evidence/WEB-019/package-check.json',json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'folder':str(out),'totalBytes':result['totalBytes'],'fileCount':8,'sourceCommit':commit},ensure_ascii=False))


if __name__=='__main__':
    main()
