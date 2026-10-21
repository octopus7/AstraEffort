#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "../ScreenDebugLogger.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FScreenDebugLoggerTest,
    "ForestDemo.ScreenDebugLogger.HelloOnBeginPlay",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FScreenDebugLoggerTest::RunTest(const FString& Parameters)
{
    if (!TestNotNull(TEXT("Engine exists"), GEngine))
    {
        return false;
    }

    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false);
    if (!TestNotNull(TEXT("Test world exists"), World))
    {
        return false;
    }
    AScreenDebugLogger* Logger = World->SpawnActor<AScreenDebugLogger>();
    if (TestNotNull(TEXT("Logger spawns"), Logger))
    {
        TestFalse(TEXT("Logger does not tick"), Logger->PrimaryActorTick.bCanEverTick);
        const uint64 MessageKey = Logger->GetUniqueID();
        TestFalse(TEXT("No message before play"), GEngine->OnScreenDebugMessageExists(MessageKey));
        Logger->DispatchBeginPlay();
        TestTrue(TEXT("BeginPlay registers a screen message"), GEngine->OnScreenDebugMessageExists(MessageKey));
        GEngine->RemoveOnScreenDebugMessage(MessageKey);
    }
    World->DestroyWorld(false);
    return !HasAnyErrors();
}

#endif
