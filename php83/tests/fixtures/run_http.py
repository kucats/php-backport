#!/usr/bin/env python3
"""Run only inside an isolated lab container; fixed loopback target, synthetic data."""
import argparse
import hashlib
import http.client
import json
import os
from pathlib import Path
import subprocess
import time

parser=argparse.ArgumentParser()
parser.add_argument('--candidate', action='store_true')
parser.add_argument('--large-mib',type=int,default=0)
parser.add_argument('--output',default='/lab/state/results.json')
args=parser.parse_args()
STATE=Path('/lab/state')
for name in ['sessions','uploads']:
    p=STATE/name;p.mkdir(parents=True,exist_ok=True);os.chown(str(p),48,48);os.chmod(str(p),0o700)
os.chown(str(STATE),48,48)
results=[]

def request(case='health',body=None,headers=None,prefix='',method=None):
    c=http.client.HTTPConnection('127.0.0.1',8080,timeout=30)
    try:
        c.request(method or ('POST' if body is not None else 'GET'),
                  prefix+'/fixture.php?case='+case,body,headers or {})
        r=c.getresponse();data=r.read()
        return r.status,dict(r.getheaders()),data
    finally:c.close()

def value(*a,**kw):
    status,headers,data=request(*a,**kw)
    assert status==200,(status,data[:120])
    return json.loads(data.decode()),headers

def healthy():
    last=None
    for i in range(100):
        try:return value()[0]
        except Exception as e:last=e;time.sleep(.1)
    raise AssertionError('server did not recover: '+str(last))

def multipart(fields=(),files=(),extra_headers=b''):
    boundary=b'FixtureBoundary20261021'
    chunks=[]
    for name,data in fields:
        chunks.extend([b'--'+boundary+b'\r\n',
            b'Content-Disposition: form-data; name="'+name.encode()+b'"\r\n',
            extra_headers,b'\r\n',data if isinstance(data,bytes) else data.encode(),b'\r\n'])
    for name,filename,data in files:
        chunks.extend([b'--'+boundary+b'\r\n',
            b'Content-Disposition: form-data; name="'+name.encode()+b'"; filename="'+filename.encode()+b'"\r\n',
            b'Content-Type: application/octet-stream\r\n',b'\r\n',data,b'\r\n'])
    chunks.append(b'--'+boundary+b'--\r\n')
    return b''.join(chunks),{'Content-Type':'multipart/form-data; boundary='+boundary.decode()}

def test(name,fn):
    started=time.time()
    try:
        detail=fn();row={'name':name,'pass':True,'detail':detail}
    except Exception as e:
        row={'name':name,'pass':False,'error':str(e)}
    row['seconds']=round(time.time()-started,3)
    results.append(row)
    Path(args.output).write_text(json.dumps({'candidate':args.candidate,'tests':results},indent=2))
    print(json.dumps(row),flush=True)

server=subprocess.Popen(['/usr/sbin/php-fpm','-F','-y','/lab/php-fpm.conf','-c','/lab/php.ini'],stdout=open(str(STATE/'fpm-stdout.log'),'ab'),stderr=subprocess.STDOUT)
web=subprocess.Popen(['/usr/sbin/nginx','-c','/lab/nginx.conf','-g','daemon off;'],stdout=open(str(STATE/'nginx-stdout.log'),'ab'),stderr=subprocess.STDOUT)

