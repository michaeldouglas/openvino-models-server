[CmdletBinding()]
param(
    [switch]$RequireModel
)

$ErrorActionPreference = "Stop"
$profilesRoot = $PSScriptRoot
$configPath = Join-Path $profilesRoot "fast\config.json"
$deploymentRoot = Split-Path -Parent $profilesRoot
$modelsRoot = Join-Path (Split-Path -Parent $deploymentRoot) "models"

if (-not (Test-Path -LiteralPath $configPath -PathType Leaf)) {
    throw "Configuração do perfil fast não encontrada: $configPath"
}

$config = Get-Content -Raw -LiteralPath $configPath | ConvertFrom-Json
$graphs = @($config.mediapipe_config_list)
if ($graphs.Count -ne 1 -or $graphs[0].name -ne "qwen3-1.7b") {
    throw "O perfil fast deve conter somente o servable qwen3-1.7b."
}

$modelPath = Join-Path $modelsRoot "OpenVINO\Qwen3-1.7B-int4-ov"
if ($RequireModel -and -not (Test-Path -LiteralPath $modelPath -PathType Container)) {
    throw "O artefato do Qwen3 1.7B não está preparado em $modelPath. Execute runtime/scripts/prepare-models.ps1."
}

[pscustomobject]@{
    profile = "fast"
    models = @($graphs | ForEach-Object { $_.name })
    config = $configPath
    model_prepared = Test-Path -LiteralPath $modelPath -PathType Container
} | ConvertTo-Json -Compress
