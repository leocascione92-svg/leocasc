# Qin Display Diagnostica 0.2 (read-only)
La versione 0.1 carica la classe MediaTek ma non trova i metodi `get...` con reflection.
Questa versione verifica `getDeclaredMethods`, `getMethod`, `getDeclaredMethod` e prova a leggere solo getter statici senza argomenti quando sono esposti.

Nessuna modifica al sistema. Nessun metodo di scrittura, root, overlay, concessione di permessi o rete.

Se Android 14 non espone i metodi, questo e' un risultato corretto. Le restrizioni sulle API non-SDK possono rendere `NoSuchMethodException` il risultato previsto.

`releases/Qin-Display-Diagnostica-0.2.apk` e' una APK debug costruita automaticamente da GitHub Actions.

La v0.2 ha un applicationId distinto, per evitare problemi di firma tra esecuzioni separate della CI. Puoi disinstallare la 0.1 quando preferisci.
