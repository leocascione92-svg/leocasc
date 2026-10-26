# Qin Display Diagnostica 0.3 — test finale compatibilità

Android del telefono non viene modificato. La build di questa app **ha targetSdk 28** per provare se i metodi MediaTek PictureQuality, invisibili a un'app targetSdk 34, sono condizionalmente limitati dal target SDK.

Le API in blocklist assoluta resteranno inaccessibili anche a targetSdk 28. La 0.3 legge solamente i metodi get..., non usa setter, non scrive impostazioni, non modifica permessi o protezioni di Android e non richiede root.

App package differente dalla 0.1 e 0.2, per evitare collisioni di firma o update. Puoi disinstallare le precedenti senza alcuna modifica al sistema.

APK compilata e pubblicata da GitHub Actions in releases/Qin-Display-Diagnostica-0.3.apk.
