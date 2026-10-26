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
                            "AOD Samsung completo\\nOrologio e contenuti One UI visibili",
                            "Impronta + batteria\\nNiente orologio; lascia visibile la fascia inferiore",
                            "Solo vortice\\nAOD oscurato completamente",
                            "Personalizzato\\nUsa le opzioni avanzate già presenti"
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


# 17) Make AOD profiles behaviorally distinct and expose animation presets clearly.

# --- Draw our own battery percentage/bar in the partial AOD profile ---
sprite = Path("upstream/app/src/main/java/eu/chainfire/holeylight/animation/SpritePlayer.java")
t = sprite.read_text(encoding="utf-8")

needle = '''    private final Paint paintTspTransparentDebug = new Paint();
    private final float dpToPx;'''
replacement = '''    private final Paint paintTspTransparentDebug = new Paint();
    private final Paint paintBattery = new Paint();
    private final Paint paintBatteryTrack = new Paint();
    private volatile boolean showBatteryStatus = false;
    private final float dpToPx;'''
if needle not in t:
    raise SystemExit("SpritePlayer paint field anchor not found")
t = t.replace(needle, replacement, 1)

needle = '''        paintTspTransparentDebug.setColor(0x4000FF00);

        handlerRender.post(() -> {'''
replacement = '''        paintTspTransparentDebug.setColor(0x4000FF00);

        paintBattery.setAntiAlias(true);
        paintBattery.setColor(Color.WHITE);
        paintBattery.setTextAlign(Paint.Align.CENTER);
        paintBatteryTrack.setAntiAlias(true);
        paintBatteryTrack.setColor(0x55FFFFFF);

        handlerRender.post(() -> {'''
if needle not in t:
    raise SystemExit("SpritePlayer paint init anchor not found")
t = t.replace(needle, replacement, 1)

needle = '''        if (Settings.DEBUG_OVERLAY) canvas.drawColor(0x80808080);
        if (isTSPMode()) {'''
replacement = '''        if (Settings.DEBUG_OVERLAY) canvas.drawColor(0x80808080);

        // S24 partial-AOD profile: Holey Light owns the battery indicator so it
        // is available even when Samsung's "show charging information" is off.
        if ((drawMode == Mode.TSP_HIDE) && showBatteryStatus) {
            android.os.BatteryManager bm = (android.os.BatteryManager)getContext().getSystemService(Context.BATTERY_SERVICE);
            int level = bm == null ? -1 : bm.getIntProperty(android.os.BatteryManager.BATTERY_PROPERTY_CAPACITY);
            if (level >= 0 && level <= 100) {
                float cx = this.width / 2f;
                float textY = this.height - (18f * dpToPx);
                float barY = this.height - (10f * dpToPx);
                float barW = Math.min(this.width * 0.42f, 180f * dpToPx);
                float barH = 3f * dpToPx;
                float left = cx - barW / 2f;
                float right = cx + barW / 2f;

                paintBattery.setTextSize(11f * dpToPx);
                paintBattery.setStyle(Paint.Style.FILL);
                canvas.drawText(level + "%", cx, textY, paintBattery);

                canvas.drawRoundRect(left, barY, right, barY + barH, barH / 2f, barH / 2f, paintBatteryTrack);
                canvas.drawRoundRect(left, barY, left + (barW * level / 100f), barY + barH, barH / 2f, barH / 2f, paintBattery);
            }
        }

        if (isTSPMode()) {'''
if needle not in t:
    raise SystemExit("SpritePlayer render anchor not found")
t = t.replace(needle, replacement, 1)

needle = '''    public void setDrawBackground(boolean drawBackground) {
        synchronized (sync) {'''
replacement = '''    public void setShowBatteryStatus(boolean value) {
        synchronized (sync) {
            if (showBatteryStatus != value) {
                showBatteryStatus = value;
                surfaceInvalidated = true;
                if (draw) callNextFrame(true);
            }
        }
    }

    public void setDrawBackground(boolean drawBackground) {
        synchronized (sync) {'''
if needle not in t:
    raise SystemExit("SpritePlayer setter anchor not found")
t = t.replace(needle, replacement, 1)
sprite.write_text(t, encoding="utf-8")

anim = Path("upstream/app/src/main/java/eu/chainfire/holeylight/animation/NotificationAnimation.java")
t = anim.read_text(encoding="utf-8")
needle = '''                spritePlayer.setDrawBackground(hideAOD);

                // Get going'''
replacement = '''                spritePlayer.setDrawBackground(hideAOD);
                spritePlayer.setShowBatteryStatus(hideAOD && !hideAODFully);

                // Get going'''
if needle not in t:
    raise SystemExit("NotificationAnimation battery status anchor not found")
t = t.replace(needle, replacement, 1)
anim.write_text(t, encoding="utf-8")

# --- Simplify/clarify the S24 profile selector ---
frag = Path("upstream/app/src/main/java/eu/chainfire/holeylight/ui/SettingsFragment.java")
t = frag.read_text(encoding="utf-8")

old = '''            if (!settings.isHideAOD()) {
                summary = "AOD Samsung completo";
            } else if (settings.isHideAODFully()) {
                summary = "Solo vortice";
            } else if (!settings.isShowAODClock()) {
                summary = "Impronta + batteria";
            } else {
                summary = "Personalizzato";
            }'''
new = '''            if (!settings.isHideAOD()) {
                summary = "AOD Samsung completo";
            } else if (settings.isHideAODFully()) {
                summary = "Vortice minimale";
            } else {
                summary = "Impronta + batteria";
            }'''
if old not in t:
    raise SystemExit("S24 profile summary block not found")
t = t.replace(old, new, 1)

old = '''                    .setItems(new CharSequence[] {
                            "AOD Samsung completo\\nOrologio e contenuti One UI visibili",
                            "Impronta + batteria\\nNiente orologio; lascia visibile la fascia inferiore",
                            "Solo vortice\\nAOD oscurato completamente",
                            "Personalizzato\\nUsa le opzioni avanzate già presenti"
                    }, (dialog, which) -> {'''
new = '''                    .setItems(new CharSequence[] {
                            "AOD Samsung completo\\nOrologio e contenuti One UI visibili",
                            "Impronta + batteria\\nSchermo nero, impronta Samsung e batteria disegnata da Holey Light",
                            "Vortice minimale\\nSchermo nero e vortice; l'impronta può restare se One UI è impostata per mostrarla"
                    }, (dialog, which) -> {'''
if old not in t:
    raise SystemExit("S24 profile items block not found")
t = t.replace(old, new, 1)

old = '''                            case 2:
                                settings.setHideAOD(true, true);
                                settings.setShowAODClock(false);
                                break;
                            case 3:
                                prefHideAOD.performClick();
                                break;'''
new = '''                            case 2:
                                settings.setHideAOD(true, true);
                                settings.setShowAODClock(false);
                                break;'''
if old not in t:
    raise SystemExit("S24 profile switch tail not found")
t = t.replace(old, new, 1)

# Hide the old advanced mask/clock controls from the normal S24 UI. They remain
# in code/state for compatibility but no longer confuse the profile selector.
needle = '''        prefHideAOD.setTitle("Mascheramento AOD (avanzato)");'''
replacement = '''        prefHideAOD.setTitle("Mascheramento AOD (avanzato)");
        prefHideAOD.setVisible(false);'''
if needle not in t:
    raise SystemExit("advanced mask title anchor not found")
t = t.replace(needle, replacement, 1)

needle = '''        prefUnholeyClock.setTitle("Mostra orologio AOD (avanzato)");'''
replacement = '''        prefUnholeyClock.setTitle("Mostra orologio AOD (avanzato)");
        prefUnholeyClock.setVisible(false);'''
if needle not in t:
    raise SystemExit("advanced clock title anchor not found")
t = t.replace(needle, replacement, 1)

# --- Clear animation pickers in the Animation section ---
anchor = '''        PreferenceCategory catAnimation = category(root, R.string.settings_category_animation_title, 0);'''
if anchor not in t:
    raise SystemExit("animation category anchor not found")

insert = anchor + '''

        Preference prefEffectScreenOn = pref(catAnimation, 0, 0, null, true, null);
        prefEffectScreenOn.setTitle("Effetto a schermo acceso");
        prefEffectScreenOn.setSummary(getString(settings.getAnimationStyle(settings.getAnimationMode(Settings.SCREEN_ON_BATTERY)).title));
        prefEffectScreenOn.setOnPreferenceClickListener(preference -> {
            final SpritePlayer.Mode[] modes = new SpritePlayer.Mode[] {
                    SpritePlayer.Mode.SWIRL,
                    SpritePlayer.Mode.SWIRL_SLOW,
                    SpritePlayer.Mode.SWIRL_FAST,
                    SpritePlayer.Mode.BLINK_SOFT,
                    SpritePlayer.Mode.BLINK,
                    SpritePlayer.Mode.SINGLE
            };
            CharSequence[] labels = new CharSequence[modes.length];
            for (int i = 0; i < modes.length; i++) {
                labels[i] = getString(settings.getAnimationStyle(modes[i]).title);
            }
            (new AlertDialog.Builder(getContext()))
                    .setTitle("Effetto a schermo acceso")
                    .setItems(labels, (dialog, which) -> {
                        SpritePlayer.Mode selected = modes[which];
                        settings.setAnimationMode(Settings.SCREEN_ON_BATTERY, selected);
                        settings.setAnimationMode(Settings.SCREEN_ON_CHARGING, selected);
                        preference.setSummary(getString(settings.getAnimationStyle(selected).title));
                    })
                    .setNegativeButton(android.R.string.cancel, null)
                    .show();
            return true;
        });

        Preference prefEffectScreenOff = pref(catAnimation, 0, 0, null, true, null);
        prefEffectScreenOff.setTitle("Effetto a schermo spento");
        prefEffectScreenOff.setSummary(getString(settings.getAnimationStyle(settings.getAnimationMode(Settings.SCREEN_OFF_BATTERY)).title));
        prefEffectScreenOff.setOnPreferenceClickListener(preference -> {
            final SpritePlayer.Mode[] modes = new SpritePlayer.Mode[] {
                    SpritePlayer.Mode.SWIRL,
                    SpritePlayer.Mode.SWIRL_SLOW,
                    SpritePlayer.Mode.SWIRL_FAST,
                    SpritePlayer.Mode.BLINK_SOFT,
                    SpritePlayer.Mode.BLINK,
                    SpritePlayer.Mode.SINGLE,
                    SpritePlayer.Mode.TSP
            };
            CharSequence[] labels = new CharSequence[modes.length];
            for (int i = 0; i < modes.length; i++) {
                labels[i] = getString(settings.getAnimationStyle(modes[i]).title);
            }
            (new AlertDialog.Builder(getContext()))
                    .setTitle("Effetto a schermo spento")
                    .setItems(labels, (dialog, which) -> {
                        SpritePlayer.Mode selected = modes[which];
                        settings.setAnimationMode(Settings.SCREEN_OFF_BATTERY, selected);
                        settings.setAnimationMode(Settings.SCREEN_OFF_CHARGING, selected);
                        preference.setSummary(getString(settings.getAnimationStyle(selected).title));
                    })
                    .setNegativeButton(android.R.string.cancel, null)
                    .show();
            return true;
        });'''
t = t.replace(anchor, insert, 1)

frag.write_text(t, encoding="utf-8")

print("Clarified AOD profiles, added in-overlay battery status, and exposed effect pickers")


# 18) Procedural S24 effects: Comet, Breath, Orbit + live preview.
sprite = Path("upstream/app/src/main/java/eu/chainfire/holeylight/animation/SpritePlayer.java")
t = sprite.read_text(encoding="utf-8")

old = "public enum Mode { SWIRL, SWIRL_SLOW, SWIRL_FAST, BLINK, BLINK_SOFT, SINGLE, TSP, TSP_HIDE }"
new = "public enum Mode { SWIRL, SWIRL_SLOW, SWIRL_FAST, COMET, BREATH, ORBIT, BLINK, BLINK_SOFT, SINGLE, TSP, TSP_HIDE }"
if old not in t:
    raise SystemExit("procedural Mode enum anchor not found")
t = t.replace(old, new, 1)

needle = '''    private final Paint paintBattery = new Paint();
    private final Paint paintBatteryTrack = new Paint();
    private volatile boolean showBatteryStatus = false;'''
replacement = '''    private final Paint paintBattery = new Paint();
    private final Paint paintBatteryTrack = new Paint();
    private final Paint paintProcedural = new Paint();
    private volatile boolean showBatteryStatus = false;'''
if needle not in t:
    raise SystemExit("procedural paint field anchor not found")
t = t.replace(needle, replacement, 1)

needle = '''        paintBatteryTrack.setAntiAlias(true);
        paintBatteryTrack.setColor(0x55FFFFFF);

        handlerRender.post(() -> {'''
replacement = '''        paintBatteryTrack.setAntiAlias(true);
        paintBatteryTrack.setColor(0x55FFFFFF);

        paintProcedural.setAntiAlias(true);
        paintProcedural.setDither(true);
        paintProcedural.setStrokeCap(Paint.Cap.ROUND);

        handlerRender.post(() -> {'''
if needle not in t:
    raise SystemExit("procedural paint init anchor not found")
t = t.replace(needle, replacement, 1)

