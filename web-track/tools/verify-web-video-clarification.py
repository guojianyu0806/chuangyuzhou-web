"""Verify the narrowly scoped Web-video render; never call a model or edit inputs."""
from pathlib import Path
import hashlib
import json
import re
import subprocess

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / 'web-track/.local/WEB-015-video-revision'
SOURCE = ROOT / 'releases/2026-10-30_创宇宙Web网盘直接上传_v1/03_创宇宙演示视频.mp4'
DRAFT = WORK / 'web-video-render-draft.mp4'
START, END = 8051, 8321


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(data)
    return h.hexdigest()


def probe(path):
    return json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)
    ], cwd=ROOT))


def audio_hash(path, decoded=False):
    command = ['ffmpeg', '-v', 'error', '-i', str(path), '-map', '0:a:0']
    command += ['-c:a', 'pcm_s16le'] if decoded else ['-c:a', 'copy']
    command += ['-f', 'hash', '-hash', 'sha256', '-']
    return subprocess.check_output(command, cwd=ROOT, text=True).strip()


def main():
    assert DRAFT.is_file()
    source_probe, output_probe = probe(SOURCE), probe(DRAFT)
    src_v = next(s for s in source_probe['streams'] if s['codec_type'] == 'video')
    out_v = next(s for s in output_probe['streams'] if s['codec_type'] == 'video')
    assert out_v['width'] == 1920 and out_v['height'] == 1080 and out_v['codec_name'] == 'h264'
    assert src_v['nb_frames'] == out_v['nb_frames'] == '12417'
    assert src_v['avg_frame_rate'] == out_v['avg_frame_rate'] == '30/1'
    assert abs(float(source_probe['format']['duration']) - float(output_probe['format']['duration'])) < .001
    packets = {'source': audio_hash(SOURCE), 'output': audio_hash(DRAFT)}
    assert packets['source'] == packets['output'], 'AAC packets changed'
    pcm = {'source': audio_hash(SOURCE, True), 'output': audio_hash(DRAFT, True)}
    assert pcm['source'] == pcm['output'], 'Decoded audio changed'
    print(json.dumps({'audioPacketsIdentical': True, 'decodedAudioIdentical': True, 'frameCountUnchanged': True}), flush=True)

    source_cap, output_cap = cv2.VideoCapture(str(SOURCE)), cv2.VideoCapture(str(DRAFT))
    asset = cv2.imdecode(np.frombuffer((ROOT / 'releases/2026-10-30_创宇宙Web视频修订_v1/assets/Web开发约定说明卡.png').read_bytes(), dtype=np.uint8), cv2.IMREAD_COLOR)
    boundary = []
    captures = WORK / 'verified-frames'
    captures.mkdir(exist_ok=True)
    for number in [START-1, START, START+1, 8100, END-1, END, END+1, 8340, 11040]:
        source_cap.set(cv2.CAP_PROP_POS_FRAMES, number)
        output_cap.set(cv2.CAP_PROP_POS_FRAMES, number)
        ok_s, s = source_cap.read()
        ok_o, o = output_cap.read()
        assert ok_s and ok_o
        top_difference = float(np.abs(s[:980].astype(np.float32) - o[:980].astype(np.float32)).mean())
        subtitle_difference = float(np.abs(s[980:].astype(np.float32) - o[980:].astype(np.float32)).mean())
        asset_difference = float(np.abs(asset.astype(np.float32) - o[:980].astype(np.float32)).mean())
        inside = START <= number < END
        assert subtitle_difference < 3.0
        if inside:
            assert asset_difference < 4.0 and top_difference > 10.0, (number, top_difference, asset_difference)
        else:
            assert top_difference < 3.0, (number, top_difference)
        ok, image = cv2.imencode('.png', o)
        assert ok
        (captures / f'{number:05d}.png').write_bytes(image.tobytes())
        boundary.append({'frame': number, 'seconds': number/30, 'insideReplacement': inside,
                         'meanTopPixelDifferenceFromSource': top_difference,
                         'meanSubtitlePixelDifferenceFromSource': subtitle_difference,
                         'meanTopPixelDifferenceFromAsset': asset_difference})
    source_cap.release()
    output_cap.release()
    print(json.dumps({'exactBoundaryChecksPassed': len(boundary), 'subtitleBandPreserved': True}), flush=True)

    # Encoding is lossy: the unedited shots must retain high visual similarity;
    # do not describe their encoded bytes or decoded pixels as identical.
    stats_path = 'web-track/.local/WEB-015-video-revision/unmodified-shots-ssim.log'
    graph = (f"[0:v]select='not(between(n,{START},{END-1}))',setpts=N/(30*TB)[s];"
             f"[1:v]select='not(between(n,{START},{END-1}))',setpts=N/(30*TB)[o];"
             f"[s][o]ssim=stats_file={stats_path}[q]")
    with (WORK / 'ssim-execution.log').open('x', encoding='utf-8', newline='\n') as log:
        result = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', str(SOURCE), '-i', str(DRAFT),
                                 '-filter_complex', graph, '-map', '[q]', '-an', '-f', 'null', '-'],
                                cwd=ROOT, stdout=log, stderr=log)
    assert result.returncode == 0
    scores = []
    for row in (ROOT / stats_path).read_text(encoding='utf-8').splitlines():
        match = re.search(r'All:([0-9.]+)', row)
        if match:
            scores.append(float(match.group(1)))
    assert len(scores) == 12417 - (END - START), len(scores)
    assert np.mean(scores) > .995 and min(scores) > .95
    protected = json.loads((WORK / 'protected-inputs.json').read_text(encoding='utf-8'))
    for item in protected:
        p = Path(item['path']) if Path(item['path']).is_absolute() else ROOT / item['path']
        assert p.stat().st_size == item['bytes'] and sha(p) == item['sha256'], item['path']
    result = {
        'recordId': 'WEB-015', 'sourceSha256': sha(SOURCE), 'renderSha256': sha(DRAFT),
        'outputBytes': DRAFT.stat().st_size, 'durationSeconds': float(output_probe['format']['duration']),
        'width': out_v['width'], 'height': out_v['height'], 'fps': out_v['avg_frame_rate'], 'frames': 12417,
        'startFrameInclusive': START, 'endFrameExclusive': END,
        'replacementSeconds': (END-START)/30, 'audioPacketHashes': packets, 'decodedAudioHashes': pcm,
        'boundaryChecks': boundary, 'unmodifiedShotsSSIM': {'frames': len(scores), 'mean': float(np.mean(scores)),
                                                         'minimum': min(scores), 'encodingIsLossy': True},
        'protectedFilesUnchanged': len(protected),
        'visualReview': {'completed': False, 'separateRecord': 'WEB-015/visual-check.json'},
        'applicationFilesEdited': False, 'modelCalls': 0, 'uploadedToCloud': False,
    }
    path = ROOT / 'web-track/evidence/WEB-015/video-check.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'ok': True, 'unmodifiedFramesCompared': len(scores), 'meanSSIM': result['unmodifiedShotsSSIM']['mean'],
                      'protectedFilesUnchanged': len(protected), 'outputSha256': result['renderSha256']}), flush=True)


if __name__ == '__main__':
    main()
