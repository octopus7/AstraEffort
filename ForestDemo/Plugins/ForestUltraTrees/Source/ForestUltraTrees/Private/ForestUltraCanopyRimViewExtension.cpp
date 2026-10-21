#include "ForestUltraCanopyRimViewExtension.h"
#include "ForestUltraCanopyRimSubsystem.h"
#include "GlobalShader.h"
#include "ShaderParameterStruct.h"
#include "RenderGraphUtils.h"
#include "PostProcess/PostProcessMaterialInputs.h"
#include "SceneTexturesConfig.h"
#include "RenderingThread.h"

static TAutoConsoleVariable<int32> CVarCanopyRim(TEXT("r.ForestUltra.CanopyRim"), 1,
    TEXT("Shared canopy silhouette paint. 0 disables the screen passes."), ECVF_RenderThreadSafe);
static TAutoConsoleVariable<int32> CVarCanopyRimGap(TEXT("r.ForestUltra.CanopyRim.GapRadius"), 3,
    TEXT("Closing radius in quarter-resolution texels (0-8). Suppresses small internal leaf gaps."), ECVF_RenderThreadSafe);
static TAutoConsoleVariable<int32> CVarCanopyRimDebug(TEXT("r.ForestUltra.CanopyRim.Debug"), 0,
    TEXT("0 normal, 1 visible stencil IDs, 2 closed quarter-resolution mask, 3 rim weight."), ECVF_RenderThreadSafe);

class FForestUltraCanopyMaskCS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FForestUltraCanopyMaskCS);
    SHADER_USE_PARAMETER_STRUCT(FForestUltraCanopyMaskCS, FGlobalShader);
    class FStage : SHADER_PERMUTATION_INT("MASK_STAGE", 5);
    using FPermutationDomain = TShaderPermutationDomain<FStage>;
    BEGIN_SHADER_PARAMETER_STRUCT(FParameters, )
        SHADER_PARAMETER_STRUCT_REF(FViewUniformShaderParameters, View)
        SHADER_PARAMETER(FIntPoint, MaskSize)
        SHADER_PARAMETER(FIntPoint, SourceMin)
        SHADER_PARAMETER(FIntPoint, SourceSize)
        SHADER_PARAMETER(int32, Radius)
        SHADER_PARAMETER(int32, Jump)
        SHADER_PARAMETER_RDG_TEXTURE(Texture2D, CustomDepth)
        SHADER_PARAMETER_RDG_TEXTURE_SRV(Texture2D<uint2>, Stencil)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>, Styles)
        SHADER_PARAMETER_RDG_TEXTURE(Texture2D<float4>, MaskInput)
        SHADER_PARAMETER_RDG_TEXTURE(Texture2D<float4>, ClosedMask)
        SHADER_PARAMETER_RDG_TEXTURE_UAV(RWTexture2D<float4>, MaskOutput)
    END_SHADER_PARAMETER_STRUCT()
    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& Parameters)
    { return IsFeatureLevelSupported(Parameters.Platform, ERHIFeatureLevel::SM5); }
};
IMPLEMENT_GLOBAL_SHADER(FForestUltraCanopyMaskCS, "/ForestUltraCanopyRim/CanopyRim.usf", "MaskCS", SF_Compute);

class FForestUltraCanopyCompositePS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FForestUltraCanopyCompositePS);
    SHADER_USE_PARAMETER_STRUCT(FForestUltraCanopyCompositePS, FGlobalShader);
    BEGIN_SHADER_PARAMETER_STRUCT(FParameters, )
        SHADER_PARAMETER_STRUCT_REF(FViewUniformShaderParameters, View)
        SHADER_PARAMETER(FIntPoint, MaskSize)
        SHADER_PARAMETER(FIntPoint, SourceMin)
        SHADER_PARAMETER(FIntPoint, SourceSize)
        SHADER_PARAMETER(int32, DebugMode)
        SHADER_PARAMETER_RDG_TEXTURE(Texture2D, CustomDepth)
        SHADER_PARAMETER_RDG_TEXTURE(Texture2D, SceneDepth)
        SHADER_PARAMETER_RDG_TEXTURE_SRV(Texture2D<uint2>, Stencil)
        SHADER_PARAMETER_RDG_TEXTURE(Texture2D, SceneColor)
        SHADER_PARAMETER_RDG_TEXTURE(Texture2D<float4>, ClosedMask)
        SHADER_PARAMETER_RDG_TEXTURE(Texture2D<float4>, Seeds)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>, Styles)
        RENDER_TARGET_BINDING_SLOTS()
    END_SHADER_PARAMETER_STRUCT()
    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& Parameters)
    { return IsFeatureLevelSupported(Parameters.Platform, ERHIFeatureLevel::SM5); }
};
IMPLEMENT_GLOBAL_SHADER(FForestUltraCanopyCompositePS, "/ForestUltraCanopyRim/CanopyRim.usf", "CompositePS", SF_Pixel);

void FForestUltraCanopyRimViewExtension::SetStyles(TArray<FVector4f> InStyles)
{
    auto Self = StaticCastSharedRef<FForestUltraCanopyRimViewExtension>(AsShared());
    ENQUEUE_RENDER_COMMAND(CanopyRimStyles)([Self, Data = MoveTemp(InStyles)](FRHICommandListImmediate&) mutable
    { Self->Styles = MoveTemp(Data); });
}

void FForestUltraCanopyRimViewExtension::SubscribeToPostProcessingPass(EPostProcessingPass Pass, const FSceneView& View,
    FPostProcessingPassDelegateArray& Callbacks, bool)
{
    // Before temporal upscaling/DOF: scene depth, stencil and color use the same jittered pixel grid.
    if (Pass == EPostProcessingPass::BeforeDOF && View.GetFeatureLevel() >= ERHIFeatureLevel::SM5 &&
        CVarCanopyRim.GetValueOnRenderThread() && Styles.ContainsByPredicate([](FVector4f S){ return S.W > 0; }))
        Callbacks.Add(FPostProcessingPassDelegate::CreateRaw(this, &FForestUltraCanopyRimViewExtension::Render));
}

