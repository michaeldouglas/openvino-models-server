[CmdletBinding()]
param(
    [ValidateSet('qwen3-1.7b', 'qwen3-8b')]
    [string]$Model = 'qwen3-8b',

    [ValidateRange(1, 4096)]
    [int]$PromptTokens = 32,

    [ValidateRange(1, 512)]
    [int]$OutputTokens = 32,

    [ValidateRange(1, 32)]
    [int]$Concurrency = 1,

    [ValidateRange(1, 1000)]
    [int]$MaxRequests = 1,

    [ValidateRange(0, 3600)]
    [int]$MaxDurationSeconds = 0,

    [ValidatePattern('^[a-zA-Z0-9][a-zA-Z0-9._-]*$')]
    [string]$RunId
)

$ErrorActionPreference = 'Stop'

$scriptRoot = [IO.Path]::GetFullPath((Split-Path -Parent $MyInvocation.MyCommand.Path))
$harnessRoot = [IO.Path]::GetFullPath((Join-Path $scriptRoot '..'))
$serverAgentsRoot = [IO.Path]::GetFullPath((Join-Path $harnessRoot '..'))
$appRoot = [IO.Path]::GetFullPath((Join-Path $serverAgentsRoot 'app'))
$benchmarkRoot = [IO.Path]::GetFullPath((Join-Path $harnessRoot '.agent-work\benchmarks\guidellm'))

if ([string]::IsNullOrWhiteSpace($RunId)) {
    $RunId = 'guidellm-{0}-{1}' -f (Get-Date -Format 'yyyyMMdd-HHmmss-fff'), ([guid]::NewGuid().ToString('N').Substring(0, 8))
}

