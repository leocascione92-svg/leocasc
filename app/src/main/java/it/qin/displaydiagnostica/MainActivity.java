package it.qin.displaydiagnostica;

import android.app.Activity;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.pm.PackageInfo;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Build;
import android.os.Bundle;
import android.view.Gravity;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;
import java.lang.reflect.Field;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;

/** Only reflective getters: never calls MediaTek set* functions or changes Android settings. */
public final class MainActivity extends Activity {
    private TextView result;
    private Button run, copy;
    private String report = "";
    private int dp(int n) { return (int)(n * getResources().getDisplayMetrics().density + 0.5f); }
    private TextView makeText(String text, int size, int color) {
        TextView t = new TextView(this);
        t.setText(text); t.setTextSize(size); t.setTextColor(color); return t;
    }

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        int bg = Color.rgb(43, 47, 51), fg = Color.rgb(232, 233, 229);
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(bg);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(16), dp(18), dp(16), dp(20));
        scroll.addView(root);

        TextView title = makeText("QIN DISPLAY", 23, fg);
        title.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        root.addView(title);
        TextView label = makeText("Diagnostica MiraVision 0.1", 15, Color.rgb(174, 197, 209));
        root.addView(label);
        TextView notice = makeText("SOLA LETTURA · Nessun root, permesso speciale o cambio colori. Verifica l'accesso alle API MediaTek originali.", 14, fg);
        notice.setPadding(0, dp(14), 0, dp(12));
        root.addView(notice);

        run = new Button(this); run.setText("ESEGUI DIAGNOSI");
        root.addView(run, new LinearLayout.LayoutParams(-1, -2));
        copy = new Button(this); copy.setText("COPIA RISULTATO"); copy.setEnabled(false);
        root.addView(copy, new LinearLayout.LayoutParams(-1, -2));

        result = makeText("Premi ESEGUI DIAGNOSI per leggere i dati. Non verra' modificata alcuna impostazione.", 14, fg);
        result.setTypeface(Typeface.MONOSPACE);
        result.setTextIsSelectable(true);
        result.setBackgroundColor(Color.rgb(57, 63, 68));
        result.setPadding(dp(12), dp(12), dp(12), dp(12));
        LinearLayout.LayoutParams box = new LinearLayout.LayoutParams(-1, -2);
        box.topMargin = dp(12);
        root.addView(result, box);
        setContentView(scroll);

        run.setOnClickListener(v -> {
            run.setEnabled(false); result.setText("Diagnosi in corso...");
            new Thread(() -> {
                final String text = diagnose();
                runOnUiThread(() -> {
                    report = text; result.setText(report);
                    run.setEnabled(true); copy.setEnabled(true);
                });
            }).start();
        });
        copy.setOnClickListener(v -> {
            ClipboardManager clipboard = (ClipboardManager)getSystemService(Context.CLIPBOARD_SERVICE);
            if (clipboard != null) {
                clipboard.setPrimaryClip(ClipData.newPlainText("Diagnostica MiraVision", report));
                Toast.makeText(this, "Risultato copiato", Toast.LENGTH_SHORT).show();
            }
        });
    }

    private String diagnose() {
        StringBuilder out = new StringBuilder("QIN DISPLAY DIAGNOSTICA 0.1\nSolo lettura\n\n");
        out.append("Modello: ").append(Build.MODEL).append("\nAndroid: ").append(Build.VERSION.RELEASE).append("\n\n");
        try {
            PackageInfo p = getPackageManager().getPackageInfo("com.mediatek.miravision.ui", 0);
            out.append("MiraVision: installata (versione ").append(p.versionName).append(")\n\n");
        } catch (Throwable e) {
            out.append("MiraVision: non visibile (").append(error(e)).append(")\n\n");
        }
        Class<?> pq;
        try {
            pq = Class.forName("com.mediatek.pq.PictureQuality");
            out.append("PictureQuality: classe accessibile\n");
        } catch (Throwable e) {
            out.append("PictureQuality: NON ACCESSIBILE\n").append(error(e)).append("\n\n");
            out.append("Il sistema non espone questa API alla nostra APK. Nessuna modifica effettuata.");
            return out.toString();
        }
        String[] names = {
            "getCapability", "getPictureMode", "getContrastIndex", "getContrastIndexRange",
            "getSaturationIndex", "getSaturationIndexRange", "getPicBrightnessIndex",
            "getPicBrightnessIndexRange", "getGammaIndex", "getGammaIndexRange",
            "getDynamicContrastIndex", "getDynamicContrastIndexRange",
            "getSharpnessIndex", "getSharpnessIndexRange"
        };
        for (String name : names) {
            out.append(name).append(": ");
            try {
                Method m = pq.getMethod(name);
                if (!Modifier.isStatic(m.getModifiers()) || m.getParameterTypes().length != 0) {
                    out.append("firma non supportata\n"); continue;
                }
                Object val = m.invoke(null);
                out.append(value(val)).append("\n");
            } catch (Throwable e) { out.append(error(e)).append("\n"); }
        }
        out.append("\nNessun metodo set... chiamato. Nessun parametro modificato.");
        return out.toString();
    }
    private static String value(Object value) {
        if (value == null) return "null";
        if (value instanceof Number || value instanceof Boolean || value instanceof String)
            return value.toString();
        StringBuilder b = new StringBuilder(value.getClass().getSimpleName()).append("{");
        int count = 0;
        for (Field f : value.getClass().getFields()) {
            try {
                Object v = f.get(value);
                if (v instanceof Number || v instanceof Boolean || v instanceof String) {
                    if (count++ > 0) b.append(", ");
                    b.append(f.getName()).append("=").append(v);
                }
            } catch (Throwable ignored) {}
        }
        return b.append("}").toString();
    }
    private static String error(Throwable e) {
        if (e instanceof InvocationTargetException && e.getCause() != null) e = e.getCause();
        String msg = e.getClass().getSimpleName();
        if (e.getMessage() != null) {
            String detail = e.getMessage();
            if (detail.length() > 140) detail = detail.substring(0, 140);
            msg += ": " + detail;
        }
        return msg;
    }
}
