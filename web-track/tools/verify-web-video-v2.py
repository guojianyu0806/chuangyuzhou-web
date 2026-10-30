"""Validate the precisely scoped Web video v2 before publishing its master."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess

import cv2
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / 'web-track/.local/WEB-019-video-v2'
SOURCE = ROOT / 'releases/2026-10-30_创宇宙Web网盘直接上传_v3/03_创宇宙Web演示视频_v1.mp4'
OUTPUT = ROOT / 'releases/2026-10-30_创宇宙Web视频修订_v2'
DRAFT = WORK / 'video-v2-draft.mp4'
MASTER = OUTPUT / '创宇宙_Web赛道演示视频_v2.mp4'
RANGES = [(8601,9224),(9250,9326),(9326,9407)]


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def probe(p): return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)]))
def audio(p, decoded):
    return subprocess.check_output(['ffmpeg','-v','error','-i',str(p),'-map','0:a:0','-c:a','pcm_s16le' if decoded else 'copy','-f','hash','-hash','sha256','-'],text=True).strip()


def main():
    assert sha(SOURCE)=='34bd7d7454ebc003cc4cc0fc6c66282089477bc06a0e655bab9d7a386b4a5e98'
    assert not MASTER.exists(), 'Never overwrite a completed video.'
    src,out=probe(SOURCE),probe(DRAFT)
    sv=next(x for x in src['streams'] if x['codec_type']=='video')
    ov=next(x for x in out['streams'] if x['codec_type']=='video')
    assert ov['codec_name']=='h264' and ov['width']==1920 and ov['height']==1080
    assert sv['nb_frames']==ov['nb_frames']=='12417' and ov['avg_frame_rate']=='30/1'
    assert abs(float(src['format']['duration'])-float(out['format']['duration']))<.001
    packets={'source':audio(SOURCE,False),'output':audio(DRAFT,False)}
    pcm={'source':audio(SOURCE,True),'output':audio(DRAFT,True)}
    assert len(set(packets.values()))==len(set(pcm.values()))==1
    print('Duration, frames, audio packet and decoded hashes passed.',flush=True)
    with (WORK/'full-decode-errors.txt').open('x',encoding='utf-8') as log:
        subprocess.run(['ffmpeg','-v','error','-i',str(DRAFT),'-map','0:v:0','-map','0:a:0','-f','null','-'],stdout=log,stderr=log,check=True)
    assert (WORK/'full-decode-errors.txt').stat().st_size==0

    assets=[np.array(Image.open(OUTPUT/'assets/交互修订说明.png').convert('RGB'))[:,:,::-1],
            np.array(Image.open(OUTPUT/'assets/反馈结果对照说明.png').convert('RGB'))[:,:,::-1]]
    cs,co=cv2.VideoCapture(str(SOURCE)),cv2.VideoCapture(str(DRAFT))
    numbers=[8051,8100,8320,8600,8601,8602,9000,9223,9224,9249,9250,9325,9326,9406,9407,9408,11040]
    records=[]; tiles=[]; frames_dir=WORK/'verified-frames';frames_dir.mkdir(exist_ok=True)
    for n in numbers:
        cs.set(cv2.CAP_PROP_POS_FRAMES,n); co.set(cv2.CAP_PROP_POS_FRAMES,n)
        oks,s=cs.read(); oko,o=co.read(); assert oks and oko
        inside=any(a<=n<b for a,b in RANGES)
        top=float(np.abs(s[:980].astype(float)-o[:980].astype(float)).mean())
        subtitle=float(np.abs(s[980:].astype(float)-o[980:].astype(float)).mean())
        assert subtitle<3, (n,subtitle)
        if inside:
            ad=float(np.abs(assets[1 if n>=9326 else 0].astype(float)-o[:980].astype(float)).mean())
            assert ad<4 and top>5,(n,ad,top)
        else:
            ad=None;assert top<3,(n,top)
        image=Image.fromarray(cv2.cvtColor(o,cv2.COLOR_BGR2RGB)); image.save(frames_dir/f'{n:05d}.png')
        thumb=image.copy();thumb.thumbnail((480,270));tile=Image.new('RGB',(480,296),'white');tile.paste(thumb,(0,26))
        ImageDraw.Draw(tile).text((8,6),f'v2 / frame {n} / {n/30:.6f}s',fill='black');tiles.append(tile)
        records.append({'frame':n,'seconds':n/30,'edited':inside,'meanTopDifference':top,'meanSubtitleDifference':subtitle,'meanAssetDifference':ad})
    cs.release();co.release()
    sheet=Image.new('RGB',(960,296*((len(tiles)+1)//2)),'white')
    for i,tile in enumerate(tiles):sheet.paste(tile,((i%2)*480,(i//2)*296))
    sheet.save(WORK/'verified-boundaries.jpg')
    print('17 boundary and preserved-shot samples passed.',flush=True)

    expr='not(between(n,8601,9223)+between(n,9250,9325)+between(n,9326,9406))'
    stats='web-track/.local/WEB-019-video-v2/unmodified-ssim.txt'
    graph=f"[0:v]select='{expr}',setpts=N/(30*TB)[s];[1:v]select='{expr}',setpts=N/(30*TB)[o];[s][o]ssim=stats_file={stats}[q]"
    with (WORK/'ssim.log').open('x',encoding='utf-8') as log:
        subprocess.run(['ffmpeg','-hide_banner','-nostats','-i',str(SOURCE),'-i',str(DRAFT),'-filter_complex',graph,'-map','[q]','-an','-f','null','-'],cwd=ROOT,stdout=log,stderr=log,check=True)
    scores=[float(m[1]) for row in (ROOT/stats).read_text().splitlines() if (m:=re.search(r'All:([0-9.]+)',row))]
    assert len(scores)==12417-sum(b-a for a,b in RANGES)==11637
    assert np.mean(scores)>.995 and min(scores)>.95
    assert sha(SOURCE)=='34bd7d7454ebc003cc4cc0fc6c66282089477bc06a0e655bab9d7a386b4a5e98'
    # Copy into a new final pathname only after structural and media checks pass.
    with MASTER.open('xb') as stream, DRAFT.open('rb') as source: shutil.copyfileobj(source,stream)
    report={'recordId':'WEB-019','sourceSha256':sha(SOURCE),'output':MASTER.relative_to(ROOT).as_posix(),
        'outputSha256':sha(MASTER),'renderSha256':sha(MASTER),'outputBytes':MASTER.stat().st_size,'durationSeconds':float(out['format']['duration']),
        'width':1920,'height':1080,'fps':'30/1','frames':12417,'ranges':RANGES,'editedFrameCount':780,
        'audioPacketHashes':packets,'decodedAudioHashes':pcm,'fullAVDecode':'passed; error log empty',
        'boundaryChecks':records,'unmodifiedShotsSSIM':{'frames':len(scores),'mean':float(np.mean(scores)),'minimum':min(scores),'encodingIsLossy':True},
        'visualReview':'See visual-check.json after inspection of fresh final frames.',
        'modelCalls':0,'sourceVideoUnchanged':True}
    evidence=ROOT/'web-track/evidence/WEB-019';evidence.mkdir(parents=True,exist_ok=True)
    with (evidence/'video-check.json').open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'master':str(MASTER),'sha256':sha(MASTER),'meanSSIM':float(np.mean(scores))},ensure_ascii=False),flush=True)


if __name__=='__main__':main()
