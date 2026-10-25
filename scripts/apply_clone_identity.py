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


# 13) S24-specific vortex geometry defaults. These values are used even after
# Reset because they replace the generic device-spec fallback for this clone.
anim = Path("upstream/app/src/main/java/eu/chainfire/holeylight/animation/NotificationAnimation.java")
t = anim.read_text(encoding="utf-8")
repls = {
    "return settings.getDpAddScaleBase(spec.dpAddScaleBase);":
        "return settings.getDpAddScaleBase(-14.50f);",
    "return settings.getDpAddScaleHorizontal(spec.dpAddScaleHorizontal);":
        "return settings.getDpAddScaleHorizontal(0.00f);",
    "return settings.getDpShiftVertical(spec.dpShiftVertical);":
        "return settings.getDpShiftVertical(-2.00f);",
    "return settings.getDpShiftHorizontal(spec.dpShiftHorizontal);":
        "return settings.getDpShiftHorizontal(-4.00f);",
    "return settings.getDpAddThickness(0);":
        "return settings.getDpAddThickness(0.00f);",
}
for old, new in repls.items():
    if old not in t:
        raise SystemExit(f"S24 tuning getter not found: {old}")
    t = t.replace(old, new, 1)
anim.write_text(t, encoding="utf-8")

# 14) Clean promotional UI safely. Keep the legacy donation Preference objects
# alive because updatePrefs() still touches them, but hide the whole Chainfire
# category so nothing promotional is shown.
frag = Path("upstream/app/src/main/java/eu/chainfire/holeylight/ui/SettingsFragment.java")
t = frag.read_text(encoding="utf-8")

needle = '''        PreferenceCategory catChainfire = category(root, R.string.settings_category_chainfire_title, 0);'''
replacement_cat = '''        PreferenceCategory catChainfire = category(root, R.string.settings_category_chainfire_title, 0);
        catChainfire.setVisible(false);'''
if needle not in t:
    raise SystemExit("Chainfire category insertion point not found")
t = t.replace(needle, replacement_cat, 1)

# Make Samsung tips useful shortcuts instead of dead informational rows.
old = '''            pref(catTips, R.string.tips_samsung_fingerprint_title, 0, null, true, null).setSummary(Html.fromHtml(getString(R.string.tips_samsung_fingerprint_description)));
            pref(catTips, R.string.tips_samsung_battery_title, 0, null, true, null).setSummary(Html.fromHtml(getString(R.string.tips_samsung_battery_description)));'''

new = '''            pref(catTips, R.string.tips_samsung_fingerprint_title, 0, null, true, preference -> {
                try {
                    Intent i = new Intent(android.provider.Settings.ACTION_SECURITY_SETTINGS);
                    startActivity(i);
                } catch (Exception e) {
                    startActivity(new Intent(android.provider.Settings.ACTION_SETTINGS));
                }
                return true;
            }).setSummary(Html.fromHtml(getString(R.string.tips_samsung_fingerprint_description)));

            pref(catTips, R.string.tips_samsung_battery_title, 0, null, true, preference -> {
                try {
                    Intent i = new Intent("android.settings.BATTERY_SETTINGS");
                    startActivity(i);
                } catch (Exception e) {
                    startActivity(new Intent(android.provider.Settings.ACTION_SETTINGS));
                }
                return true;
            }).setSummary(Html.fromHtml(getString(R.string.tips_samsung_battery_description)));'''

if old not in t:
    raise SystemExit("Samsung tips block not found")
t = t.replace(old, new, 1)

# Upstream updatePrefs() can make the top donation preference visible again.
old = '''            if (activity != null) {
                boolean donateAtTop = activity.iapAvailable && settings.getPurchased().length == 0;
                int iSummary = activity.iapAvailable ? R.string.donate_description_iap : R.string.donate_description_paypal;
                boolean enabled = activity.iapAvailable;
                
                prefDonateTop.setSummary(iSummary);
                prefDonateTop.setEnabled(enabled);
                prefDonateTop.setVisible(donateAtTop);

                prefDonateBottom.setSummary(iSummary);
                prefDonateBottom.setEnabled(enabled);
                prefDonateBottom.setVisible(!donateAtTop);
            }'''

new = '''            if (activity != null) {
                if (prefDonateTop != null) prefDonateTop.setVisible(false);
                if (prefDonateBottom != null) prefDonateBottom.setVisible(false);
            }'''

if old not in t:
    raise SystemExit("donation visibility block not found")
t = t.replace(old, new, 1)

frag.write_text(t, encoding="utf-8")

# Keep billing code untouched for compatibility. The promotional category is hidden,
# so the user sees no donation/Play Store/Twitter entries.

print("Applied S24 defaults, actionable AOD shortcuts, and UI cleanup")


