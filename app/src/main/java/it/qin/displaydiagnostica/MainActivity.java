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
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;
import java.lang.reflect.Field;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;

/**
 * Read-only vendor API probe. No setter, accessibility service, privileged permission,
 * overlay, or device configuration change is used.
 */
public final class MainActivity extends Activity {
    private TextView reportView;
    private Button runButton, copyButton;
    private String lastReport = "";
    private int dp(int n) {
        return (int)(getResources().getDisplayMetrics().density * n + 0.5f);
    }
    private TextView text(String value, int size, int color) {
        TextView t = new TextView(this);
        t.setText(value); t.setTextSize(size); t.setTextColor(color); return t;
    }
    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        final int fg = Color.rgb(236, 237, 234);
        ScrollView screen = new ScrollView(this);
        screen.setFillViewport(true);
        screen.setBackgroundColor(Color.rgb(45, 49, 52));
        LinearLayout column = new LinearLayout(this);
        column.setOrientation(LinearLayout.VERTICAL);
        column.setPadding(dp(16), dp(18), dp(16), dp(20));
        screen.addView(column);

        TextView title = text("QIN DISPLAY", 24, fg);
        title.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        column.addView(title);
        column.addView(text("MiraVision · Diagnostica 0.2", 16, Color.rgb(181, 204, 219)));
        TextView description = text("SOLA LETTURA. Controlla la visibilità dei metodi MediaTek e le restrizioni di Android 14. Non cambia alcuna impostazione.", 14, fg);
        description.setPadding(0, dp(16), 0, dp(16));
        column.addView(description);

        runButton = new Button(this); runButton.setText("ESEGUI DIAGNOSI");
        column.addView(runButton, new LinearLayout.LayoutParams(-1, -2));
        copyButton = new Button(this); copyButton.setText("COPIA RISULTATO");
        copyButton.setEnabled(false);
        column.addView(copyButton, new LinearLayout.LayoutParams(-1, -2));

        reportView = text("Premi ESEGUI DIAGNOSI. Nessun parametro del display verrà modificato.", 14, fg);
        reportView.setTypeface(Typeface.MONOSPACE);
        reportView.setTextIsSelectable(true);
        reportView.setBackgroundColor(Color.rgb(61, 66, 70));
        reportView.setPadding(dp(12), dp(12), dp(12), dp(12));
        LinearLayout.LayoutParams reportParams = new LinearLayout.LayoutParams(-1, -2);
        reportParams.topMargin = dp(12);
        column.addView(reportView, reportParams);
        setContentView(screen);

