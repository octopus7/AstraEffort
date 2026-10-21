param([string]$Project,[string]$LogPath,[string]$TimingPath,[string[]]$EditorArguments)
$requested = [int]$EditorArguments[0]
@{exit_code=$requested}|ConvertTo-Json|Set-Content -LiteralPath $TimingPath
exit $requested
