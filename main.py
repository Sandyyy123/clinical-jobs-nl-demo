"""Run: python main.py --input fixtures.json --output output --dry-run"""
import argparse
import json
import os
from pathlib import Path
import tempfile
from clinical_jobs import process, render, csv_export


def atomic_write(path, content):
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix='.pending-')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f: f.write(content)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,default=Path(__file__).with_name('fixtures.json'))
    p.add_argument('--output',type=Path,default=Path('output'))
    p.add_argument('--dry-run',action='store_true',help='Validate/process fixtures without writing outputs')
    a=p.parse_args();result=process(json.loads(a.input.read_text()))
    if not a.dry_run:
        a.output.mkdir(parents=True,exist_ok=True)
        for name, content in [('jobs.json',json.dumps(result,indent=2)),('jobs.csv',csv_export(result['jobs'])),('report.html',render(result))]:
            atomic_write(a.output/name,content)
    print(json.dumps({'input_count':result['input_count'],'matching':len(result['jobs']),'excluded':len(result['excluded']),'dry_run':a.dry_run}))

if __name__=='__main__':main()
