param([Parameter(Mandatory=$true)][string]$ProjectRoot)
$ErrorActionPreference = 'Stop'
$resolvedProject = (Resolve-Path -LiteralPath $ProjectRoot).Path
$wrapper = Join-Path $resolvedProject 'gradlew.bat'
if (-not (Test-Path -LiteralPath $wrapper -PathType Leaf)) { throw 'gradlew.bat is missing.' }
if (-not (Get-Command java -ErrorAction SilentlyContinue) -and -not $env:JAVA_HOME) { throw 'Java is unavailable.' }

# Check clients and CPU-active daemons without stopping shared Gradle processes.
$javaProcesses = @(Get-CimInstance Win32_Process -Filter "Name = 'java.exe' OR Name = 'javaw.exe'")
$clients = @($javaProcesses | Where-Object { $_.CommandLine -match 'GradleWrapperMain|GradleMain|GradleWorkerMain' })
if ($clients.Count) { throw 'Another Gradle client or worker is running. Retry when it finishes.' }
$daemons = @($javaProcesses | Where-Object { $_.CommandLine -match 'GradleDaemon' })
$before = @{}
foreach ($daemon in $daemons) {
    $process = Get-Process -Id $daemon.ProcessId -ErrorAction SilentlyContinue
    if ($process) { $before[$daemon.ProcessId] = $process.CPU }
}
if ($before.Count) {
    Start-Sleep -Milliseconds 700
    foreach ($processId in $before.Keys) {
        $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
        if ($process -and ($process.CPU - $before[$processId]) -gt 0.15) {
            throw 'An existing Gradle daemon is active. Retry when the build finishes.'
        }
    }
}
Push-Location -LiteralPath $resolvedProject
try {
    & $wrapper clean :app:clean --max-workers=1 --no-parallel --console=plain --no-daemon
    if ($LASTEXITCODE -ne 0) { throw "Gradle clean failed with exit code $LASTEXITCODE." }
} finally {
    Pop-Location
}