# 16) S24 AOD profiles + extra notification animation presets.
# Reuse the stable original renderer and sprite sheets; the new presets vary the
# original swirl/blink timing rather than introducing a second renderer.

# --- SpritePlayer modes backed by the existing stable sprite sheets ---
sprite = Path("upstream/app/src/main/java/eu/chainfire/holeylight/animation/SpritePlayer.java")
t = sprite.read_text(encoding="utf-8")

old = "public enum Mode { SWIRL, BLINK, SINGLE, TSP, TSP_HIDE }"
new = "public enum Mode { SWIRL, SWIRL_SLOW, SWIRL_FAST, BLINK, BLINK_SOFT, SINGLE, TSP, TSP_HIDE }"
if old not in t:
    raise SystemExit("SpritePlayer Mode enum not found")
t = t.replace(old, new, 1)

old = '''            switch (drawMode) {
                case SWIRL: return spriteSheetSwirl;
                case BLINK: return spriteSheetBlink;
                case SINGLE: return spriteSheetSingle;
            }'''
new = '''            switch (drawMode) {
                case SWIRL:
                case SWIRL_SLOW:
                case SWIRL_FAST:
                    return spriteSheetSwirl;
                case BLINK:
                case BLINK_SOFT:
                    return spriteSheetBlink;
                case SINGLE:
                    return spriteSheetSingle;
            }'''
if old not in t:
    raise SystemExit("SpritePlayer getSpriteSheet switch not found")
t = t.replace(old, new, 1)
sprite.write_text(t, encoding="utf-8")

# --- Settings knows how to persist the new presets ---
settings_file = Path("upstream/app/src/main/java/eu/chainfire/holeylight/misc/Settings.java")
t = settings_file.read_text(encoding="utf-8")
old = '''            new AnimationStyle("swirl", SpritePlayer.Mode.SWIRL, R.string.animation_style_swirl_title, R.string.animation_style_location_camera, 5.5f),
            new AnimationStyle("blink", SpritePlayer.Mode.BLINK, R.string.animation_style_blink_title, R.string.animation_style_location_camera, 3.5f),
            new AnimationStyle("pie", SpritePlayer.Mode.SINGLE, R.string.animation_style_single_title, R.string.animation_style_location_camera, 3.5f),
            new AnimationStyle("tsp", SpritePlayer.Mode.TSP, R.string.animation_style_tsp_title, R.string.animation_style_location_screen_center, -1f),'''
new = '''            new AnimationStyle("swirl", SpritePlayer.Mode.SWIRL, R.string.animation_style_swirl_title, R.string.animation_style_location_camera, 5.5f),
            new AnimationStyle("swirl_slow", SpritePlayer.Mode.SWIRL_SLOW, R.string.animation_style_swirl_slow_title, R.string.animation_style_location_camera, 5.5f),
            new AnimationStyle("swirl_fast", SpritePlayer.Mode.SWIRL_FAST, R.string.animation_style_swirl_fast_title, R.string.animation_style_location_camera, 5.5f),
            new AnimationStyle("blink_soft", SpritePlayer.Mode.BLINK_SOFT, R.string.animation_style_blink_soft_title, R.string.animation_style_location_camera, 3.5f),
            new AnimationStyle("blink", SpritePlayer.Mode.BLINK, R.string.animation_style_blink_title, R.string.animation_style_location_camera, 3.5f),
            new AnimationStyle("pie", SpritePlayer.Mode.SINGLE, R.string.animation_style_single_title, R.string.animation_style_location_camera, 3.5f),
            new AnimationStyle("tsp", SpritePlayer.Mode.TSP, R.string.animation_style_tsp_title, R.string.animation_style_location_screen_center, -1f),'''
if old not in t:
    raise SystemExit("Animation style table not found")
t = t.replace(old, new, 1)
settings_file.write_text(t, encoding="utf-8")

# --- Mode-specific speed multipliers; the user's tuning speed remains the base ---
anim = Path("upstream/app/src/main/java/eu/chainfire/holeylight/animation/NotificationAnimation.java")
t = anim.read_text(encoding="utf-8")
old = '''    public float getSpeedFactor() {
        return settings.getSpeedFactor();
    }'''
new = '''    public float getSpeedFactor() {
        float base = settings.getSpeedFactor();
        switch (mode) {
            case SWIRL_SLOW:
                return base * 0.65f;
            case SWIRL_FAST:
                return base * 1.55f;
            case BLINK_SOFT:
                return base * 0.60f;
            default:
                return base;
        }
    }'''
if old not in t:
    raise SystemExit("NotificationAnimation speed getter not found")
t = t.replace(old, new, 1)
anim.write_text(t, encoding="utf-8")

