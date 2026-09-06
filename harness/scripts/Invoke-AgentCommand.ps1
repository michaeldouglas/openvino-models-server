[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-z0-9]+(?:-[a-z0-9]+)*$')]
    [string] $Agent,

    [Parameter(Mandatory = $true)]
    [string] $FilePath,

    [Parameter(Mandatory = $false)]
    [string[]] $ArgumentList = @(),

    [Parameter(Mandatory = $false)]
    [string] $WorkingDirectory,

    [Parameter(Mandatory = $false)]
    [ValidatePattern('^[a-zA-Z0-9][a-zA-Z0-9._-]*$')]
    [string] $RunId
)

$scriptRoot = [IO.Path]::GetFullPath((Split-Path -Parent $MyInvocation.MyCommand.Path))
$harnessRoot = [IO.Path]::GetFullPath((Join-Path $scriptRoot '..'))
$serverAgentsRoot = [IO.Path]::GetFullPath((Join-Path $harnessRoot '..'))
$defaultAppRoot = [IO.Path]::GetFullPath((Join-Path $serverAgentsRoot 'app'))
$workRoot = [IO.Path]::GetFullPath((Join-Path $harnessRoot '.agent-work'))

if ([string]::IsNullOrWhiteSpace($WorkingDirectory)) {
    $WorkingDirectory = $defaultAppRoot
}

$workingItem = Get-Item -LiteralPath $WorkingDirectory -ErrorAction Stop
if (-not $workingItem.PSIsContainer) {
    throw "WorkingDirectory must be a directory: $WorkingDirectory"
}
$workingDirectory = $workingItem.FullName

if ([string]::IsNullOrWhiteSpace($RunId)) {
    $RunId = '{0}-{1}' -f (Get-Date -Format 'yyyyMMdd-HHmmss-fff'), ([guid]::NewGuid().ToString('N').Substring(0, 8))
}

$runRoot = [IO.Path]::GetFullPath((Join-Path $workRoot (Join-Path (Join-Path 'runs' $RunId) $Agent)))
$workRootWithSeparator = $workRoot.TrimEnd('\') + '\'
if (-not $runRoot.StartsWith($workRootWithSeparator, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Resolved run directory is outside the agent work area."
}

$runPaths = @{
    tmp = Join-Path $runRoot 'tmp'
    logs = Join-Path $runRoot 'logs'
    reports = Join-Path $runRoot 'reports'
    scratch = Join-Path $runRoot 'scratch'
}
foreach ($path in @($runPaths.tmp, $runPaths.logs, $runPaths.reports)) {
    New-Item -ItemType Directory -Force -Path $path | Out-Null
}

$manifestPath = Join-Path $runRoot 'run.json'
$manifest = [ordered]@{
    run_id = $RunId
    agent = $Agent
    harness_root = $harnessRoot
    application_root = $defaultAppRoot
    working_directory = $workingDirectory
    file_path = $FilePath
    arguments = @($ArgumentList)
    status = 'running'
    started_at = (Get-Date).ToUniversalTime().ToString('o')
    paths = $runPaths
}
$manifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $manifestPath -Encoding utf8

$previousEnvironment = @{}
function Set-ScopedEnvironment {
    param([string] $Name, [AllowNull()][string] $Value)
    if (-not $previousEnvironment.ContainsKey($Name)) {
        $previousEnvironment[$Name] = [Environment]::GetEnvironmentVariable($Name, 'Process')
    }
    [Environment]::SetEnvironmentVariable($Name, $Value, 'Process')
}

$pytestBaseTemp = Join-Path $runPaths.tmp 'pytest'
$scopedEnvironment = @{
    TEMP = $runPaths.tmp
    TMP = $runPaths.tmp
    PYTHONDONTWRITEBYTECODE = '1'
    COVERAGE_FILE = Join-Path $runPaths.reports '.coverage'
    RUFF_CACHE_DIR = Join-Path $workRoot 'cache/ruff'
    MYPY_CACHE_DIR = Join-Path $workRoot 'cache/mypy'
}
$existingPytestOptions = [Environment]::GetEnvironmentVariable('PYTEST_ADDOPTS', 'Process')
$scopedEnvironment['PYTEST_ADDOPTS'] = if ([string]::IsNullOrWhiteSpace($existingPytestOptions)) {
    "--basetemp=$pytestBaseTemp"
} else {
    "$existingPytestOptions --basetemp=$pytestBaseTemp"
}

$exitCode = 1
$stdout = ''
$stderr = ''
$process = $null
try {
    foreach ($entry in $scopedEnvironment.GetEnumerator()) {
        Set-ScopedEnvironment -Name $entry.Key -Value ([string]$entry.Value)
    }

    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = $FilePath
    $startInfo.WorkingDirectory = $workingDirectory
    $startInfo.UseShellExecute = $false
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true

    if (-not ($startInfo.PSObject.Properties.Name -contains 'ArgumentList')) {
        throw 'This runner requires a PowerShell/.NET runtime with ProcessStartInfo.ArgumentList support to preserve argument boundaries.'
    }
    foreach ($argument in $ArgumentList) {
        [void]$startInfo.ArgumentList.Add($argument)
    }

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $startInfo
    [void]$process.Start()
    $manifest.process_id = $process.Id
    $manifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $manifestPath -Encoding utf8

    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()
    $process.WaitForExit()
    $stdout = $stdoutTask.GetAwaiter().GetResult()
    $stderr = $stderrTask.GetAwaiter().GetResult()
    $exitCode = $process.ExitCode
}
catch {
    $stderr = $_.Exception.Message
    $exitCode = 1
}
finally {
    if ($process -and -not $process.HasExited) {
        $process.Kill()
        $process.WaitForExit()
    }
    $stdout | Set-Content -LiteralPath (Join-Path $runPaths.logs 'stdout.log') -Encoding utf8
    $stderr | Set-Content -LiteralPath (Join-Path $runPaths.logs 'stderr.log') -Encoding utf8
    $manifest.status = if ($exitCode -eq 0) { 'completed' } else { 'failed' }
    $manifest.exit_code = $exitCode
    $manifest.finished_at = (Get-Date).ToUniversalTime().ToString('o')
    $manifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $manifestPath -Encoding utf8
    foreach ($entry in $previousEnvironment.GetEnumerator()) {
        [Environment]::SetEnvironmentVariable($entry.Key, $entry.Value, 'Process')
    }
}

if (-not [string]::IsNullOrEmpty($stdout)) {
    [Console]::Out.Write($stdout)
}
if (-not [string]::IsNullOrEmpty($stderr)) {
    [Console]::Error.Write($stderr)
}
Write-Output "AGENT_RUN=$runRoot"
exit $exitCode
