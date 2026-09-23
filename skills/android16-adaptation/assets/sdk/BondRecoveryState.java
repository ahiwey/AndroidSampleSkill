package com.oudmon.ble.base.bluetooth;

import java.util.Locale;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

/** Addresses awaiting explicit re-pairing or confirmed link encryption after key loss. */
public final class BondRecoveryState {
    private static final Set<String> missingKeys = ConcurrentHashMap.newKeySet();

    private BondRecoveryState() { }

    public static void onKeyMissing(String address) {
        if (address != null && !address.isEmpty()) missingKeys.add(address.toUpperCase(Locale.ROOT));
    }

    public static void onBondRestored(String address) {
        if (address != null) missingKeys.remove(address.toUpperCase(Locale.ROOT));
    }

    public static boolean needsRecovery(String address) {
        return address != null && missingKeys.contains(address.toUpperCase(Locale.ROOT));
    }
}
