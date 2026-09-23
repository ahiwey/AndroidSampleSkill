# Library and SDK preflight

Read before changing dependencies or SDK sources. A matching filename is not enough
to authorize replacement. Keep the current library when evidence does not require a change.

## Decision order

1. Identify the selected variant's **resolved** dependencies, local AAR/JAR inputs,
   SDK source modules and final shipped ABIs. Inventory Java-only JARs too; absence
   of native entries means no native fix is needed, not complete API-36 compatibility.
2. Run `python scripts/inspect-native.py <exact-archive> ...` from this skill for
   read-only hashes, embedded `classes.jar` hashes and native measurements. It reads
   direct archive entries only; inspect embedded archives/resolved inputs separately.
   Do not traverse the whole Gradle cache. Repeat on the new final APK/AAB after edits.
3. Match candidates against [library-catalog.json](library-catalog.json): original
   coordinate/version/SHA-256, minSdk, Java API/classes, original ABI set, STL/JNI
   dependencies, licenses and observed platform defect. A different hash/version is
   a new candidate to inspect, not permission to force the known patch.
4. Choose **KEEP**, **REPLACE**, **REBUILD_FROM_SOURCE**, **PATCH_SDK_SOURCE**, or
   **BLOCKED** with the exact reason. An identical supplier AAR is KEEP. Native build
   flags in the host app cannot repair prebuilt ELF files.
5. Before replacement, check for duplicate Maven/local declarations and transitive
   copies. Preserve package/signing/version/minSdk and ABI coverage. Adapt SDK patches
   to real symbols and call chains; never replace a whole private SDK module from a case.
6. Verify changed Java API/linkage, minSdk, final artifacts and the affected runtime
   features. Keep original/candidate hashes and evidence in the project's existing
   task report. Do not call a catalog entry universally compatible or Play-approved.

## ABI and delivery scope

- Default 16 KB ELF acceptance covers `arm64-v8a` / `x86_64`. Preserve delivered
  `armeabi-v7a` and other legacy ABIs at their existing supported baseline.
- ARMv7 `LOAD=4096` alone is normal inventory, not `MUST_FIX`, `BLOCKED`, a warning,
  a supplier request, or a repeated final-answer reminder. Do not ask for a waiver
  on each project. Only surface a real crash/linkage failure, ABI coverage regression,
  or an explicitly requested stricter ABI contract.
- Basic adaptation and full release readiness are different scopes. Default
  implementation should finish the requested baseline with proportional verification.
  Do not automatically expand it to Play Console review, full peripheral coverage or
  every foldable scenario. Preserve unverified results without claiming approval.
- `inspect-native.py --mode release` additionally checks 64-bit RELRO ends against
  the live official guidance. Default baseline output records RELRO measurements but
  does not use them as its LOAD gate. Known 64-bit risks stay in evidence and prevent
  claims of complete native/release readiness; do not quietly erase or label them fixed.
- ZIP alignment, AAB page-size metadata and runtime loading are separate checks.
  A static PASS or one tested ABI does not establish all-ABI runtime compatibility.

## Duktape 1.2.0 candidate

This case replaced **one AAR and no JAR**. The bundled candidate is at
`assets/libraries/duktape-android-1.2.0-16k.aar`; it is reusable only for the exact
cataloged original and an app with minSdk >= 26. Its Java `classes.jar` and all seven
ABI paths are preserved. The AAR includes source, provenance and licenses under
`META-INF/duktape-rebuild/` (Duktape engine MIT notice remains in its source).

The candidate passes LOAD alignment, and its x86_64 bridge was exercised on API 36
with 16 KB pages and compatibility mode disabled. Original ARM64/MIPS binaries were
retained. The ARM64 RELRO end remains unaligned and ARM64 16 KB runtime is unverified.
**Do not auto-select this candidate for complete release-readiness remediation.**
The `-16k` filename is historical; measured capabilities, not its name, govern reuse.

