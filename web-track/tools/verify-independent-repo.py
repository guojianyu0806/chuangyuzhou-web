"""Verify the independent repository without reading runtime/config secrets."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import subprocess

ROOT=Path(__file__).resolve().parents[2]
META=json.loads((ROOT/'WEB-REPOSITORY.json').read_text(encoding='utf-8'))
BASE=META['historyBaseline']


def git(args, cwd=ROOT):
    return subprocess.run(['git']+args,cwd=cwd,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE).stdout


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    expected_main=git(['rev-list',BASE]).decode().splitlines()
    main=git(['rev-list','main']).decode().splitlines()
    assert len(expected_main)==203 and set(expected_main).issubset(main)
    snapshots=git(['rev-list',META['historicalSnapshotsBranch']]).decode().splitlines()
    assert len(snapshots)==25 and snapshots[0]==META['historicalSnapshotsHead']
    assert git(['rev-parse','codex/web-separation-baseline']).decode().strip()==BASE
    assert git(['remote','get-url','origin']).decode().strip()=='https://github.com/'+META['repository']+'.git'
    assert not (ROOT/'.git/objects/info/alternates').exists()
    assert not git(['for-each-ref','--format=%(refname)','refs/codex']).strip()
    packs=list((ROOT/'.git/objects/pack').glob('*.pack'))
    assert packs and all(p.stat().st_nlink==1 for p in packs)
    assert not any((ROOT/x).exists() for x in ['app','yuzhou','submission','delivery','evidence','docs'])
    git(['fsck','--full','--no-reflogs'])
    app=ROOT/META['application']
    manifest=json.loads((app/'SOURCE-MANIFEST.json').read_text(encoding='utf-8'))
    for row in manifest['files']:
        p=app/row['path']
        assert p.is_file() and not p.is_symlink() and p.stat().st_nlink==1
        data=p.read_bytes()
        assert len(data)==row['bytes'] and digest(data)==row['sha256'],row['path']
        historical=git(['show',BASE+':'+p.relative_to(ROOT).as_posix()])
        assert data==historical,row['path']
    package=ROOT/'web-track/materials/2026-10-23_创宇宙Web技术文档_v1'
    material=[]
    for p in sorted(package.iterdir()):
        if p.is_file():
            data=p.read_bytes()
            assert data==git(['show',BASE+':'+p.relative_to(ROOT).as_posix()]),p.name
            material.append({'path':p.relative_to(ROOT).as_posix(),'sha256':digest(data)})
    forbidden=[]
    # Only the planned Git index is inspected. Never traverse .env or runtime.
    for name in git(['ls-files','-z']).decode('utf-8').split(chr(0)):
        parts=Path(name).parts
        if any(x in parts for x in ['.cu-runtime','.local','node_modules']) or Path(name).name=='.env' or Path(name).suffix in ['.db','.sqlite','.pem','.key']:
            forbidden.append(name)
    assert not forbidden
    original_check=None
    before_path=ROOT/'.git/source-state-before.json'
    if before_path.exists():
        before=json.loads(before_path.read_text(encoding='utf-8'))
        original=ROOT.parent/'传智杯AI创新应用挑战赛'
        current={'head':git(['rev-parse','HEAD'],original).decode().strip(),'heads':git(['for-each-ref','--format=%(refname) %(objectname)','refs/heads','refs/tags'],original).decode(),'statusSha256':digest(git(['status','--porcelain=v1','-z','--untracked-files=all'],original)),'remote':git(['remote','get-url','origin'],original).decode().strip(),'dirtyFiles':{p:digest((original/p).read_bytes()) for p in before['dirtyFiles']}}
        assert current==before,'Original repository state changed'
        assert git(['rev-list',BASE],original).decode().splitlines()==expected_main
        assert git(['rev-list',META['historicalSnapshotsBranch']],original).decode().splitlines()==snapshots
        original_check={'head':current['head'],'refsUnchanged':True,'statusUnchanged':True,'remoteUnchanged':True,'existingModifiedFileHashesUnchanged':True,'allOriginalCommitShasMatch':True}
    result={'recordId':'WEB-007','checkedAt':datetime.now(timezone.utc).isoformat(),'sourceBaseline':BASE,'originalMainCommitsPreserved':len(expected_main),'snapshotCommitsPreserved':len(snapshots),'existingCommitMetadataUnchangedBySha':True,'newMainCommitCount':len(main),'independentObjectStore':True,'gitFsckPassed':True,'sourceFilesUnchanged':len(manifest['files']),'pdfPackageFilesUnchanged':material,'privateTrackedPaths':forbidden,'originalRepository':original_check}
    out=ROOT/'web-track/evidence/WEB-007/repository-check.json'
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'ok':True,'mainHistory':len(expected_main),'snapshotHistory':len(snapshots),'sourceFiles':len(manifest['files']),'pdfPackageFiles':len(material),'originalUntouched':original_check is not None},ensure_ascii=False))


if __name__=='__main__':
    main()
