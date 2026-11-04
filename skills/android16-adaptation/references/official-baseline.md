# Official Android 16 baseline

Source verification is per item: the toolchain/general baseline was checked 2026-08-17; Play target API, the Android-16-target behavior page and the 16 KB guide were re-opened 2026-10-09. Other links are pointers, not claims of a new check. Re-open relevant sources before making policy, deadline, or minimum-version claims.

## Toolchain and Play policy

- [Minimum AGP by API level](https://developer.android.com/build/releases/about-agp): API 36 requires AGP 8.9.1 or newer; API 36.1 has a different minimum.
- [AGP 8.9 release notes](https://developer.android.com/build/releases/agp-8-9-0-release-notes): Gradle 8.11.1 and JDK 17 compatibility details.
- [Set up the Android 16 SDK](https://developer.android.com/about/versions/16/setup-sdk): Android Studio and compile/target SDK setup.
- [Google Play target API requirements](https://support.google.com/googleplay/android-developer/answer/11926878?hl=en-AU): phone/tablet, Wear OS, TV, Automotive, and XR deadlines and exceptions.

As rechecked 2026-10-09, Google Play requires phone/tablet new apps and app updates to target API 36 from 2026-08-31, with an extension path to 2026-11-01 described by Play. Existing-app availability is a separate API-35 requirement. Recheck the live policy and any app-specific Console extension before using these dates in a submission decision.

## Android 16 behavior

- [Changes for apps targeting Android 16](https://developer.android.com/about/versions/16/behavior-changes-16): edge-to-edge, predictive back, large-screen restrictions, health permissions, BLE, safer intents, media, and local-network opt-in guidance.
- [Changes affecting all apps on Android 16](https://developer.android.com/about/versions/16/behavior-changes-all): JobScheduler quotas, ART, ordered broadcasts, accessibility, device form factors, and other compatibility surfaces.
- [Predictive back migration](https://developer.android.com/guide/navigation/custom-back/predictive-back-gesture)
- [Views edge-to-edge](https://developer.android.com/develop/ui/views/layout/edge-to-edge)
- [Compose insets](https://developer.android.com/develop/ui/compose/system/insets-ui)
- [Adaptive layouts](https://developer.android.com/develop/ui/compose/layouts/adaptive)
- [Local network permission migration](https://developer.android.com/privacy-and-security/local-network-permission)

## Packaging, native code, and health

- [Support 16 KB page sizes](https://developer.android.com/guide/practices/page-sizes), rechecked 2026-10-09: Play requirement concerns 64-bit devices for apps targeting API 35 or higher; the current guide says unsupported app updates cannot be released starting **2027-02-01**. The guide names arm64-v8a/x86_64 for ELF checks and includes RELRO in native verification. Do not demand ARMv7 16 KB alignment as a default. This is a dated statement of the guide, not proof of any app's Console eligibility, an individual extension, or runtime safety. A future submission deadline does not make an incompatible library compatible; inspect known native faults and recheck the live requirement at release time.
- [Migrate from Google Fit to Health Connect](https://developer.android.com/health-and-fitness/health-connect/migration/fit)
- [Health Connect permissions](https://developer.android.com/health-and-fitness/guides/health-connect/plan/data-types)

## Source discipline

- Prefer primary Android Developers, Play Console Help, library release notes, and supplier release notes.
- Record the access date when a requirement can change.
- Distinguish a platform fact from an inference about the current project.
- Do not copy version numbers from another repository without checking compatibility and resolved dependencies.
