from pathlib import Path

overlay = Path("upstream/app/src/main/java/eu/chainfire/holeylight/animation/Overlay.java")
text = overlay.read_text(encoding="utf-8")

old = """        params.gravity = Gravity.LEFT | Gravity.TOP;
        params.setTitle("HoleyLight");"""

new = """        params.gravity = Gravity.LEFT | Gravity.TOP;

        // S24 / modern Android: allow the accessibility overlay to occupy the
        // display-cutout area instead of being clipped at the top safe inset.
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
            params.layoutInDisplayCutoutMode =
                    (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R)
                            ? WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_ALWAYS
                            : WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES;
        }

        params.setTitle("HoleyLight");"""

if old not in text:
    raise SystemExit("Overlay.java insertion point not found; upstream changed")

overlay.write_text(text.replace(old, new, 1), encoding="utf-8")
print("Applied S24 display-cutout overlay fix")
