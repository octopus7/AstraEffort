# ForestDemo

Unreal Engine 5.7 C++ project. Open `ForestDemo.uproject` and press Play.
The single level, `/Game/Maps/main`, is based on the engine's Basic template.
Its `ScreenDebugLogger` actor displays a green `Hello` for 10 seconds at BeginPlay.
Screen debug messages are intended for development, not Shipping builds.

Build with Visual Studio 2022 C++ tools and the Windows SDK:

```powershell
& 'C:/Program Files/Epic Games/UE_5.7/Engine/Build/BatchFiles/Build.bat' ForestDemoEditor Win64 Development "${PWD}/ForestDemo.uproject" -WaitMutex
```

`Scripts/create_main.py` documents how the level was generated. It refuses to
overwrite an existing level. Binaries, caches, IDE files, and local editor state
are excluded by `.gitignore`; source, configuration, and Content are tracked.

Validation performed with UE 5.7:
- Development Editor build succeeded.
- `Scripts/verify_main.py` reloaded the saved map and verified that it is the
  only project map, with Basic template actors and exactly one logger.
- `ForestDemo.ScreenDebugLogger.HelloOnBeginPlay` automation test passed,
  verifying that BeginPlay registers an engine screen message and ticking is off.

The automation test runs without rendering; visual placement was not checked.
If building in a restricted environment, `-NoUBA -NoUBALocal` disables the build
accelerator. Keep temporary paths stable across builds; UBT caches its environment.