needle = '''    private final Choreographer.FrameCallback frameCallback = new Choreographer.FrameCallback() {'''
method = '''    private void renderProceduralFrame(Canvas canvas, long diff) {
        if (drawBackground) {
            canvas.drawColor(Color.BLACK, PorterDuff.Mode.SRC);
        } else if (!canvas.isHardwareAccelerated()) {
            canvas.drawColor(Color.TRANSPARENT, PorterDuff.Mode.CLEAR);
        }

        int[] activeColors = ((colors != null) && (colors.length > 0)) ? colors : new int[] { Color.WHITE };
        float cx = width / 2f;
        float cy = height / 2f;
        float radius = Math.max(2f * dpToPx, Math.min(width, height) / 2f - (4f * dpToPx));
        float safeSpeed = Math.max(0.15f, speed);

        paintProcedural.setShader(null);
        paintProcedural.setColorFilter(null);

        if (drawMode == Mode.COMET) {
            float cycle = 1700f / safeSpeed;
            float phase = ((diff % (long)Math.max(1f, cycle)) / cycle) * 360f;
            paintProcedural.setStyle(Paint.Style.STROKE);
            paintProcedural.setStrokeWidth(3.2f * dpToPx);
            for (int i = 0; i < 9; i++) {
                int alpha = Math.max(18, 255 - (i * 27));
                int c = activeColors[i % activeColors.length];
                paintProcedural.setColor((c & 0x00FFFFFF) | (alpha << 24));
                float start = phase - (i * 8f);
                canvas.drawArc(cx - radius, cy - radius, cx + radius, cy + radius, start, 20f, false, paintProcedural);
            }
            double head = Math.toRadians(phase + 20f);
            paintProcedural.setStyle(Paint.Style.FILL);
            paintProcedural.setColor(activeColors[0]);
            canvas.drawCircle(
                    cx + ((float)Math.cos(head) * radius),
                    cy + ((float)Math.sin(head) * radius),
                    3.4f * dpToPx,
                    paintProcedural
            );
        } else if (drawMode == Mode.BREATH) {
            float cycle = 2300f / safeSpeed;
            float part = (diff % (long)Math.max(1f, cycle)) / cycle;
            float wave = 0.5f + 0.5f * (float)Math.sin((part * Math.PI * 2.0) - (Math.PI / 2.0));
            int alpha = 60 + Math.round(195f * wave);
            float breatheRadius = radius - ((1f - wave) * 2.5f * dpToPx);
            paintProcedural.setStyle(Paint.Style.STROKE);
            paintProcedural.setStrokeWidth((2.0f + (3.4f * wave)) * dpToPx);
            int c = activeColors[0];
            paintProcedural.setColor((c & 0x00FFFFFF) | (alpha << 24));
            canvas.drawCircle(cx, cy, breatheRadius, paintProcedural);
        } else if (drawMode == Mode.ORBIT) {
            float cycle = 1850f / safeSpeed;
            float phase = ((diff % (long)Math.max(1f, cycle)) / cycle) * 360f;
            paintProcedural.setStyle(Paint.Style.FILL);
            final int dots = 4;
            for (int i = 0; i < dots; i++) {
                float angle = phase + ((360f / dots) * i);
                double rad = Math.toRadians(angle);
                int c = activeColors[i % activeColors.length];
                int alpha = 255 - (i * 35);
                paintProcedural.setColor((c & 0x00FFFFFF) | (alpha << 24));
                float dotR = (i == 0 ? 3.8f : 2.7f) * dpToPx;
                canvas.drawCircle(
                        cx + ((float)Math.cos(rad) * radius),
                        cy + ((float)Math.sin(rad) * radius),
                        dotR,
                        paintProcedural
                );
            }
        }
    }

''' + needle
if needle not in t:
    raise SystemExit("frame callback anchor not found")
t = t.replace(needle, method, 1)

needle = '''                    if (isTSPMode()) {
                        boolean draw;'''
# leave TSP start unchanged; insert procedural branch before spriteSheet-null branch later.
if needle not in t:
    raise SystemExit("TSP frame branch anchor not found")

needle = '''                    } else if (spriteSheet == null) { // still loading'''
replacement = '''                    } else if (isProceduralMode()) {
                        boolean doDraw = true;
                        if (onAnimationListener != null) {
                            doDraw = onAnimationListener.onAnimationFrameStart(true);
                        }
                        if (doDraw) {
                            Canvas canvas = surfaceView.getHolder().lockCanvas();
                            if (canvas != null) {
                                try {
                                    renderProceduralFrame(canvas, diff);
                                } finally {
                                    try {
                                        surfaceView.getHolder().unlockCanvasAndPost(canvas);
                                    } catch (IllegalStateException e) {
                                        // no action
                                    }
                                }
                            }
                        }
                        if (onAnimationListener != null) {
                            onAnimationListener.onAnimationFrameEnd(doDraw);
                        }
                    } else if (spriteSheet == null) { // still loading'''
if needle not in t:
    raise SystemExit("procedural frame insertion anchor not found")
t = t.replace(needle, replacement, 1)

old = '''            if (wanted && ((getSpriteSheet() != null) || (spriteSheetLoading > 0) || isTSPMode()) && (getWindowVisibility() == View.VISIBLE) && (getVisibility() == View.VISIBLE)) {'''
new = '''            if (wanted && ((getSpriteSheet() != null) || (spriteSheetLoading > 0) || isTSPMode() || isProceduralMode()) && (getWindowVisibility() == View.VISIBLE) && (getVisibility() == View.VISIBLE)) {'''
if old not in t:
    raise SystemExit("procedural evaluate anchor not found")
t = t.replace(old, new, 1)

needle = '''    public boolean isTSPMode() {
        return isTSPMode(drawMode);
    }'''
replacement = '''    public boolean isProceduralMode() {
        return isProceduralMode(drawMode);
    }

    public boolean isProceduralMode(Mode mode) {
        return (mode == Mode.COMET) || (mode == Mode.BREATH) || (mode == Mode.ORBIT);
    }

    public boolean isTSPMode() {
        return isTSPMode(drawMode);
    }'''
if needle not in t:
    raise SystemExit("procedural helper anchor not found")
t = t.replace(needle, replacement, 1)

old = '''    public boolean isMultiColorMode(Mode mode) {
        return (mode == Mode.SINGLE) || isTSPMode(mode);
    }'''
new = '''    public boolean isMultiColorMode(Mode mode) {
        return (mode == Mode.SINGLE) || isTSPMode(mode) || isProceduralMode(mode);
    }'''
if old not in t:
    raise SystemExit("procedural multicolor anchor not found")
t = t.replace(old, new, 1)

sprite.write_text(t, encoding="utf-8")

# Persist the new modes and give them labels.
settings_file = Path("upstream/app/src/main/java/eu/chainfire/holeylight/misc/Settings.java")
t = settings_file.read_text(encoding="utf-8")
needle = '''            new AnimationStyle("swirl_fast", SpritePlayer.Mode.SWIRL_FAST, R.string.animation_style_swirl_fast_title, R.string.animation_style_location_camera, 5.5f),
            new AnimationStyle("blink_soft", SpritePlayer.Mode.BLINK_SOFT, R.string.animation_style_blink_soft_title, R.string.animation_style_location_camera, 3.5f),'''
replacement = '''            new AnimationStyle("swirl_fast", SpritePlayer.Mode.SWIRL_FAST, R.string.animation_style_swirl_fast_title, R.string.animation_style_location_camera, 5.5f),
            new AnimationStyle("comet", SpritePlayer.Mode.COMET, R.string.animation_style_comet_title, R.string.animation_style_location_camera, 4.5f),
            new AnimationStyle("breath", SpritePlayer.Mode.BREATH, R.string.animation_style_breath_title, R.string.animation_style_location_camera, 3.0f),
            new AnimationStyle("orbit", SpritePlayer.Mode.ORBIT, R.string.animation_style_orbit_title, R.string.animation_style_location_camera, 4.0f),
            new AnimationStyle("blink_soft", SpritePlayer.Mode.BLINK_SOFT, R.string.animation_style_blink_soft_title, R.string.animation_style_location_camera, 3.5f),'''
if needle not in t:
    raise SystemExit("procedural animation style table anchor not found")
t = t.replace(needle, replacement, 1)
settings_file.write_text(t, encoding="utf-8")

for rel, strings in [
    ("upstream/app/src/main/res/values/strings.xml", [
        ("animation_style_comet_title", "Comet"),
        ("animation_style_breath_title", "Breathing ring"),
        ("animation_style_orbit_title", "Orbit"),
    ]),
    ("upstream/app/src/main/res/values-it/strings.xml", [
        ("animation_style_comet_title", "Cometa"),
        ("animation_style_breath_title", "Respiro"),
        ("animation_style_orbit_title", "Orbit"),
    ]),
]:
    p = Path(rel)
    txt = p.read_text(encoding="utf-8")
    if "animation_style_comet_title" not in txt:
        block = "\n" + "\n".join([f'    <string name="{k}">{v}</string>' for k, v in strings]) + "\n"
        txt = txt.replace("</resources>", block + "</resources>")
        p.write_text(txt, encoding="utf-8")

# Overlay preview: preview selected effect for ~2.2 s while the settings screen is open.
overlay = Path("upstream/app/src/main/java/eu/chainfire/holeylight/animation/Overlay.java")
t = overlay.read_text(encoding="utf-8")
needle = '''    public void show(int[] colors, Drawable[] icons, boolean forceRefresh) {'''
preview = '''    public void preview(SpritePlayer.Mode previewMode) {
        if (terminated || animation == null) return;
        handler.removeCallbacks(evaluateLoop);
        animation.setMode(previewMode, false);
        animation.setShowAODClock(false, false);
        animation.setHideAOD(false, false);
        animation.setDoze(false);
        createOverlay();
        animation.play(new int[] { Color.WHITE }, new Drawable[0], false, true);
        handler.postDelayed(() -> {
            if (terminated || animation == null) return;
            animation.stop(true);
            removeOverlay();
            forceRefresh = true;
            evaluate(true);
        }, 2200);
    }

''' + needle
if needle not in t:
    raise SystemExit("Overlay preview anchor not found")
t = t.replace(needle, preview, 1)
overlay.write_text(t, encoding="utf-8")

# Expose procedural modes in the clear screen-on/off effect pickers and preview on selection.
frag = Path("upstream/app/src/main/java/eu/chainfire/holeylight/ui/SettingsFragment.java")
t = frag.read_text(encoding="utf-8")

old = '''                    SpritePlayer.Mode.SWIRL_FAST,
                    SpritePlayer.Mode.BLINK_SOFT,
                    SpritePlayer.Mode.BLINK,
                    SpritePlayer.Mode.SINGLE
            };'''
new = '''                    SpritePlayer.Mode.SWIRL_FAST,
                    SpritePlayer.Mode.COMET,
                    SpritePlayer.Mode.BREATH,
                    SpritePlayer.Mode.ORBIT,
                    SpritePlayer.Mode.BLINK_SOFT,
                    SpritePlayer.Mode.BLINK,
                    SpritePlayer.Mode.SINGLE
            };'''
if old not in t:
    raise SystemExit("screen-on procedural picker anchor not found")
t = t.replace(old, new, 1)

old = '''                    SpritePlayer.Mode.SWIRL_FAST,
                    SpritePlayer.Mode.BLINK_SOFT,
                    SpritePlayer.Mode.BLINK,
                    SpritePlayer.Mode.SINGLE,
                    SpritePlayer.Mode.TSP
            };'''
new = '''                    SpritePlayer.Mode.SWIRL_FAST,
                    SpritePlayer.Mode.COMET,
                    SpritePlayer.Mode.BREATH,
                    SpritePlayer.Mode.ORBIT,
                    SpritePlayer.Mode.BLINK_SOFT,
                    SpritePlayer.Mode.BLINK,
                    SpritePlayer.Mode.SINGLE,
                    SpritePlayer.Mode.TSP
            };'''
if old not in t:
    raise SystemExit("screen-off procedural picker anchor not found")
t = t.replace(old, new, 1)

old = '''                        preference.setSummary(getString(settings.getAnimationStyle(selected).title));
                    })'''
new = '''                        preference.setSummary(getString(settings.getAnimationStyle(selected).title));
                        eu.chainfire.holeylight.animation.Overlay overlay = eu.chainfire.holeylight.animation.Overlay.getInstance();
                        if (overlay != null) overlay.preview(selected);
                    })'''
count = t.count(old)
if count < 2:
    raise SystemExit("effect picker preview anchors not found")
t = t.replace(old, new, 2)

frag.write_text(t, encoding="utf-8")

print("Added procedural Comet/Breath/Orbit effects with live preview")


# 19) More procedural effects + simplified optional AOD Helper UI.
sprite = Path("upstream/app/src/main/java/eu/chainfire/holeylight/animation/SpritePlayer.java")
t = sprite.read_text(encoding="utf-8")

old = "public enum Mode { SWIRL, SWIRL_SLOW, SWIRL_FAST, COMET, BREATH, ORBIT, BLINK, BLINK_SOFT, SINGLE, TSP, TSP_HIDE }"
new = "public enum Mode { SWIRL, SWIRL_SLOW, SWIRL_FAST, COMET, DOUBLE_COMET, BREATH, HEARTBEAT, RADAR, NEON, ORBIT, RIPPLE, BLINK, BLINK_SOFT, SINGLE, TSP, TSP_HIDE }"
if old not in t:
    raise SystemExit("extended procedural Mode enum anchor not found")
