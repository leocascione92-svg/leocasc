# Qin Display Diagnostica 0.4 (sola lettura)
Versione per verificare le API com.mediatek.pq.PictureQuality del Qin F25 Pro Android 14.

## Cosa fa
1. Legge la visibilità iniziale dei metodi (v0.3: zero).
2. Tenta di applicare, nel **solo processo di questa app**, una esenzione limitata al prefisso `Lcom/mediatek/pq/PictureQuality;` tramite il pattern Java di FreeReflection.
3. Rilegge la lista dei metodi e, soltanto se realmente esposti, esegue i metodi senza parametri `get...` (mai `set...`).
4. Mostra gli eventuali errori di Android o MediaTek. Nessuna persistenza della modifica dopo la chiusura forzata dell'app.

## Non fa
Nessun root, sblocco bootloader, modifica firmware, cambiamento di autorizzazioni, modifica di impostazioni globali o scrittura dei parametri display.
Questo non supera eventuali autorizzazioni `signature|privileged` del fornitore: se MediaTek nega l'accesso, il test deve arrestarsi.

La tecnica di reflection è ispirata alla classe BootstrapClass di **tiann/FreeReflection**, distribuita sotto licenza MIT. https://github.com/tiann/FreeReflection

La v0.4 ha identificatore separato dalle versioni precedenti per non dipendere dalla firma debug di build precedenti. Distribuzione debug tramite GitHub Actions.
