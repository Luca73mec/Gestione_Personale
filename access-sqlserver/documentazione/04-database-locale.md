# Caso 2: database Access locale

## Quando usare questa versione

Questa versione non usa SQL Server, ODBC, Internet o file eseguibili. Il
database e le maschere risiedono nello stesso file Access `.accdb`.

## Installazione

1. Crea un database Access vuoto.
2. Premi `ALT+F11`.
3. Seleziona **Inserisci > Modulo**.
4. Copia il contenuto di `access/vba/modSetupLocale.bas`.
5. Salva il modulo come `modSetupLocale`.
6. Posiziona il cursore dentro `SetupLocale`.
7. Premi `F5`.
8. Apri `frmLocaleMenu` dal riquadro di navigazione.

## Cosa viene creato

- sei tabelle locali per personale, patenti, corsi, partecipazioni, note e
  passaporti;
- una query elenco personale;
- una query scadenzario;
- menu principale;
- elenco personale;
- scheda personale per inserimento e modifica.

Il modulo non inserisce dati dimostrativi.

## Limiti importanti

- Ogni copia del file Access contiene dati separati.
- Non esiste sincronizzazione automatica tra piu PC.
- Un file Access condiviso su rete non equivale a un database server.
- Per dati personali reali servono backup, permessi di cartella, controllo degli
  accessi e approvazione degli amministratori.
- Questa versione e adatta come prototipo o uso individuale; per uso multiutente
  continuativo e preferibile SQL Server.