t = t.replace(old, new, 1)

old = '''    public boolean isProceduralMode(Mode mode) {
        return (mode == Mode.COMET) || (mode == Mode.BREATH) || (mode == Mode.ORBIT);
    }'''
new = '''    public boolean isProceduralMode(Mode mode) {
        return (mode == Mode.COMET) ||
                (mode == Mode.DOUBLE_COMET) ||
                (mode == Mode.BREATH) ||
                (mode == Mode.HEARTBEAT) ||
                (mode == Mode.RADAR) ||
                (mode == Mode.NEON) ||
                (mode == Mode.ORBIT) ||
                (mode == Mode.RIPPLE);
    }'''
if old not in t:
    raise SystemExit("extended procedural helper anchor not found")
t = t.replace(old, new, 1)

old = '''        } else if (drawMode == Mode.ORBIT) {
            float cycle = 1850f / safeSpeed;
            float phase = ((diff % (long)Math.max(1f, cycle)) / cycle) * 360f;
            paintProcedural.setStyle(Paint.Style.FILL);
            final int dots = 4;
            for (int i = 0; i < dots; i++) {
                float angle = phase + ((360f / dots) * i);
                double rad = Math.toRadians(angle);
                int c = activeColors[i % activeColors.length];
                int alpha = 255 - (i * 35);
                paintProcedural.setColor((c & 0x00FFFFFF) | (alpha << 24));
                float dotR = (i == 0 ? 3.8f : 2.7f) * dpToPx;
                canvas.drawCircle(
                        cx + ((float)Math.cos(rad) * radius),
                        cy + ((float)Math.sin(rad) * radius),
                        dotR,
                        paintProcedural
                );
            }
        }
    }

    private final Choreographer.FrameCallback frameCallback = new Choreographer.FrameCallback() {'''

new = '''        } else if (drawMode == Mode.ORBIT) {
            float cycle = 1850f / safeSpeed;
            float phase = ((diff % (long)Math.max(1f, cycle)) / cycle) * 360f;
            paintProcedural.setStyle(Paint.Style.FILL);
            final int dots = 4;
            for (int i = 0; i < dots; i++) {
                float angle = phase + ((360f / dots) * i);
                double rad = Math.toRadians(angle);
                int c = activeColors[i % activeColors.length];
                int alpha = 255 - (i * 35);
                paintProcedural.setColor((c & 0x00FFFFFF) | (alpha << 24));
                float dotR = (i == 0 ? 3.8f : 2.7f) * dpToPx;
                canvas.drawCircle(
                        cx + ((float)Math.cos(rad) * radius),
                        cy + ((float)Math.sin(rad) * radius),
                        dotR,
                        paintProcedural
                );
            }
        } else if (drawMode == Mode.DOUBLE_COMET) {
            float cycle = 1900f / safeSpeed;
            float phase = ((diff % (long)Math.max(1f, cycle)) / cycle) * 360f;
            paintProcedural.setStyle(Paint.Style.STROKE);
            paintProcedural.setStrokeWidth(3.0f * dpToPx);
            for (int head = 0; head < 2; head++) {
                float base = phase + (head * 180f);
                for (int i = 0; i < 8; i++) {
                    int alpha = Math.max(20, 245 - (i * 29));
                    int c = activeColors[(head + i) % activeColors.length];
                    paintProcedural.setColor((c & 0x00FFFFFF) | (alpha << 24));
                    canvas.drawArc(
                            cx - radius, cy - radius, cx + radius, cy + radius,
                            base - (i * 8.5f), 18f, false, paintProcedural
                    );
                }
            }
        } else if (drawMode == Mode.HEARTBEAT) {
            float cycle = 1650f / safeSpeed;
            float part = (diff % (long)Math.max(1f, cycle)) / cycle;
            double d1 = (part - 0.18f) / 0.055f;
            double d2 = (part - 0.34f) / 0.070f;
            float beat = (float)Math.min(1.0,
                    Math.exp(-(d1 * d1)) + (0.72 * Math.exp(-(d2 * d2))));
            int alpha = 42 + Math.round(213f * beat);
            int c = activeColors[0];
            paintProcedural.setStyle(Paint.Style.STROKE);
            paintProcedural.setStrokeWidth((1.8f + (4.8f * beat)) * dpToPx);
            paintProcedural.setColor((c & 0x00FFFFFF) | (alpha << 24));
            canvas.drawCircle(cx, cy, radius - (2.2f * beat * dpToPx), paintProcedural);
        } else if (drawMode == Mode.RADAR) {
            float cycle = 2150f / safeSpeed;
            float phase = ((diff % (long)Math.max(1f, cycle)) / cycle) * 360f;
            int c = activeColors[0];
            paintProcedural.setStyle(Paint.Style.STROKE);
            paintProcedural.setStrokeWidth(1.5f * dpToPx);
            paintProcedural.setColor((c & 0x00FFFFFF) | 0x33000000);
            canvas.drawCircle(cx, cy, radius, paintProcedural);
            for (int i = 0; i < 7; i++) {
                int alpha = Math.max(24, 240 - (i * 31));
                paintProcedural.setStrokeWidth((3.6f - (i * 0.28f)) * dpToPx);
                paintProcedural.setColor((c & 0x00FFFFFF) | (alpha << 24));
                canvas.drawArc(
                        cx - radius, cy - radius, cx + radius, cy + radius,
                        phase - (i * 10f), 32f, false, paintProcedural
                );
            }
        } else if (drawMode == Mode.NEON) {
            float cycle = 2400f / safeSpeed;
            float phase = ((diff % (long)Math.max(1f, cycle)) / cycle) * 360f;
            int c = activeColors[0];
            int rgb = c & 0x00FFFFFF;
            int[] gradientColors = new int[] {
                    rgb,
                    rgb | 0x22000000,
                    rgb | 0xAA000000,
                    c | 0xFF000000,
                    Color.WHITE,
                    c | 0xFF000000,
                    rgb | 0x22000000,
                    rgb
            };
            float[] positions = new float[] { 0f, 0.16f, 0.34f, 0.48f, 0.52f, 0.58f, 0.78f, 1f };
            Shader neon = new SweepGradient(cx, cy, gradientColors, positions);
            Matrix matrix = new Matrix();
            matrix.preRotate(phase, cx, cy);
            neon.setLocalMatrix(matrix);

            paintProcedural.setStyle(Paint.Style.STROKE);
            paintProcedural.setShader(neon);
            paintProcedural.setStrokeWidth(7.0f * dpToPx);
            paintProcedural.setAlpha(70);
            canvas.drawCircle(cx, cy, radius, paintProcedural);
            paintProcedural.setStrokeWidth(3.0f * dpToPx);
            paintProcedural.setAlpha(255);
            canvas.drawCircle(cx, cy, radius, paintProcedural);
            paintProcedural.setShader(null);
            paintProcedural.setAlpha(255);
        } else if (drawMode == Mode.RIPPLE) {
            float cycle = 2100f / safeSpeed;
            float part = (diff % (long)Math.max(1f, cycle)) / cycle;
            int c = activeColors[0];
            paintProcedural.setStyle(Paint.Style.STROKE);
            for (int i = 0; i < 3; i++) {
                float p = (part + (i / 3f)) % 1f;
                float rr = radius * (0.63f + (0.37f * p));
                int alpha = Math.max(10, Math.round(210f * (1f - p)));
                paintProcedural.setStrokeWidth((1.2f + (2.5f * (1f - p))) * dpToPx);
                paintProcedural.setColor((c & 0x00FFFFFF) | (alpha << 24));
                canvas.drawCircle(cx, cy, rr, paintProcedural);
            }
        }
    }

    private final Choreographer.FrameCallback frameCallback = new Choreographer.FrameCallback() {'''

if old not in t:
    raise SystemExit("extended procedural renderer anchor not found")
t = t.replace(old, new, 1)
sprite.write_text(t, encoding="utf-8")

settings_file = Path("upstream/app/src/main/java/eu/chainfire/holeylight/misc/Settings.java")
t = settings_file.read_text(encoding="utf-8")
old = '''            new AnimationStyle("comet", SpritePlayer.Mode.COMET, R.string.animation_style_comet_title, R.string.animation_style_location_camera, 4.5f),
            new AnimationStyle("breath", SpritePlayer.Mode.BREATH, R.string.animation_style_breath_title, R.string.animation_style_location_camera, 3.0f),
            new AnimationStyle("orbit", SpritePlayer.Mode.ORBIT, R.string.animation_style_orbit_title, R.string.animation_style_location_camera, 4.0f),'''
new = '''            new AnimationStyle("comet", SpritePlayer.Mode.COMET, R.string.animation_style_comet_title, R.string.animation_style_location_camera, 4.5f),
            new AnimationStyle("double_comet", SpritePlayer.Mode.DOUBLE_COMET, R.string.animation_style_double_comet_title, R.string.animation_style_location_camera, 4.8f),
            new AnimationStyle("breath", SpritePlayer.Mode.BREATH, R.string.animation_style_breath_title, R.string.animation_style_location_camera, 3.0f),
            new AnimationStyle("heartbeat", SpritePlayer.Mode.HEARTBEAT, R.string.animation_style_heartbeat_title, R.string.animation_style_location_camera, 3.2f),
            new AnimationStyle("radar", SpritePlayer.Mode.RADAR, R.string.animation_style_radar_title, R.string.animation_style_location_camera, 4.0f),
            new AnimationStyle("neon", SpritePlayer.Mode.NEON, R.string.animation_style_neon_title, R.string.animation_style_location_camera, 4.6f),
            new AnimationStyle("orbit", SpritePlayer.Mode.ORBIT, R.string.animation_style_orbit_title, R.string.animation_style_location_camera, 4.0f),
            new AnimationStyle("ripple", SpritePlayer.Mode.RIPPLE, R.string.animation_style_ripple_title, R.string.animation_style_location_camera, 3.8f),'''
if old not in t:
    raise SystemExit("extended animation style table anchor not found")
t = t.replace(old, new, 1)
settings_file.write_text(t, encoding="utf-8")

for rel, strings in [
    ("upstream/app/src/main/res/values/strings.xml", [
        ("animation_style_double_comet_title", "Double comet"),
        ("animation_style_heartbeat_title", "Heartbeat"),
        ("animation_style_radar_title", "Radar"),
        ("animation_style_neon_title", "Neon sweep"),
        ("animation_style_ripple_title", "Ripple"),
    ]),
    ("upstream/app/src/main/res/values-it/strings.xml", [
        ("animation_style_double_comet_title", "Doppia cometa"),
        ("animation_style_heartbeat_title", "Heartbeat"),
        ("animation_style_radar_title", "Radar"),
        ("animation_style_neon_title", "Neon sweep"),
        ("animation_style_ripple_title", "Ripple"),
    ]),
]:
    p = Path(rel)
    txt = p.read_text(encoding="utf-8")
    if "animation_style_double_comet_title" not in txt:
        block = "\n" + "\n".join([f'    <string name="{k}">{v}</string>' for k, v in strings]) + "\n"
        txt = txt.replace("</resources>", block + "</resources>")
        p.write_text(txt, encoding="utf-8")

frag = Path("upstream/app/src/main/java/eu/chainfire/holeylight/ui/SettingsFragment.java")
t = frag.read_text(encoding="utf-8")

old = '''                    SpritePlayer.Mode.SWIRL_FAST,
                    SpritePlayer.Mode.COMET,
                    SpritePlayer.Mode.BREATH,
                    SpritePlayer.Mode.ORBIT,
                    SpritePlayer.Mode.BLINK_SOFT,'''
new = '''                    SpritePlayer.Mode.SWIRL_FAST,
                    SpritePlayer.Mode.COMET,
                    SpritePlayer.Mode.DOUBLE_COMET,
                    SpritePlayer.Mode.BREATH,
                    SpritePlayer.Mode.HEARTBEAT,
                    SpritePlayer.Mode.RADAR,
                    SpritePlayer.Mode.NEON,
                    SpritePlayer.Mode.ORBIT,
                    SpritePlayer.Mode.RIPPLE,
                    SpritePlayer.Mode.BLINK_SOFT,'''
if t.count(old) < 2:
    raise SystemExit("extended effect picker anchors not found")
t = t.replace(old, new, 2)

# Replace the old technical helper category with one optional, understandable item.
needle = '''        refreshS24Profile.run();

        prefHideAOD.setTitle("Mascheramento AOD (avanzato)");'''
