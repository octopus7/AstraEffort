# ForestDemo Implementation Plan

> Execute inline using the native tools in this session.

**Goal:** Create the requested minimal UE 5.7 project under ForestDemo.
**Architecture:** One runtime module and one actor placed in a Basic template map.
**Tech Stack:** Unreal Engine 5.7, C++, Unreal editor Python.
**Spec:** ../specs/2026-10-21-forest-demo-design.md

## Global Constraints
- Project folder and project name: ForestDemo.
- Only project map: /Game/Maps/main.
- Greeting: Hello, green, 10 seconds at BeginPlay.

## Implementation and verification
- [x] Create project descriptor, targets, module, configuration and .gitignore.
- [x] Implement AScreenDebugLogger::BeginPlay and disable ticking.
- [x] Build ForestDemoEditor Win64 Development with the installed UE 5.7.
- [x] Generate main from Template_Default and save one ScreenDebugLogger actor.
- [x] Reload main and verify its actors and single-map inventory.
- [x] Verify runtime Hello and review generated-file exclusions.

## Review Focus
- Startup map resolves after a clean editor launch.
- Saved map references the native class successfully.
- Template floor, lighting and PlayerStart remain present.
- BeginPlay produces the screen message, with no tick required.
- Generated build products stay ignored; the map remains trackable.
