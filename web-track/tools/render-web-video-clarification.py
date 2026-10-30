"""Render one clarified development-scope card into a NEW Web video.

Only source frames [8051, 8321) are changed. Original audio is stream-copied.
Source videos, application files, old PDFs and submission folders are read-only.
"""
from pathlib import Path
import hashlib
import json
import subprocess

import cv2
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'releases/2026-10-30_创宇宙Web网盘直接上传_v1/03_创宇宙演示视频.mp4'
OUTPUT = ROOT / 'releases/2026-10-30_创宇宙Web视频修订_v1'
WORK = ROOT / 'web-track/.local/WEB-015-video-revision'
SOURCE_SHA = 'ab2816d9bab7a6ce9196575b1d95619a094d8386761dfb235130eafba233ae81'
START_FRAME, END_FRAME = 8051, 8321
FPS = 30
BG, INK, PURPLE = '#F2EFFA', '#292233', '#70509A'


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def font(size, bold=False):
    return ImageFont.truetype('C:/Windows/Fonts/' + ('Dengb.ttf' if bold else 'Deng.ttf'), size)


def text(draw, xy, value, size=32, fill=INK, bold=False, width=None, leading=None):
    face = font(size, bold)
    x, y = xy
    leading = leading or int(size * 1.55)
    for paragraph in value.split('\n'):
        line = ''
        for char in paragraph:
            if width and line and draw.textlength(line + char, font=face) > width:
                draw.text((x, y), line, font=face, fill=fill)
                y += leading
                line = char
            else:
                line += char
        draw.text((x, y), line, font=face, fill=fill)
        y += leading
    return y