replacement = '''        refreshS24Profile.run();

        Preference prefAODPowerSave = pref(catS24AOD, 0, 0, null, true, null);
        prefAODPowerSave.setTitle("Risparmio AOD automatico");

        Runnable refreshAODPowerSave = () -> {
            AODControl.AODHelperState state = AODControl.getAODHelperState(getContext());
            if (state == AODControl.AODHelperState.OK) {
                prefAODPowerSave.setSummary(settings.isAODHelperControl()
                        ? "Attivo — spegne l'AOD di sistema quando non ci sono notifiche"
                        : "Disattivato — tocca per attivare");
            } else if (state == AODControl.AODHelperState.NEEDS_UPDATE) {
                prefAODPowerSave.setSummary("Opzionale — AOD Helper va aggiornato");
            } else if (state == AODControl.AODHelperState.NEEDS_PERMISSIONS) {
                prefAODPowerSave.setSummary("Opzionale — AOD Helper richiede autorizzazioni");
            } else {
                prefAODPowerSave.setSummary("Opzionale — richiede il companion AOD Helper");
            }
        };

        prefAODPowerSave.setOnPreferenceClickListener(preference -> {
            AODControl.AODHelperState state = AODControl.getAODHelperState(getContext());
            if (state != AODControl.AODHelperState.OK) {
                Activity activity = getActivity();
                if (activity instanceof MainActivity) {
                    ((MainActivity)activity).aodHelperInstructions();
                }
                return true;
            }
            settings.setAODHelperControl(!settings.isAODHelperControl());
            refreshAODPowerSave.run();
            return true;
        });
        refreshAODPowerSave.run();

        prefHideAOD.setTitle("Mascheramento AOD (avanzato)");'''
if needle not in t:
    raise SystemExit("AOD power save insertion anchor not found")
t = t.replace(needle, replacement, 1)

needle = '''        PreferenceCategory catAODHelper = category(root, R.string.settings_category_aod_helper_title, R.string.settings_category_aod_helper_description);'''
replacement = '''        PreferenceCategory catAODHelper = category(root, R.string.settings_category_aod_helper_title, R.string.settings_category_aod_helper_description);
        catAODHelper.setVisible(false);'''
if needle not in t:
    raise SystemExit("legacy AOD helper category anchor not found")
t = t.replace(needle, replacement, 1)

frag.write_text(t, encoding="utf-8")

print("Added DoubleComet/Heartbeat/Radar/Neon/Ripple and simplified AOD Helper UI")


# 20) Procedural effect controls + keep AOD Helper entirely out of the normal UI.

# --- Persist global procedural effect controls ---
settings_file = Path("upstream/app/src/main/java/eu/chainfire/holeylight/misc/Settings.java")
t = settings_file.read_text(encoding="utf-8")

needle = '''    private static final String SPEED_FACTOR = "speed_factor";'''
replacement = '''    private static final String SPEED_FACTOR = "speed_factor";

    private static final String EFFECT_DIRECTION = "effect_direction";
    private static final String EFFECT_SPEED = "effect_speed";
    private static final String EFFECT_INTENSITY = "effect_intensity";
    private static final String EFFECT_TRAIL = "effect_trail";
    private static final String EFFECT_ORBIT_DOTS = "effect_orbit_dots";
    private static final String EFFECT_RIPPLE_WAVES = "effect_ripple_waves";'''
if needle not in t:
    raise SystemExit("effect settings constants anchor not found")
t = t.replace(needle, replacement, 1)

needle = '''    public void setSpeedFactor(float value) {
        value = Math.min(Math.max(value, 0.5f), 2.0f);

        put(SPEED_FACTOR, value, true);
    }'''
replacement = '''    public void setSpeedFactor(float value) {
        value = Math.min(Math.max(value, 0.5f), 2.0f);

        put(SPEED_FACTOR, value, true);
    }

    public int getEffectDirection() {
        return prefs.getInt(EFFECT_DIRECTION, 1);
    }

    public void setEffectDirection(int value) {
        put(EFFECT_DIRECTION, value < 0 ? -1 : 1, true);
    }

    public float getEffectSpeed() {
        return prefs.getFloat(EFFECT_SPEED, 1.0f);
    }

    public void setEffectSpeed(float value) {
        put(EFFECT_SPEED, Math.min(Math.max(value, 0.5f), 2.0f), true);
    }

    public float getEffectIntensity() {
        return prefs.getFloat(EFFECT_INTENSITY, 1.0f);
    }

    public void setEffectIntensity(float value) {
        put(EFFECT_INTENSITY, Math.min(Math.max(value, 0.5f), 1.5f), true);
    }

    public float getEffectTrail() {
        return prefs.getFloat(EFFECT_TRAIL, 1.0f);
    }

    public void setEffectTrail(float value) {
        put(EFFECT_TRAIL, Math.min(Math.max(value, 0.5f), 2.0f), true);
    }

    public int getEffectOrbitDots() {
        return prefs.getInt(EFFECT_ORBIT_DOTS, 4);
    }

    public void setEffectOrbitDots(int value) {
        put(EFFECT_ORBIT_DOTS, Math.min(Math.max(value, 2), 8), true);
    }

    public int getEffectRippleWaves() {
        return prefs.getInt(EFFECT_RIPPLE_WAVES, 3);
    }

    public void setEffectRippleWaves(int value) {
        put(EFFECT_RIPPLE_WAVES, Math.min(Math.max(value, 2), 6), true);
    }'''
if needle not in t:
    raise SystemExit("effect settings getters anchor not found")
t = t.replace(needle, replacement, 1)
settings_file.write_text(t, encoding="utf-8")

# --- Apply controls in the procedural renderer ---
sprite = Path("upstream/app/src/main/java/eu/chainfire/holeylight/animation/SpritePlayer.java")
t = sprite.read_text(encoding="utf-8")

needle = '''        float radius = Math.max(2f * dpToPx, Math.min(width, height) / 2f - (4f * dpToPx));
        float safeSpeed = Math.max(0.15f, speed);

        paintProcedural.setShader(null);'''
replacement = '''        float radius = Math.max(2f * dpToPx, Math.min(width, height) / 2f - (4f * dpToPx));

        Settings effectSettings = Settings.getInstance(getContext());
        int effectDirection = effectSettings.getEffectDirection();
        float effectSpeed = effectSettings.getEffectSpeed();
        float effectIntensity = effectSettings.getEffectIntensity();
        float effectTrail = effectSettings.getEffectTrail();
        int effectOrbitDots = effectSettings.getEffectOrbitDots();
        int effectRippleWaves = effectSettings.getEffectRippleWaves();

        float safeSpeed = Math.max(0.15f, speed * effectSpeed);

        paintProcedural.setShader(null);'''
if needle not in t:
    raise SystemExit("effect renderer settings anchor not found")
t = t.replace(needle, replacement, 1)

# Comet: direction + trail + intensity
old = '''            float phase = ((diff % (long)Math.max(1f, cycle)) / cycle) * 360f;
            paintProcedural.setStyle(Paint.Style.STROKE);
            paintProcedural.setStrokeWidth(3.2f * dpToPx);
            for (int i = 0; i < 9; i++) {
                int alpha = Math.max(18, 255 - (i * 27));'''
new = '''            float phase = ((diff % (long)Math.max(1f, cycle)) / cycle) * 360f * effectDirection;
            paintProcedural.setStyle(Paint.Style.STROKE);
            paintProcedural.setStrokeWidth(3.2f * effectIntensity * dpToPx);
            int trailSteps = Math.max(4, Math.min(16, Math.round(9f * effectTrail)));
            for (int i = 0; i < trailSteps; i++) {
                int alpha = Math.max(18, Math.min(255, Math.round((255 - (i * (235f / trailSteps))) * effectIntensity)));'''
if old not in t:
    raise SystemExit("comet controls anchor not found")
t = t.replace(old, new, 1)

t = t.replace(
'''                    3.4f * dpToPx,
                    paintProcedural''',
'''                    3.4f * effectIntensity * dpToPx,
                    paintProcedural''',
1)

# Breath
old = '''            int alpha = 60 + Math.round(195f * wave);
            float breatheRadius = radius - ((1f - wave) * 2.5f * dpToPx);
            paintProcedural.setStyle(Paint.Style.STROKE);
            paintProcedural.setStrokeWidth((2.0f + (3.4f * wave)) * dpToPx);'''
new = '''            int alpha = Math.min(255, Math.round((60 + (195f * wave)) * effectIntensity));
            float breatheRadius = radius - ((1f - wave) * 2.5f * dpToPx);
            paintProcedural.setStyle(Paint.Style.STROKE);
            paintProcedural.setStrokeWidth((2.0f + (3.4f * wave)) * effectIntensity * dpToPx);'''
if old not in t:
    raise SystemExit("breath controls anchor not found")
t = t.replace(old, new, 1)

# Orbit
old = '''            float phase = ((diff % (long)Math.max(1f, cycle)) / cycle) * 360f;
            paintProcedural.setStyle(Paint.Style.FILL);
            final int dots = 4;
            for (int i = 0; i < dots; i++) {
                float angle = phase + ((360f / dots) * i);'''
new = '''            float phase = ((diff % (long)Math.max(1f, cycle)) / cycle) * 360f * effectDirection;
            paintProcedural.setStyle(Paint.Style.FILL);
            final int dots = effectOrbitDots;
            for (int i = 0; i < dots; i++) {
                float angle = phase + ((360f / dots) * i);'''
if old not in t:
    raise SystemExit("orbit controls anchor not found")
t = t.replace(old, new, 1)

old = '''                int alpha = 255 - (i * 35);
                paintProcedural.setColor((c & 0x00FFFFFF) | (alpha << 24));
                float dotR = (i == 0 ? 3.8f : 2.7f) * dpToPx;'''
new = '''                int alpha = Math.max(70, Math.min(255, Math.round((255 - (i * (140f / dots))) * effectIntensity)));
                paintProcedural.setColor((c & 0x00FFFFFF) | (alpha << 24));
                float dotR = (i == 0 ? 3.8f : 2.7f) * effectIntensity * dpToPx;'''
if old not in t:
    raise SystemExit("orbit intensity anchor not found")
t = t.replace(old, new, 1)

# Double comet
old = '''            float phase = ((diff % (long)Math.max(1f, cycle)) / cycle) * 360f;
            paintProcedural.setStyle(Paint.Style.STROKE);
            paintProcedural.setStrokeWidth(3.0f * dpToPx);
            for (int head = 0; head < 2; head++) {
                float base = phase + (head * 180f);
                for (int i = 0; i < 8; i++) {
                    int alpha = Math.max(20, 245 - (i * 29));'''
new = '''            float phase = ((diff % (long)Math.max(1f, cycle)) / cycle) * 360f * effectDirection;
            paintProcedural.setStyle(Paint.Style.STROKE);
            paintProcedural.setStrokeWidth(3.0f * effectIntensity * dpToPx);
            int trailSteps = Math.max(4, Math.min(15, Math.round(8f * effectTrail)));
            for (int head = 0; head < 2; head++) {
                float base = phase + (head * 180f);
                for (int i = 0; i < trailSteps; i++) {
                    int alpha = Math.max(20, Math.min(255, Math.round((245 - (i * (220f / trailSteps))) * effectIntensity)));'''
if old not in t:
    raise SystemExit("double comet controls anchor not found")
t = t.replace(old, new, 1)

# Heartbeat intensity
old = '''            int alpha = 42 + Math.round(213f * beat);
            int c = activeColors[0];
            paintProcedural.setStyle(Paint.Style.STROKE);
            paintProcedural.setStrokeWidth((1.8f + (4.8f * beat)) * dpToPx);'''
new = '''            int alpha = Math.min(255, Math.round((42 + (213f * beat)) * effectIntensity));
            int c = activeColors[0];
            paintProcedural.setStyle(Paint.Style.STROKE);
            paintProcedural.setStrokeWidth((1.8f + (4.8f * beat)) * effectIntensity * dpToPx);'''
if old not in t:
    raise SystemExit("heartbeat controls anchor not found")
t = t.replace(old, new, 1)

# Radar direction/trail/intensity
old = '''            float phase = ((diff % (long)Math.max(1f, cycle)) / cycle) * 360f;
            int c = activeColors[0];
            paintProcedural.setStyle(Paint.Style.STROKE);
            paintProcedural.setStrokeWidth(1.5f * dpToPx);
            paintProcedural.setColor((c & 0x00FFFFFF) | 0x33000000);
            canvas.drawCircle(cx, cy, radius, paintProcedural);
            for (int i = 0; i < 7; i++) {
                int alpha = Math.max(24, 240 - (i * 31));
                paintProcedural.setStrokeWidth((3.6f - (i * 0.28f)) * dpToPx);'''
new = '''            float phase = ((diff % (long)Math.max(1f, cycle)) / cycle) * 360f * effectDirection;
            int c = activeColors[0];
            paintProcedural.setStyle(Paint.Style.STROKE);
            paintProcedural.setStrokeWidth(1.5f * effectIntensity * dpToPx);
            paintProcedural.setColor((c & 0x00FFFFFF) | 0x33000000);
            canvas.drawCircle(cx, cy, radius, paintProcedural);
            int radarSteps = Math.max(4, Math.min(14, Math.round(7f * effectTrail)));
            for (int i = 0; i < radarSteps; i++) {
                int alpha = Math.max(24, Math.min(255, Math.round((240 - (i * (210f / radarSteps))) * effectIntensity)));
                paintProcedural.setStrokeWidth(Math.max(1.0f, 3.6f - (i * (2.0f / radarSteps))) * effectIntensity * dpToPx);'''
if old not in t:
    raise SystemExit("radar controls anchor not found")
t = t.replace(old, new, 1)

# Neon direction/intensity
old = '''            float phase = ((diff % (long)Math.max(1f, cycle)) / cycle) * 360f;
            int c = activeColors[0];'''
new = '''            float phase = ((diff % (long)Math.max(1f, cycle)) / cycle) * 360f * effectDirection;
            int c = activeColors[0];'''
