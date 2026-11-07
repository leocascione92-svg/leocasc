# LocationLab 1.0 — versione finale

App Android indipendente per posizioni GPS simulate, senza pubblicita e senza associazioni con file PDF, P7M o documenti. Theme scuro e mappe OpenStreetMap con cache.

## Novita della versione finale
- **Apri in Maps**: usa il punto scelto sulla mappa.
- **Esporta preferiti / Importa preferiti**: menu ⋮. Backup LocationLab-preferiti.json con Storage Access Framework, senza permessi di archiviazione. Importa senza cancellare i preferiti precedenti, con deduplicazione.
- **Torna alla posizione reale**: pulsante ◎ sotto lo zoom. Richiede permesso di localizzazione preciso, ignora coordinate mock e richiede di interrompere la simulazione per distinguere posizione reale e fittizia.

## Compilazione e download
Aprire Actions → LocationLab Android APK → ultima compilazione verde → Artifacts → LocationLab-1.0-APK. Nello ZIP è presente LocationLab-1.0.apk.

## Installazione
1. Consenti installazione di APK dalla fonte scelta.
2. Apri Opzioni sviluppatore → App per posizione fittizia → LocationLab.
3. Verifica la simulazione prima di disinstallare un eventuale altro GPS Emulator.

*Avvertenza aggiornamenti*: le build debug GitHub potrebbero essere firmate con chiavi diverse. Se un aggiornamento non si installa, il dispositivo potrebbe richiedere la disinstallazione precedente: questa cancella preferiti e dati locali non esportati. Per le successive versioni occorre una firma persistente.

© OpenStreetMap contributors.
