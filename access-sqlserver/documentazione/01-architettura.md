# Architettura operativa

## Obiettivo

Fornire ai responsabili autorizzati un'applicazione Access per la gestione dei
dati del personale, con dati conservati in modo centralizzato su SQL Server.

## Componenti

```text
PC aziendale
  Access 2019 64 bit
  Front-end locale .accdb
        |
        | ODBC 64 bit e autenticazione Windows
        v
Server SQL aziendale
  Database GestionePersonale
```

## Front-end Access

Ogni postazione deve avere una copia locale del front-end. Il front-end
conterra maschere, query, report, menu e moduli VBA. Non deve contenere dati
operativi locali e non deve essere aperto direttamente da una cartella di rete
condivisa.

## Database SQL Server

SQL Server conservera le tabelle operative, le viste, i permessi e, in una fase
successiva, il registro delle operazioni. Il file SQLite del progetto Python
non sara usato nell'ambiente aziendale.

## Parametri da confermare

- Nome o indirizzo del server SQL Server: da definire con gli amministratori.
- Nome del database: da definire.
- Nome del gruppo Windows autorizzato: da definire.
- Driver ODBC aziendale approvato: da definire.
- Modalita di backup e ripristino: da definire.
