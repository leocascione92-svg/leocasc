# LocationLab 3.0

Applicazione Android senza pubblicità, con tema nero e simulazione GPS per **posizione fissa** o **percorso**.

## Novità
- Selettore Posizione fissa / Percorso; pulsante di avvio che cambia secondo la modalità selezionata.
- Percorso **a piedi** e **in auto** calcolato sui grafi OpenStreetMap tramite routing FOSSGIS/OSRM; mostra la polilinea reale, la simula punto per punto e aggiorna la direzione.
- Modalità **aereo** su rotta ortodromica tra i due punti, con velocità impostabile.
- Itinerari salvati localmente dopo il calcolo e riutilizzabili senza nuovo download.
- Velocità, altitudine, precisione GPS, preferiti, esportazione, notifiche e localizzazione mantenuti dalle versioni precedenti.

Il servizio di routing è una risorsa pubblica soggetta a disponibilità e limiti. Le coordinate di partenza e arrivo sono trasmesse al server FOSSGIS quando richiedi una rotta pedonale o automobilistica. Non vengono calcolati percorsi stradali in linea retta quando il servizio non funziona. [Informativa sul routing](https://routing.openstreetmap.de/about.html).

### APK
Apri **Actions > LocationLab Android APK**, seleziona una compilazione riuscita e scarica l'artefatto `LocationLab-3.0-APK` contenente `LocationLab-3.0.apk`.

I sorgenti Android completi sono in `LocationLab-source.tar.xz`, estratto e compilato automaticamente dal workflow.

**Aggiornamenti:** le firme delle build debug di GitHub potrebbero variare. Se serve disinstallare la versione precedente, esporta prima i preferiti. La simulazione richiede di impostare LocationLab in Opzioni sviluppatore > App per posizione fittizia. Testare la rotta e i controlli sul telefono prima di utilizzarla al posto della versione precedente.

© OpenStreetMap contributors · Routing © FOSSGIS.