# Replace only next occurrence after RADAR block's start by targeted split
radar_pos = t.find("} else if (drawMode == Mode.NEON)")
if radar_pos == -1:
    raise SystemExit("neon block not found")
segment = t[radar_pos:]
if old not in segment:
    raise SystemExit("neon phase anchor not found")
segment = segment.replace(old, new, 1)
t = t[:radar_pos] + segment

old = '''            paintProcedural.setStrokeWidth(7.0f * dpToPx);
            paintProcedural.setAlpha(70);
            canvas.drawCircle(cx, cy, radius, paintProcedural);
            paintProcedural.setStrokeWidth(3.0f * dpToPx);'''
new = '''            paintProcedural.setStrokeWidth(7.0f * effectIntensity * dpToPx);
            paintProcedural.setAlpha(Math.min(150, Math.round(70f * effectIntensity)));
            canvas.drawCircle(cx, cy, radius, paintProcedural);
            paintProcedural.setStrokeWidth(3.0f * effectIntensity * dpToPx);'''
if old not in t:
    raise SystemExit("neon intensity anchor not found")
t = t.replace(old, new, 1)

# Ripple waves/intensity
old = '''            paintProcedural.setStyle(Paint.Style.STROKE);
            for (int i = 0; i < 3; i++) {
                float p = (part + (i / 3f)) % 1f;
                float rr = radius * (0.63f + (0.37f * p));
                int alpha = Math.max(10, Math.round(210f * (1f - p)));
                paintProcedural.setStrokeWidth((1.2f + (2.5f * (1f - p))) * dpToPx);'''
new = '''            paintProcedural.setStyle(Paint.Style.STROKE);
            int waves = effectRippleWaves;
            for (int i = 0; i < waves; i++) {
                float p = (part + (i / (float)waves)) % 1f;
                float rr = radius * (0.63f + (0.37f * p));
                int alpha = Math.max(10, Math.min(255, Math.round(210f * (1f - p) * effectIntensity)));
                paintProcedural.setStrokeWidth((1.2f + (2.5f * (1f - p))) * effectIntensity * dpToPx);'''
if old not in t:
    raise SystemExit("ripple controls anchor not found")
t = t.replace(old, new, 1)

sprite.write_text(t, encoding="utf-8")

# --- Expose controls in Animation section ---
frag = Path("upstream/app/src/main/java/eu/chainfire/holeylight/ui/SettingsFragment.java")
t = frag.read_text(encoding="utf-8")

anchor = '''        Preference prefAODBrightness = pref(catAnimation, R.string.settings_animation_brightness_title, 0, null, true, null);'''
if anchor not in t:
    raise SystemExit("effect controls UI insertion anchor not found")

controls = '''        Runnable previewCurrentEffect = () -> {
            eu.chainfire.holeylight.animation.Overlay overlay = eu.chainfire.holeylight.animation.Overlay.getInstance();
            if (overlay != null) {
                overlay.preview(settings.getAnimationMode(Settings.SCREEN_ON_BATTERY));
            }
        };

        Preference prefEffectDirection = pref(catAnimation, 0, 0, null, true, null);
        prefEffectDirection.setTitle("Direzione effetti");
        prefEffectDirection.setSummary(settings.getEffectDirection() < 0 ? "Antiorario" : "Orario");
        prefEffectDirection.setOnPreferenceClickListener(preference -> {
            int value = settings.getEffectDirection() < 0 ? 1 : -1;
            settings.setEffectDirection(value);
            preference.setSummary(value < 0 ? "Antiorario" : "Orario");
            previewCurrentEffect.run();
            return true;
        });

        Preference prefEffectSpeed = pref(catAnimation, 0, 0, null, true, null);
        prefEffectSpeed.setTitle("Velocità effetti");
        prefEffectSpeed.setSummary(String.format(Locale.ENGLISH, "%.2fx", settings.getEffectSpeed()));
        prefEffectSpeed.setOnPreferenceClickListener(preference -> {
            final float[] values = new float[] { 0.50f, 0.75f, 1.00f, 1.25f, 1.50f, 2.00f };
            final CharSequence[] labels = new CharSequence[] { "0,50x", "0,75x", "1,00x", "1,25x", "1,50x", "2,00x" };
            (new AlertDialog.Builder(getContext()))
                    .setTitle("Velocità effetti")
                    .setItems(labels, (dialog, which) -> {
                        settings.setEffectSpeed(values[which]);
                        preference.setSummary(labels[which]);
                        previewCurrentEffect.run();
                    })
                    .setNegativeButton(android.R.string.cancel, null)
                    .show();
            return true;
        });

        Preference prefEffectIntensity = pref(catAnimation, 0, 0, null, true, null);
        prefEffectIntensity.setTitle("Intensità / glow");
        prefEffectIntensity.setSummary(Math.round(settings.getEffectIntensity() * 100f) + "%");
        prefEffectIntensity.setOnPreferenceClickListener(preference -> {
            final float[] values = new float[] { 0.50f, 0.75f, 1.00f, 1.25f, 1.50f };
            final CharSequence[] labels = new CharSequence[] { "50%", "75%", "100%", "125%", "150%" };
            (new AlertDialog.Builder(getContext()))
                    .setTitle("Intensità / glow")
                    .setItems(labels, (dialog, which) -> {
                        settings.setEffectIntensity(values[which]);
                        preference.setSummary(labels[which]);
                        previewCurrentEffect.run();
                    })
                    .setNegativeButton(android.R.string.cancel, null)
                    .show();
            return true;
        });

        Preference prefEffectTrail = pref(catAnimation, 0, 0, null, true, null);
        prefEffectTrail.setTitle("Lunghezza scia");
        prefEffectTrail.setSummary(String.format(Locale.ENGLISH, "%.2fx", settings.getEffectTrail()));
        prefEffectTrail.setOnPreferenceClickListener(preference -> {
            final float[] values = new float[] { 0.55f, 0.80f, 1.00f, 1.35f, 1.70f, 2.00f };
            final CharSequence[] labels = new CharSequence[] { "Molto corta", "Corta", "Normale", "Lunga", "Molto lunga", "Massima" };
            (new AlertDialog.Builder(getContext()))
                    .setTitle("Lunghezza scia")
                    .setItems(labels, (dialog, which) -> {
                        settings.setEffectTrail(values[which]);
                        preference.setSummary(labels[which]);
                        previewCurrentEffect.run();
                    })
                    .setNegativeButton(android.R.string.cancel, null)
                    .show();
            return true;
        });

        Preference prefEffectOrbitDots = pref(catAnimation, 0, 0, null, true, null);
        prefEffectOrbitDots.setTitle("Punti Orbit");
        prefEffectOrbitDots.setSummary(String.valueOf(settings.getEffectOrbitDots()));
        prefEffectOrbitDots.setOnPreferenceClickListener(preference -> {
            final int[] values = new int[] { 2, 3, 4, 6, 8 };
            final CharSequence[] labels = new CharSequence[] { "2", "3", "4", "6", "8" };
            (new AlertDialog.Builder(getContext()))
                    .setTitle("Punti Orbit")
                    .setItems(labels, (dialog, which) -> {
                        settings.setEffectOrbitDots(values[which]);
                        preference.setSummary(labels[which]);
                        previewCurrentEffect.run();
                    })
                    .setNegativeButton(android.R.string.cancel, null)
                    .show();
            return true;
        });

        Preference prefEffectRippleWaves = pref(catAnimation, 0, 0, null, true, null);
        prefEffectRippleWaves.setTitle("Onde Ripple");
        prefEffectRippleWaves.setSummary(String.valueOf(settings.getEffectRippleWaves()));
        prefEffectRippleWaves.setOnPreferenceClickListener(preference -> {
            final int[] values = new int[] { 2, 3, 4, 5, 6 };
            final CharSequence[] labels = new CharSequence[] { "2", "3", "4", "5", "6" };
            (new AlertDialog.Builder(getContext()))
                    .setTitle("Onde Ripple")
                    .setItems(labels, (dialog, which) -> {
                        settings.setEffectRippleWaves(values[which]);
                        preference.setSummary(labels[which]);
                        previewCurrentEffect.run();
                    })
                    .setNegativeButton(android.R.string.cancel, null)
                    .show();
            return true;
        });

''' + anchor
t = t.replace(anchor, controls, 1)

# Remove the optional AOD Helper shortcut we added in the previous pass.
start = t.find('''        Preference prefAODPowerSave = pref(catS24AOD, 0, 0, null, true, null);''')
if start != -1:
    end_marker = '''        refreshAODPowerSave.run();

'''
    end = t.find(end_marker, start)
    if end == -1:
        raise SystemExit("AOD Helper shortcut end not found")
    end += len(end_marker)
    t = t[:start] + t[end:]

frag.write_text(t, encoding="utf-8")

print("Added procedural effect controls and removed AOD Helper from normal UI")


# 21) Color Chase / Arc Sweep / Spark + presets + per-app effects.

# --- New procedural modes and rendering ---
sprite = Path("upstream/app/src/main/java/eu/chainfire/holeylight/animation/SpritePlayer.java")
t = sprite.read_text(encoding="utf-8")

old = "public enum Mode { SWIRL, SWIRL_SLOW, SWIRL_FAST, COMET, DOUBLE_COMET, BREATH, HEARTBEAT, RADAR, NEON, ORBIT, RIPPLE, BLINK, BLINK_SOFT, SINGLE, TSP, TSP_HIDE }"
new = "public enum Mode { SWIRL, SWIRL_SLOW, SWIRL_FAST, COMET, DOUBLE_COMET, BREATH, HEARTBEAT, RADAR, NEON, COLOR_CHASE, ARC_SWEEP, SPARK, ORBIT, RIPPLE, BLINK, BLINK_SOFT, SINGLE, TSP, TSP_HIDE }"
if old not in t:
    raise SystemExit("mode enum for extra effects not found")
t = t.replace(old, new, 1)

old = '''                (mode == Mode.NEON) ||
                (mode == Mode.ORBIT) ||
                (mode == Mode.RIPPLE);'''
new = '''                (mode == Mode.NEON) ||
                (mode == Mode.COLOR_CHASE) ||
                (mode == Mode.ARC_SWEEP) ||
                (mode == Mode.SPARK) ||
                (mode == Mode.ORBIT) ||
                (mode == Mode.RIPPLE);'''
if old not in t:
    raise SystemExit("procedural mode helper extension anchor not found")
t = t.replace(old, new, 1)

old = '''        } else if (drawMode == Mode.RIPPLE) {
            float cycle = 2100f / safeSpeed;
            float part = (diff % (long)Math.max(1f, cycle)) / cycle;
            int c = activeColors[0];
            paintProcedural.setStyle(Paint.Style.STROKE);
            int waves = effectRippleWaves;
            for (int i = 0; i < waves; i++) {
                float p = (part + (i / (float)waves)) % 1f;
                float rr = radius * (0.63f + (0.37f * p));
                int alpha = Math.max(10, Math.min(255, Math.round(210f * (1f - p) * effectIntensity)));
                paintProcedural.setStrokeWidth((1.2f + (2.5f * (1f - p))) * effectIntensity * dpToPx);
                paintProcedural.setColor((c & 0x00FFFFFF) | (alpha << 24));
                canvas.drawCircle(cx, cy, rr, paintProcedural);
            }
        }
    }'''

