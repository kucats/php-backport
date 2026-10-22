<?php
/* Synthetic lab only. No legacy code, credentials, or production callbacks. */
if (!function_exists('http_response_code')) {
    function http_response_code($code = null) {
        static $status = 200;
        $previous = $status;
        if ($code !== null) {
            $status = (int)$code;
            header('HTTP/1.1 '.$status.' Fixture');
        }
        return $previous;
    }
}
$state = '/lab/state';
$case = isset($_GET['case']) ? $_GET['case'] : 'health';
header('Content-Type: application/json');
switch ($case) {
case 'health':
    echo json_encode(array('pid'=>getmypid(), 'version'=>PHP_VERSION,
        'sapi'=>PHP_SAPI, 'part_limit'=>ini_get('max_multipart_body_parts')));
    break;
case 'upload':
    $files = array();
    foreach ($_FILES as $key=>$file) {
        $entry=array('error'=>$file['error'], 'size'=>$file['size'], 'name'=>$file['name']);
        if ($file['error']===UPLOAD_ERR_OK) {
            $entry['sha256']=hash_file('sha256',$file['tmp_name']);
            $entry['is_uploaded']=is_uploaded_file($file['tmp_name']);
            $entry['moved']=move_uploaded_file($file['tmp_name'], $state.'/object.bin');
        }
        $files[$key]=$entry;
    }
    echo json_encode(array('pid'=>getmypid(), 'post_count'=>count($_POST),
        'post'=>$_POST, 'files'=>$files, 'peak'=>memory_get_peak_usage(true)));
    break;
case 'session':
    session_start();
    if (!isset($_SESSION['count'])) $_SESSION['count']=0;
    $_SESSION['count']++;
    echo json_encode(array('count'=>$_SESSION['count'], 'pid'=>getmypid()));
    break;
case 'download':
    $path=$state.'/object.bin';
    if (!is_file($path)) { http_response_code(404); exit; }
    $size=filesize($path); $start=0; $end=$size-1;
    if (isset($_SERVER['HTTP_RANGE']) && preg_match('/^bytes=(\d+)-(\d*)$/',$_SERVER['HTTP_RANGE'],$m)) {
        $start=(int)$m[1]; if ($m[2]!=='') $end=min($end,(int)$m[2]);
        if ($start>$end || $start>=$size) { http_response_code(416); exit; }
        http_response_code(206);
        header('Content-Range: bytes '.$start.'-'.$end.'/'.$size);
    }
    header('Content-Type: application/octet-stream');
    header('Content-Length: '.($end-$start+1));
    $f=fopen($path,'rb'); fseek($f,$start);
    for($left=$end-$start+1;$left>0;$left-=strlen($chunk)) {
        $chunk=fread($f,min($left,65536)); if ($chunk==='') break; echo $chunk;
    }
    fclose($f);
    break;
case 'delete':
    echo json_encode(array('deleted'=>is_file($state.'/object.bin') && unlink($state.'/object.bin')));
    break;
case 'sync':
    $f=fopen($state.'/registry.dat','c+'); flock($f,LOCK_EX);
    ftruncate($f,0); fwrite($f,"fixture<>node1<>sha256\n"); fflush($f);
    flock($f,LOCK_UN); fclose($f);
    echo json_encode(array('ok'=>file_get_contents($state.'/registry.dat')==="fixture<>node1<>sha256\n"));
    break;
case 'legacy':
    $a=array('literal'=>'ok');
    $s='abcdef'; $bytes=$s[2];
    echo json_encode(array('offset'=>$bytes, 'crypt'=>crypt('fixture-password','vi'),
        'preg'=>preg_match('/^[a-z]+$/','abc'), 'split'=>explode('<>', 'a<>b'),
        'utf8_bytes'=>strlen("日本語"), 'mb_utf8_chars'=>mb_strlen("日本語", 'UTF-8')));
    break;
case 'oom':
    register_shutdown_function(function() use($state){file_put_contents($state.'/oom-shutdown','called');});
    $x=str_repeat('x',128*1024*1024);
    echo json_encode(array('unexpected'=>strlen($x)));
    break;
case 'fatal':
    set_error_handler(function(){return false;});
    $obj=new stdClass(); $obj->value=array_fill(0,1000,'fixture');
    fixture_missing_function();
    break;
case 'timeout':
    set_time_limit(1);
    while (true) { $n=hash('sha256','fixture'); }
    break;
case 'cleanup-warning':
    class FixtureCleanup {
        function __destruct(){trigger_error('fixture cleanup diagnostic',E_USER_WARNING);}
    }
    set_error_handler(function(){return false;});
    $obj=new FixtureCleanup();
    echo json_encode(array('ok'=>true,'pid'=>getmypid()));
    break;
default:
    http_response_code(404);
    echo '{}';
}
