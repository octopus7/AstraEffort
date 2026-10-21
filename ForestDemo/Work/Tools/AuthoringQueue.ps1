# Tests use distinct mutexes, queue directories and fake child executables.
function Invoke-AuthoringQueue {
    param([string]$Project,[string]$LogPath,[string]$TimingPath,[string]$EngineExe,
        [string[]]$EngineArguments,[string]$QueueRoot,[string]$MutexName,[string]$GuardToken,[string]$WorkersRoot,[string]$GuardCommandMarker='')
    $ErrorActionPreference='Stop'
    $projectPath=[IO.Path]::GetFullPath($Project).Replace('\','/')
    $theme='Unknown';$effort=$null;$priority=2
    $workersPrefix=[IO.Path]::GetFullPath($WorkersRoot).Replace('\','/').TrimEnd('/')+'/'
    if($projectPath.StartsWith($workersPrefix,[StringComparison]::OrdinalIgnoreCase)){
        $privatePath=$projectPath.Substring($workersPrefix.Length)
        if($privatePath -match '^MountainStation/(medium|high|xhigh|ultra)/.+\.uproject$'){$theme='MountainStation';$effort=$Matches[1].ToLowerInvariant();$priority=if($effort -eq 'medium'){-1}else{1}}
        elseif($privatePath -match '^(medium|high|xhigh|ultra)/.+\.uproject$'){$theme='Forest';$effort=$Matches[1].ToLowerInvariant();$priority=0}
    }
    [IO.Directory]::CreateDirectory($QueueRoot)|Out-Null
    foreach($path in @($TimingPath,$LogPath)){[IO.Directory]::CreateDirectory((Split-Path -Parent ([IO.Path]::GetFullPath($path))))|Out-Null}
    $encoding=[Text.UTF8Encoding]::new($false)
    function Write-State($path,$value){
        $temp=$path+'.tmp';[IO.File]::WriteAllText($temp,($value|ConvertTo-Json -Depth 6),$encoding)
        [IO.File]::Move($temp,$path,$true)
    }
    function Identity($p){return @{pid=$p.Id;start_ticks=$p.StartTime.ToUniversalTime().Ticks.ToString()}}
    function Is-Live($identity){
        if(!$identity){return $false}
        try{$p=[Diagnostics.Process]::GetProcessById([int]$identity.pid)}catch [ArgumentException]{return $false}
        try{return !$p.HasExited -and $p.StartTime.ToUniversalTime().Ticks.ToString() -eq [string]$identity.start_ticks}
        finally{$p.Dispose()}
    }
    function Lock-Queue {try{[void]$queueMutex.WaitOne()}catch [Threading.AbandonedMutexException]{}}
    $owner=Identity ([Diagnostics.Process]::GetCurrentProcess())
    $id=[guid]::NewGuid().ToString('N');$ticketPath=Join-Path $QueueRoot ('ticket-'+$id+'.json')
    $leasePath=Join-Path $QueueRoot 'active.json';$sequencePath=Join-Path $QueueRoot 'sequence.json'
    $queueMutex=[Threading.Mutex]::new($false,$MutexName+'_Queue');$engineMutex=[Threading.Mutex]::new($false,$MutexName)
    $acquired=$false;$process=$null;$runStarted=$null;$exitCode=1;$waitStarted=[DateTimeOffset]::UtcNow
    try {
        Lock-Queue
        try {
            $sequence=if(Test-Path -LiteralPath $sequencePath){[long](Get-Content $sequencePath -Raw|ConvertFrom-Json)+1}else{1}
            Write-State $sequencePath $sequence
            Write-State $ticketPath @{id=$id;owner=$owner;sequence=$sequence;priority=$priority;theme=$theme;effort=$effort;project=$projectPath}
        }finally{$queueMutex.ReleaseMutex()}
        Write-Host "Waiting for Unreal slot ($theme/$effort; Station medium first, then Forest, other Station, unknown; FIFO within priority)."
        while(!$process){
            Lock-Queue
            try {
                $tickets=@(foreach($file in Get-ChildItem -LiteralPath $QueueRoot -Filter 'ticket-*.json'){
                    $ticket=Get-Content -LiteralPath $file.FullName -Raw|ConvertFrom-Json
                    if(Is-Live $ticket.owner){$ticket}else{Remove-Item -LiteralPath $file.FullName}
                })
                $head=$tickets|Sort-Object priority,sequence|Select-Object -First 1
                $lease=if(Test-Path -LiteralPath $leasePath){Get-Content -LiteralPath $leasePath -Raw|ConvertFrom-Json}else{$null}
                $engineAlive=$lease -and (Is-Live $lease.engine)
                if($head.id -eq $id -and !$engineAlive){
                    try{$acquired=$engineMutex.WaitOne(0)}catch [Threading.AbandonedMutexException]{$acquired=$true}
                    if($acquired){
                        # Covers a launcher crash between process spawn and writing its PID, including old runners.
                        $exeName=[IO.Path]::GetFileName($EngineExe).Replace("'","''")
                        $orphans=@(Get-CimInstance Win32_Process -Filter "Name = '$exeName'" | Where-Object {
                            # Normalize duplicated separators in older launchers' command lines too.
                            (!$_.CommandLine) -or (
                                ($_.CommandLine -replace '[\\/]+','/').Contains(($GuardToken -replace '[\\/]+','/'),[StringComparison]::OrdinalIgnoreCase) -and
                                (!$GuardCommandMarker -or $_.CommandLine.Contains($GuardCommandMarker,[StringComparison]::OrdinalIgnoreCase))
                            )
                        })
                        if($orphans.Count){$engineMutex.ReleaseMutex();$acquired=$false}
                        else {
                            Write-State $leasePath @{ticket_id=$id;owner=$owner;engine=$null;project=$projectPath}
                            $info=[Diagnostics.ProcessStartInfo]::new($EngineExe)
                            $info.WorkingDirectory=Split-Path -Parent ([IO.Path]::GetFullPath($Project));$info.UseShellExecute=$false
                            $info.CreateNoWindow=$true;$info.WindowStyle='Hidden';$info.RedirectStandardOutput=$true;$info.RedirectStandardError=$true
                            foreach($arg in $EngineArguments){$info.ArgumentList.Add($arg)}
                            $process=[Diagnostics.Process]::Start($info);$runStarted=[DateTimeOffset]$process.StartTime.ToUniversalTime()
                            Write-State $leasePath @{ticket_id=$id;owner=$owner;engine=(Identity $process);project=$projectPath}
                            Remove-Item -LiteralPath $ticketPath
                        }
                    }
                }
            }finally{$queueMutex.ReleaseMutex()}
            if(!$process){Start-Sleep -Milliseconds 200}
        }
        $stdoutTask=$process.StandardOutput.ReadToEndAsync();$stderrTask=$process.StandardError.ReadToEndAsync()
        $process.WaitForExit();$stdoutText=$stdoutTask.GetAwaiter().GetResult();$stderrText=$stderrTask.GetAwaiter().GetResult();$exitCode=$process.ExitCode
        if($exitCode -ne 0){Write-Host $stdoutText;Write-Host $stderrText}
    } finally {
        $finished=[DateTimeOffset]::UtcNow
        try {
            Lock-Queue
            try {
                if(Test-Path -LiteralPath $ticketPath){Remove-Item -LiteralPath $ticketPath}
                if(Test-Path -LiteralPath $leasePath){
                    $lease=Get-Content -LiteralPath $leasePath -Raw|ConvertFrom-Json
                    if($lease.ticket_id -eq $id -and !(Is-Live $lease.engine)){Remove-Item -LiteralPath $leasePath}
                }
            }finally{$queueMutex.ReleaseMutex()}
        } finally {
            if($acquired){$engineMutex.ReleaseMutex()}
            $engineMutex.Dispose();$queueMutex.Dispose();if($process){$process.Dispose()}
        }
        $timing=[ordered]@{
            wait_started_at_utc=$waitStarted.ToString('o');run_started_at_utc=$(if($runStarted){$runStarted.ToString('o')}else{$null})
            finished_at_utc=$finished.ToString('o');wait_seconds=$(if($runStarted){($runStarted-$waitStarted).TotalSeconds}else{($finished-$waitStarted).TotalSeconds})
            execution_seconds=$(if($runStarted){($finished-$runStarted).TotalSeconds}else{0});exit_code=$exitCode;project=$Project;log=$LogPath
            queue_theme=$theme;queue_effort=$effort;queue_priority=$priority
        }
        [IO.File]::WriteAllText([IO.Path]::GetFullPath($TimingPath),($timing|ConvertTo-Json)+"`n",$encoding)
        Write-Host ($timing|ConvertTo-Json -Compress)
    }
    return $exitCode
}