new = '''        } else if (drawMode == Mode.RIPPLE) {
            float cycle = 2100f / safeSpeed;
            float part = (diff % (long)Math.max(1f, cycle)) / cycle;
            int c = activeColors[0];
            paintProcedural.setStyle(Paint.Style.STROKE);
            int waves = effectRippleWaves;
            for (int i = 0; i < waves; i++) {
                float p = (part + (i / (float)waves)) % 1f;
                float rr = radius * (0.63f + (0.37f * p));
                int alpha = Math.max(10, Math.min(255, Math.round(210f * (1f - p) * effectIntensity)));
                paintProcedural.setStrokeWidth((1.2f + (2.5f * (1f - p))) * effectIntensity * dpToPx);
                paintProcedural.setColor((c & 0x00FFFFFF) | (alpha << 24));
                canvas.drawCircle(cx, cy, rr, paintProcedural);
            }
        } else if (drawMode == Mode.COLOR_CHASE) {
            float cycle = 2600f / safeSpeed;
            float phase = ((diff % (long)Math.max(1f, cycle)) / cycle) * 360f * effectDirection;
            paintProcedural.setStyle(Paint.Style.STROKE);
            paintProcedural.setStrokeWidth(3.0f * effectIntensity * dpToPx);
            int segments = Math.max(8, activeColors.length * 4);
            for (int i = 0; i < segments; i++) {
                int c = activeColors[i % activeColors.length];
                if (activeColors.length == 1) {
                    float[] hsv = new float[3];
                    Color.colorToHSV(c, hsv);
                    hsv[0] = (hsv[0] + (i * (360f / segments))) % 360f;
                    c = Color.HSVToColor(hsv);
                }
                int alpha = Math.min(255, Math.round(230f * effectIntensity));
                paintProcedural.setColor((c & 0x00FFFFFF) | (alpha << 24));
                float start = phase + (i * (360f / segments));
                canvas.drawArc(cx - radius, cy - radius, cx + radius, cy + radius,
                        start, (260f / segments), false, paintProcedural);
            }
        } else if (drawMode == Mode.ARC_SWEEP) {
            float cycle = 2300f / safeSpeed;
            float phase = ((diff % (long)Math.max(1f, cycle)) / cycle) * 360f * effectDirection;
            int c = activeColors[0];
            int steps = Math.max(5, Math.min(20, Math.round(10f * effectTrail)));
            paintProcedural.setStyle(Paint.Style.STROKE);
            for (int i = 0; i < steps; i++) {
                float p = i / (float)steps;
                int alpha = Math.max(16, Math.min(255, Math.round(255f * (1f - p) * effectIntensity)));
                paintProcedural.setStrokeWidth((4.0f - (2.0f * p)) * effectIntensity * dpToPx);
                paintProcedural.setColor((c & 0x00FFFFFF) | (alpha << 24));
                float dir = effectDirection < 0 ? -1f : 1f;
                canvas.drawArc(cx - radius, cy - radius, cx + radius, cy + radius,
                        phase - (dir * i * 7f), dir * (40f + (80f * effectTrail / steps)), false, paintProcedural);
            }
        } else if (drawMode == Mode.SPARK) {
            float cycle = 1750f / safeSpeed;
            float phase = ((diff % (long)Math.max(1f, cycle)) / cycle) * 360f * effectDirection;
            paintProcedural.setStyle(Paint.Style.FILL);
            int sparks = Math.max(8, Math.round(12f * effectTrail));
            for (int i = 0; i < sparks; i++) {
                float baseAngle = phase + (i * (360f / sparks));
                float wobble = 10f * (float)Math.sin((diff / 130.0) + (i * 1.73));
                float angle = baseAngle + wobble;
                double rad = Math.toRadians(angle);
                float radial = radius - ((i % 3) * 1.8f * dpToPx);
                float pulse = 0.45f + 0.55f * (float)Math.abs(Math.sin((diff / 170.0) + (i * 0.9)));
                int c = activeColors[i % activeColors.length];
                int alpha = Math.min(255, Math.round((80f + 175f * pulse) * effectIntensity));
                paintProcedural.setColor((c & 0x00FFFFFF) | (alpha << 24));
                float rr = (1.2f + (2.4f * pulse)) * effectIntensity * dpToPx;
                canvas.drawCircle(
                        cx + ((float)Math.cos(rad) * radial),
                        cy + ((float)Math.sin(rad) * radial),
                        rr, paintProcedural
                );
            }
        }
    }'''

if old not in t:
    raise SystemExit("renderer extension anchor not found")
t = t.replace(old, new, 1)
sprite.write_text(t, encoding="utf-8")

# --- Register titles / styles ---
settings_file = Path("upstream/app/src/main/java/eu/chainfire/holeylight/misc/Settings.java")
t = settings_file.read_text(encoding="utf-8")

old = '''            new AnimationStyle("neon", SpritePlayer.Mode.NEON, R.string.animation_style_neon_title, R.string.animation_style_location_camera, 4.6f),
            new AnimationStyle("orbit", SpritePlayer.Mode.ORBIT, R.string.animation_style_orbit_title, R.string.animation_style_location_camera, 4.0f),'''
new = '''            new AnimationStyle("neon", SpritePlayer.Mode.NEON, R.string.animation_style_neon_title, R.string.animation_style_location_camera, 4.6f),
            new AnimationStyle("color_chase", SpritePlayer.Mode.COLOR_CHASE, R.string.animation_style_color_chase_title, R.string.animation_style_location_camera, 4.5f),
            new AnimationStyle("arc_sweep", SpritePlayer.Mode.ARC_SWEEP, R.string.animation_style_arc_sweep_title, R.string.animation_style_location_camera, 4.2f),
            new AnimationStyle("spark", SpritePlayer.Mode.SPARK, R.string.animation_style_spark_title, R.string.animation_style_location_camera, 4.4f),
            new AnimationStyle("orbit", SpritePlayer.Mode.ORBIT, R.string.animation_style_orbit_title, R.string.animation_style_location_camera, 4.0f),'''
if old not in t:
    raise SystemExit("animation style extension anchor not found")
t = t.replace(old, new, 1)

# per-app effect setting helpers
needle = '''    private static final String EFFECT_RIPPLE_WAVES = "effect_ripple_waves";'''
replacement = '''    private static final String EFFECT_RIPPLE_WAVES = "effect_ripple_waves";
    private static final String EFFECT_PACKAGE_PREFIX = "effect_package:";'''
if needle not in t:
    raise SystemExit("package effect constant anchor not found")
t = t.replace(needle, replacement, 1)

needle = '''    public void setEffectRippleWaves(int value) {
        put(EFFECT_RIPPLE_WAVES, Math.min(Math.max(value, 2), 6), true);
    }'''
replacement = '''    public void setEffectRippleWaves(int value) {
        put(EFFECT_RIPPLE_WAVES, Math.min(Math.max(value, 2), 6), true);
    }

    public SpritePlayer.Mode getEffectForPackage(String packageName) {
        if (packageName == null) return null;
        String styleName = prefs.getString(EFFECT_PACKAGE_PREFIX + packageName, null);
        if (styleName == null) return null;
        AnimationStyle style = getAnimationStyle(styleName);
        return style == null ? null : style.mode;
    }

    public void setEffectForPackage(String packageName, SpritePlayer.Mode mode) {
        if (packageName == null) return;
        edit();
        try {
            String key = EFFECT_PACKAGE_PREFIX + packageName;
            if (mode == null) {
                editor.remove(key);
            } else {
                AnimationStyle style = getAnimationStyle(mode);
                if (style != null) editor.putString(key, style.name);
            }
        } finally {
            save(true);
        }
    }'''
if needle not in t:
    raise SystemExit("package effect helpers anchor not found")
t = t.replace(needle, replacement, 1)
settings_file.write_text(t, encoding="utf-8")

for rel, strings in [
    ("upstream/app/src/main/res/values/strings.xml", [
        ("animation_style_color_chase_title", "Color chase"),
        ("animation_style_arc_sweep_title", "Arc sweep"),
        ("animation_style_spark_title", "Spark"),
    ]),
    ("upstream/app/src/main/res/values-it/strings.xml", [
        ("animation_style_color_chase_title", "Color chase"),
        ("animation_style_arc_sweep_title", "Arc sweep"),
        ("animation_style_spark_title", "Spark"),
    ]),
]:
    p = Path(rel)
    txt = p.read_text(encoding="utf-8")
    if "animation_style_color_chase_title" not in txt:
        block = "\n" + "\n".join([f'    <string name="{k}">{v}</string>' for k, v in strings]) + "\n"
        txt = txt.replace("</resources>", block + "</resources>")
        p.write_text(txt, encoding="utf-8")

# --- Pass notification package to Overlay, then apply per-app effect if one app is active ---
listener = Path("upstream/app/src/main/java/eu/chainfire/holeylight/service/NotificationListenerService.java")
t = listener.read_text(encoding="utf-8")

old = '''            int[] currentColors = new int[currentNotifications.size()];
            Drawable[] currentIcons = new Drawable[currentNotifications.size()];
            for (int i = 0; i < currentNotifications.size(); i++) {
                currentColors[i] = currentNotifications.get(i).getColor();
                currentIcons[i] = currentNotifications.get(i).getIconDrawable(this);
            }
            if (overlay != null) {
                overlay.show(currentColors, currentIcons, forceRefresh);'''
new = '''            int[] currentColors = new int[currentNotifications.size()];
            Drawable[] currentIcons = new Drawable[currentNotifications.size()];
            String[] currentPackages = new String[currentNotifications.size()];
            for (int i = 0; i < currentNotifications.size(); i++) {
                currentColors[i] = currentNotifications.get(i).getColor();
                currentIcons[i] = currentNotifications.get(i).getIconDrawable(this);
                currentPackages[i] = currentNotifications.get(i).getPackageName();
            }
            if (overlay != null) {
                overlay.show(currentColors, currentIcons, currentPackages, forceRefresh);'''
if old not in t:
    raise SystemExit("listener package forwarding anchor not found")
t = t.replace(old, new, 1)
listener.write_text(t, encoding="utf-8")

overlay = Path("upstream/app/src/main/java/eu/chainfire/holeylight/animation/Overlay.java")
t = overlay.read_text(encoding="utf-8")

# add packages field near colors/icons
needle = '''    private int[] colors = new int[0];
    private Drawable[] icons = new Drawable[0];'''
replacement = '''    private int[] colors = new int[0];
    private Drawable[] icons = new Drawable[0];
    private String[] packages = new String[0];'''
if needle not in t:
    raise SystemExit("overlay packages field anchor not found")
t = t.replace(needle, replacement, 1)

# override renderMode when exactly one unique package is active
needle = '''        SpritePlayer.Mode renderMode = settings.getAnimationMode(mode);
        SpritePlayer.Mode renderModeOff = settings.getAnimationMode(modeOff);'''
replacement = '''        SpritePlayer.Mode renderMode = settings.getAnimationMode(mode);
        SpritePlayer.Mode renderModeOff = settings.getAnimationMode(modeOff);

        String singlePackage = null;
        if ((packages != null) && (packages.length > 0)) {
            singlePackage = packages[0];
            for (int i = 1; i < packages.length; i++) {
                if ((singlePackage == null) || !singlePackage.equals(packages[i])) {
                    singlePackage = null;
                    break;
                }
            }
        }
        if (singlePackage != null) {
            SpritePlayer.Mode packageMode = settings.getEffectForPackage(singlePackage);
            if (packageMode != null) {
                renderMode = packageMode;
                renderModeOff = packageMode;
            }
        }'''
if needle not in t:
    raise SystemExit("overlay per-package mode anchor not found")
t = t.replace(needle, replacement, 1)

old = '''    public void show(int[] colors, Drawable[] icons, boolean forceRefresh) {
        if (terminated) return;
        handler.removeCallbacks(evaluateLoop);
        this.colors = colors;
        this.icons = icons;'''
new = '''    public void show(int[] colors, Drawable[] icons, boolean forceRefresh) {
        show(colors, icons, new String[0], forceRefresh);
    }

    public void show(int[] colors, Drawable[] icons, String[] packages, boolean forceRefresh) {
        if (terminated) return;
        handler.removeCallbacks(evaluateLoop);
        this.colors = colors;
        this.icons = icons;
        this.packages = packages == null ? new String[0] : packages;'''
if old not in t:
    raise SystemExit("overlay show overload anchor not found")
t = t.replace(old, new, 1)
overlay.write_text(t, encoding="utf-8")

# --- UI: expose new effects, presets, per-app picker ---
frag = Path("upstream/app/src/main/java/eu/chainfire/holeylight/ui/SettingsFragment.java")
t = frag.read_text(encoding="utf-8")

old = '''                    SpritePlayer.Mode.RADAR,
                    SpritePlayer.Mode.NEON,
                    SpritePlayer.Mode.ORBIT,'''
new = '''                    SpritePlayer.Mode.RADAR,
                    SpritePlayer.Mode.NEON,
                    SpritePlayer.Mode.COLOR_CHASE,
                    SpritePlayer.Mode.ARC_SWEEP,
                    SpritePlayer.Mode.SPARK,
                    SpritePlayer.Mode.ORBIT,'''
if t.count(old) < 2:
    raise SystemExit("effect picker new modes anchors not found")
t = t.replace(old, new, 2)

# insert presets + per-app before Direction effects
anchor = '''        Preference prefEffectDirection = pref(catAnimation, 0, 0, null, true, null);'''
if anchor not in t:
    raise SystemExit("preset/per-app UI anchor not found")

