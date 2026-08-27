# Official Android 16 baseline

Last verified: 2026-08-17. Re-open these sources before making policy, deadline, or minimum-version claims.

## Toolchain and Play policy

- [Minimum AGP by API level](https://developer.android.com/build/releases/about-agp): API 36 requires AGP 8.9.1 or newer; API 36.1 has a different minimum.
- [AGP 8.9 release notes](https://developer.android.com/build/releases/agp-8-9-0-release-notes): Gradle 8.11.1 and JDK 17 compatibility details.
- [Set up the Android 16 SDK](https://developer.android.com/about/versions/16/setup-sdk): Android Studio and compile/target SDK setup.
- [Google Play target API requirements](https://support.google.com/googleplay/android-developer/answer/11926878?hl=en-AU): phone/tablet, Wear OS, TV, Automotive, and XR deadlines and exceptions.

As verified on the date above, Google Play requires phone/tablet new apps and app updates to target API 36 from 2026-08-31, with an extension path described by Play. Do not reuse this sentence after the verification date without checking the live policy.

## Android 16 behavior

- [Changes for apps targeting Android 16](https://developer.android.com/about/versions/16/behavior-changes-16): edge-to-edge, predictive back, large-screen restrictions, health permissions, BLE, safer intents, media, and local-network opt-in guidance.
- [Changes affecting all apps on Android 16](https://developer.android.com/about/versions/16/behavior-changes-all): JobScheduler quotas, ART, ordered broadcasts, accessibility, device form factors, and other compatibility surfaces.
- [Predictive back migration](https://developer.android.com/guide/navigation/custom-back/predictive-back-gesture)
- [Views edge-to-edge](https://developer.android.com/develop/ui/views/layout/edge-to-edge)
- [Compose insets](https://developer.android.com/develop/ui/compose/system/insets-ui)
- [Adaptive layouts](https://developer.android.com/develop/ui/compose/layouts/adaptive)
- [Local network permission migration](https://developer.android.com/privacy-and-security/local-network-permission)

## Packaging, native code, and health

- [Support 16 KB page sizes](https://developer.android.com/guide/practices/page-sizes)
- [Migrate from Google Fit to Health Connect](https://developer.android.com/health-and-fitness/health-connect/migration/fit)
- [Health Connect permissions](https://developer.android.com/health-and-fitness/guides/health-connect/plan/data-types)

## Source discipline

- Prefer primary Android Developers, Play Console Help, library release notes, and supplier release notes.
- Record the access date when a requirement can change.
- Distinguish a platform fact from an inference about the current project.
- Do not copy version numbers from another repository without checking compatibility and resolved dependencies.