def main():
    assert sha(SOURCE) == SOURCE_SHA
    if OUTPUT.exists():
        raise FileExistsError('Refusing to overwrite an existing version: ' + str(OUTPUT))
    WORK.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True)
    assets = OUTPUT / 'assets'
    assets.mkdir()
    protected = []
    for old_name in ['2026-10-29_创宇宙Web预指导提交_v1', '2026-10-30_创宇宙Web网盘直接上传_v1']:
        for p in sorted((ROOT / 'releases' / old_name).iterdir()):
            if p.is_file():
                protected.append({'path': p.relative_to(ROOT).as_posix(), 'bytes': p.stat().st_size, 'sha256': sha(p)})
    original = Path('E:/传智杯/传智杯AI创新应用挑战赛/delivery/2026-10-20_创宇宙网盘提交_v3/“创宇宙”正式提交视频.mp4')
    assert sha(original) == SOURCE_SHA
    protected.append({'path': str(original), 'bytes': original.stat().st_size, 'sha256': SOURCE_SHA})
    with (WORK / 'protected-inputs.json').open('x', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(protected, ensure_ascii=False, indent=2) + '\n')

    cap = cv2.VideoCapture(str(SOURCE))
    assert cap.isOpened()
    cap.set(cv2.CAP_PROP_POS_FRAMES, 8100)
    ok, frame = cap.read()
    cap.release()
    assert ok
    source_frame = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    # This crop contains only the genuine user feedback bubble and its original
    # date. It deliberately excludes the assistant's historical summary below.
    excerpt = source_frame.crop((72, 185, 912, 556))
    excerpt.save(assets / '真实反馈节选.png')

    card = Image.new('RGB', (1920, 980), BG)
    draw = ImageDraw.Draw(card)
    text(draw, (50, 38), '把修改范围写进开发约定', 44)
    for box in [(48, 111, 936, 926), (984, 111, 1872, 926)]:
        draw.rounded_rectangle(box, radius=23, fill='white', outline='#D8D2E2', width=2)
    text(draw, (72, 132), '开发时的反馈 · 原文节选', 27, PURPLE)
    card.paste(excerpt, (72, 185))
    text(draw, (92, 610), '反馈关注的操作', 36, bold=True)
    text(draw, (92, 680), '恢复从左侧直接拖入方块\n双击进入相应内容编辑\n保留缩小后的颜色与阴影层次', 31, width=760, leading=55)
    text(draw, (1008, 132), '开发约定要点 · 本版整理', 27, PURPLE)
    text(draw, (1038, 218), '明确目标，也保留边界', 41, bold=True)
    draw.line((1038, 282, 1818, 282), fill='#D8D2E2', width=2)
    y = 320
    items = [
        ('01', '说明本次调整目标', '明确要修改的模块、交互与预期结果。'),
        ('02', '保留已经完成的内容', '其他功能、已有资料和相关布局继续保留。'),
        ('03', '核对修改后的实际表现', '对照原操作检查结果，再记录本轮修改。'),
    ]
    for number, heading, body in items:
        draw.rounded_rectangle((1038, y + 4, 1090, y + 50), radius=10, fill='#F0E9F8')
        text(draw, (1048, y + 9), number, 23, PURPLE, True)
        text(draw, (1110, y), heading, 34, bold=True)
        text(draw, (1110, y + 61), body, 29, fill='#51485D', width=690, leading=44)
        y += 166
    text(draw, (1038, 862), '依据真实开发要求整理，原始记录另存于开发证据。', 24, fill='#746A80', width=780)
    asset = assets / 'Web开发约定说明卡.png'
    card.save(asset)

    metadata = {
        'recordId': 'WEB-015', 'sourceVideo': SOURCE.relative_to(ROOT).as_posix(),
        'sourceSha256': SOURCE_SHA, 'sourceFrameForGenuineExcerpt': 8100,
        'startFrameInclusive': START_FRAME, 'endFrameExclusive': END_FRAME,
        'startSeconds': START_FRAME / FPS, 'endSeconds': END_FRAME / FPS,
        'replacementHeight': 980, 'originalSubtitleBandPreserved': [980, 1080],
        'scope': 'Only this development-scope card. Old ports, startup shots, naming, other historical shots and all narration intentionally remain as requested.',
        'newCardIsAnExplanatorySummaryNotAFabricatedHistoricalScreenshot': True,
        'asset': asset.relative_to(ROOT).as_posix(), 'assetSha256': sha(asset),
        'outputMasterDirectory': OUTPUT.relative_to(ROOT).as_posix(),
        'audioMode': 'Stream copy; exact packet and decoded audio hashes must be verified before delivery.',
    }
    with (WORK / 'edit-plan.json').open('x', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n')
    draft = WORK / 'web-video-render-draft.mp4'
    graph = f"[0:v][1:v]overlay=0:0:eof_action=repeat:repeatlast=1:enable='between(n,{START_FRAME},{END_FRAME-1})'[v]"
    command = ['ffmpeg', '-hide_banner', '-nostats', '-n', '-i', str(SOURCE), '-i', str(asset),
               '-filter_complex', graph, '-map', '[v]', '-map', '0:a:0',
               '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-profile:v', 'high', '-level:v', '4.0',
               '-pix_fmt', 'yuv420p', '-fps_mode', 'passthrough', '-c:a', 'copy',
               '-map_metadata', '0', '-metadata', 'title=创宇宙 Web赛道演示视频 v1',
               '-movflags', '+faststart', '-progress', str(WORK / 'render-progress.txt'), str(draft)]
    with (WORK / 'render-command.json').open('x', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(command, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'card': str(asset), 'draft': str(draft), 'changedSeconds': [START_FRAME/FPS, END_FRAME/FPS]}, ensure_ascii=False), flush=True)
    with (WORK / 'render.log').open('x', encoding='utf-8', newline='\n') as log:
        result = subprocess.run(command, cwd=ROOT, stdout=log, stderr=log)
    if result.returncode:
        raise RuntimeError('Render failed; diagnostic log is preserved')
    print(json.dumps({'renderComplete': True, 'draftBytes': draft.stat().st_size, 'draftSha256': sha(draft)}), flush=True)


if __name__ == '__main__':
    main()
