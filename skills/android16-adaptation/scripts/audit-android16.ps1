[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string]$ProjectRoot = (Get-Location).Path,

    [string]$AppModule = "app",

    [string]$OutputPath,

    [ValidateRange(1, 100)]
    [int]$MaxFilesPerCheck = 20
)

$ErrorActionPreference = "Stop"

$resolvedRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path.TrimEnd('\', '/')
$excludedDirectoryPattern = '[\\/](\.git|\.gradle|build|out|node_modules|\.idea)[\\/]'
$sourceExtensions = @('.gradle', '.kts', '.kt', '.java', '.xml', '.toml', '.properties', '.pro', '.mk', '.cmake', '.cpp', '.c', '.h')

function Get-RelativePath {
    param([string]$Path)

    if ($Path.StartsWith($resolvedRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $Path.Substring($resolvedRoot.Length).TrimStart('\', '/')
    }

    return $Path
}

function Get-RepositoryFiles {
    $git = Get-Command git -ErrorAction SilentlyContinue
    if ($git -and (Test-Path -LiteralPath (Join-Path $resolvedRoot '.git'))) {
        $relativePaths = @(& $git.Source -c core.quotepath=false -C $resolvedRoot ls-files --cached --others --exclude-standard)
        foreach ($relativePath in $relativePaths) {
            $fullPath = Join-Path $resolvedRoot $relativePath
            if (Test-Path -LiteralPath $fullPath -PathType Leaf) {
                Get-Item -LiteralPath $fullPath
            }
        }
        return
    }

    Get-ChildItem -LiteralPath $resolvedRoot -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -notmatch $excludedDirectoryPattern }
}

$repositoryFiles = @(Get-RepositoryFiles)
$sourceFiles = @($repositoryFiles | Where-Object {
    $sourceExtensions -contains $_.Extension.ToLowerInvariant() -or $_.Name -in @('gradlew', 'gradlew.bat')
})
$searchablePaths = @($sourceFiles | Select-Object -ExpandProperty FullName)

$checks = @(
    [pscustomobject]@{
        Name = 'Build toolchain and SDK levels'
        Why = 'Confirm API 36 build baseline and locate variant-specific overrides.'
        Patterns = @('compileSdk(?:Version)?\s*[= ]\s*36', 'targetSdk(?:Version)?\s*[= ]\s*36', 'com\.android\.tools\.build:gradle', 'com\.android\.application', 'distributionUrl=.*gradle-', 'jvmToolchain', 'VERSION_17')
    },
    [pscustomobject]@{
        Name = 'Edge-to-edge and insets'
        Why = 'Find shared handling, opt-outs, fixed spacers, and pages that may need exceptions.'
        Patterns = @('enableEdgeToEdge', 'WindowInsets(?:Compat)?', 'setDecorFitsSystemWindows', 'windowOptOutEdgeToEdgeEnforcement', 'fitsSystemWindows', 'statusBarHeight', 'navigationBarHeight', 'adjustPan', 'adjustResize', 'ImmersionBar')
    },
    [pscustomobject]@{
        Name = 'Back navigation'
        Why = 'Find obsolete interception and supported predictive-back callbacks.'
        Patterns = @('onBackPressed\s*\(', 'KEYCODE_BACK', 'onKeyDown\s*\(', 'OnBackPressedDispatcher', 'OnBackPressedCallback', 'OnBackInvokedDispatcher', 'BackHandler', 'enableOnBackInvokedCallback')
    },
    [pscustomobject]@{
        Name = 'Large-screen restrictions and metrics'
        Why = 'Find restrictions ignored on large screens and physical-display assumptions.'
        Patterns = @('screenOrientation', 'resizeableActivity', 'minAspectRatio', 'maxAspectRatio', 'setRequestedOrientation', 'getRequestedOrientation', 'getRealMetrics', 'DisplayMetrics', 'WindowSizeClass', 'PROPERTY_COMPAT_ALLOW_RESTRICTED_RESIZABILITY')
    },
    [pscustomobject]@{
        Name = 'Background work and scheduling'
        Why = 'Locate work affected by quotas, stop reasons, or missed fixed-rate executions.'
        Patterns = @('enqueueUniquePeriodicWork', 'ExistingPeriodicWorkPolicy\.(REPLACE|UPDATE)', 'PeriodicWorkRequest', 'JobScheduler', 'JobService', 'jobFinished', 'getStopReason', 'scheduleAtFixedRate', 'setImportantWhileForeground', 'foregroundServiceType')
    },
    [pscustomobject]@{
        Name = 'Exported components and intent security'
        Why = 'Locate external entry points and intent/URI forwarding surfaces.'
        Patterns = @('android:exported', '<provider', '<receiver', '<service', 'PendingIntent', 'FLAG_(?:MUTABLE|IMMUTABLE)', 'getParcelableExtra', 'grantUriPermission', 'FileProvider', 'removeLaunchSecurityProtection', 'intentMatchingFlags')
    },
    [pscustomobject]@{
        Name = 'Bluetooth bonding'
        Why = 'Determine whether Android 16 bond-loss events and OEM fallback apply.'
        Patterns = @('createBond', 'removeBond', 'ACTION_BOND_STATE_CHANGED', 'ACTION_KEY_MISSING', 'ACTION_ENCRYPTION_CHANGE', 'CompanionDeviceManager', 'RESULT_DISCOVERY_TIMEOUT', 'RESULT_USER_REJECTED')
    },
    [pscustomobject]@{
        Name = 'Local network access'
        Why = 'Find LAN traffic that must be exercised with Android 16 local-network restrictions.'
        Patterns = @('DatagramSocket', 'MulticastSocket', 'ServerSocket', 'NsdManager', 'mDNS', 'SSDP', 'NEARBY_WIFI_DEVICES', 'WifiNetworkSpecifier', 'http://(?:192\.168\.|10\.|172\.(?:1[6-9]|2[0-9]|3[01])\.)', '\.local(?:[/:"'']|$)')
    },
    [pscustomobject]@{
        Name = 'Health Connect and Google Fit'
        Why = 'Locate granular health permissions and any independent Fit retirement work.'
        Patterns = @('HealthConnectClient', 'android\.permission\.health', 'BODY_SENSORS', 'READ_HEART_RATE', 'READ_HEALTH_DATA_IN_BACKGROUND', 'FitnessOptions', 'com\.google\.android\.gms\.fitness', 'Google Fit')
    },
    [pscustomobject]@{
        Name = 'Media, text, accessibility, and themed icons'
        Why = 'Find selected-photo, font-height, announcement, and monochrome-icon surfaces.'
        Patterns = @('READ_MEDIA_VISUAL_USER_SELECTED', 'PickVisualMedia', 'MediaStore\.getVersion', 'ACTION_PICK', 'elegantTextHeight', 'announceForAccessibility', 'TYPE_ANNOUNCEMENT', 'monochrome')
    },
    [pscustomobject]@{
        Name = 'Native code and ABI configuration'
        Why = 'Identify native inputs; formal 16 KB acceptance still requires final APK/AAB inspection.'
        Patterns = @('jniLibs', 'externalNativeBuild', 'ndkVersion', 'abiFilters', 'System\.loadLibrary', 'ReLinker')
    }
)

$lines = [System.Collections.Generic.List[string]]::new()
$lines.Add('# Android 16 static audit leads')
$lines.Add('')
$lines.Add("- Project root: ``$resolvedRoot``")
$lines.Add("- App module hint: ``$AppModule``")
$lines.Add("- Source/config files scanned: $($sourceFiles.Count)")
$lines.Add('- Scope: read-only static search; generated build outputs and caches are excluded.')
$lines.Add('- Warning: a match is a lead, not a defect or proof of completion. Final artifacts, runtime behavior, and manual flows require separate evidence.')
$lines.Add('')

foreach ($check in $checks) {
    $matches = @()
    if ($searchablePaths.Count -gt 0) {
        $matches = @(Select-String -LiteralPath $searchablePaths -Pattern $check.Patterns -AllMatches -ErrorAction SilentlyContinue)
    }

    $matchedFiles = @($matches | Select-Object -ExpandProperty Path -Unique | Sort-Object)
    $lines.Add("## $($check.Name)")
    $lines.Add('')
    $lines.Add("- Why: $($check.Why)")
    $lines.Add("- Matching lines: $($matches.Count)")
    $lines.Add("- Matching files: $($matchedFiles.Count)")

    if ($matchedFiles.Count -eq 0) {
        $lines.Add('- Files: none found by this search; inspect dependencies, generated manifests, and final artifacts before marking `NOT_APPLICABLE`.')
    }
    else {
        $lines.Add('- Files:')
        foreach ($path in ($matchedFiles | Select-Object -First $MaxFilesPerCheck)) {
            $lines.Add("  - ``$(Get-RelativePath -Path $path)``")
        }
        if ($matchedFiles.Count -gt $MaxFilesPerCheck) {
            $lines.Add("  - ... $($matchedFiles.Count - $MaxFilesPerCheck) more")
        }
    }

    $lines.Add('')
}

$nativeFiles = @($repositoryFiles | Where-Object { $_.Extension.ToLowerInvariant() -eq '.so' })
$archiveFiles = @($repositoryFiles | Where-Object { $_.Extension.ToLowerInvariant() -in @('.aar', '.apk', '.aab') })

$lines.Add('## Native artifacts present in the repository')
$lines.Add('')
$lines.Add("- Direct `.so` files outside excluded directories: $($nativeFiles.Count)")
$lines.Add("- AAR/APK/AAB files outside excluded directories: $($archiveFiles.Count)")
$lines.Add('- These counts do not replace resolved-dependency or final-output inspection for ABI and 16 KB compatibility.')
$lines.Add('')
$lines.Add('## Required next output')
$lines.Add('')
$lines.Add('Classify each section as `MUST_FIX`, `CONDITIONAL`, `NOT_APPLICABLE`, `DONE`, `BLOCKED`, or `NOT_VERIFIED`, and attach evidence for that classification.')

$report = $lines -join [Environment]::NewLine

if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    $report
}
else {
    $resolvedOutput = [System.IO.Path]::GetFullPath((Join-Path (Get-Location) $OutputPath))
    $parent = Split-Path -Parent $resolvedOutput
    if ($parent -and -not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
    Set-Content -LiteralPath $resolvedOutput -Value $report -Encoding UTF8
    Write-Output $resolvedOutput
}
