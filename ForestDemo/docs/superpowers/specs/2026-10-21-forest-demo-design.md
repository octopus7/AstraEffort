# ForestDemo design

Create the project in `D:/github/AstraEffort/ForestDemo` using Unreal Engine 5.7.
Keep exactly one project level: `/Game/Maps/main`, generated from the engine Basic
template `/Engine/Maps/Templates/Template_Default`. Set it as the editor startup
and game default map. Add one native `AScreenDebugLogger` actor to that map.
At BeginPlay it displays green `Hello` for 10 seconds using the engine screen debug
message API, guarding against a missing engine and dedicated server execution.
Disable actor ticking. Include an Unreal `.gitignore` and build instructions.
Verify with an editor build, saved-map inspection, and runtime greeting checks.