FScreenPassTexture FForestUltraCanopyRimViewExtension::Render(FRDGBuilder& Graph, const FSceneView& View, const FPostProcessMaterialInputs& Inputs)
{
    if (!Inputs.SceneTextures.SceneTextures) return Inputs.ReturnUntouchedSceneColorForPostProcessing(Graph);
    const auto* Scene = Inputs.SceneTextures.SceneTextures->GetContents();
    if (!Scene->CustomDepthTexture || !Scene->CustomStencilTexture || !Scene->SceneDepthTexture)
        return Inputs.ReturnUntouchedSceneColorForPostProcessing(Graph);
    RDG_EVENT_SCOPE(Graph, "CanopyRim QuarterResolution");
    const FScreenPassTexture Color = FScreenPassTexture::CopyFromSlice(Graph, Inputs.GetInput(EPostProcessMaterialInput::SceneColor));
    const FIntPoint Size = UForestUltraCanopyRimSubsystem::MaskExtent(Color.ViewRect.Size());
    const int32 Radius = FMath::Clamp(CVarCanopyRimGap.GetValueOnRenderThread(), 0, 8);
    auto* Palette = Graph.CreateSRV(CreateStructuredBuffer(Graph, TEXT("CanopyRim.Styles"), Styles));
    const auto Desc = FRDGTextureDesc::Create2D(Size, PF_FloatRGBA, FClearValueBinding::None, TexCreate_ShaderResource | TexCreate_UAV);
    auto MakeTexture = [&](const TCHAR* Name) { return Graph.CreateTexture(Desc, Name); };
    auto Dispatch = [&](int32 Stage, FRDGTextureRef Input, FRDGTextureRef Closed, FRDGTextureRef Output, int32 Jump)
    {
        auto* P = Graph.AllocParameters<FForestUltraCanopyMaskCS::FParameters>();
        P->View = View.ViewUniformBuffer;
        P->MaskSize = Size; P->SourceMin = Color.ViewRect.Min; P->SourceSize = Color.ViewRect.Size();
        P->Radius = Radius; P->Jump = Jump;
        P->CustomDepth = Scene->CustomDepthTexture; P->Stencil = Scene->CustomStencilTexture;
        P->Styles = Palette; P->MaskInput = Input; P->ClosedMask = Closed; P->MaskOutput = Graph.CreateUAV(Output);
        FForestUltraCanopyMaskCS::FPermutationDomain Permutation; Permutation.Set<FForestUltraCanopyMaskCS::FStage>(Stage);
        TShaderMapRef<FForestUltraCanopyMaskCS> Shader(GetGlobalShaderMap(View.GetFeatureLevel()), Permutation);
        FComputeShaderUtils::AddPass(Graph, RDG_EVENT_NAME("CanopyRim Mask stage=%d jump=%d %dx%d", Stage, Jump, Size.X, Size.Y),
            Shader, P, FComputeShaderUtils::GetGroupCount(Size, FIntPoint(8,8)));
    };
    auto* Mask = MakeTexture(TEXT("CanopyRim.Mask"));
    Dispatch(0, nullptr, nullptr, Mask, 0);
    FRDGTextureRef Closed = Mask;
    if (Radius > 0)
    {
        auto* Dilated = MakeTexture(TEXT("CanopyRim.Dilate"));
        Closed = MakeTexture(TEXT("CanopyRim.Close"));
        Dispatch(1, Mask, nullptr, Dilated, 0);
        Dispatch(2, Dilated, Mask, Closed, 0);
    }
    FRDGTextureRef Seeds = MakeTexture(TEXT("CanopyRim.Boundary"));
    Dispatch(3, Closed, nullptr, Seeds, 0);
    // Width is limited to 128 source pixels = 32 mask texels; no full-screen distance field is needed.
    for (int32 Jump = 32; Jump >= 1; Jump /= 2)
    {
        auto* Next = MakeTexture(TEXT("CanopyRim.Distance"));
        Dispatch(4, Seeds, Closed, Next, Jump);
        Seeds = Next;
    }
    FScreenPassRenderTarget Output = Inputs.OverrideOutput;
    if (!Output.IsValid()) Output = FScreenPassRenderTarget::CreateFromInput(Graph, Color, View.GetOverwriteLoadAction(), TEXT("CanopyRim.Color"));
    auto* P = Graph.AllocParameters<FForestUltraCanopyCompositePS::FParameters>();
    P->View = View.ViewUniformBuffer; P->MaskSize = Size;
    P->SourceMin = Color.ViewRect.Min; P->SourceSize = Color.ViewRect.Size();
    P->DebugMode = CVarCanopyRimDebug.GetValueOnRenderThread();
    P->CustomDepth = Scene->CustomDepthTexture; P->SceneDepth = Scene->SceneDepthTexture; P->Stencil = Scene->CustomStencilTexture;
    P->SceneColor = Color.Texture; P->ClosedMask = Closed; P->Seeds = Seeds; P->Styles = Palette;
    P->RenderTargets[0] = Output.GetRenderTargetBinding();
    TShaderMapRef<FForestUltraCanopyCompositePS> Shader(GetGlobalShaderMap(View.GetFeatureLevel()));
    AddDrawScreenPass(Graph, RDG_EVENT_NAME("CanopyRim Composite"), View,
        FScreenPassTextureViewport(Output), FScreenPassTextureViewport(Color), Shader, P);
    return Output;
}
