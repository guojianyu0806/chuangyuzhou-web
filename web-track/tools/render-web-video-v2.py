"""Create a new Web video with clearly labeled summaries of genuine feedback.

No chat text is rewritten. Only the specified historical-dialogue pictures are
replaced; the short application close-up, prior card, audio and subtitles stay.
"""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

import cv2
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'releases/2026-10-30_创宇宙Web网盘直接上传_v3/03_创宇宙Web演示视频_v1.mp4'
OUTPUT = ROOT / 'releases/2026-10-30_创宇宙Web视频修订_v2'
WORK = ROOT / 'web-track/.local/WEB-019-video-v2'
SOURCE_SHA = '34bd7d7454ebc003cc4cc0fc6c66282089477bc06a0e655bab9d7a386b4a5e98'
RANGES = [(8601, 9224), (9250, 9326), (9326, 9407)]
BG, INK, PURPLE = '#F2EFFA', '#292233', '#70509A'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def font(size, bold=False):
    return ImageFont.truetype('C:/Windows/Fonts/' + ('Dengb.ttf' if bold else 'Deng.ttf'), size)


def text(draw, xy, value, size=32, fill=INK, bold=False, width=None, leading=None):
    face = font(size, bold); x, y = xy; leading = leading or int(size * 1.55)
    for paragraph in value.split('\n'):
        line = ''
        for char in paragraph:
            if width and line and draw.textlength(line + char, font=face) > width:
                draw.text((x, y), line, font=face, fill=fill); y += leading; line = char
            else:
                line += char
        draw.text((x, y), line, font=face, fill=fill); y += leading
    return y


def frame(number):
    cap = cv2.VideoCapture(str(SOURCE)); cap.set(cv2.CAP_PROP_POS_FRAMES, number)
    ok, pixels = cap.read(); cap.release(); assert ok
    return Image.fromarray(cv2.cvtColor(pixels, cv2.COLOR_BGR2RGB))


