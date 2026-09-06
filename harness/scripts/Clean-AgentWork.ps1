[CmdletBinding()]
param(
    [switch] $Apply,
    [switch] $Caches,
    [Parameter(Mandatory = $false)]
    [ValidatePattern('^[a-zA-Z0-9][a-zA-Z0-9._-]*$')]
    [string] $RunId
)

$scriptRoot = [IO.Path]::GetFullPath((Split-Path -Parent $MyInvocation.MyCommand.Path))
$harnessRoot = [IO.Path]::GetFullPath((Join-Path $scriptRoot '..'))
$workRoot = [IO.Path]::GetFullPath((Join-Path $harnessRoot '.agent-work'))

if (-not (Test-Path -LiteralPath $workRoot -PathType Container)) {
    Write-Output "Nothing to clean: $workRoot does not exist."
    exit 0
}

function Assert-SafePath {
    param([Parameter(Mandatory = $true)][string] $Path)
    $item = Get-Item -LiteralPath $Path -Force -ErrorAction Stop
    if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "Refusing a reparse point: $Path"
    }
    $resolved = [IO.Path]::GetFullPath($item.FullName)
    $rootPrefix = $workRoot.TrimEnd('\') + '\'
    if (-not $resolved.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase) -and
        $resolved -ne $workRoot) {
        throw "Refusing a path outside .agent-work: $resolved"
    }
    return $item
}

function Assert-SafeTree {
    param([Parameter(Mandatory = $true)][string] $Path)
    [void](Assert-SafePath -Path $Path)
    $reparse = Get-ChildItem -LiteralPath $Path -Force -Recurse -ErrorAction Stop |
        Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 }
    if ($reparse) {
        throw "Refusing a tree containing a reparse point: $Path"
    }
}

[void](Assert-SafePath -Path $workRoot)
$runRoot = Join-Path $workRoot 'runs'
$candidates = New-Object System.Collections.Generic.List[string]
if (Test-Path -LiteralPath $runRoot -PathType Container) {
    [void](Assert-SafePath -Path $runRoot)
    $runDirs = Get-ChildItem -LiteralPath $runRoot -Directory -Force
    foreach ($runDir in $runDirs) {
        if ($runDir.Name -match '[\\/]') { throw "Invalid run directory name." }
        if (-not [string]::IsNullOrWhiteSpace($RunId) -and $runDir.Name -ne $RunId) { continue }
        [void](Assert-SafePath -Path $runDir.FullName)
        $agentDirs = Get-ChildItem -LiteralPath $runDir.FullName -Directory -Force
        foreach ($agentDir in $agentDirs) {
            [void](Assert-SafePath -Path $agentDir.FullName)
            $manifestPath = Join-Path $agentDir.FullName 'run.json'
            if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) { continue }
            $manifest = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json
            if ($manifest.status -notin @('completed', 'failed')) { continue }
            foreach ($name in @('tmp', 'scratch')) {
                $candidate = Join-Path $agentDir.FullName $name
                if (Test-Path -LiteralPath $candidate) {
                    [void](Assert-SafeTree -Path $candidate)
                    [void]$candidates.Add($candidate)
                }
            }
        }
    }
}

$cacheRoot = Join-Path $workRoot 'cache'
if ($Caches -and (Test-Path -LiteralPath $cacheRoot -PathType Container)) {
    $activeManifests = @()
    if (Test-Path -LiteralPath $runRoot -PathType Container) {
        $activeManifests = Get-ChildItem -LiteralPath $runRoot -Filter 'run.json' -File -Force -Recurse |
            ForEach-Object {
                try {
                    $candidateManifest = Get-Content -Raw -LiteralPath $_.FullName | ConvertFrom-Json
                    if ($candidateManifest.status -eq 'running') { $_ }
                }
                catch {
                    throw "Refusing cache cleanup because manifest cannot be read: $($_.FullName)"
                }
            }
    }
    if ($activeManifests.Count -gt 0) {
        throw 'Refusing cache cleanup while an agent run is active.'
    }
    [void](Assert-SafeTree -Path $cacheRoot)
    [void]$candidates.Add($cacheRoot)
}

if ($candidates.Count -eq 0) {
    Write-Output 'Nothing eligible for cleanup.'
    exit 0
}

if (-not $Apply) {
    Write-Output 'Preview only. No files were removed.'
    foreach ($candidate in $candidates) {
        Write-Output "WOULD_REMOVE=$candidate"
    }
    exit 0
}

foreach ($candidate in $candidates) {
    [void](Assert-SafeTree -Path $candidate)
    Remove-Item -LiteralPath $candidate -Recurse -Force -ErrorAction Stop
    Write-Output "REMOVED=$candidate"
}
