param(
    [string[]]$Languages = @("en", "fr", "de", "ja", "vi", "ko", "ar"),
    [string]$Pipeline = "integrated_chinese",
    [switch]$ForceSlides,
    [switch]$ForceNarration
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$contentBuilderDir = Resolve-Path (Join-Path $scriptDir "..")
$projectRoot = Resolve-Path (Join-Path $contentBuilderDir "..\..")
$renderScript = Join-Path $contentBuilderDir "render_narration.py"
$artifactRoot = Join-Path $contentBuilderDir "artifacts\$Pipeline"

function Invoke-Stage2ForLanguage {
    param([string]$Lang)

    $jsonDir = Join-Path $artifactRoot "output_json\$Lang"
    if (-not (Test-Path $jsonDir)) {
        throw "Missing output JSON directory for language '$Lang': $jsonDir"
    }

    $jsonCount = (Get-ChildItem -Path $jsonDir -Filter "*_data*.json" -File | Measure-Object).Count
    if ($jsonCount -eq 0) {
        throw "No lesson JSON files found for language '$Lang' in: $jsonDir"
    }

    $args = @(
        $renderScript,
        $jsonDir,
        "--pipeline", $Pipeline,
        "--lang", $Lang
    )

    if ($ForceSlides) {
        $args += "--force-slides"
    }
    if ($ForceNarration) {
        $args += "--force-narration"
    }

    Write-Host ""
    Write-Host "============================================================"
    Write-Host "Stage 2 start: $Pipeline / $Lang ($jsonCount lesson JSON files)"
    Write-Host "============================================================"
    Write-Host "python $($args -join ' ')"
    Write-Host ""

    & python @args
    if ($LASTEXITCODE -ne 0) {
        throw "Stage 2 failed for language '$Lang' with exit code $LASTEXITCODE."
    }

    Write-Host ""
    Write-Host "Stage 2 complete: $Pipeline / $Lang"
}

Push-Location $projectRoot
try {
    Write-Host "Sequential Stage 2 language run"
    Write-Host "Pipeline: $Pipeline"
    Write-Host "Languages: $($Languages -join ' -> ')"
    Write-Host "ForceSlides: $ForceSlides"
    Write-Host "ForceNarration: $ForceNarration"

    foreach ($lang in $Languages) {
        Invoke-Stage2ForLanguage -Lang $lang
    }

    Write-Host ""
    Write-Host "All requested Stage 2 language runs completed successfully."
}
finally {
    Pop-Location
}
