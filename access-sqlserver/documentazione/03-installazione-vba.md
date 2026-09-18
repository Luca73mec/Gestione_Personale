# Installazione del modulo VBA

## Prerequisiti

- Access 2019 a 64 bit.
- Database SQL Server gia creato con `database/001_schema.sql`.
- Driver ODBC SQL Server a 64 bit installato e approvato dagli amministratori.
- Account Windows autorizzato al database.

## Inserimento del modulo

1. Crea un database Access vuoto in formato `.accdb`.
2. Premi `ALT+F11` per aprire l'editor VBA.
3. Seleziona **Inserisci > Modulo**.
4. Copia il contenuto di `access/vba/modSetupInterfaccia.bas` nel modulo. Se il
  file mostra una riga `Attribute VB_Name = ...`, non copiarla: e una riga
  interna ai file VBA esportati e provoca un errore quando viene incollata.
5. Salva il modulo con il nome `modSetupInterfaccia`.
6. Posiziona il cursore dentro `SetupInterfaccia`.
7. Premi `F5`.
8. Inserisci nome server, database e driver ODBC quando richiesto.

## Risultato

Il modulo crea:

- collegamenti ODBC alle tabelle e alle viste SQL Server;
- query salvate per elenco personale e scadenzario;
- `frmMenu` come menu principale;
- `frmPersonale` come elenco consultabile;
- `frmPersonaleDettaglio` per inserimento e modifica dell'anagrafica.

## Note di sicurezza

- Il collegamento usa l'autenticazione Windows e non salva password.
- Il collegamento richiede cifratura TLS e un certificato SQL Server riconosciuto
  dalla postazione; gli amministratori devono verificare questa configurazione.
- Non inserire password nel codice VBA.
- Il modulo presuppone che SQL Server e i gruppi Windows siano gia stati
  autorizzati dagli amministratori.
- Le maschere create sono una base iniziale: prima dell'uso reale devono essere
  collaudate con dati non personali e approvate dal responsabile competente.

## Limiti della prima versione

La prima versione crea l'interfaccia per anagrafica, menu e scadenzario. Le
maschere dedicate a patenti, corsi, note e passaporti saranno aggiunte dopo il
collaudo del collegamento SQL Server e dell'anagrafica.