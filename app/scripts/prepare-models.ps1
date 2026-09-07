[CmdletBinding()]
param(
    [string]$Image = "openvino/model_server:2026.3.1-gpu",
    [switch]$SkipDownload
)

$ErrorActionPreference = "Stop"
$appRoot = Split-Path -Parent $PSScriptRoot
$modelsRoot = Join-Path $appRoot "models"
New-Item -ItemType Directory -Path $modelsRoot -Force | Out-Null

$definitions = @(
    [pscustomobject]@{
        Alias = "qwen3-1.7b"
        Source = "OpenVINO/Qwen3-1.7B-int4-ov"
        RelativePath = "OpenVINO/Qwen3-1.7B-int4-ov"
        MaxNumSeqs = 4
    },
    [pscustomobject]@{
        Alias = "qwen3-8b"
        Source = "OpenVINO/Qwen3-8B-int4-ov"
        RelativePath = "OpenVINO/Qwen3-8B-int4-ov"
        MaxNumSeqs = 1
    }
)

function Invoke-Docker {
    param([string[]]$Arguments)

    & docker @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Comando Docker falhou com código $LASTEXITCODE."
    }
}

function Test-PreparedModel {
    param([string]$ModelPath)

    $required = @(
        "graph.pbtxt",
        "openvino_model.xml",
        "openvino_model.bin",
        "openvino_tokenizer.xml",
        "openvino_tokenizer.bin",
        "tokenizer.json"
    )
    foreach ($file in $required) {
        if (-not (Test-Path -LiteralPath (Join-Path $ModelPath $file) -PathType Leaf)) {
            return $false
        }
    }
    return $true
}

$prepared = @()
foreach ($definition in $definitions) {
    $modelPath = Join-Path $modelsRoot $definition.RelativePath
    if (-not (Test-PreparedModel $modelPath)) {
        if ($SkipDownload) {
            Write-Warning "Modelo $($definition.Alias) não está preparado; ele não será incluído no catálogo OVMS."
            continue
        }

        Write-Host "Preparando $($definition.Source) ..."
        Invoke-Docker @(
            "run", "--rm",
            "--volume", "$modelsRoot`:/models",
            $Image,
            "--pull",
            "--source_model", $definition.Source,
            "--model_repository_path", "/models",
            "--target_device", "GPU",
            "--task", "text_generation",
            "--max_num_seqs", "$($definition.MaxNumSeqs)"
        )
    }

    if (Test-PreparedModel $modelPath) {
        $prepared += $definition
    } else {
        throw "O modelo $($definition.Alias) não possui todos os arquivos obrigatórios após a preparação."
    }
}

if ($prepared.Count -eq 0) {
    throw "Nenhum modelo preparado foi encontrado em $modelsRoot."
}

$configPath = Join-Path $modelsRoot "config.json"
$config = if (Test-Path -LiteralPath $configPath -PathType Leaf) {
    Get-Content -Raw -LiteralPath $configPath | ConvertFrom-Json
} else {
    [pscustomobject]@{
        model_config_list = @()
        mediapipe_config_list = @()
    }
}

$managedAliases = @($definitions | ForEach-Object { $_.Alias })
$existingGraphs = @($config.mediapipe_config_list | Where-Object {
        $_.name -notin $managedAliases
    })
$managedGraphs = @($prepared | ForEach-Object {
        [pscustomobject]@{
            name = $_.Alias
            base_path = $_.RelativePath
            graph_path = "graph.pbtxt"
        }
    })
$config.mediapipe_config_list = @($existingGraphs + $managedGraphs)
if ($null -eq $config.model_config_list) {
    $config | Add-Member -NotePropertyName model_config_list -NotePropertyValue @()
}

$temporaryConfig = Join-Path $modelsRoot ("config.json.tmp-{0}" -f $PID)
$json = $config | ConvertTo-Json -Depth 10
[System.IO.File]::WriteAllText($temporaryConfig, $json, [System.Text.UTF8Encoding]::new($false))
Move-Item -LiteralPath $temporaryConfig -Destination $configPath -Force

Write-Host "Configuração OVMS atualizada em $configPath"
Write-Host "Modelos preparados: $($prepared.Alias -join ', ')"
