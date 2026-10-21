param([ValidateSet('Test','Worker','Child')][string]$Mode='Test',[string]$Config)
$ErrorActionPreference='Stop'
if ($Mode -eq 'Child') {
    $c=Get-Content -LiteralPath $Config -Raw | ConvertFrom-Json
    [IO.File]::WriteAllText($c.started,[DateTimeOffset]::UtcNow.ToString('o'))
    while (!(Test-Path -LiteralPath $c.release)) { Start-Sleep -Milliseconds 50 }
    [IO.File]::WriteAllText($c.ended,[DateTimeOffset]::UtcNow.ToString('o'))
    exit 0
}
if (!(Test-Path (Join-Path $PSScriptRoot 'AuthoringQueue.ps1'))) { throw 'Forest-priority queue helper is not implemented.' }
. (Join-Path $PSScriptRoot 'AuthoringQueue.ps1')
if ($Mode -eq 'Worker') {
    $c=Get-Content -LiteralPath $Config -Raw | ConvertFrom-Json
    $exe=if($c.fail_launch){Join-Path $c.root 'nonexistent-test-engine.exe'}else{(Get-Process -Id $PID).Path}
    $result=Invoke-AuthoringQueue -Project $c.project -LogPath $c.log -TimingPath $c.timing -EngineExe $exe -EngineArguments @('-NoProfile','-File',$PSCommandPath,'-Mode','Child','-Config',$Config) -QueueRoot $c.queue -MutexName $c.mutex -GuardToken $c.root -WorkersRoot $c.workers_root -GuardCommandMarker '-Mode Child'
    exit $result
}
$root=Join-Path ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../Saved/Coordination'))) ('Test-'+[guid]::NewGuid().ToString('N'))
[IO.Directory]::CreateDirectory($root) | Out-Null
$mutexName='Local\AstraEffort_UE_TEST_'+[guid]::NewGuid().ToString('N')
$jobs=@{}
function Assert($condition,$message) { if (!$condition) { throw $message } }
function Until([scriptblock]$condition) { $deadline=[DateTime]::UtcNow.AddSeconds(25); while (!(& $condition)) { if([DateTime]::UtcNow -gt $deadline){throw 'Timed out waiting for test condition'}; Start-Sleep -Milliseconds 50 } }
function Start-JobProcess($name,$theme,$failLaunch=$false,$effort='high') {
    $dir=Join-Path $root $name; [IO.Directory]::CreateDirectory($dir) | Out-Null
    $workerPath=if($theme -eq 'Forest'){'Saved/Workers/medium/ForestDemo'}elseif($theme -eq 'MountainStation'){"Saved/Workers/MountainStation/$effort/ForestDemo"}else{'Saved/Workers/Unassigned/ForestDemo'}
    if($name -eq 'F1'){$workerPath='Saved/Workers/xhigh/Project/ForestDemo'}
    $filename=if($name -eq 'F2'){'ArbitraryScratch.uproject'}else{'ForestDemo.uproject'}
    $project=Join-Path $dir ($workerPath+'/'+$filename);[IO.Directory]::CreateDirectory((Split-Path $project))|Out-Null;[IO.File]::WriteAllText($project,'{}')
    $c=[ordered]@{root=$root;workers_root=(Join-Path $dir 'Saved/Workers');project=$project;log="$dir/run.log";timing="$dir/timing.json";queue="$root/queue";mutex=$mutexName;started="$dir/start";ended="$dir/end";release="$dir/release";fail_launch=$failLaunch}
    $file="$dir/config.json"; $c | ConvertTo-Json | Set-Content -LiteralPath $file
    $info=[Diagnostics.ProcessStartInfo]::new((Get-Process -Id $PID).Path);$info.UseShellExecute=$false;$info.CreateNoWindow=$true;$info.WindowStyle='Hidden';$info.RedirectStandardOutput=$true;$info.RedirectStandardError=$true
    foreach($arg in @('-NoProfile','-File',$PSCommandPath,'-Mode','Worker','-Config',$file)){$info.ArgumentList.Add($arg)}
    $p=[Diagnostics.Process]::Start($info);$jobs[$name]=@{process=$p;config=$c;stdout=$p.StandardOutput.ReadToEndAsync();stderr=$p.StandardError.ReadToEndAsync()}
}
function Release-Child($name) {[IO.File]::WriteAllText($jobs[$name].config.release,'go')}
function Wait-Ticket($name) { Until { @(Get-ChildItem "$root/queue" -Filter 'ticket-*.json' -ErrorAction SilentlyContinue | Where-Object { (Get-Content $_.FullName -Raw | ConvertFrom-Json).project -eq $jobs[$name].config.project.Replace('\','/') }).Count -eq 1 } }
try {
    Start-JobProcess 'running' 'MountainStation';Until {Test-Path $jobs.running.config.started}
    foreach($pair in @(@('U1','Unknown','high'),@('M1','MountainStation','high'),@('F1','Forest','high'),@('M2','MountainStation','ultra'),@('F2','Forest','high'),@('P1','MountainStation','medium'),@('P2','MountainStation','medium'))){Start-JobProcess $pair[0] $pair[1] $false $pair[2];Wait-Ticket $pair[0]}
    Assert (!(Test-Path $jobs.F1.config.started) -and !(Test-Path $jobs.P1.config.started)) 'Waiting priority job preempted an active MountainStation child'
    Release-Child 'running';$previous='running'
    $order=@('P1','P2','F1','F2','M1','M2','U1')
    foreach($name in $order) {
        Until { (Test-Path $jobs[$previous].config.ended) -and @($order|Where-Object {(Test-Path $jobs[$_].config.started) -and !(Test-Path $jobs[$_].config.ended)}).Count -gt 0 }
        Assert (Test-Path $jobs[$name].config.started) "Priority/FIFO violation: expected $name next"
        Assert (Test-Path $jobs[$previous].config.ended) 'Child executions overlapped'
        foreach($later in $order | Where-Object {$_ -ne $name -and !(Test-Path $jobs[$_].config.ended)}){Assert (!(Test-Path $jobs[$later].config.started)) "Priority/FIFO violation: $later started before $name finished"}
        Release-Child $name;$previous=$name
    }
    foreach($job in $jobs.Values){Until {$job.process.HasExited};Assert ($job.process.ExitCode -eq 0) ($job.stderr.GetAwaiter().GetResult())}
    $priorityTiming=Get-Content $jobs.P1.config.timing -Raw|ConvertFrom-Json
    Assert ($priorityTiming.queue_priority -eq -1 -and $priorityTiming.queue_effort -eq 'medium') 'Station medium timing metadata is wrong'
    Start-JobProcess 'holder' 'MountainStation';Until {Test-Path $jobs.holder.config.started}
    Start-JobProcess 'cancelled' 'Forest';Wait-Ticket 'cancelled';$jobs.cancelled.process.Kill();$jobs.cancelled.process.WaitForExit()
    Start-JobProcess 'after_cancel' 'MountainStation';Wait-Ticket 'after_cancel';Release-Child 'holder'
    Until {Test-Path $jobs.after_cancel.config.started};Release-Child 'after_cancel';Until {$jobs.after_cancel.process.HasExited}
    Assert ($jobs.after_cancel.process.ExitCode -eq 0) 'Stale waiting ticket blocked the queue'
    Start-JobProcess 'failed_start' 'Forest' $true;Until {$jobs.failed_start.process.HasExited}
    Assert ($jobs.failed_start.process.ExitCode -ne 0) 'Missing child executable unexpectedly succeeded'
    # Kill only our synthetic launcher while its child remains alive: lease must block admission.
    Start-JobProcess 'orphan' 'MountainStation';Until {Test-Path $jobs.orphan.config.started}
    $jobs.orphan.process.Kill();$jobs.orphan.process.WaitForExit()
    Start-JobProcess 'after_orphan' 'Forest';Wait-Ticket 'after_orphan';Start-Sleep -Milliseconds 600
    Assert (!(Test-Path $jobs.after_orphan.config.started)) 'Live orphan child was overlapped'
    # Simulate the spawn-before-lease crash window. Process discovery must still protect the child.
    $testQueueMutex=[Threading.Mutex]::new($false,$mutexName+'_Queue');[void]$testQueueMutex.WaitOne()
    try{Remove-Item -LiteralPath "$root/queue/active.json"}finally{$testQueueMutex.ReleaseMutex();$testQueueMutex.Dispose()}
    Start-Sleep -Milliseconds 600
    Assert (!(Test-Path $jobs.after_orphan.config.started)) 'Untracked live child was overlapped'
    Release-Child 'orphan';Until {Test-Path $jobs.after_orphan.config.started};Release-Child 'after_orphan';Until {$jobs.after_orphan.process.HasExited}
    Assert ($jobs.after_orphan.process.ExitCode -eq 0) 'Orphan recovery failed'
    Write-Output "PASS: Station medium > Forest > other Station > unknown, FIFO per priority, no preemption/overlap, cancelled-ticket cleanup, failed-start recovery, tracked/untracked orphan guard. Evidence: $root"
} finally {
    foreach($job in $jobs.Values){[IO.File]::WriteAllText($job.config.release,'cleanup')}
}
