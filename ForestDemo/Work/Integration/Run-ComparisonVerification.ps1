param([Parameter(Mandatory)][string]$RequestPath)
$ErrorActionPreference = 'Stop'
$request = Get-Content -LiteralPath $RequestPath -Raw | ConvertFrom-Json
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$prefix = [IO.Path]::GetFullPath((Join-Path $projectRoot 'Saved/Workers/Supervisor')) + [IO.Path]::DirectorySeparatorChar
$private = [IO.Path]::GetFullPath($request.project)
if (!$private.StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase)) { throw 'Refusing a non-supervisor project' }
if (!$request.final_defaults_applied) { throw 'Prepare the final candidate first' }
$evidence = [IO.Path]::GetFullPath($request.evidence)
$expectedEvidence = [IO.Path]::GetFullPath((Join-Path (Split-Path -Parent $private) 'Evidence'))
if ($evidence -ne $expectedEvidence -or [IO.Path]::GetFullPath($request.candidate_manifest) -ne (Join-Path $expectedEvidence 'candidate_snapshot.json')) { throw 'Request evidence/manifest paths do not match its private project' }
if ([IO.Path]::GetFullPath($RequestPath) -ne (Join-Path (Split-Path -Parent $private) 'request.json')) { throw 'Request must belong to the prepared snapshot' }
$helper = Join-Path $PSScriptRoot 'Invoke-QueueCall.ps1'
$script = Join-Path $PSScriptRoot 'verify_all_maps.py'
$project = Join-Path $private 'ForestDemo.uproject'
$pwsh = (Get-Process -Id $PID).Path
$savedEnvironment = $env:FOREST_INTEGRATION_REQUEST
function Invoke-QueuedEditor($name, $arguments) {
    $callPath = Join-Path $evidence ($name+'_invocation.json')
    $call = @{project=$project;log=(Join-Path $evidence ($name+'.log'));timing=(Join-Path $evidence ($name+'_timing.json'));arguments=@($arguments)}
    [IO.File]::WriteAllText($callPath,($call|ConvertTo-Json -Depth 5),[Text.UTF8Encoding]::new($false))
    & $pwsh -NoProfile -File $helper -InvocationJson $callPath
    if ($LASTEXITCODE -ne 0) { throw "$name editor process failed ($LASTEXITCODE)" }
}
try {
    $env:FOREST_INTEGRATION_REQUEST = [IO.Path]::GetFullPath($RequestPath)
    # Separate processes are essential: the shared runner calls exit at completion.
    Invoke-QueuedEditor 'maps' @(('-ExecutePythonScript='+$script),'-RenderOffscreen','-nosound')
    $maps = Get-Content -LiteralPath (Join-Path $evidence 'saved_maps_validation.json') -Raw | ConvertFrom-Json
    if (!$maps.passed) { throw 'Saved-map checks failed; inspect evidence before retrying' }
    $automation = Join-Path $evidence 'Automation'
    Invoke-QueuedEditor 'hello' @('-ExecCmds=Automation RunTests ForestDemo.ScreenDebugLogger.HelloOnBeginPlay','-TestExit=Automation Test Queue Empty',('-ReportExportPath='+$automation),'-RenderOffscreen','-nosound')
    $helloLog = Get-Content -LiteralPath (Join-Path $evidence 'hello.log') -Raw
    if ($helloLog -notmatch 'Test Completed\. Result=\{Success\} Name=\{HelloOnBeginPlay\} Path=\{ForestDemo\.ScreenDebugLogger\.HelloOnBeginPlay\}') { throw 'Exact HelloOnBeginPlay Success marker missing; inspect automation report' }
    $automationReport = Get-Content -LiteralPath (Join-Path $automation 'index.json') -Raw | ConvertFrom-Json
    if (@($automationReport.tests).Count -ne 1 -or $automationReport.tests[0].fullTestPath -ne 'ForestDemo.ScreenDebugLogger.HelloOnBeginPlay' -or $automationReport.tests[0].state -ne 'Success') { throw 'Expected exactly one successful native Hello automation result' }
    $manifest = Get-Content -LiteralPath $request.candidate_manifest -Raw | ConvertFrom-Json
    $changed = @(foreach ($file in $manifest.files) { if ((Get-FileHash -LiteralPath (Join-Path $private $file.path)).Hash -ne $file.sha256) { $file.path } })
    if ($changed.Count) { throw "Candidate changed during verification: $($changed -join ', ')" }
    $report = [ordered]@{baseline_commit=$request.baseline_commit;completed_at_utc=[DateTimeOffset]::UtcNow.ToString('o');saved_maps_passed=$true;native_hello_automation_passed=$true;candidate_hashes_unchanged=$true;map_count=$maps.maps.Count;maps_log_sha256=(Get-FileHash -LiteralPath (Join-Path $evidence 'maps.log')).Hash;hello_log_sha256=(Get-FileHash -LiteralPath (Join-Path $evidence 'hello.log')).Hash;passed=$true}
    [IO.File]::WriteAllText((Join-Path $evidence 'integration_result.json'),($report|ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false))
    $report | ConvertTo-Json
} finally { $env:FOREST_INTEGRATION_REQUEST = $savedEnvironment }
