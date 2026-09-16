param(
    [string]$ProjectRoot = ".",
    [ValidateSet("component", "layout", "screen", "interaction", "custom-view")]
    [string]$Scope = "screen",
    [ValidateSet("static", "paparazzi", "device")]
    [string]$Validation = "static",
    [switch]$DeviceAuthorized,
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

function Select-Route([string]$Choice, [bool]$Authorized, [int]$PhysicalCount, [int]$EmulatorCount, [bool]$Paparazzi) {
    if ($Choice -eq "static") { return "static-only" }
    if ($Choice -eq "paparazzi") {
        if ($Paparazzi) { return "paparazzi" }
        return "unverified"
    }
    if (-not $Authorized) { return "needs-device-consent" }
    if ($PhysicalCount -gt 0) { return "physical-device" }
    if ($EmulatorCount -gt 0) { return "connected-emulator" }
    return "unverified"
}

if ($SelfTest) {
    $devices = Parse-AdbDevices @("List of devices attached", "PHONE device model:Pixel", "emulator-5554 device model:sdk_gphone", "LOCKED unauthorized")
    if ($devices.physical.Count -ne 1 -or $devices.emulators.Count -ne 1) { throw "device parsing failed" }
    $cases = @(
        @("static", $false, 1, 1, $true, "static-only"),
        @("paparazzi", $false, 1, 1, $true, "paparazzi"),
        @("paparazzi", $false, 1, 1, $false, "unverified"),
        @("device", $false, 1, 1, $true, "needs-device-consent"),
        @("device", $true, 1, 1, $true, "physical-device"),
        @("device", $true, 0, 1, $false, "connected-emulator"),
        @("device", $true, 0, 0, $true, "unverified")
    )
    foreach ($case in $cases) {
        if ((Select-Route $case[0] $case[1] $case[2] $case[3] $case[4]) -ne $case[5]) { throw "route case failed" }
    }
    @{status="ok"; test="visual_qa_router"; cases=$cases.Count+1} | ConvertTo-Json -Compress
    exit 0
}

$resolved = (Resolve-Path -LiteralPath $ProjectRoot).Path
$devices = @{ physical=@(); emulators=@() }
$deviceProbe = $false
if ($Validation -eq "device" -and $DeviceAuthorized) {
    $adb = Get-Command adb -ErrorAction SilentlyContinue
    if ($adb) {
        $deviceProbe = $true
        $lines = & $adb.Source devices -l 2>$null
        if ($LASTEXITCODE -eq 0) { $devices = Parse-AdbDevices $lines }
    }
}
$files = @("build.gradle","build.gradle.kts","settings.gradle","settings.gradle.kts","app/build.gradle","app/build.gradle.kts","gradle/libs.versions.toml") |
    ForEach-Object { Join-Path $resolved $_ } | Where-Object { Test-Path -LiteralPath $_ }
$paparazzi = $false; $roborazzi = $false
foreach ($file in $files) {
    if (Select-String -LiteralPath $file -Pattern "paparazzi" -SimpleMatch -Quiet) { $paparazzi = $true }
    if (Select-String -LiteralPath $file -Pattern "roborazzi" -SimpleMatch -Quiet) { $roborazzi = $true }
}
$route = Select-Route $Validation ([bool]$DeviceAuthorized) $devices.physical.Count $devices.emulators.Count $paparazzi
@{
    status="ok"; route=$route; scope=$Scope; mode="quick"; choice=$Validation; device_probe_performed=$deviceProbe
    physical_devices=$devices.physical; connected_emulators=$devices.emulators
    existing_frameworks=@{paparazzi=$paparazzi; roborazzi=$roborazzi}
    detection_limit="Text hints only; custom module/build-logic setup and actual test tasks need confirmation."
    requires_dependency_change=$false; auto_install_dependencies=$false
    final_build_timeout_seconds=600; stricter_project_budget_wins=$true
    full_visual_matrix=$false; mcp_allowed=$false
    note="Routing is not verification. Honor the user's choice; no automatic fallback or installation. Paparazzi checks rendered fixtures, not device interactions."
} | ConvertTo-Json -Depth 5 -Compress
