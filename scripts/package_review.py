"""Build the portable Skill from its committed files, with recursive byte checks."""
import hashlib,io,json,re,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SKILL=ROOT/'earnings-review'
def audit(name,data):
    lower=data.lower()
    # Scan paths and credential-like strings without embedding operator identity.
    if re.search(rb'/(?:users|home)/[a-z0-9._-]+/',lower) or re.search(rb'(?:ghp_|github_pat_|hf_)[a-zA-Z0-9]{20,}',data):
        raise ValueError('Public identity/credential pattern: '+name)
    if name.endswith(('.zip','.whl')):
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            for m in z.infolist():
                if m.filename.startswith('/') or '..' in Path(m.filename).parts:raise ValueError('Archive path')
                if not m.is_dir():audit(name+':'+m.filename,z.read(m))
files={p.relative_to(SKILL).as_posix():p.read_bytes() for p in sorted(SKILL.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc' and p.name!='manifest.json'}
manifest={'skillVersion':'0.3.0','packageVersion':'0.5.0','publisher':'AhaSignals','files':{k:hashlib.sha256(v).hexdigest() for k,v in files.items()}}
(SKILL/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
files['manifest.json']=(SKILL/'manifest.json').read_bytes()
out=ROOT/'dist';out.mkdir(exist_ok=True);target=out/'earnings-review-skill-0.3.0.zip'
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
    for name,data in files.items():
        audit(name,data);zi=zipfile.ZipInfo('earnings-review/'+name,(2026,11,4,0,0,0));zi.compress_type=zipfile.ZIP_DEFLATED;zi.external_attr=0o100644<<16;z.writestr(zi,data)
audit(target.name,target.read_bytes())
(out/'SHA256SUMS').write_text(hashlib.sha256(target.read_bytes()).hexdigest()+'  '+target.name+'\n')
print('Portable Skill built; expanded archive identity and credential checks passed.')
