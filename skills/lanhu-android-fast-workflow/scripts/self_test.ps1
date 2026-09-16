param([string]$Python = "python", [switch]$ValidateSkill)
$ErrorActionPreference = "Stop"
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
foreach ($exe in @("node", "javac", "java", $Python)) {
    if (-not (Get-Command $exe -ErrorAction SilentlyContinue)) { throw "Missing test prerequisite: $exe" }
}
function Invoke-Checked([string]$Exe, [string[]]$Arguments) {
    & $Exe @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Exe failed with exit $LASTEXITCODE" }
}
if ($ValidateSkill) {
    Invoke-Checked $Python @((Join-Path $scriptRoot "validate_skill.py"))
}
Invoke-Checked "node" @("--check", (Join-Path $scriptRoot "lanhu_pull.mjs"))
Invoke-Checked "node" @("--check", (Join-Path $scriptRoot "state_map.mjs"))
Invoke-Checked "node" @((Join-Path $scriptRoot "lanhu_pull.mjs"), "--self-test")
Invoke-Checked "node" @((Join-Path $scriptRoot "state_map.mjs"), "--self-test")
Invoke-Checked $Python @((Join-Path $scriptRoot "local_assets.py"), "--self-test", "--work-dir", $scriptRoot)
& (Join-Path $scriptRoot "visual_qa_router.ps1") -SelfTest
Invoke-Checked $Python @("-B", "-X", "utf8", "-m", "unittest", "discover", "-s", (Join-Path $scriptRoot "../tests"), "-p", "test_resource_usage.py")
& (Join-Path $scriptRoot "../tests/image_review_test.ps1") -WorkDirectory $scriptRoot

$testOutput = Join-Path $scriptRoot ("java-test-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $testOutput | Out-Null
try {
    Invoke-Checked "javac" @("-d", $testOutput, (Join-Path $scriptRoot "ImageDiff.java"))
    Invoke-Checked "java" @("-cp", $testOutput, "ImageDiff", "--self-test")
} finally {
    $resolvedOutput = (Resolve-Path -LiteralPath $testOutput).Path
    $resolvedRoot = (Resolve-Path -LiteralPath $scriptRoot).Path
    if ((Split-Path -Parent $resolvedOutput) -ne $resolvedRoot -or (Split-Path -Leaf $resolvedOutput) -notlike "java-test-*") {
        throw "Refusing cleanup outside the generated test directory"
    }
    Remove-Item -LiteralPath $resolvedOutput -Recurse -Force
}
@{status="ok"; suite="lanhu-android-fast-workflow"} | ConvertTo-Json -Compress
