# Verification and release matrix

## Verification order

1. Discover modules, variants, and real task names.
2. Run focused unit tests/static checks for changed logic.
3. Compile the narrowest affected variant when source/resources/manifest/dependencies changed.
4. Build release APK/AAB when packaging, signing input, manifests, native libraries, or release readiness is in scope.
5. Inspect final merged/output artifacts.
6. Run emulator and physical-device matrices.
7. Record manual flows separately.

Example commands must be adapted to the actual project:

```powershell
.\gradlew.bat :<APP_MODULE>:tasks --all
.\gradlew.bat :<APP_MODULE>:test<VARIANT>UnitTest --max-workers=1 --no-parallel
.\gradlew.bat :<APP_MODULE>:lint<VARIANT> --max-workers=1 --no-parallel
.\gradlew.bat :<APP_MODULE>:assemble<DEBUG_VARIANT> --max-workers=1 --no-parallel
.\gradlew.bat :<APP_MODULE>:assemble<RELEASE_VARIANT> --max-workers=1 --no-parallel
.\gradlew.bat :<APP_MODULE>:bundle<RELEASE_VARIANT> --max-workers=1 --no-parallel
```

For native outputs:

```text
zipalign -c -P 16 -v 4 <APK>
bundletool dump config --bundle=<AAB>
llvm-readelf -l <SO>
adb shell getconf PAGE_SIZE
```

Expected AAB metadata and ELF/runtime details must follow the live 16 KB guide; keep raw reports as evidence.

## Device matrix

| Environment | Required coverage |
| --- | --- |
| Android 16 API 36 Pixel/emulator | gestures, three-button navigation, edge-to-edge, predictive back, permissions |
| Android 16 16 KB environment | `PAGE_SIZE=16384`, startup, every native-backed feature |
| Android 15 API 35 | edge-to-edge and permission regression |
| Minimum supported API | startup, navigation, insets, permissions, core flows |
| Major OEM Android 16 device | Bluetooth, background, notifications, permissions, system bars |
| Foldable | inner/outer display, fold/unfold, hinge, state restoration |
| `sw600dp` tablet | rotations, split screen, baseline layout usability |
| Freeform/desktop window | continuous resize, focus, IME, task continuity |

Only include rows applicable to the product type, but justify exclusions.

## Manual flow groups

- install, update, cold/warm start, process death, reboot, sign-in/out, account switch
- primary navigation, dialogs/sheets, toasts/snackbars, themes, dark mode
- top/bottom controls, list boundaries, cutouts, gesture and three-button navigation
- all input fields, keyboard changes, focus scrolling, submit/back behavior
- predictive-back start/cancel/complete, cross-activity/task/home, WebView, dialogs
- notification grant/deny/revoke, foreground/background/killed delivery and routing
- camera, selected photos, crop, share, FileProvider, revoke/reselect
- jobs with network changes, Doze, process death, reboot, standby buckets
- Arabic, Thai, Indic scripts, German expansion, RTL, font clipping
- applicable BLE, LAN, Health Connect, native-feature, foldable, and tablet flows

Record every result as `PASS`, `FAIL`, `BLOCKED`, or `NOT_RUN` with device/environment, build identifier, evidence path, and defect link.

## Release gates

### P0 — stop release

Startup/native crash, data corruption, broken payment/update/critical transfer, security exposure, or all users unable to complete a critical flow.

### P1 — stop or pause rollout

Critical operation obscured by insets/IME, back navigation corrupts or exits work, persistent BLE reconnect loop, long-term background failure, permission/intent breakage, or repeatable OEM critical regression.

### First release checklist

- target-36 debug/release/AAB outputs and identity/signing inputs verified
- merged manifest and resolved dependencies reviewed
- Android 16 phone critical path has no known P0/P1
- edge-to-edge and back-navigation evidence present
- every delivered native ABI passes final-artifact and runtime gates, or release is `BLOCKED`
- exported/intent/provider audit has no untreated high-risk finding
- each conditional surface has completion or `NOT_APPLICABLE` evidence
- temporary large-screen exception, if any, is proven and time-bounded
- manual coverage meets the project's agreed threshold
- rollback artifact, rollback criteria, monitoring, and owners exist

## Rollout

A common starting pattern is internal testing followed by `5% → 20% → 50% → 100%`, observing at least 24 hours per stage. Adjust to population size and risk.

Compare against the previous target-SDK baseline:

- crash-free and ANR
- native load/crash and 16 KB warnings
- window/insets/IME crashes and complaints
- `SecurityException`, intent, URI, and permission failures
- WorkManager/JobScheduler stop reasons, retries, and latency
- BLE bond/reconnect loops and hidden-API failures
- LAN permission, `EPERM`, timeout, and aborted connections
- Health authorization/write failures
- state loss or duplicate work after resize/fold/recreation

Any P0 or stable P1 pauses rollout and invokes the documented rollback path.
