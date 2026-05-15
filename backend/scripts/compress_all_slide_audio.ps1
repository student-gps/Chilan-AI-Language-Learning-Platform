$ErrorActionPreference = "Stop"

$RepoDir = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $RepoDir

python backend\scripts\compress_slide_audio.py `
    --langs en fr de es ja ko vi pt ru th it ar id ms `
    --bitrate 40k `
    --sample-rate 24000 `
    --apply
