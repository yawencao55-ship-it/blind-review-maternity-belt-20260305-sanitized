param(
  [Parameter(Mandatory=$true)] [string]$RepoName
)

$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path

# Assumes gh is already authenticated to the anonymous account.
gh auth status | Out-Host

gh repo create $RepoName --public --source $here --remote anon_origin --push

$sha = git -C $here rev-parse HEAD
Write-Host "Repo URL: https://github.com/$((gh api user --jq .login))/$RepoName"
Write-Host "Tree URL: https://github.com/$((gh api user --jq .login))/$RepoName/tree/$sha"
