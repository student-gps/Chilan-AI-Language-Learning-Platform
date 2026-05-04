param(
    [string]$Pipeline = "integrated_chinese"
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$contentBuilderDir = Resolve-Path (Join-Path $scriptDir "..")
$projectRoot = Resolve-Path (Join-Path $contentBuilderDir "..\..")
$localizeScript = Join-Path $contentBuilderDir "localize.py"
$stage2Script = Join-Path $contentBuilderDir "render_narration.py"
$artifactRoot = Join-Path $contentBuilderDir "artifacts\$Pipeline"
$languages = @("ja", "vi")

function Invoke-Step {
    param(
        [string]$Name,
        [string[]]$CommandArgs
    )

    Write-Host ""
    Write-Host "============================================================"
    Write-Host $Name
    Write-Host "============================================================"
    Write-Host "python $($CommandArgs -join ' ')"
    Write-Host ""

    & python @CommandArgs
    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed with exit code $LASTEXITCODE."
    }
}

Push-Location $projectRoot
try {
    Write-Host "Sequential localize + full Stage2 run"
    Write-Host "Pipeline: $Pipeline"
    Write-Host "Languages: $($languages -join ' -> ')"

    foreach ($lang in $languages) {
        Invoke-Step `
            -Name "Localize $lang" `
            -CommandArgs @($localizeScript, "--pipeline", $Pipeline, "--lang", $lang, "--force")

        $jsonDir = Join-Path $artifactRoot "output_json\$lang"
        if (-not (Test-Path $jsonDir)) {
            throw "Missing localized JSON directory for '$lang': $jsonDir"
        }

        Invoke-Step `
            -Name "Full Stage2 $lang (TTS + slides)" `
            -CommandArgs @($stage2Script, $jsonDir, "--pipeline", $Pipeline, "--lang", $lang, "--force-narration", "--force-slides")
    }

    Write-Host ""
    Write-Host "ja -> vi localize + full Stage2 completed successfully."
}
finally {
    Pop-Location
}
