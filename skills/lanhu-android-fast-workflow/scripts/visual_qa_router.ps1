param(
    [string]$ProjectRoot = ".",
    [ValidateSet("component", "layout", "screen", "interaction", "custom-view")]
    [string]$Scope = "screen",
    [switch]$SelfTest
)
$ErrorActionPreference = "Stop"

function Parse-AdbDevices([string[]]$Lines) {
    $physical = @(); $emulators = @()
    foreach ($line in $Lines) {
        if ($line -match "^(\S+)\s+device(?:\s+(.*))?$") {
            $entry = @{ serial = $Matches[1]; metadata = $Matches[2] }
            if ($entry.serial.StartsWith("emulator-") -or $entry.metadata -match "(?i)(sdk_gphone|generic_x86|emulator|virtual)") {
                $emulators += $entry
            } else { $physical += $entry }
        }
    }
    return @{ physical = $physical; emulators = $emulators }
}

function Select-Route([int]$PhysicalCount, [bool]$Paparazzi, [bool]$Roborazzi, [string]$TargetScope) {
    if ($PhysicalCount -gt 0) { return "physical-device" }
    if ($TargetScope -in @("component", "layout")) {
        if ($Paparazzi) { return "paparazzi" }
        if ($Roborazzi) { return "roborazzi" }
    } elseif ($Roborazzi) { return "roborazzi" }
    return "unverified"
}

if ($SelfTest) {
    $devices = Parse-AdbDevices @("List of devices attached", "PHONE device model:Pixel", "emulator-5554 device model:sdk_gphone", "LOCKED unauthorized")
    if ($devices.physical.Count -ne 1 -or $devices.emulators.Count -ne 1) { throw "device parsing failed" }
    $cases = @(
        @(1, $false, $false, "screen", "physical-device"),
        @(0, $true, $false, "layout", "paparazzi"),
        @(0, $true, $false, "interaction", "unverified"),
        @(0, $false, $true, "screen", "roborazzi"),
        @(0, $false, $true, "component", "roborazzi"),
        @(0, $false, $false, "layout", "unverified")
    )
    foreach ($case in $cases) {
        if ((Select-Route $case[0] $case[1] $case[2] $case[3]) -ne $case[4]) { throw "route case failed" }
    }
    @{status="ok"; test="visual_qa_router"; cases=$cases.Count+1} | ConvertTo-Json -Compress
    exit 0
}

$resolved = (Resolve-Path -LiteralPath $ProjectRoot).Path
$adb = Get-Command adb -ErrorAction SilentlyContinue
$devices = @{ physical=@(); emulators=@() }
if ($adb) {
    $lines = & $adb.Source devices -l 2>$null
    if ($LASTEXITCODE -eq 0) { $devices = Parse-AdbDevices $lines }
}
$files = @("build.gradle","build.gradle.kts","settings.gradle","settings.gradle.kts","app/build.gradle","app/build.gradle.kts","gradle/libs.versions.toml") |
    ForEach-Object { Join-Path $resolved $_ } | Where-Object { Test-Path -LiteralPath $_ }
$paparazzi = $false; $roborazzi = $false
foreach ($file in $files) {
    if (Select-String -LiteralPath $file -Pattern "paparazzi" -SimpleMatch -Quiet) { $paparazzi = $true }
    if (Select-String -LiteralPath $file -Pattern "roborazzi" -SimpleMatch -Quiet) { $roborazzi = $true }
}
$route = Select-Route $devices.physical.Count $paparazzi $roborazzi $Scope
@{
    status="ok"; route=$route; scope=$Scope; mode="quick"
    physical_devices=$devices.physical; connected_emulators=$devices.emulators
    existing_frameworks=@{paparazzi=$paparazzi; roborazzi=$roborazzi}
    detection_limit="Text hints only; custom module/build-logic setup and actual test tasks need confirmation."
    requires_dependency_change=$false; auto_install_dependencies=$false
    final_build_timeout_seconds=600; stricter_project_budget_wins=$true
    full_visual_matrix=$false; mcp_allowed=$false
    note="Read-only routing. Device authorization/unlock/data still required. Unverified means skip, not install dependencies."
} | ConvertTo-Json -Depth 5 -Compress
