# Progetto Access + SQL Server

## Scopo

Questa cartella contiene la progettazione della versione aziendale del sistema,
destinata a postazioni Windows 10 Enterprise LTSC con Microsoft Access 2019 a
64 bit.

Il progetto Python esistente resta separato e continua a essere utilizzato
come riferimento per la struttura dei dati e le regole applicative.

## Architettura prevista

```text
Access 2019 a 64 bit
        |
        | ODBC 64 bit con autenticazione Windows
        v
SQL Server aziendale
```

- Access sara il front-end con maschere, query, report e menu.
- SQL Server sara il database centrale.
- L'accesso sara limitato alla rete aziendale.
- I permessi saranno assegnati tramite gruppi Windows autorizzati.
- Nessun eseguibile o accesso Internet sara richiesto sulle postazioni.

## Struttura

- `database/`: schema, viste, ruoli e migrazione dei dati.
- `access/maschere/`: progettazione delle maschere Access.
- `access/query/`: query e collegamenti alle viste SQL Server.
- `access/report/`: report e stampe.
- `access/vba/`: moduli VBA compatibili con Access 2019 a 64 bit.
- `documentazione/`: architettura, sicurezza e installazione.
- `test/`: verifiche del database e dell'interfaccia.

## Vincoli di compatibilita

- Access 2019 a 64 bit.
- Driver ODBC SQL Server a 64 bit.
- Nessuna dipendenza da Internet.
- Nessun accesso diretto degli utenti al file fisico del database.
- Autenticazione Windows, quando disponibile sul server aziendale.

## Stato iniziale

La prima fase consiste nel definire lo schema SQL Server equivalente al
database SQLite usato dal progetto Python e nel verificare con gli
amministratori il server e il gruppo Windows autorizzato.