def prepare():
    assert sha(SOURCE) == SOURCE_SHA
    if OUTPUT.exists(): raise FileExistsError('Preserve existing video versions: ' + str(OUTPUT))
    OUTPUT.mkdir(parents=True); (OUTPUT / 'assets').mkdir(); WORK.mkdir(parents=True, exist_ok=True)
    # Genuine feedback including its displayed timestamp, from the original card.
    full = frame(9326)
    excerpt = full.crop((72, 185, 912, 556))
    excerpt.save(OUTPUT / 'assets/真实用户反馈节选.png')
    card = Image.new('RGB', (1920, 980), BG); draw = ImageDraw.Draw(card)
    text(draw, (50, 38), '根据实际反馈修正搭建交互', 44)
    for bounds in [(48, 111, 936, 926), (984, 111, 1872, 926)]:
        draw.rounded_rectangle(bounds, radius=23, fill='white', outline='#D8D2E2', width=2)
    text(draw, (72, 132), '开发时的反馈 · 原文节选', 27, PURPLE)
    card.paste(excerpt, (72, 185))
    text(draw, (92, 602), '反馈聚焦的操作', 36, bold=True)
    text(draw, (92, 667), '从左侧直接拖入方块\n双击进入相应内容编辑\n缩小后仍保留颜色与阴影层次', 31, width=760, leading=57)
    text(draw, (1008, 132), '该轮交互修订 · 本版整理', 27, PURPLE)
    items = [
        ('01', '恢复直接拖入', '将方块库中的内容拖入实际搭建画布。'),
        ('02', '完善双击入口', '双击方块进入对应内容，继续查看与编辑。'),
        ('03', '调整视觉与反馈', '去掉多余选中外框，保留层次与操作反馈。'),
        ('04', '核对已有操作', '检查拖入、双击及缩放后的实际表现。'),
    ]
    y = 224
    for number, heading, body in items:
        draw.rounded_rectangle((1038, y + 3, 1090, y + 49), radius=10, fill='#F0E9F8')
        text(draw, (1048, y + 8), number, 23, PURPLE, True)
        text(draw, (1110, y), heading, 34, bold=True)
        text(draw, (1110, y + 58), body, 28, fill='#51485D', width=690, leading=43)
        y += 150
    text(draw, (1038, 862), '依据真实开发记录整理；原始对话另存开发证据。', 24, fill='#746A80', width=780)
    card.save(OUTPUT / 'assets/交互修订说明.png')

    # Preserve the source comparison card's right panel verbatim. Replace its
    # left panel with a genuine user excerpt and visibly contemporary summary.
    comparison = full.crop((0, 0, 1920, 980)); draw = ImageDraw.Draw(comparison)
    draw.rounded_rectangle((48, 111, 936, 926), radius=23, fill='white', outline='#D8D2E2', width=2)
    text(draw, (72, 132), '真实反馈节选与操作要点 · 本版整理', 27, PURPLE)
    comparison.paste(excerpt, (72, 185))
    text(draw, (92, 615), '从反馈到修订', 36, bold=True)
    text(draw, (92, 680), '恢复直接拖入，补齐双击编辑入口。\n调整选中外框，保留缩放后的视觉层次。\n右侧为修改后的方块库与画布实录。', 30, width=760, leading=55)
    text(draw, (92, 868), '原始开发记录保留在证据材料中。', 24, fill='#746A80')
    comparison.save(OUTPUT / 'assets/反馈结果对照说明.png')
    plan = {'sourceVideo': SOURCE.relative_to(ROOT).as_posix(), 'sourceSha256': SOURCE_SHA,
            'ranges': [{'startFrameInclusive': a, 'endFrameExclusive': b, 'startSeconds': a/30, 'endSeconds': b/30} for a,b in RANGES],
            'sourceFrameForGenuineExcerpt': 9326, 'genuineExcerptBounds': [72,185,912,556],
            'originalSubtitleBandPreserved': [980,1080], 'originalAudioStreamCopied': True,
            'applicationCloseUpPreservedFrames': [9224,9250], 'summaryVisiblyLabeled': True,
            'newCardIsNotARewrittenHistoricalChat': True}
    (WORK / 'edit-plan.json').write_text(json.dumps(plan, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def render():
    assert sha(SOURCE) == SOURCE_SHA
    draft = WORK / 'video-v2-draft.mp4'
    command = ['ffmpeg', '-hide_banner', '-nostats', '-n', '-i', str(SOURCE),
        '-i', str(OUTPUT / 'assets/交互修订说明.png'), '-i', str(OUTPUT / 'assets/反馈结果对照说明.png'),
        '-filter_complex', "[0:v][1:v]overlay=0:0:eof_action=repeat:repeatlast=1:enable='between(n,8601,9223)+between(n,9250,9325)'[a];[a][2:v]overlay=0:0:eof_action=repeat:repeatlast=1:enable='between(n,9326,9406)'[v]",
        '-map','[v]','-map','0:a:0','-c:v','libx264','-preset','medium','-crf','17','-profile:v','high','-level:v','4.0',
        '-pix_fmt','yuv420p','-fps_mode','passthrough','-c:a','copy','-map_metadata','0',
        '-metadata','title=创宇宙 Web赛道演示视频 v2','-movflags','+faststart',
        '-progress',str(WORK / 'render-progress.txt'),str(draft)]
    (WORK / 'render-command.json').write_text(json.dumps(command, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    with (WORK / 'render.log').open('x', encoding='utf-8') as log:
        subprocess.run(command, cwd=ROOT, stdout=log, stderr=log, check=True)
    print(json.dumps({'rendered': str(draft), 'bytes': draft.stat().st_size, 'sha256': sha(draft)}, ensure_ascii=False))


if __name__ == '__main__':
    if '--render' in sys.argv: render()
    else: prepare()
