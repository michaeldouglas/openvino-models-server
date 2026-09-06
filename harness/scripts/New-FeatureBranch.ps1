[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Name,

    [switch]$Confirmed,

    [switch]$ReuseExisting
)

$ErrorActionPreference = 'Stop'

$scriptPath = $MyInvocation.MyCommand.Path
$harnessRoot = (Resolve-Path -LiteralPath (Join-Path (Split-Path -Parent $scriptPath) '..')).Path
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $harnessRoot '..')).Path
Set-Location -LiteralPath $repoRoot

$confirmationText = 'Deseja criar uma nova branch de feature para esta tarefa? Sugestão: feature/<nome-descritivo>. Se não, continuarei na branch atual.'
if (-not $Confirmed) {
    Write-Error "Confirmação explícita obrigatória antes de criar/trocar branch. Pergunta a ser apresentada ao usuário: $confirmationText" -ErrorAction Continue
    exit 2
}

$currentBranch = (& git branch --show-current).Trim()
if ([string]::IsNullOrWhiteSpace($currentBranch)) {
    throw 'Não foi possível determinar a branch atual.'
}

$dirty = @(git status --porcelain)
if ($dirty.Count -gt 0) {
    throw 'Existem alterações locais. Preserve-as e verifique sua relação com a tarefa antes de trocar de branch; o script não faz stash nem descarte automático.'
}

$slug = $Name.ToLowerInvariant() -replace '[^a-z0-9]+', '-'
$slug = $slug.Trim('-')
if ([string]::IsNullOrWhiteSpace($slug)) {
    throw 'O nome da feature não produz um identificador válido.'
}
$branchName = "feature/$slug"

& git fetch origin develop --prune
if ($LASTEXITCODE -ne 0) {
    throw 'Falha ao atualizar origin/develop.'
}

$baseRef = (& git rev-parse --verify 'refs/remotes/origin/develop').Trim()
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($baseRef)) {
    throw 'origin/develop não existe. Inicialize essa referência a partir de main antes de criar uma feature.'
}

$localExists = $null -ne (git branch --list -- $branchName)
$remoteExists = $null -ne (git ls-remote --exit-code --heads origin $branchName 2>$null)
if ($localExists -or $remoteExists) {
    if (-not $ReuseExisting) {
        throw "A branch '$branchName' já existe localmente ou no remote. Inspecione seu conteúdo e contexto antes de reutilizá-la; use -ReuseExisting somente após essa decisão."
    }

    if ($localExists) {
        & git switch $branchName
    } else {
        & git switch --track "origin/$branchName"
    }
    if ($LASTEXITCODE -ne 0) {
        throw "Não foi possível reutilizar '$branchName'."
    }
} else {
    & git switch -c $branchName $baseRef
    if ($LASTEXITCODE -ne 0) {
        throw "Não foi possível criar '$branchName' a partir de origin/develop ($baseRef)."
    }
}

[PSCustomObject]@{
    REPOSITORY_ROOT = $repoRoot
    CURRENT_BRANCH = $currentBranch
    FEATURE_BRANCH = $branchName
    BASE = "origin/develop@$baseRef"
    REUSED = [bool]($localExists -or $remoteExists)
} | ConvertTo-Json -Compress