# --- New titles (fallback English + Italian) ---
for rel, strings in [
    ("upstream/app/src/main/res/values/strings.xml", [
        ("animation_style_swirl_slow_title", "Slow swirl"),
        ("animation_style_swirl_fast_title", "Fast swirl"),
        ("animation_style_blink_soft_title", "Soft pulse"),
    ]),
    ("upstream/app/src/main/res/values-it/strings.xml", [
        ("animation_style_swirl_slow_title", "Vortice lento"),
        ("animation_style_swirl_fast_title", "Vortice rapido"),
        ("animation_style_blink_soft_title", "Pulsazione morbida"),
    ]),
]:
    p = Path(rel)
    txt = p.read_text(encoding="utf-8")
    if "animation_style_swirl_slow_title" not in txt:
        block = "\n" + "\n".join([f'    <string name="{k}">{v}</string>' for k, v in strings]) + "\n"
        txt = txt.replace("</resources>", block + "</resources>")
        p.write_text(txt, encoding="utf-8")

# --- Settings UI: real S24 AOD profiles and expanded animation chooser ---
frag = Path("upstream/app/src/main/java/eu/chainfire/holeylight/ui/SettingsFragment.java")
t = frag.read_text(encoding="utf-8")

old = '''            CharSequence[] options = new CharSequence[screenOff ? 5 : 4];
            options[0] = Html.fromHtml(String.format(Locale.ENGLISH, Settings.AnimationStyle.HTML_FORMAT, getString(R.string.operation_mode_disabled_title), getString(R.string.operation_mode_disabled_description)));
            options[1] = settings.getAnimationStyle(SpritePlayer.Mode.SWIRL).getHtmlDisplay(getContext(), charging);
            options[2] = settings.getAnimationStyle(SpritePlayer.Mode.BLINK).getHtmlDisplay(getContext(), charging);
            options[3] = settings.getAnimationStyle(SpritePlayer.Mode.SINGLE).getHtmlDisplay(getContext(), charging);
            if (screenOff) {
                options[4] = settings.getAnimationStyle(SpritePlayer.Mode.TSP).getHtmlDisplay(getContext(), charging);
            }'''
new = '''            CharSequence[] options = new CharSequence[screenOff ? 8 : 7];
            options[0] = Html.fromHtml(String.format(Locale.ENGLISH, Settings.AnimationStyle.HTML_FORMAT, getString(R.string.operation_mode_disabled_title), getString(R.string.operation_mode_disabled_description)));
            options[1] = settings.getAnimationStyle(SpritePlayer.Mode.SWIRL).getHtmlDisplay(getContext(), charging);
            options[2] = settings.getAnimationStyle(SpritePlayer.Mode.SWIRL_SLOW).getHtmlDisplay(getContext(), charging);
            options[3] = settings.getAnimationStyle(SpritePlayer.Mode.SWIRL_FAST).getHtmlDisplay(getContext(), charging);
            options[4] = settings.getAnimationStyle(SpritePlayer.Mode.BLINK_SOFT).getHtmlDisplay(getContext(), charging);
            options[5] = settings.getAnimationStyle(SpritePlayer.Mode.BLINK).getHtmlDisplay(getContext(), charging);
            options[6] = settings.getAnimationStyle(SpritePlayer.Mode.SINGLE).getHtmlDisplay(getContext(), charging);
            if (screenOff) {
                options[7] = settings.getAnimationStyle(SpritePlayer.Mode.TSP).getHtmlDisplay(getContext(), charging);
            }'''
if old not in t:
    raise SystemExit("operation options block not found")
t = t.replace(old, new, 1)

old = '''                                case 1:
                                    settings.setAnimationMode(mode, SpritePlayer.Mode.SWIRL);
                                    break;
                                case 2:
                                    settings.setAnimationMode(mode, SpritePlayer.Mode.BLINK);
                                    break;
                                case 3:
                                    settings.setAnimationMode(mode, SpritePlayer.Mode.SINGLE);
                                    break;
                                case 4:
                                    settings.setAnimationMode(mode, SpritePlayer.Mode.TSP);
                                    break;'''
new = '''                                case 1:
                                    settings.setAnimationMode(mode, SpritePlayer.Mode.SWIRL);
                                    break;
                                case 2:
                                    settings.setAnimationMode(mode, SpritePlayer.Mode.SWIRL_SLOW);
                                    break;
                                case 3:
                                    settings.setAnimationMode(mode, SpritePlayer.Mode.SWIRL_FAST);
                                    break;
                                case 4:
                                    settings.setAnimationMode(mode, SpritePlayer.Mode.BLINK_SOFT);
                                    break;
                                case 5:
                                    settings.setAnimationMode(mode, SpritePlayer.Mode.BLINK);
                                    break;
                                case 6:
                                    settings.setAnimationMode(mode, SpritePlayer.Mode.SINGLE);
                                    break;
                                case 7:
                                    settings.setAnimationMode(mode, SpritePlayer.Mode.TSP);
                                    break;'''
