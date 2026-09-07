[CmdletBinding()]
param(
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [string[]]$Models = @("qwen3-1.7b"),
    [int[]]$Concurrencies = @(1, 2, 4),
    [int]$PromptTokens = 32,
    [int[]]$OutputTokens = @(32, 128),
    [int]$Requests = 10,
    [int]$PollSeconds = 2,
    [string]$ProfileName = "default",
    [string]$Device = "GPU",
    [ValidateRange(0, 10)]
    [int]$WarmupRequests = 2,
    [ValidateRange(1, 512)]
    [int]$WarmupOutputTokens = 16
)

$ErrorActionPreference = "Stop"
$runnerRoot = Split-Path -Parent $PSScriptRoot
$resultsRoot = Join-Path $runnerRoot "results"
$matrixId = "matrix-{0}" -f (Get-Date -Format "yyyyMMdd-HHmmss")
$matrixRoot = Join-Path $resultsRoot $matrixId
New-Item -ItemType Directory -Path $matrixRoot -Force | Out-Null
$resourceBeforePath = Join-Path $matrixRoot "docker-stats-before.log"
$resourceAfterPath = Join-Path $matrixRoot "docker-stats-after.log"

$rows = [System.Collections.Generic.List[object]]::new()

function Save-DockerStats {
    param(
        [string]$Path,
        [string]$Label,
        [string]$CaseId
    )

    Add-Content -LiteralPath $Path -Value "[$Label][$CaseId]"
    try {
        $snapshot = @(docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" 2>&1)
        Add-Content -LiteralPath $Path -Value $snapshot
    } catch {
        Add-Content -LiteralPath $Path -Value "docker stats indisponível: $($_.Exception.Message)"
    }
}

function Invoke-Warmup {
    param(
        [string]$Model,
        [int]$Count,
        [int]$OutputTokenCount
    )

    for ($index = 1; $index -le $Count; $index++) {
        $body = @{
            model = $Model
            text = "Responda apenas com uma palavra: pronto"
            max_tokens = $OutputTokenCount
            temperature = 0.2
        } | ConvertTo-Json
        Invoke-RestMethod -Method Post -Uri "$BaseUrl/v1/generate/sync" `
            -ContentType "application/json" -Body $body | Out-Null
    }
}

foreach ($model in $Models) {
    foreach ($concurrency in $Concurrencies) {
        foreach ($outputTokenCount in $OutputTokens) {
            $caseId = "$model-c$($concurrency)-o$($outputTokenCount)"
            Save-DockerStats -Path $resourceBeforePath -Label "before" -CaseId $caseId
            Invoke-Warmup -Model $model -Count $WarmupRequests -OutputTokenCount $WarmupOutputTokens
            $body = @{
                model = $model
                prompt_tokens = $PromptTokens
                output_tokens = $outputTokenCount
                concurrency = $concurrency
                max_requests = $Requests
            } | ConvertTo-Json

            $job = Invoke-RestMethod -Method Post -Uri "$BaseUrl/v1/benchmarks" `
                -ContentType "application/json" -Body $body
            do {
                Start-Sleep -Seconds $PollSeconds
                $status = Invoke-RestMethod -Method Get -Uri "$BaseUrl/v1/benchmarks/$($job.run_id)"
            } while ($status.status -eq "running")
            Save-DockerStats -Path $resourceAfterPath -Label "after" -CaseId $caseId

            $ttftMs = $null
            $latencyMs = $null
            $tokensPerSecond = $null
            if ($status.status -eq "completed") {
                $report = Invoke-RestMethod -Method Get `
                    -Uri "$BaseUrl/v1/benchmarks/$($job.run_id)/report?format=json"
                $sample = @($report.benchmarks[0].requests.successful)[0]
                $ttftMs = $sample.time_to_first_token_ms
                $latencyMs = [double]$sample.request_latency * 1000
                $tokensPerSecond = $sample.tokens_per_second
                $report | ConvertTo-Json -Depth 30 | Set-Content `
                    -LiteralPath (Join-Path $matrixRoot "$($job.run_id).json") -Encoding utf8
            }

            $rows.Add([pscustomobject]@{
                profile = $ProfileName
                device = $Device
                model = $model
                prompt_tokens = $PromptTokens
                output_tokens = $outputTokenCount
                concurrency = $concurrency
                run_id = $job.run_id
                status = $status.status
                successful_requests = $status.successful_requests
                errors = $status.errored_requests
                ttft_ms = $ttftMs
                latency_ms = $latencyMs
                tokens_per_second = $tokensPerSecond
                warmup_requests = $WarmupRequests
                results_path = $status.results_path
            })
        }
    }
}

$rows | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $matrixRoot "matrix.json") -Encoding utf8
$rows | Export-Csv -LiteralPath (Join-Path $matrixRoot "matrix.csv") -NoTypeInformation -Encoding utf8
Write-Host "Matriz concluída: $matrixRoot"
