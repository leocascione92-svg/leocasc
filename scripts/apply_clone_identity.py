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
