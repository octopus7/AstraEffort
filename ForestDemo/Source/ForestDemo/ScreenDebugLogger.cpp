#include "ScreenDebugLogger.h"
#include "Engine/Engine.h"

AScreenDebugLogger::AScreenDebugLogger()
{
    PrimaryActorTick.bCanEverTick = false;
}

void AScreenDebugLogger::BeginPlay()
{
    Super::BeginPlay();

    if (GEngine && GetNetMode() != NM_DedicatedServer)
    {
        GEngine->AddOnScreenDebugMessage(static_cast<uint64>(GetUniqueID()), 10.0f, FColor::Green, TEXT("Hello"));
    }
}
