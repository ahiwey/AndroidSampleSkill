# Android 16 audit and implementation checklist

Use this after the Skill's scope pass. Search only relevant source/configuration directories and final artifacts; exclude `.git`, `.gradle`, and generated build caches unless inspecting a deliberate output.

## Evidence table

| Surface | Initial evidence | Completion evidence |
| --- | --- | --- |
| Toolchain | Gradle files, version catalogs, wrapper, runtime JDK | sync/build output and merged manifest |
| Edge-to-edge | base activities/themes, inset handlers, fixed spacers | focused tests plus screenshots/manual flows |
| Back | callbacks and old back/key overrides | state tests plus gesture/three-button flows |
| Large screens | manifest restrictions, layouts, window metrics | target device/window matrix |
| Jobs | work declarations and scheduling callers | tests, stop reasons, standby/device evidence |
| BLE | bond APIs, receivers, reconnect state machine | event/state tests and real devices |
| LAN | sockets, discovery, LAN URLs, hotspots | compat flag, permission, denial/recovery flows |
| Health | dependencies, permissions, rationale, data types | authorization and per-type read/write evidence |
| Intents | exported components and external inputs | negative tests and merged manifest |
| Media/text | picker, MediaStore, camera/share, locales | selected-photo and language/RTL flows |
| Native/16 KB | resolved dependencies and final `.so` list | ZIP, AAB, ELF, and 16 KB runtime evidence |
| Google Fit | dependencies, scopes, source/stored keys | migration tests or `NOT_APPLICABLE` proof |

## Targeted search groups

### Build and variants

```text
compileSdk | targetSdk | com.android.application | com.android.library
com.android.tools.build:gradle | distributionUrl | javaToolchains | jvmToolchain
productFlavors | buildTypes | applicationId | namespace | abiFilters
```

Confirm values may come from convention plugins, version catalogs, root extensions, environment properties, or CI—not only `app/build.gradle`.

### Window and layout

```text
windowOptOutEdgeToEdgeEnforcement | enableEdgeToEdge | WindowCompat
WindowInsets | WindowInsetsCompat | fitSystemWindows
statusBarHeight | navigationBarHeight | setDecorFitsSystemWindows
screenOrientation | resizeableActivity | minAspectRatio | maxAspectRatio
setRequestedOrientation | getRequestedOrientation | getRealMetrics
DisplayMetrics | smallestScreenWidthDp | sw600dp | WindowSizeClass
adjustPan | adjustResize | clipToPadding | onSizeChanged
```

Check base classes and exceptions. Count fixed orientation declarations, but inspect reachability and business need before changing them.

### Back navigation

```text
onBackPressed | KEYCODE_BACK | onKeyDown | onKeyUp
OnBackPressedDispatcher | OnBackPressedCallback | OnBackInvokedDispatcher
BackHandler | PredictiveBackHandler | enableOnBackInvokedCallback
WebView.canGoBack | Dialog.setCancelable
```

Write a state/event/result matrix for every special interception. Include gesture start, cancellation, completion, and three-button back.

### Work and platform scheduling

```text
PeriodicWorkRequest | enqueueUniquePeriodicWork | ExistingPeriodicWorkPolicy
JobScheduler | JobService | jobFinished | getStopReason
scheduleAtFixedRate | AlarmManager | DownloadManager
setImportantWhileForeground | foregroundServiceType | startForegroundService
android:priority | IntentFilter.setPriority
```

Do not mechanically replace scheduling policies. Prove whether a repeated enqueue should update configuration or restart work.

### Components and external input

```text
android:exported | intent-filter | provider | receiver | service
PendingIntent | FLAG_MUTABLE | FLAG_IMMUTABLE | getParcelableExtra
startActivity | startService | sendBroadcast | nested Intent
FileProvider | grantUriPermission | FLAG_GRANT_READ_URI_PERMISSION
removeLaunchSecurityProtection | intentMatchingFlags
```

For each exported entry, identify caller, accepted action/URI/MIME/extras, authentication/permission boundary, and rejection behavior.

### BLE and peripherals

```text
createBond | removeBond | ACTION_BOND_STATE_CHANGED
ACTION_KEY_MISSING | ACTION_ENCRYPTION_CHANGE
CompanionDeviceManager | RESULT_DISCOVERY_TIMEOUT | RESULT_USER_REJECTED
BluetoothGatt | reconnect | retry | unpair | forget
```

Minimum matrix columns: connection state, bond state, event, automatic action, user prompt, timeout, recovery, and OEM fallback.

### Local network

```text
Socket | ServerSocket | DatagramSocket | MulticastSocket
NsdManager | mDNS | SSDP | multicast | broadcast
http://192.168. | http://10. | http://172.16. | .local
WifiNetworkSpecifier | WifiNetworkSuggestion | NEARBY_WIFI_DEVICES
WebView | Cronet | OkHttp | native socket
```

Do not decide LAN applicability from URL literals alone. Device discovery and native/transitive libraries may hide access.

### Health, Fit, media, and accessibility

```text
HealthConnectClient | android.permission.health | BODY_SENSORS
BODY_SENSORS_BACKGROUND | READ_HEART_RATE | READ_HEALTH_DATA_IN_BACKGROUND
Google Fit | FitnessOptions | Fitness.get | fitness.activity
READ_MEDIA_VISUAL_USER_SELECTED | READ_MEDIA_IMAGES | PhotoPicker
MediaStore.getVersion | ACTION_PICK | PickVisualMedia | FileProvider
elegantTextHeight | announceForAccessibility | TYPE_ANNOUNCEMENT
monochrome | adaptive-icon
```

Health permission needs depend on actual APIs and data types. A write-only Health Connect integration does not automatically need sensor-read permissions.

### Native and final artifacts

```text
.so | jniLibs | externalNativeBuild | ndkVersion | abiFilters
System.loadLibrary | ReLinker | local AAR | local JAR
```

Inspect resolved AARs and final APK/AAB. For each delivered ABI record library path, ELF result, supplier/source ownership, runtime feature, and remediation status.

## Android 16-specific decision reminders

- Edge-to-edge and predictive back are target-36 behaviors; all-app changes must also be reviewed.
- `PROPERTY_COMPAT_ALLOW_RESTRICTED_RESIZABILITY` is a temporary Stage A escape hatch, not an adaptive-layout fix, and does not apply when targeting API 37.
- Android 16 local-network protection is exercised with the documented compat flow; future permission behavior must be rechecked before implementation.
- A single missing 16 KB-compatible delivered ABI blocks formal native acceptance. Supporting both 32-bit and 64-bit requires compatible native libraries for every ABI actually shipped.
- Reflection and third-party SDK behavior need graceful failure and supplier evidence; absence of a static crash does not prove OEM compatibility.