block = '''        Preference prefEffectPreset = pref(catAnimation, 0, 0, null, true, null);
        prefEffectPreset.setTitle("Preset effetti");
        prefEffectPreset.setSummary("Personalizzato");
        prefEffectPreset.setOnPreferenceClickListener(preference -> {
            final CharSequence[] labels = new CharSequence[] { "Discreto", "Normale", "Wow" };
            (new AlertDialog.Builder(getContext()))
                    .setTitle("Preset effetti")
                    .setItems(labels, (dialog, which) -> {
                        if (which == 0) {
                            settings.setEffectSpeed(0.75f);
                            settings.setEffectIntensity(0.70f);
                            settings.setEffectTrail(0.65f);
                            settings.setEffectOrbitDots(3);
                            settings.setEffectRippleWaves(2);
                        } else if (which == 1) {
                            settings.setEffectSpeed(1.00f);
                            settings.setEffectIntensity(1.00f);
                            settings.setEffectTrail(1.00f);
                            settings.setEffectOrbitDots(4);
                            settings.setEffectRippleWaves(3);
                        } else {
                            settings.setEffectSpeed(1.50f);
                            settings.setEffectIntensity(1.40f);
                            settings.setEffectTrail(1.70f);
                            settings.setEffectOrbitDots(6);
                            settings.setEffectRippleWaves(5);
                        }
                        preference.setSummary(labels[which]);
                        previewCurrentEffect.run();
                    })
                    .setNegativeButton(android.R.string.cancel, null)
                    .show();
            return true;
        });

        Preference prefPerAppEffects = pref(catAnimation, 0, 0, null, true, null);
        prefPerAppEffects.setTitle("Effetti per app");
        prefPerAppEffects.setSummary("Scegli un effetto diverso per singole app");
        prefPerAppEffects.setOnPreferenceClickListener(preference -> {
            android.content.pm.PackageManager pm = getContext().getPackageManager();
            java.util.List<android.content.pm.ApplicationInfo> apps = pm.getInstalledApplications(0);
            java.util.ArrayList<android.content.pm.ApplicationInfo> shown = new java.util.ArrayList<>();
            for (android.content.pm.ApplicationInfo app : apps) {
                if (pm.getLaunchIntentForPackage(app.packageName) != null) {
                    shown.add(app);
                }
            }
            java.util.Collections.sort(shown, (a, b) ->
                    pm.getApplicationLabel(a).toString().compareToIgnoreCase(pm.getApplicationLabel(b).toString()));

            CharSequence[] labels = new CharSequence[shown.size()];
            for (int i = 0; i < shown.size(); i++) {
                android.content.pm.ApplicationInfo ai = shown.get(i);
                SpritePlayer.Mode saved = settings.getEffectForPackage(ai.packageName);
                String suffix = saved == null ? "" : " — " + getString(settings.getAnimationStyle(saved).title);
                labels[i] = pm.getApplicationLabel(ai) + suffix;
            }

            (new AlertDialog.Builder(getContext()))
                    .setTitle("Effetti per app")
                    .setItems(labels, (dialog, which) -> {
                        android.content.pm.ApplicationInfo ai = shown.get(which);
                        final SpritePlayer.Mode[] modes = new SpritePlayer.Mode[] {
                                null,
                                SpritePlayer.Mode.SWIRL,
                                SpritePlayer.Mode.COMET,
                                SpritePlayer.Mode.DOUBLE_COMET,
                                SpritePlayer.Mode.BREATH,
                                SpritePlayer.Mode.HEARTBEAT,
                                SpritePlayer.Mode.RADAR,
                                SpritePlayer.Mode.NEON,
                                SpritePlayer.Mode.COLOR_CHASE,
                                SpritePlayer.Mode.ARC_SWEEP,
                                SpritePlayer.Mode.SPARK,
                                SpritePlayer.Mode.ORBIT,
                                SpritePlayer.Mode.RIPPLE,
                                SpritePlayer.Mode.BLINK_SOFT,
                                SpritePlayer.Mode.BLINK,
                                SpritePlayer.Mode.SINGLE
                        };
                        CharSequence[] effectLabels = new CharSequence[modes.length];
                        effectLabels[0] = "Usa effetto globale";
                        for (int j = 1; j < modes.length; j++) {
                            effectLabels[j] = getString(settings.getAnimationStyle(modes[j]).title);
                        }
                        (new AlertDialog.Builder(getContext()))
                                .setTitle(pm.getApplicationLabel(ai))
                                .setItems(effectLabels, (dialog2, selected) -> {
                                    settings.setEffectForPackage(ai.packageName, modes[selected]);
                                    if (modes[selected] != null) {
                                        eu.chainfire.holeylight.animation.Overlay overlay = eu.chainfire.holeylight.animation.Overlay.getInstance();
                                        if (overlay != null) overlay.preview(modes[selected]);
                                    }
                                })
                                .setNegativeButton(android.R.string.cancel, null)
                                .show();
                    })
                    .setNegativeButton(android.R.string.cancel, null)
                    .show();
            return true;
        });

''' + anchor
t = t.replace(anchor, block, 1)
frag.write_text(t, encoding="utf-8")

print("Added ColorChase/ArcSweep/Spark, presets and per-app effects")


# 22) Minimal fix from known-good 7741fc7d build:
# move battery info OUT of the camera SurfaceView and place it in a tiny
# independent side overlay, away from the S24 fingerprint sensor.
#
# No other AOD behavior is changed in this pass.

# --- Stop drawing battery percentage/bar inside the camera SurfaceView.
sprite = Path("upstream/app/src/main/java/eu/chainfire/holeylight/animation/SpritePlayer.java")
t = sprite.read_text(encoding="utf-8")

start = t.find('''        // S24 partial-AOD profile: Holey Light owns the battery indicator so it''')
if start == -1:
    raise SystemExit("battery render block start not found")
end = t.find('''        if (isTSPMode()) {''', start)
if end == -1:
    raise SystemExit("battery render block end not found")
t = t[:start] + t[end:]
sprite.write_text(t, encoding="utf-8")

# --- Render battery status in a small side window, only with no notifications.
overlay = Path("upstream/app/src/main/java/eu/chainfire/holeylight/animation/Overlay.java")
t = overlay.read_text(encoding="utf-8")

needle = '''    private boolean added = false;
    private final ResolutionTracker resolutionTracker;'''
replacement = '''    private boolean added = false;

    // S24 battery status panel: a very small independent overlay positioned
    // to the RIGHT of the ultrasonic fingerprint target. It never spans the
    // center of the screen, so One UI can keep rendering the fingerprint icon.
    private android.widget.LinearLayout s24BatteryPanel = null;
    private android.widget.TextView s24BatteryText = null;
    private android.widget.ProgressBar s24BatteryBar = null;
    private boolean s24BatteryPanelAdded = false;

    private final ResolutionTracker resolutionTracker;'''
if needle not in t:
    raise SystemExit("Overlay fields anchor not found")
t = t.replace(needle, replacement, 1)

needle = '''    private void updateParams() {
        if (terminated) return;
        animation.applyDimensions();
    }

    private void createOverlay() {'''
replacement = '''    private int s24dp(float value) {
        return Math.round(android.util.TypedValue.applyDimension(
                android.util.TypedValue.COMPLEX_UNIT_DIP,
                value,
                spritePlayer.getContext().getResources().getDisplayMetrics()
        ));
    }

    private void ensureS24BatteryPanel(Context context) {
        if (s24BatteryPanel != null) return;

        s24BatteryPanel = new android.widget.LinearLayout(context);
        s24BatteryPanel.setOrientation(android.widget.LinearLayout.VERTICAL);
        s24BatteryPanel.setGravity(Gravity.CENTER);
        s24BatteryPanel.setBackgroundColor(Color.TRANSPARENT);

        s24BatteryText = new android.widget.TextView(context);
        s24BatteryText.setTextColor(Color.WHITE);
        s24BatteryText.setTextSize(android.util.TypedValue.COMPLEX_UNIT_SP, 10f);
        s24BatteryText.setGravity(Gravity.CENTER);
        s24BatteryText.setIncludeFontPadding(false);
        s24BatteryPanel.addView(
                s24BatteryText,
                new android.widget.LinearLayout.LayoutParams(
                        s24dp(92f),
                        android.view.ViewGroup.LayoutParams.WRAP_CONTENT
                )
        );

        s24BatteryBar = new android.widget.ProgressBar(
                context,
                null,
                android.R.attr.progressBarStyleHorizontal
        );
        s24BatteryBar.setIndeterminate(false);
        s24BatteryBar.setMax(100);
        s24BatteryBar.setProgressTintList(
                android.content.res.ColorStateList.valueOf(Color.WHITE)
        );
        s24BatteryBar.setProgressBackgroundTintList(
                android.content.res.ColorStateList.valueOf(0x44FFFFFF)
        );

        android.widget.LinearLayout.LayoutParams barParams =
                new android.widget.LinearLayout.LayoutParams(
                        s24dp(72f),
                        Math.max(2, s24dp(3f))
                );
        barParams.topMargin = s24dp(4f);
        s24BatteryPanel.addView(s24BatteryBar, barParams);
    }

    private void showS24BatteryPanel(Context context) {
        ensureS24BatteryPanel(context);

        android.os.BatteryManager bm =
                (android.os.BatteryManager)context.getSystemService(Context.BATTERY_SERVICE);
        int level = bm == null
                ? -1
                : bm.getIntProperty(android.os.BatteryManager.BATTERY_PROPERTY_CAPACITY);
        if (level < 0 || level > 100) {
            hideS24BatteryPanel();
            return;
        }

        s24BatteryText.setText(level + "%");
        s24BatteryBar.setProgress(level);

        if (s24BatteryPanelAdded) return;

        WindowManager.LayoutParams p = new WindowManager.LayoutParams(
                s24dp(100f),
                s24dp(34f),
                WindowManager.LayoutParams.TYPE_ACCESSIBILITY_OVERLAY,
                  WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE
                | WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE
                | WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN
                | WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
                PixelFormat.TRANSLUCENT
        );
        // Keep this tiny window on the far right, level with the fingerprint
        // region but not covering the center sensor target.
        p.gravity = Gravity.RIGHT | Gravity.BOTTOM;
        p.x = s24dp(12f);
        p.y = s24dp(155f);
        p.setTitle("HoleyLight S24 Battery Side");
        if (windowToken != null) p.token = windowToken;

        try {
            windowManager.addView(s24BatteryPanel, p);
            s24BatteryPanelAdded = true;
        } catch (Exception e) {
            e.printStackTrace();
            s24BatteryPanelAdded = false;
        }
    }

    private void hideS24BatteryPanel() {
        if (!s24BatteryPanelAdded || s24BatteryPanel == null) return;
        try {
            windowManager.removeView(s24BatteryPanel);
        } catch (Exception ignored) {
        }
        s24BatteryPanelAdded = false;
    }

    private void updateParams() {
        if (terminated) return;
        animation.applyDimensions();
    }

    private void createOverlay() {'''
if needle not in t:
    raise SystemExit("Overlay helper insertion anchor not found")
t = t.replace(needle, replacement, 1)

needle = '''        boolean hideAODEffective = activeHide || isHideAODAndDoze;

        if (forceRefresh) log("Force refresh");'''
replacement = '''        boolean hideAODEffective = activeHide || isHideAODAndDoze;

        // Exact user-requested behavior: only when there are NO notification
        // colors and the partial AOD profile is selected. Notifications keep
        // using the untouched 7741fc7d animation path.
        boolean showBatteryAtSide =
                !haveColors &&
                settings.isHideAOD() &&
                !settings.isHideAODFully() &&
                (doze || !on);

        if (showBatteryAtSide) {
            showS24BatteryPanel(context);
        } else {
            hideS24BatteryPanel();
        }

        if (forceRefresh) log("Force refresh");'''
if needle not in t:
    raise SystemExit("Overlay evaluate battery anchor not found")
t = t.replace(needle, replacement, 1)

old = '''            if (animation.isPlaying()) animation.stop(true);
            removeOverlay();
            animation = null;'''
new = '''            if (animation.isPlaying()) animation.stop(true);
            removeOverlay();
            hideS24BatteryPanel();
            animation = null;'''
if old not in t:
    raise SystemExit("Overlay shutdown cleanup anchor not found")
t = t.replace(old, new, 1)

overlay.write_text(t, encoding="utf-8")

print("Moved no-notification battery info to a tiny side panel; 7741 base otherwise unchanged")


# 23) S24 bottom battery panel + reduced AOD.
# Built on top of the known-good 7741fc7d base and the minimal side-panel fix.
# The notification/AOD renderer itself is otherwise left untouched.

# --- Persist the reduced-AOD profile as a separate S24 setting.
settings_file = Path("upstream/app/src/main/java/eu/chainfire/holeylight/misc/Settings.java")
t = settings_file.read_text(encoding="utf-8")

needle = '''    public static final String AOD_SHOW_CLOCK = "aod_show_clock";
    public static final boolean AOD_SHOW_CLOCK_DEFAULT = false;'''
replacement = '''    public static final String AOD_SHOW_CLOCK = "aod_show_clock";
    public static final boolean AOD_SHOW_CLOCK_DEFAULT = false;

    public static final String S24_REDUCED_AOD = "s24_reduced_aod";
    public static final boolean S24_REDUCED_AOD_DEFAULT = false;'''
if needle not in t:
    raise SystemExit("S24 reduced AOD constant anchor not found")
t = t.replace(needle, replacement, 1)

needle = '''    public void setShowAODClock(boolean value) {
        put(AOD_SHOW_CLOCK, value, true);
    }'''
replacement = '''    public void setShowAODClock(boolean value) {
        put(AOD_SHOW_CLOCK, value, true);
    }

    public boolean isS24ReducedAOD() {
        return prefs.getBoolean(S24_REDUCED_AOD, S24_REDUCED_AOD_DEFAULT);
    }

    public void setS24ReducedAOD(boolean value) {
        put(S24_REDUCED_AOD, value, true);
    }'''
if needle not in t:
    raise SystemExit("S24 reduced AOD getter anchor not found")
t = t.replace(needle, replacement, 1)
settings_file.write_text(t, encoding="utf-8")

# --- Upgrade the tiny battery side window into a bottom-centered panel.
overlay = Path("upstream/app/src/main/java/eu/chainfire/holeylight/animation/Overlay.java")
t = overlay.read_text(encoding="utf-8")

needle = '''    private android.widget.LinearLayout s24BatteryPanel = null;
    private android.widget.TextView s24BatteryText = null;
    private android.widget.ProgressBar s24BatteryBar = null;
    private boolean s24BatteryPanelAdded = false;'''
