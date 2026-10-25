from pathlib import Path

# 1) Separate Android application id. Java package names intentionally stay original.
gradle = Path("upstream/app/build.gradle")
s = gradle.read_text(encoding="utf-8")
old = 'applicationId "eu.chainfire.holeylight"'
new = 'applicationId "eu.chainfire.holeylight.s24clone"'
if old not in s:
    raise SystemExit("applicationId insertion point not found")
gradle.write_text(s.replace(old, new, 1), encoding="utf-8")

# 2) Make the launcher/app label unmistakable.
strings = Path("upstream/app/src/main/res/values/strings.xml")
s = strings.read_text(encoding="utf-8")
old = '<string translatable="false" name="app_name">Holey Light</string>'
new = '<string translatable="false" name="app_name">Holey Light S24 Clone</string>'
if old not in s:
    raise SystemExit("app_name insertion point not found")
strings.write_text(s.replace(old, new, 1), encoding="utf-8")

# 3) Alarm action must follow the clone applicationId.
manifest = Path("upstream/app/src/main/AndroidManifest.xml")
s = manifest.read_text(encoding="utf-8")
old = '<action android:name="eu.chainfire.holeylight.ALARM" />'
new = '<action android:name="${applicationId}.ALARM" />'
if old not in s:
    raise SystemExit("Alarm action insertion point not found")
manifest.write_text(s.replace(old, new, 1), encoding="utf-8")

# 4) The AOD helper remains the original Chainfire helper package.
aod = Path("upstream/app/src/main/java/eu/chainfire/holeylight/misc/AODControl.java")
s = aod.read_text(encoding="utf-8")
needle = 'BuildConfig.APPLICATION_ID + ".aodhelper"'
count = s.count(needle)
if count < 2:
    raise SystemExit(f"Expected AOD helper references, found {count}")
s = s.replace(needle, '"eu.chainfire.holeylight.aodhelper"')
aod.write_text(s, encoding="utf-8")

# 5) Distinguish the adaptive launcher icon on modern Samsung devices.
icon_bg = Path("upstream/app/src/main/res/values/ic_launcher_background_jh.xml")
s = icon_bg.read_text(encoding="utf-8")
old = '<color name="ic_launcher_background_jh">#FFFFFF</color>'
new = '<color name="ic_launcher_background_jh">#1E88E5</color>'
if old not in s:
    raise SystemExit("launcher background insertion point not found")
icon_bg.write_text(s.replace(old, new, 1), encoding="utf-8")

print("Applied S24 clone identity patch")


# 6) Modern Android/S24: do not require a fake Companion Device association.
permissions = Path("upstream/app/src/main/java/eu/chainfire/holeylight/misc/Permissions.java")
t = permissions.read_text(encoding="utf-8")
old = '''        } else if (((CompanionDeviceManager)context.getSystemService(COMPANION_DEVICE_SERVICE)).getAssociations().size() == 0) {
            return Needed.COMPANION_DEVICE;
        } else if (ContextCompat.checkSelfPermission(context, Manifest.permission.READ_PHONE_STATE) != PackageManager.PERMISSION_GRANTED) {'''
new = '''        } else if (ContextCompat.checkSelfPermission(context, Manifest.permission.READ_PHONE_STATE) != PackageManager.PERMISSION_GRANTED) {'''
if old not in t:
    raise SystemExit("Companion-device requirement block not found")
permissions.write_text(t.replace(old, new, 1), encoding="utf-8")

# 7) Remove the no-longer-needed companion-device feature declaration.
manifest = Path("upstream/app/src/main/AndroidManifest.xml")
t = manifest.read_text(encoding="utf-8")
old = '''    <uses-feature android:name="android.software.companion_device_setup"/>\n\n'''
if old not in t:
    raise SystemExit("companion device feature declaration not found")
manifest.write_text(t.replace(old, "", 1), encoding="utf-8")

# 8) Permission wizard is now four real steps instead of five.
main = Path("upstream/app/src/main/java/eu/chainfire/holeylight/ui/MainActivity.java")
t = main.read_text(encoding="utf-8")
repls = {
    'getString(R.string.permission_required) + " 2/5"': 'getString(R.string.permission_required) + " 1/4"',
    'getString(R.string.permission_required) + " 3/5"': 'getString(R.string.permission_required) + " 2/4"',
    'getString(R.string.permission_required) + " 4/5"': 'getString(R.string.permission_required) + " 3/4"',
    'getString(R.string.permission_required) + " 5/5"': 'getString(R.string.permission_required) + " 4/4"',
}
for old, new in repls.items():
    if old not in t:
        raise SystemExit(f"permission wizard label not found: {old}")
    t = t.replace(old, new, 1)
main.write_text(t, encoding="utf-8")

print("Removed obsolete Companion Device pairing requirement")