if old not in t:
    raise SystemExit("operation switch block not found")
t = t.replace(old, new, 1)

# Insert S24 profile selector immediately after the legacy Hide AOD preference.
anchor = '''        prefHideAOD.setOnPreferenceClickListener(preference -> {
            String FORMAT = "%s<br><small>%s</small>";
            (new AlertDialog.Builder(getContext()))
                    .setTitle(preference.getTitle())
                    .setItems(new CharSequence[] {
                            getString(R.string.disabled),
                            Html.fromHtml(String.format(Locale.ENGLISH, FORMAT, getString(R.string.hide_aod_full_title), getString(R.string.hide_aod_full_description))),
                            Html.fromHtml(String.format(Locale.ENGLISH, FORMAT, getString(R.string.hide_aod_partial_title), getString(R.string.hide_aod_partial_description))),
                    }, (dialog, which) -> {
                        switch (which) {
                            case 0:
                                settings.setHideAOD(false);
                                break;
                            case 1:
                                settings.setHideAOD(true, true);
                                break;
                            case 2:
                                settings.setHideAOD(true, false);
                                break;
                        }
                    })
                    .setNegativeButton(android.R.string.cancel, null)
                    .show();
            return false;
        });'''
if anchor not in t:
    raise SystemExit("Hide AOD block not found")

profile = anchor + '''

        // S24-friendly profiles: they map directly to Holey Light's existing
        // partial/full AOD masking behavior. Samsung still renders fingerprint
        // and battery information in the exposed lower area.
        PreferenceCategory catS24AOD = category(root, 0, 0);
        catS24AOD.setTitle("AOD S24");

        Preference prefS24Profile = pref(catS24AOD, 0, 0, null, true, null);
        prefS24Profile.setTitle("Modalità AOD");

        Runnable refreshS24Profile = () -> {
            String summary;
            if (!settings.isHideAOD()) {
                summary = "AOD Samsung completo";
            } else if (settings.isHideAODFully()) {
                summary = "Solo vortice";
            } else if (!settings.isShowAODClock()) {
                summary = "Impronta + batteria";
            } else {
                summary = "Personalizzato";
            }
            prefS24Profile.setSummary(summary);
        };

        prefS24Profile.setOnPreferenceClickListener(preference -> {
            (new AlertDialog.Builder(getContext()))
                    .setTitle("Modalità AOD S24")
                    .setItems(new CharSequence[] {
                            "AOD Samsung completo\nOrologio e contenuti One UI visibili",
                            "Impronta + batteria\nNiente orologio; lascia visibile la fascia inferiore",
                            "Solo vortice\nAOD oscurato completamente",
                            "Personalizzato\nUsa le opzioni avanzate già presenti"
                    }, (dialog, which) -> {
                        switch (which) {
                            case 0:
                                settings.setHideAOD(false, false);
                                settings.setShowAODClock(false);
                                break;
                            case 1:
                                settings.setHideAOD(true, false);
                                settings.setShowAODClock(false);
                                break;
                            case 2:
                                settings.setHideAOD(true, true);
                                settings.setShowAODClock(false);
                                break;
                            case 3:
                                prefHideAOD.performClick();
                                break;
                        }
                        refreshS24Profile.run();
                    })
                    .setNegativeButton(android.R.string.cancel, null)
                    .show();
            return true;
        });
        refreshS24Profile.run();

        prefHideAOD.setTitle("Mascheramento AOD (avanzato)");'''
t = t.replace(anchor, profile, 1)

# Rename the old clock toggle so it reads as an advanced/custom control.
old = '''        prefUnholeyClock = check(catAnimation, R.string.settings_animation_unholey_light_show_clock_title, 0, Settings.AOD_SHOW_CLOCK, Settings.AOD_SHOW_CLOCK_DEFAULT, true);'''
new = '''        prefUnholeyClock = check(catAnimation, R.string.settings_animation_unholey_light_show_clock_title, 0, Settings.AOD_SHOW_CLOCK, Settings.AOD_SHOW_CLOCK_DEFAULT, true);
        prefUnholeyClock.setTitle("Mostra orologio AOD (avanzato)");'''
if old not in t:
    raise SystemExit("AOD clock preference not found")
t = t.replace(old, new, 1)

# Remove the old Samsung Tips block entirely: profiles above replace it.
start = t.find("        if (Manufacturer.isSamsung()) {\n            PreferenceCategory catTips = category(root, R.string.settings_category_tips, 0);")
if start != -1:
    end = t.find("\n\n        updatePrefs(null, true);", start)
    if end == -1:
        raise SystemExit("Samsung tips block end not found")
    t = t[:start] + t[end:]

frag.write_text(t, encoding="utf-8")

print("Added S24 AOD profiles and extra animation presets")