replacement = '''    private android.widget.LinearLayout s24BatteryPanel = null;
    private android.widget.TextView s24ClockText = null;
    private android.widget.TextView s24BatteryText = null;
    private android.widget.TextView s24BatteryDetail = null;
    private android.widget.ProgressBar s24BatteryBar = null;
    private boolean s24BatteryPanelAdded = false;

    private final Runnable s24BatteryTicker = new Runnable() {
        @Override
        public void run() {
            if (s24BatteryPanelAdded && spritePlayer != null) {
                updateS24BatteryPanel(spritePlayer.getContext());
                handler.postDelayed(this, 60000L);
            }
        }
    };'''
if needle not in t:
    raise SystemExit("S24 panel fields anchor not found")
t = t.replace(needle, replacement, 1)

start = t.find('''    private void ensureS24BatteryPanel(Context context) {''')
if start == -1:
    raise SystemExit("ensureS24BatteryPanel start not found")
end = t.find('''    private void hideS24BatteryPanel() {''', start)
if end == -1:
    raise SystemExit("hideS24BatteryPanel anchor not found")

new_methods = '''    private void ensureS24BatteryPanel(Context context) {
        if (s24BatteryPanel != null) return;

        s24BatteryPanel = new android.widget.LinearLayout(context);
        s24BatteryPanel.setOrientation(android.widget.LinearLayout.VERTICAL);
        s24BatteryPanel.setGravity(Gravity.CENTER);
        s24BatteryPanel.setBackgroundColor(Color.TRANSPARENT);

        s24ClockText = new android.widget.TextView(context);
        s24ClockText.setTextColor(Color.WHITE);
        s24ClockText.setTextSize(android.util.TypedValue.COMPLEX_UNIT_SP, 13f);
        s24ClockText.setGravity(Gravity.CENTER);
        s24ClockText.setIncludeFontPadding(false);
        s24BatteryPanel.addView(
                s24ClockText,
                new android.widget.LinearLayout.LayoutParams(
                        s24dp(180f),
                        android.view.ViewGroup.LayoutParams.WRAP_CONTENT
                )
        );

        s24BatteryText = new android.widget.TextView(context);
        s24BatteryText.setTextColor(Color.WHITE);
        s24BatteryText.setTextSize(android.util.TypedValue.COMPLEX_UNIT_SP, 11f);
        s24BatteryText.setGravity(Gravity.CENTER);
        s24BatteryText.setIncludeFontPadding(false);
        s24BatteryPanel.addView(
                s24BatteryText,
                new android.widget.LinearLayout.LayoutParams(
                        s24dp(180f),
                        android.view.ViewGroup.LayoutParams.WRAP_CONTENT
                )
        );

        s24BatteryDetail = new android.widget.TextView(context);
        s24BatteryDetail.setTextColor(0xDDFFFFFF);
        s24BatteryDetail.setTextSize(android.util.TypedValue.COMPLEX_UNIT_SP, 9f);
        s24BatteryDetail.setGravity(Gravity.CENTER);
        s24BatteryDetail.setIncludeFontPadding(false);
        android.widget.LinearLayout.LayoutParams detailParams =
                new android.widget.LinearLayout.LayoutParams(
                        s24dp(180f),
                        android.view.ViewGroup.LayoutParams.WRAP_CONTENT
                );
        detailParams.topMargin = s24dp(2f);
        s24BatteryPanel.addView(s24BatteryDetail, detailParams);

        s24BatteryBar = new android.widget.ProgressBar(
                context,
                null,
                android.R.attr.progressBarStyleHorizontal
        );
        s24BatteryBar.setIndeterminate(false);
        s24BatteryBar.setMax(100);
        s24BatteryBar.setProgressTintList(
                android.content.res.ColorStateList.valueOf(Color.WHITE)
        );
        s24BatteryBar.setProgressBackgroundTintList(
                android.content.res.ColorStateList.valueOf(0x44FFFFFF)
        );

        android.widget.LinearLayout.LayoutParams barParams =
                new android.widget.LinearLayout.LayoutParams(
                        s24dp(92f),
                        Math.max(2, s24dp(3f))
                );
        barParams.topMargin = s24dp(4f);
        s24BatteryPanel.addView(s24BatteryBar, barParams);
    }

    private String s24FormatDuration(long millis) {
        if (millis <= 0) return null;
        long minutes = Math.max(1L, millis / 60000L);
        long hours = minutes / 60L;
        long mins = minutes % 60L;
        if (hours > 0L && mins > 0L) return hours + " h " + mins + " m";
        if (hours > 0L) return hours + " h";
        return mins + " m";
    }

    private long s24EstimateDischargeRemaining(android.os.BatteryManager bm) {
        if (bm == null) return -1L;
        long chargeCounter = bm.getLongProperty(android.os.BatteryManager.BATTERY_PROPERTY_CHARGE_COUNTER);
        long currentNow = bm.getLongProperty(android.os.BatteryManager.BATTERY_PROPERTY_CURRENT_NOW);
        if (chargeCounter <= 0L || currentNow == 0L || currentNow == Long.MIN_VALUE) return -1L;

        double hours = (double)chargeCounter / (double)Math.abs(currentNow);
        if (hours < (5.0 / 60.0) || hours > (24.0 * 7.0)) return -1L;
        return (long)(hours * 60.0 * 60.0 * 1000.0);
    }

    private void updateS24BatteryPanel(Context context) {
        if (s24BatteryPanel == null) return;

        android.os.BatteryManager bm =
                (android.os.BatteryManager)context.getSystemService(Context.BATTERY_SERVICE);
        int level = bm == null
                ? -1
                : bm.getIntProperty(android.os.BatteryManager.BATTERY_PROPERTY_CAPACITY);
        if (level < 0 || level > 100) return;

        boolean charging = Battery.isCharging(context);
        boolean reduced = settings.isS24ReducedAOD();

        s24ClockText.setVisibility(reduced ? View.VISIBLE : View.GONE);
        if (reduced) {
            java.text.SimpleDateFormat sdf =
                    new java.text.SimpleDateFormat("HH:mm", java.util.Locale.getDefault());
            s24ClockText.setText(sdf.format(new java.util.Date()));
        }

        s24BatteryText.setText((charging ? "⚡ " : "") + level + "%");

        String detail = null;
        if (charging && Build.VERSION.SDK_INT >= Build.VERSION_CODES.P && bm != null) {
            long remaining = bm.computeChargeTimeRemaining();
            String formatted = s24FormatDuration(remaining);
            if (formatted != null) detail = formatted + " alla carica max";
        } else if (!charging) {
            long estimate = s24EstimateDischargeRemaining(bm);
            String formatted = s24FormatDuration(estimate);
            if (formatted != null) detail = "≈ " + formatted + " autonomia";
        }

        if (detail == null) {
            detail = charging ? "In carica" : "";
        }
        s24BatteryDetail.setText(detail);
        s24BatteryDetail.setVisibility(detail.length() > 0 ? View.VISIBLE : View.GONE);

        s24BatteryBar.setProgress(level);
        // Reduced AOD stays as light as possible: text only, no progress-bar refresh.
        s24BatteryBar.setVisibility(reduced ? View.GONE : View.VISIBLE);
    }

    private void showS24BatteryPanel(Context context) {
        ensureS24BatteryPanel(context);
        updateS24BatteryPanel(context);

        boolean reduced = settings.isS24ReducedAOD();

        if (s24BatteryPanelAdded) {
            WindowManager.LayoutParams current =
                    (WindowManager.LayoutParams)s24BatteryPanel.getLayoutParams();
            int wantedHeight = s24dp(reduced ? 70f : 54f);
            if (current.height != wantedHeight) {
                current.height = wantedHeight;
                try {
                    windowManager.updateViewLayout(s24BatteryPanel, current);
                } catch (Exception ignored) {
                }
            }
            return;
        }

        WindowManager.LayoutParams p = new WindowManager.LayoutParams(
                s24dp(190f),
                s24dp(reduced ? 70f : 54f),
                WindowManager.LayoutParams.TYPE_ACCESSIBILITY_OVERLAY,
                  WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE
                | WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE
                | WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN
                | WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
                PixelFormat.TRANSLUCENT
        );

        // The S24 fingerprint target sits above this region. Keeping the panel
        // centered but low gives the requested order: fingerprint -> time (optional)
        // -> battery, without covering the ultrasonic sensor itself.
        p.gravity = Gravity.CENTER_HORIZONTAL | Gravity.BOTTOM;
        p.x = 0;
        p.y = s24dp(46f);
        p.setTitle("HoleyLight S24 Bottom Info");
        if (windowToken != null) p.token = windowToken;

        try {
            windowManager.addView(s24BatteryPanel, p);
            s24BatteryPanelAdded = true;
            handler.removeCallbacks(s24BatteryTicker);
            handler.postDelayed(s24BatteryTicker, 60000L);
        } catch (Exception e) {
            e.printStackTrace();
            s24BatteryPanelAdded = false;
        }
    }

'''
t = t[:start] + new_methods + t[end:]

old = '''    private void hideS24BatteryPanel() {
        if (!s24BatteryPanelAdded || s24BatteryPanel == null) return;
        try {
            windowManager.removeView(s24BatteryPanel);
        } catch (Exception ignored) {
        }
        s24BatteryPanelAdded = false;
    }'''
new = '''    private void hideS24BatteryPanel() {
        handler.removeCallbacks(s24BatteryTicker);
        if (!s24BatteryPanelAdded || s24BatteryPanel == null) return;
        try {
            windowManager.removeView(s24BatteryPanel);
        } catch (Exception ignored) {
        }
        s24BatteryPanelAdded = false;
    }'''
if old not in t:
    raise SystemExit("hideS24BatteryPanel block not found")
t = t.replace(old, new, 1)

old = '''        // Exact user-requested behavior: only when there are NO notification
        // colors and the partial AOD profile is selected. Notifications keep
        // using the untouched 7741fc7d animation path.
        boolean showBatteryAtSide =
                !haveColors &&
                settings.isHideAOD() &&
                !settings.isHideAODFully() &&
                (doze || !on);

        if (showBatteryAtSide) {
            showS24BatteryPanel(context);
        } else {
            hideS24BatteryPanel();
        }'''
new = '''        // Only when there are NO notifications and the partial S24 AOD profile
        // is active. Notifications keep using the untouched 7741fc7d animation path.
        boolean showBottomInfo =
                !haveColors &&
                settings.isHideAOD() &&
                !settings.isHideAODFully() &&
                (doze || !on);

        if (showBottomInfo) {
            showS24BatteryPanel(context);
        } else {
            hideS24BatteryPanel();
        }'''
if old not in t:
    raise SystemExit("showBatteryAtSide block not found")
t = t.replace(old, new, 1)

overlay.write_text(t, encoding="utf-8")

# --- Add the reduced-AOD choice to the S24 profile selector.
frag = Path("upstream/app/src/main/java/eu/chainfire/holeylight/ui/SettingsFragment.java")
t = frag.read_text(encoding="utf-8")

old = '''            if (!settings.isHideAOD()) {
                summary = "AOD Samsung completo";
            } else if (settings.isHideAODFully()) {
                summary = "Vortice minimale";
            } else {
                summary = "Impronta + batteria";
            }'''
new = '''            if (!settings.isHideAOD()) {
                summary = "AOD Samsung completo";
            } else if (settings.isHideAODFully()) {
                summary = "Vortice minimale";
            } else if (settings.isS24ReducedAOD()) {
                summary = "AOD ridotto";
            } else {
                summary = "Impronta + batteria";
            }'''
if old not in t:
    raise SystemExit("final S24 profile summary block not found")
t = t.replace(old, new, 1)

old = '''                    .setItems(new CharSequence[] {
                            "AOD Samsung completo\\nOrologio e contenuti One UI visibili",
                            "Impronta + batteria\\nSchermo nero, impronta Samsung e batteria disegnata da Holey Light",
                            "Vortice minimale\\nSchermo nero e vortice; l'impronta può restare se One UI è impostata per mostrarla"
                    }, (dialog, which) -> {'''
new = '''                    .setItems(new CharSequence[] {
                            "AOD Samsung completo\\nOrologio e contenuti One UI visibili",
                            "Impronta + batteria\\nImpronta Samsung; sotto percentuale e autonomia/carica",
                            "AOD ridotto\\nImpronta; sotto ora piccola e informazioni batteria",
                            "Vortice minimale\\nSchermo nero e vortice; l'impronta può restare se One UI è impostata per mostrarla"
                    }, (dialog, which) -> {'''
if old not in t:
    raise SystemExit("final S24 profile list block not found")
t = t.replace(old, new, 1)

old = '''                        switch (which) {
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
                        }'''
new = '''                        switch (which) {
                            case 0:
                                settings.setS24ReducedAOD(false);
                                settings.setHideAOD(false, false);
                                settings.setShowAODClock(false);
                                break;
                            case 1:
                                settings.setS24ReducedAOD(false);
                                settings.setHideAOD(true, false);
                                settings.setShowAODClock(false);
                                break;
                            case 2:
                                settings.setS24ReducedAOD(true);
                                settings.setHideAOD(true, false);
                                settings.setShowAODClock(false);
                                break;
                            case 3:
                                settings.setS24ReducedAOD(false);
                                settings.setHideAOD(true, true);
                                settings.setShowAODClock(false);
                                break;
                        }'''
if old not in t:
    raise SystemExit("final S24 profile switch block not found")
t = t.replace(old, new, 1)

frag.write_text(t, encoding="utf-8")

print("Added bottom-centered battery info and S24 reduced AOD mode")
