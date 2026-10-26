# Qin Display Diagnostica 0.1

Prototipo per Qin F25 Pro con Android 14. **Sola lettura.**

- Non richiede root.
- Non chiede permessi speciali, accesso Internet, accessibilità o sovrapposizioni.
- Non modifica la saturazione, la gamma o il contrasto.
- Verifica se `com.mediatek.pq.PictureQuality` è accessibile da una comune APK.
- Tenta unicamente le chiamate ai metodi `get...` per raccogliere un rapporto copiabile.

Il messaggio 'PictureQuality: NON ACCESSIBILE' è un risultato diagnostico valido,
non un errore da aggirare con strumenti invasivi.

## APK

Il workflow GitHub Actions compila la APK di debug e, se dispone dei permessi
necessari, la pubblica in `releases/Qin-Display-Diagnostica-0.1.apk`
su questo ramo dedicato.

La APK di debug è firmata automaticamente da Android Gradle Plugin ed è installabile
come normale applicazione. Non installare altre MiraVision APK in sostituzione
dell'originale.
