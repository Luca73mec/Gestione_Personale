# Passaggio consegne per il prossimo agente

## Obiettivo dell'utente

Portare il progetto Gestione Personale su PC aziendali Windows 10 Enterprise
LTSC 1809 con Access 2019 a 64 bit, senza richiedere eseguibili, Internet o
privilegi amministrativi durante l'uso.

L'utente ha scelto provvisoriamente il **caso 2**: database Access locale,
senza SQL Server e senza ODBC. La versione SQL Server resta nel repository come
percorso futuro separato.

## Repository e stato

- Repository: `https://github.com/Luca73mec/Gestione_Personale.git`
- Branch: `main`
- Ultima release: `v0.1.13`
- Modulo locale: `access-sqlserver/access/vba/modSetupLocale.bas`
- Guida locale: `access-sqlserver/documentazione/04-database-locale.md`
- Modulo SQL Server: `access-sqlserver/access/vba/modSetupInterfaccia.bas`
- Schema SQL Server: `access-sqlserver/database/001_schema.sql`

Il modulo locale e stato corretto progressivamente per:

- rimuovere `Attribute VB_Name`, che non va incollato nell'editor VBA;
- usare `TEXT(255)` invece di dimensioni superiori a 255;
- usare `COUNTER PRIMARY KEY` per gli ID autoincrementanti;
- usare `LONGTEXT` invece di `MEMO` nella definizione SQL;
- uniformare il nome della routine `CreaQueryLocal`.

## Procedura attuale sul PC Windows

1. Creare un nuovo database Access `.accdb` vuoto.
2. Aprire l'editor VBA con `ALT+F11`.
3. Creare un modulo standard.
4. Copiare il contenuto di `modSetupLocale.bas` dalla versione piu recente.
5. Non copiare eventuali righe `Attribute VB_Name` se dovessero comparire.
6. Salvare il modulo come `modSetupLocale`.
7. Eseguire **Debug > Compila progetto**.
8. Posizionare il cursore in `SetupLocale` e premere `F5`.
9. Aprire la maschera `frmLocaleMenu`.

## Stato di verifica

Il codice e stato controllato staticamente su macOS, ma non e stato compilato
in Access reale. Gli errori di Access vanno quindi raccolti con:

- numero dell'errore;
- testo completo;
- riga evidenziata;
- nome della procedura in cui si verifica.

Non chiedere all'utente di ripetere tentativi alla cieca: dopo ogni errore
acquisire queste quattro informazioni e correggere una sola causa per volta.

## Prossimo lavoro consigliato

### Se il modulo continua a dare errore SQL

Sostituire la costruzione tramite stringhe `CREATE TABLE` con la creazione
tramite DAO `TableDef`, `Fields.Append` e `CreateField`. Questa tecnica evita le
differenze di sintassi del motore Access e permette di individuare il campo
problematico in modo preciso.

### Dopo la creazione delle tabelle

1. Verificare che esistano le sei tabelle:
   `personale`, `patente`, `corso`, `partecipazione_corso`,
   `nota_caratteristica`, `passaporto_servizio`.
2. Verificare che esistano le query `qryLocalePersonale` e
   `qryLocaleScadenzario`.
3. Verificare la creazione di `frmLocaleMenu`, `frmLocalePersonale` e
   `frmLocaleDettaglio`.
4. Testare inserimento e modifica di un record fittizio.
5. Aggiungere, in moduli separati, maschere per patenti, corsi, note e
   passaporti.
6. Aggiungere controllo accessi, backup e protezione del file prima di usare
   dati personali reali.

## Vincoli da rispettare

- Non usare dati personali reali nei test.
- Non usare il database SQLite del progetto Python come database operativo
  aziendale.
- Non pubblicare password, stringhe di connessione con credenziali o dati
  personali su GitHub.
- Non proporre metodi per aggirare i controlli degli amministratori.
- Il database Access locale non sincronizza piu PC: chiarire sempre questo
  limite all'utente.
- Non modificare la versione SQL Server mentre si corregge il caso locale.
- Prima di ogni pubblicazione, eseguire `git diff --check` e controllare i file
  inclusi nel commit.