$runRoot = [IO.Path]::GetFullPath((Join-Path $benchmarkRoot $RunId))
$benchmarkPrefix = $benchmarkRoot.TrimEnd('\') + '\'
if (-not $runRoot.StartsWith($benchmarkPrefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Resolved benchmark directory is outside .agent-work: $runRoot"
}

$modelPaths = @{
    'qwen3-1.7b' = Join-Path $appRoot 'models\OpenVINO\Qwen3-1.7B-int4-ov'
    'qwen3-8b' = Join-Path $appRoot 'models\OpenVINO\Qwen3-8B-int4-ov'
}
$tokenizerHostPath = $modelPaths[$Model]
if (-not (Test-Path -LiteralPath $tokenizerHostPath -PathType Container)) {
    throw "Tokenizer/model directory is not prepared: $tokenizerHostPath"
}

New-Item -ItemType Directory -Path $runRoot -Force | Out-Null
$image = 'ghcr.io/vllm-project/guidellm:v0.7.3@sha256:e3ad2371bfa8e42f2c3d1251b62d0d9c9706c27ae2143c8c048eb5fc6aebb558'
$tokenizerContainerPath = "/models/$Model"
$profile = if ($Concurrency -eq 1) {
    'kind=synchronous'
} else {
    "kind=concurrent,streams=$Concurrency"
}
$backend = [ordered]@{
    kind = 'openai_http'
    target = 'http://ovms:8000'
    model = $Model
    request_format = '/v1/chat/completions'
    stream = $true
    validate_backend = $false
    # GuideLLM 0.7.3 adds continuous_usage_stats by default. OVMS accepts
    # include_usage but rejects that extra stream option, so null removes it
    # during GuideLLM's request normalization.
    extras = @{ body = @{ temperature = 0.2; stream_options = @{ continuous_usage_stats = $null } } }
} | ConvertTo-Json -Depth 10 -Compress
$tokenizer = [ordered]@{
    kind = 'huggingface_auto'
    model = $tokenizerContainerPath
} | ConvertTo-Json -Compress
$data = "kind=synthetic_text,prompt_tokens=$PromptTokens,output_tokens=$OutputTokens"

$manifestPath = Join-Path $runRoot 'run-manifest.json'
$manifest = [ordered]@{
    run_id = $RunId
    harness_root = $harnessRoot
    application_root = $appRoot
    working_directory = $appRoot
    image = $image
    model = $Model
    endpoint = 'http://ovms:8000/v1/chat/completions'
    request_format = '/v1/chat/completions'
    tokenizer_host_path = $tokenizerHostPath
    tokenizer_container_path = $tokenizerContainerPath
    prompt_tokens = $PromptTokens
    output_tokens = $OutputTokens
    concurrency = $Concurrency
    profile = $profile
    max_requests = $MaxRequests
    max_duration_seconds = $MaxDurationSeconds
    token_count_source = 'OVMS usage when returned; local HuggingFace tokenizer mounted read-only for GuideLLM generation/counting.'
    status = 'running'
    started_at = (Get-Date).ToUniversalTime().ToString('o')
}
$manifest | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $manifestPath -Encoding utf8
$transcriptPath = Join-Path $runRoot 'run.log'
$transcriptStarted = $false
$preflightCode = "import urllib.request; response=urllib.request.urlopen('http://ovms:8000/v1/models', timeout=5); print(response.status); raise SystemExit(0 if response.status == 200 else 1)"

$guidellmArgs = @(
    'run',
    '--backend', $backend,
    '--profile', $profile,
    '--data', $data,
    '--tokenizer', $tokenizer,
    '--constraint', "kind=max_requests,count=$MaxRequests",
    # Keep one full metric sample per requested operation so aggregate
    # token-rate statistics are retained in JSON/CSV/HTML.
    '--metrics', "kind=generative,sample_size=$MaxRequests,prefer_response_metrics=false",
    '--output', "kind=json,path=/results/$RunId/benchmarks.json",
    '--output', "kind=csv,path=/results/$RunId/benchmarks.csv",
    '--output', "kind=html,path=/results/$RunId/benchmarks.html"
)
if ($MaxDurationSeconds -gt 0) {
    $guidellmArgs += @('--constraint', "kind=max_duration,seconds=$MaxDurationSeconds")
}

$exitCode = 1
Push-Location -LiteralPath $appRoot
try {
    Start-Transcript -LiteralPath $transcriptPath -Force | Out-Null
    $transcriptStarted = $true
    & docker compose --profile benchmark run --rm --no-deps --entrypoint python guidellm -c $preflightCode
    if ($LASTEXITCODE -ne 0) {
        throw 'OVMS não respondeu com sucesso a /v1/models dentro da rede Compose.'
    }
    & docker compose --profile benchmark run --rm --no-deps guidellm @guidellmArgs
    $exitCode = $LASTEXITCODE
    if ($exitCode -eq 0) {
        $expectedReports = @('benchmarks.json', 'benchmarks.csv', 'benchmarks.html')
        $missingReports = @($expectedReports | Where-Object {
                -not (Test-Path -LiteralPath (Join-Path $runRoot $_) -PathType Leaf)
            })
        if ($missingReports.Count -gt 0) {
            $exitCode = 1
            Write-Error "GuideLLM terminou sem gerar: $($missingReports -join ', ')"
        }
        else {
            $report = Get-Content -LiteralPath (Join-Path $runRoot 'benchmarks.json') -Raw | ConvertFrom-Json
            $benchmark = @($report.benchmarks) | Select-Object -First 1
            $successfulRequests = [int]$benchmark.scheduler_state.successful_requests
            $erroredRequests = [int]$benchmark.scheduler_state.errored_requests
            if ($successfulRequests -lt 1 -or $erroredRequests -gt 0) {
                $exitCode = 1
                Write-Error "GuideLLM não produziu uma medição válida: successful_requests=$successfulRequests, errored_requests=$erroredRequests"
            }
        }
    }
}
catch {
    Write-Error $_
    $exitCode = 1
}
finally {
    if ($transcriptStarted) {
        Stop-Transcript | Out-Null
    }
    Pop-Location
    $manifest.status = if ($exitCode -eq 0) { 'completed' } else { 'failed' }
    $manifest.exit_code = $exitCode
    $manifest.finished_at = (Get-Date).ToUniversalTime().ToString('o')
    $manifest | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $manifestPath -Encoding utf8
}

Write-Output "GUIDELLM_RUN=$runRoot"
exit $exitCode