# 9) Modern fallback when notification-channel inspection is denied without a
# Companion Device association. Keep notifications visible using their own
# accent color (or white) instead of dropping the whole batch.
listener = Path("upstream/app/src/main/java/eu/chainfire/holeylight/service/NotificationListenerService.java")
t = listener.read_text(encoding="utf-8")

old = '''                    List<NotificationChannel> chans = getNotificationChannels(sbn.getPackageName(), Process.myUserHandle());
                    for (NotificationChannel chan : chans) {'''

new = '''                    List<NotificationChannel> chans;
                    try {
                        chans = getNotificationChannels(sbn.getPackageName(), Process.myUserHandle());
                    } catch (SecurityException channelAccessDenied) {
                        chans = new ArrayList<>();
                        shouldShowLights = true;
                        c = ((not.color & 0x00FFFFFF) != 0)
                                ? (not.color | 0xFF000000)
                                : Color.WHITE;
                        cChan = c;
                        log("Channel access denied for %s; fallback color #%08X", sbn.getPackageName(), c);
                    }
                    for (NotificationChannel chan : chans) {'''

if old not in t:
    raise SystemExit("notification-channel lookup block not found")
t = t.replace(old, new, 1)

# The old outer catch was specifically masking the companion-association failure.
# Keep it as a safety net, but with the local fallback above it should no longer
# swallow ordinary notifications.
listener.write_text(t, encoding="utf-8")

# 10) Let Holey Light's own persistent test notification exercise AOD too.
tracker = Path("upstream/app/src/main/java/eu/chainfire/holeylight/service/NotificationTracker.java")
t = tracker.read_text(encoding="utf-8")
old = '''            boolean blockSelf = isSelf && !screenOn && !TestRunner.isRunning();'''
new = '''            boolean blockSelf = false; // S24 clone: allow the built-in test notification on AOD'''
if old not in t:
    raise SystemExit("self-notification AOD block not found")
tracker.write_text(t.replace(old, new, 1), encoding="utf-8")

print("Added no-companion notification color fallback and AOD self-test support")


# 11) Add a direct renderer diagnostic that bypasses NotificationListenerService.
main = Path("upstream/app/src/main/java/eu/chainfire/holeylight/ui/MainActivity.java")
t = main.read_text(encoding="utf-8")

needle = '''        MenuItem item = menu.add("");
        item.setShowAsAction(MenuItem.SHOW_AS_ACTION_ALWAYS);
        item.setActionView(layout);
        return true;'''

replacement = '''        MenuItem vortexTest = menu.add("TEST VORTEX DIRETTO");
        vortexTest.setShowAsAction(MenuItem.SHOW_AS_ACTION_NEVER);
        vortexTest.setOnMenuItemClickListener(clicked -> {
            eu.chainfire.holeylight.animation.Overlay overlay =
                    eu.chainfire.holeylight.animation.Overlay.getInstance();
            if (overlay == null) {
                android.widget.Toast.makeText(
                        MainActivity.this,
                        "Overlay NON inizializzato: AccessibilityService non collegato",
                        android.widget.Toast.LENGTH_LONG
                ).show();
            } else {
                overlay.show(
                        new int[] { 0xFFFFFFFF },
                        new android.graphics.drawable.Drawable[0],
                        true
                );
                android.widget.Toast.makeText(
                        MainActivity.this,
                        "Overlay diretto inviato: dovrebbe apparire il vortice bianco",
                        android.widget.Toast.LENGTH_LONG
                ).show();
            }
            return true;
        });

        MenuItem item = menu.add("");
        item.setShowAsAction(MenuItem.SHOW_AS_ACTION_ALWAYS);
        item.setActionView(layout);
        return true;'''

if needle not in t:
    raise SystemExit("options menu insertion point not found")
main.write_text(t.replace(needle, replacement, 1), encoding="utf-8")

print("Added direct vortex renderer diagnostic")


# 12) Fix accessibility detection when original Holey Light and clone coexist.
# The upstream fallback only searches for the Java service class name, so an
# enabled original installation can make the clone falsely believe its own
# accessibility service is enabled.
permissions = Path("upstream/app/src/main/java/eu/chainfire/holeylight/misc/Permissions.java")
t = permissions.read_text(encoding="utf-8")
old = '''                String name = AccessibilityService.class.getCanonicalName();
                if ((services != null) && (name != null) && (services.contains(name))) {
                    return accessibilityManager.isEnabled();
                }'''
new = '''                String name = AccessibilityService.class.getCanonicalName();
                String component = (name == null) ? null : (BuildConfig.APPLICATION_ID + "/" + name);
                if ((services != null) && (component != null) && services.contains(component)) {
                    return accessibilityManager.isEnabled();
                }'''
if old not in t:
    raise SystemExit("accessibility fallback block not found")
permissions.write_text(t.replace(old, new, 1), encoding="utf-8")

print("Fixed clone-vs-original accessibility service detection")