        runButton.setOnClickListener(v -> {
            runButton.setEnabled(false);
            reportView.setText("Diagnosi in corso...");
            new Thread(() -> {
                String collected = diagnosticReport();
                runOnUiThread(() -> {
                    lastReport = collected;
                    reportView.setText(collected);
                    copyButton.setEnabled(true);
                    runButton.setEnabled(true);
                });
            }).start();
        });
        copyButton.setOnClickListener(v -> {
            ClipboardManager clip = (ClipboardManager)getSystemService(Context.CLIPBOARD_SERVICE);
            if (clip != null) {
                clip.setPrimaryClip(ClipData.newPlainText("Qin Display 0.2", lastReport));
                Toast.makeText(this, "Diagnosi copiata", Toast.LENGTH_SHORT).show();
            }
        });
    }

    private String diagnosticReport() {
        StringBuilder sb = new StringBuilder();
        sb.append("QIN DISPLAY DIAGNOSTICA 0.2\nSOLA LETTURA\n\n");
        sb.append("Modello: ").append(Build.MODEL).append("\n");
        sb.append("Android: ").append(Build.VERSION.RELEASE).append("\n");
        sb.append("targetSdk: ").append(getApplicationInfo().targetSdkVersion).append("\n\n");

        try {
            PackageInfo info = getPackageManager().getPackageInfo("com.mediatek.miravision.ui", 0);
            sb.append("MiraVision: ").append(info.versionName).append("\n");
        } catch (Throwable e) {
            sb.append("MiraVision: non rilevata (").append(err(e)).append(")\n");
        }

        Class<?> pq;
        try {
            pq = Class.forName("com.mediatek.pq.PictureQuality");
            sb.append("PictureQuality: classe trovata\n");
            ClassLoader loader = pq.getClassLoader();
            sb.append("ClassLoader: ").append(loader == null ? "bootstrap" : loader.getClass().getSimpleName()).append("\n");
        } catch (Throwable e) {
            sb.append("PictureQuality: classe NON accessibile\n").append(err(e)).append("\n");
            return sb.toString();
        }

        Method[] declared;
        try {
            declared = pq.getDeclaredMethods();
            sb.append("Metodi dichiarati visibili: ").append(declared.length).append("\n");
            int shown = 0;
            for (Method method : declared) {
                if (shown++ >= 24) { sb.append("...\n"); break; }
                sb.append("  ").append(method.getName()).append("() -> ").append(method.getReturnType().getSimpleName()).append("\n");
            }
        } catch (Throwable e) {
            sb.append("getDeclaredMethods: ").append(err(e)).append("\n");
        }
        try {
            sb.append("Metodi pubblici visibili: ").append(pq.getMethods().length).append("\n");
        } catch (Throwable e) {
            sb.append("getMethods: ").append(err(e)).append("\n");
        }
        sb.append("\nTEST LETTURA PROTETTA\n");
        String[] requested = {"getCapability", "getPictureMode", "getContrastIndex", "getContrastIndexRange",
                "getSaturationIndex", "getSaturationIndexRange", "getGammaIndex", "getGammaIndexRange",
                "getPicBrightnessIndex", "getPicBrightnessIndexRange", "getSharpnessIndex", "getSharpnessIndexRange",
                "getDynamicContrastIndex", "getDynamicContrastIndexRange"};
        int accessible = 0;
        for (String methodName : requested) {
            sb.append(methodName).append(": ");
            Method getter;
            boolean declaredOnly = false;
            try {
                getter = pq.getMethod(methodName);
            } catch (NoSuchMethodException e) {
                try {
                    getter = pq.getDeclaredMethod(methodName);
                    declaredOnly = true;
                } catch (Throwable e2) {
                    sb.append("NON visibile (getMethod e getDeclaredMethod)\n");
                    continue;
                }
            } catch (Throwable e) {
                sb.append(err(e)).append("\n");
                continue;
            }
            if (!Modifier.isStatic(getter.getModifiers()) || getter.getParameterTypes().length != 0) {
                sb.append("firma non invocabile\n");
                continue;
            }
            sb.append(declaredOnly ? "dichiarato, " : "pubblico, ");
            try {
                if (declaredOnly && !getter.isAccessible()) getter.setAccessible(true);
                Object result = getter.invoke(null);
                accessible++;
                sb.append("valore = ").append(format(result)).append("\n");
            } catch (Throwable e) {
                sb.append("lettura negata: ").append(err(e)).append("\n");
            }
        }
        sb.append("\nMetodi letti correttamente: ").append(accessible).append("/").append(requested.length).append("\n");
        sb.append("Nessun setter invocato. Nessuna impostazione modificata.");
        return sb.toString();
    }
    private static String format(Object value) {
        if (value == null) return "null";
        if (value instanceof Number || value instanceof Boolean || value instanceof String)
            return String.valueOf(value);
        StringBuilder b = new StringBuilder(value.getClass().getSimpleName()).append("{");
        int count = 0;
        for (Field field : value.getClass().getFields()) {
            try {
                Object member = field.get(value);
                if (member instanceof Number || member instanceof Boolean || member instanceof String) {
                    if (count++ > 0) b.append(", ");
                    b.append(field.getName()).append("=").append(member);
                }
            } catch (Throwable ignored) {}
        }
        return b.append("}").toString();
    }
    private static String err(Throwable t) {
        if (t instanceof InvocationTargetException && t.getCause() != null) t = t.getCause();
        String msg = t.getClass().getSimpleName();
        if (t.getMessage() != null) {
            String detail = t.getMessage();
            msg += ": " + detail.substring(0, Math.min(detail.length(), 100));
        }
        return msg;
    }
}