Use [reproduce-duktape-case.py](../scripts/reproduce-duktape-case.py) only to reproduce
this historical baseline. Explicit `--reproduce-case`, `--sdk-root`, `--original-aar`,
`--work-dir` and `--output` are required. Choose work/output under the target project,
never inside the installed skill. The script does not install SDKs or prove runtime.
It pins upstream commit and original AAR hash; source changes only add typed declarations
for two existing date hooks. Legacy ABI rebuilds in this recipe reproduce the old case,
**not** the default future ARMv7 requirement. For new defects, rebuild only affected
in-scope ABIs using an appropriate current toolchain and revalidate rather than
automatically running this case recipe.

## RTK and Java-only libraries

The recorded RTK 1.15.0 AAR matched the reference project's SHA exactly. It was **not
replaced**; its ARMv7 DSP stays at the existing 4 KB baseline. No private vendor AAR,
JAR or SDK source tree is bundled. Obtain authorized compatible supplier artifacts
only for a demonstrated in-scope defect. Do not copy unrelated RTK versions, strip
ABIs, suppress missing-class failures or patch binary headers to manufacture a pass.

Three app-local Google service stub classes were removed in this case only because
the official resolved dependencies already owned those exact FQCNs and the stubs
conflicted with R8. This was not a JAR upgrade. In another project, establish the
duplicate-class evidence and actual replacement API before removing any class.

## BLE SDK source recipe

Apply only when bonding/reconnect code exists and lacks equivalent key-loss handling.
Typical symbol aliases: `BleBaseControl`, `BleOperateManager`, `SppHandle`, device
receiver and application registration. Names are search leads, not required paths.

| State / event | Expected action |
| --- | --- |
| Current BLE/classic device, API 36 KEY_MISSING | Mark its normalized address for recovery; cancel scheduled retries; notify once |
| Same address repeated KEY_MISSING | Remain blocked without duplicate user notification |
| Unrelated device event | Leave the current device's recovery state unchanged |
| GATT failure precedes KEY_MISSING | Do not auto-remove the bond on API 36; avoid the callback/broadcast race |
| Reconnect, createBond or SPP start while marked | Stop that automatic attempt for the affected address |
| Successful encryption status AND encryption enabled | Clear only this address; do not clear on encryption failure |
| BOND_BONDED, or explicit system/user bond removal | Permit fresh pairing/recovery for that address |
| API < 36 | Preserve the existing platform behavior unless independently defective |

Reusable source: [BondRecoveryState.java](../assets/sdk/BondRecoveryState.java) contains the minimal pure-Java address state from the verified case. Adapt its package to the target SDK; reuse an existing equivalent class instead of adding a second state owner. It does not register receivers or patch call sites automatically.

Guard examples after mapping the actual SDK symbols:

```java
if (BondRecoveryState.needsRecovery(address)) return; // Automatic retry/pairing/SPP entry.
if (!rtkBindTag && Build.VERSION.SDK_INT < 36) {
    unBondedDevice(address); // Preserve old-platform behavior only.
}
```

Use the correct return value for each method. A receiver records key loss and cancels pending retries; guards alone are incomplete.

Implementation: use one owner for a thread-safe address set with `Locale.ROOT`
normalization; distinguish BLE and classic addresses. Register API-36 broadcasts
conditionally. Add guards to every *actual* automatic reconnect/pairing/SPP entry,
including already queued callbacks. Confirm the UI retains an explicit recovery path.
The previous implementation used memory-only state; check process recreation and OEM
event delivery for the target SDK instead of treating it as guaranteed persistence.
Preserve protocol bytes, retry timing outside recovery and existing success behavior.

Verify unrelated-address isolation, duplicate key loss, BLE/classic independence,
null/empty address handling and failure-before-broadcast ordering. Pure state tests
do not establish real peripheral re-pairing/OTA behavior. If equivalent protection
already exists, record KEEP and avoid double receivers or redundant guards.