try:
    initial=healthy();parent=int((STATE/'php-fpm.pid').read_text().strip())
    test('nginx_fpm_identity',lambda: {'initial':initial,'parent':parent})

    def ordinary_upload():
        data=(b'fixture-object\x00\xff'+bytes(range(256)))*4096
        body,h=multipart([('com','fixture comment'),('dlkey','fixture-key')],[('upfile','fixture.bin',data)])
        x,_=value('upload',body,h)
        f=x['files']['upfile']
        assert f['sha256']==hashlib.sha256(data).hexdigest()
        assert f['moved'] and f['is_uploaded'] and f['size']==len(data)
        assert x['post']['com']=='fixture comment'
        status,_,download=request('download')
        assert status==200 and download==data
        status,headers,partial=request('download',headers={'Range':'bytes=17-117'})
        assert status==206 and partial==data[17:118]
        assert 'Content-Range' in headers
        assert value('delete')[0]['deleted']
        return {'bytes':len(data),'sha256':f['sha256'],'range_bytes':len(partial)}
    test('upload_download_range_delete',ordinary_upload)

    def sessions():
        x,h=value('session')
        cookie=h['Set-Cookie'].split(';',1)[0]
        y,_=value('session',headers={'Cookie':cookie})
        assert x['count']==1 and y['count']==2
        return {'session_persists':True}
    test('ordinary_sessions',sessions)

    def legacy():
        x,_=value('legacy')
        assert x['offset']=='c' and x['preg']==1 and x['split']==['a','b']
        assert x['utf8_bytes']==9 and x['mb_utf8_chars']==3 and len(x['crypt'])==13
        return x
    test('legacy_language_and_crypt',legacy)
    test('synthetic_sync_file_contract',lambda:value('sync')[0])

    def progress():
        sid='fixtureprogress20261021'
        path=STATE/'sessions'/('sess_'+sid)
        if path.exists():path.unlink()
        body,h=multipart([('PHP_SESSION_UPLOAD_PROGRESS','fixture')],[('upfile','fixture.bin',b'fixture')])
        h['Cookie']='PHPSESSID='+sid
        x,_=value('upload',body,h)
        present=path.exists() and b'upload_progress_' in path.read_bytes()
        assert present== (True),('progress present',present)
        return {'progress_state_created':present,'ordinary_upload_ok':x['files']['upfile']['moved']}
    test('upload_progress_early_session_path',progress)

    def part_limit():
        body,h=multipart([('field'+str(i),'v') for i in range(12)])
        x,_=value('upload',body,h,prefix='/parts')
        assert x['post_count']==8,x['post_count']
        return {'accepted_fields':x['post_count']}
    test('multipart_total_part_limit',part_limit)

    def empty_controls():
        body,h=multipart(files=[('empty'+str(i),'',b'') for i in range(1500)])
        x,_=value('upload',body,h)
        expected=1020
        assert len(x['files'])==expected,(len(x['files']),expected)
        return {'empty_file_controls_registered':len(x['files'])}
    test('empty_file_controls_count_toward_total',empty_controls)

    def empty_controls_limited():
        body,h=multipart(files=[('empty'+str(i),'',b'') for i in range(30)])
        x,_=value('upload',body,h,prefix='/parts')
        expected=8
        assert len(x['files'])==expected,(len(x['files']),expected)
        return {'empty_file_controls_registered':len(x['files'])}
    test('explicit_part_limit_includes_empty_file_controls',empty_controls_limited)

    def headers_stress():
        extra=b''.join(('X-Fixture-%06d: abcdefghijklmnop\r\n'%i).encode() for i in range(250000))
        body,h=multipart([('com','ok')],extra_headers=extra)
        try:
            x,_=value('upload',body,h)
            succeeded=x['post'].get('com')=='ok'
            peak=x['peak']
        except Exception:
            succeeded=False;peak=None
        assert succeeded==args.candidate,('request_success',succeeded)
        healthy()
        return {'request_bytes':len(body),'request_success':succeeded,'peak':peak}
    test('bounded_unknown_multipart_header_memory',headers_stress)

    def duplicate_headers():
        body,h=multipart([('com','ok')],extra_headers=b'Content-Type: text/plain\r\n'*250000)
        try:
            x,_=value('upload',body,h)
            succeeded=x['post'].get('com')=='ok'
            peak=x['peak']
        except Exception:
            succeeded=False;peak=None
        assert succeeded==args.candidate,('request_success',succeeded)
        healthy()
        return {'request_bytes':len(body),'request_success':succeeded,'peak':peak}
    test('bounded_duplicate_multipart_header_memory',duplicate_headers)

    def nested_input():
        body,h=multipart([('tree[a][b][c]','ok'),('deep'+'[a]'*70,'rejected')])
        x,_=value('upload',body,h)
        assert x['post']['tree']['a']['b']['c']=='ok'
        assert 'deep' not in x['post']
        return {'normal_nesting_preserved':True,'excessive_nesting_rejected':True}
    test('nested_input_and_existing_depth_limit',nested_input)

    def startup_oom():
        before=healthy()['pid']
        body,h=multipart([('large_field',b'x'*(32*1024*1024))])
        try:request('upload',body,h)
        except Exception:pass
        after=healthy()['pid']
        assert server.poll() is None
        return {'worker_replaced':before!=after,'parent_alive':True,'field_bytes':32*1024*1024}
    test('multipart_startup_oom_before_application',startup_oom)

    def oom():
        marker=STATE/'oom-shutdown'
        if marker.exists():marker.unlink()
        before=healthy()['pid']
        try:request('oom')
        except Exception:pass
        after=healthy()['pid']
        assert server.poll() is None
        return {'worker_replaced':after!=before,'shutdown_callback_ran':marker.exists(),'parent_alive':True}
    test('application_oom_then_next_request',oom)

    def state_cycles():
        pids=set()
        for i in range(25):
            request('fatal')
            value(prefix='/warn')
            value('cleanup-warning')
            pids.add(healthy()['pid'])
        assert len(pids)==1,pids
        return {'cycles':25,'worker_count':len(pids),'parent_alive':server.poll() is None}
    test('fatal_warning_cleanup_repeated_worker',state_cycles)

    def timeouts():
        before=healthy()['pid'];request('timeout');after=healthy()['pid']
        assert server.poll() is None and before==after
        return {'worker_survived_timeout':True}
    test('execution_timeout_then_next_request',timeouts)

    if args.large_mib:
        def large():
            size=args.large_mib*1024*1024
            boundary='FixtureLarge20261021'
            prefix=('--'+boundary+'\r\nContent-Disposition: form-data; name="upfile"; filename="large.bin"\r\nContent-Type: application/octet-stream\r\n\r\n').encode()
            suffix=('\r\n--'+boundary+'--\r\n').encode()
            c=http.client.HTTPConnection('127.0.0.1',8080,timeout=180)
            c.putrequest('POST','/fixture.php?case=upload')
            c.putheader('Content-Type','multipart/form-data; boundary='+boundary)
            c.putheader('Content-Length',str(len(prefix)+size+len(suffix)))
            c.endheaders();c.send(prefix)
            block=b'fixture-large-body'*65536;left=size;digest=hashlib.sha256()
            while left:
                data=block[:min(left,len(block))];c.send(data);digest.update(data);left-=len(data)
            c.send(suffix);r=c.getresponse();status=r.status;x=json.loads(r.read().decode());c.close()
            assert status==200
            f=x['files']['upfile'];assert f['moved'] and f['size']==size and f['sha256']==digest.hexdigest()
            assert x['peak']<24*1024*1024
            value('delete')
            return {'file_bytes':size,'sha256':f['sha256'],'peak_php_memory':x['peak']}
        test('large_streaming_upload',large)
finally:
    for p in [web,server]:
        p.terminate()
        try:p.wait(timeout=10)
        except subprocess.TimeoutExpired:p.kill();p.wait()

summary={'candidate':args.candidate,'passed':sum(r['pass'] for r in results),'total':len(results),'tests':results}
Path(args.output).write_text(json.dumps(summary,indent=2))
print(json.dumps({'passed':summary['passed'],'total':summary['total']}),flush=True)
raise SystemExit(0 if summary['passed']==summary['total'] else 1)
