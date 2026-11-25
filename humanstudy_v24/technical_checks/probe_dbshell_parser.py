"""Exercise just the original dbshell argument parser in each preserved source tree."""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPERIMENT = ROOT.parent / 'ICSE2027_6658_RegressionAudit_20261105_v11/experiment'
TARGET = EXPERIMENT / 'sources/django__django-15851'
DEPENDENCIES = EXPERIMENT / 'runtime_dependencies'
PROBE = '''
import contextlib, hashlib, io, json, sys
from pathlib import Path
sys.path[:0] = [sys.argv[1], sys.argv[2]]
from django.core.management.commands import dbshell
if sys.argv[3] == 'inject_import_in_process':
    import argparse
    dbshell.argparse = argparse
result = {'source': str(Path(dbshell.__file__).resolve()), 'sha256': hashlib.sha256(Path(dbshell.__file__).read_bytes()).hexdigest()}
try:
    with contextlib.redirect_stderr(io.StringIO()):
        parser = dbshell.Command().create_parser('manage.py','dbshell')
        args = parser.parse_args(['--','--help'])
except (Exception, SystemExit) as error:
    result.update(status='exception', exception=type(error).__name__, message=str(error))
else:
    result.update(status='returned', parameters=args.parameters)
print(json.dumps(result))
'''

def main():
    results = {}
    for variant, mode in [('base','original'),('candidate','original'),('developer','original'),('candidate','inject_import_in_process')]:
        package = TARGET / variant
        expected = package / 'django/core/management/commands/dbshell.py'
        run = subprocess.run([sys.executable,'-I','-B','-c',PROBE,str(package),str(DEPENDENCIES),mode],
                             cwd=ROOT, capture_output=True,text=True,timeout=20,check=True)
        result = json.loads(run.stdout)
        assert Path(result['source']) == expected
        assert result['sha256'] == hashlib.sha256(expected.read_bytes()).hexdigest()
        results[variant if mode=='original' else 'candidate_import_diagnostic'] = result
    assert results['base']['status']=='returned' and results['developer']['status']=='returned'
    assert results['candidate']['exception']=='NameError' and "'argparse'" in results['candidate']['message']
    assert results['candidate_import_diagnostic']['status']=='returned'
    evidence = {'issue':'django__django-15851','probe':'Command.create_parser and parse_args only',
                'variants':results,'original_result_files_modified':False,'dbshell_or_database_started':False,
                'limit':'The injected-import variant is diagnostic. It does not test the backend argument order.'}
    with (ROOT/'dbshell_parser_probe.json').open('x',encoding='utf-8') as output:
        json.dump(evidence,output,ensure_ascii=False,indent=2);output.write('\n')
    print(json.dumps({k:(v['status'],v.get('exception'),v.get('parameters')) for k,v in results.items()},ensure_ascii=False))

if __name__=='__main__':main()
