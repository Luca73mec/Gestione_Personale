# Sicurezza e accessi

## Principi

- Accesso solo dalla rete aziendale autorizzata.
- Nessuna pubblicazione su Internet.
- Nessuna password scritta nel file Access o nel codice VBA.
- Autenticazione tramite account Windows aziendale, quando supportata.
- Permessi applicati anche in SQL Server, non solo nascosti nelle maschere.
- Backup e ripristino gestiti dagli amministratori.

## Ruoli applicativi iniziali

| Ruolo | Consultazione | Inserimento/modifica | Cancellazione | Configurazione |
| --- | --- | --- | --- | --- |
| Responsabile trattamento | Si | Si | Da autorizzare | No |
| Consultazione | Si | No | No | No |
| Amministratore applicativo | Si | Si | Si | Limitata |

I nomi dei gruppi Windows che corrisponderanno ai ruoli devono essere forniti
dagli amministratori di sistema. Fino a quel momento non devono essere inseriti
nomi inventati nello script SQL.

## Controlli da implementare

1. Identificazione dell'utente Windows.
2. Verifica dell'appartenenza al gruppo autorizzato.
3. Controllo dei permessi SQL Server sull'operazione richiesta.
4. Registrazione delle modifiche ai dati personali.
5. Blocco o chiusura della sessione dopo inattivita, se richiesto dalle regole
   aziendali.

## Verifiche necessarie prima del collaudo

- autorizzazione del database e della cartella di distribuzione del front-end;
- cifratura e conservazione dei backup;
- elenco degli utenti autorizzati;
- procedura per revocare immediatamente un accesso;
- prova di ripristino da backup;
- approvazione del responsabile della sicurezza e della privacy.
