[CmdletBinding()]
param(
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [string[]]$Models = @("qwen3-1.7b", "qwen3-8b"),
    [int[]]$Concurrencies = @(1, 2, 4),
    [int]$PromptTokens = 32,
    [int[]]$OutputTokens = @(32, 128),
    [int]$Requests = 10,
    [int]$PollSeconds = 2
)

$ErrorActionPreference = "Stop"
$runnerRoot = Split-Path -Parent $PSScriptRoot
$resultsRoot = Join-Path $runnerRoot "results"
$matrixId = "matrix-{0}" -f (Get-Date -Format "yyyyMMdd-HHmmss")
$matrixRoot = Join-Path $resultsRoot $matrixId
New-Item -ItemType Directory -Path $matrixRoot -Force | Out-Null

$rows = [System.Collections.Generic.List[object]]::new()
foreach ($model in $Models) {
    foreach ($concurrency in $Concurrencies) {
        foreach ($outputTokenCount in $OutputTokens) {
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
                results_path = $status.results_path
            })
        }
    }
}

$rows | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $matrixRoot "matrix.json") -Encoding utf8
$rows | Export-Csv -LiteralPath (Join-Path $matrixRoot "matrix.csv") -NoTypeInformation -Encoding utf8
Write-Host "Matriz concluída: $matrixRoot"
