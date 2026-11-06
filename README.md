# LocationLab 0.2 — Android GPS emulator senza annunci

App Android **indipendente**, creata da zero, per scegliere una posizione sulla mappa e fornirla ad Android tramite le API ufficiali per le posizioni di test. Non contiene SDK pubblicitari, tracker né codice dell’app proprietaria GPS Emulator.

## Funzioni implementate

- Mappa OpenStreetMap, zoom, trascinamento, selezione posizione con tocco.
- Inserimento coordinate e ricerca indirizzo tramite geocoder di Android, se disponibile.
- Mock GPS statico con aggiornamento continuo e notifica visibile per avvio/arresto.
- Preferiti e cronologia memorizzati in locale.
- Nessuna registrazione né pubblicità; nessuna apertura di PDF, `.p7m` o altri documenti.

**Requisiti:** Android 8.0+; permesso di posizione; impostazione `Opzioni sviluppatore → Seleziona app per posizione simulata → LocationLab`. Funzionalità di simulazione dipendente dal dispositivo e dalle app che ricevono il GPS. Le app possono rilevare che la posizione è fittizia.

## Installare l’APK da GitHub

1. Aprire **Actions** del repository GitHub e selezionare il workflow `LocationLab Android APK`.
2. Aprire l’ultima esecuzione riuscita e nella sezione **Artifacts** scaricare `LocationLab-v0.2-debug` (ZIP contenente `LocationLab-v0.2-debug.apk`).
3. Estrarre lo ZIP e installare l’APK sul telefono, autorizzando l'installazione dal browser/file manager.
4. Attivare le *Opzioni sviluppatore* di Android e selezionare `LocationLab` come app di posizione fittizia.
5. Concedere l'accesso alla posizione, scegliere il punto sulla mappa e premere `Avvia simulazione`; per interrompere toccare `Ferma`.

**Nota sulla firma:** il file di GitHub Actions è un APK **debug**, firmato automaticamente dal runner con una chiave temporanea. Per installare una versione generata in una esecuzione successiva potrebbe essere necessario disinstallare la precedente: preferiti e cronologia andrebbero persi. Per aggiornamenti regolari serve una chiave di firma release persistente, da configurare mediante i *GitHub Secrets*; non caricarla nel repository.

## Build

Il file `LocationLab-source.tar.xz` del ramo contiene i sorgenti. La compilazione automatica usa JDK 17, Gradle 8.11.1 e Android SDK 35, senza richiedere `gradle-wrapper.jar`. In locale: estrarre l’archivio, aprire la cartella `LocationLab` in Android Studio e compilare `:app:assembleDebug`.

## Limiti attuali

Questa versione implementa il **posizionamento statico**; non include ancora percorsi simulati con movimento, mappe satellitari o formati `.gpsemu`. Il workflow è una compilazione automatica, non un test reale sul tuo telefono. La geocodifica dipende dal servizio disponibile sul dispositivo. Le mappe richiedono Internet, usano il servizio di tile OpenStreetMap con attribuzione visibile e cache temporanea e rispettano la [policy del servizio](https://operations.osmfoundation.org/policies/tiles/).

Il progetto conserva il package `it.locationlab.app` e può convivere con l'app originale.