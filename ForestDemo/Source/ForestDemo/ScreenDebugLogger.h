#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "ScreenDebugLogger.generated.h"

/** Displays a greeting on screen when play begins. */
UCLASS()
class FORESTDEMO_API AScreenDebugLogger : public AActor
{
    GENERATED_BODY()

public:
    AScreenDebugLogger();

protected:
    virtual void BeginPlay() override;
};
