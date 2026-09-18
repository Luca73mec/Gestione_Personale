# Manifest del progetto

## Nome del progetto

Gestione Personale Web

## Obiettivo del progetto

Applicazione web locale per la gestione del personale, dei fascicoli matricolari, delle valutazioni, delle patenti, dei passaporti di servizio, dei corsi e delle relative scadenze.

## Struttura delle cartelle

```text
GestionePersonaleWeb/
├── .rules/                      # Regole operative per lo sviluppo e l'isolamento test
├── access/                      # Modulo VBA Access di origine/riferimento
├── access-sqlserver/            # Progetto migrazione Access + SQL Server
├── app/                         # Backend HTTP e parser PDF
├── database/                    # SQLite, schema, dati CIFIGE e seed
├── static/                      # Frontend HTML, CSS e JavaScript
├── tests/                       # Test automatici
├── scripts/                     # Automazione versionamento e push
├── .github/workflows/           # Automazione GitHub Releases
├── .gitignore                   # Esclusioni Git per cache e database locale
├── run.sh                       # Avvio locale dell'applicazione
├── VERSION                      # Versione semantica MAJOR.MINOR.PATCH
├── PROJECT_MANIFEST.md          # Contesto e regole per gli agenti
└── README.md                    # Documentazione principale
```

## Regole di versionamento

- Il file `VERSION` usa esclusivamente il formato `MAJOR.MINOR.PATCH`.
- Ogni commit preparato tramite `scripts/push.sh` o `scripts/push.ps1` incrementa automaticamente il PATCH.
- La versione deve essere aggiornata prima del commit e deve sempre essere inclusa nello staging.
- Il messaggio di commit obbligatorio è `Update version to X.Y.Z`.
- Il Manifest deve riportare la stessa versione e l'ora dell'ultimo aggiornamento.
- Ogni versione pubblicata crea il tag Git `vX.Y.Z` e una GitHub Release con lo stesso nome.

## Convenzioni di naming e commit

- Python: moduli e funzioni in `snake_case`, classi in `PascalCase`.
- JavaScript: variabili e funzioni in `camelCase`.
- Cartelle e file di automazione usano nomi descrittivi in minuscolo, quando possibile.
- I commit automatici usano esclusivamente il formato `Update version to X.Y.Z`.

## Workflow operativo

1. Eseguire `scripts/push.sh` su Linux/macOS oppure `scripts/push.ps1` su Windows PowerShell.
2. Lo script legge `VERSION`, incrementa il PATCH e aggiorna questo Manifest.
3. Lo script aggiunge i file modificati, verifica che `VERSION` sia incluso, crea il commit, esegue `git push` e pubblica il tag `vX.Y.Z`.
4. Il workflow GitHub Actions crea automaticamente la Release corrispondente con note generate dai commit.
5. Prima del primo push, configurare il repository Git locale e il remote GitHub.
6. Quando vengono aggiunti file o cartelle importanti, aggiornare la sezione della struttura.

## Stato attuale del progetto

Versione corrente: `0.1.10`

## Ultimo aggiornamento

2026-09-18 16:12:12+02:00

## Note per agenti esterni

Questo repository contiene una SPA offline con backend Python standard library e database SQLite locale. Gli agenti devono preservare l'assenza di dipendenze esterne salvo richiesta esplicita, mantenere sincronizzati `VERSION` e questo Manifest e usare gli script ufficiali per preparare commit e push. In caso di incoerenza, correggere prima la versione e il timestamp del Manifest. La cartella `database/` può contenere il database SQLite generato localmente; i file sorgente da mantenere sotto controllo sono soprattutto schema e seed.

## Regola per prove, test e isolamento dati fittizi

- È tassativamente vietato lasciare record fittizi, dati di prova o corsi temporanei nel database operativo `database/personale.db`.
- Ogni suite di test automatizzato o script di prova DEVE operare in isolamento (tramite database SQLite temporaneo dedicato oppure attraverso blocchi `setUp` e `tearDown` scrupolosi che eliminano tutti i record creati per la prova).
- Al termine delle verifiche, il database principale deve contenere solo ed esclusivamente i dati legittimamente censiti e i corsi ufficiali approvati (es. serie `CIFIGE-%`). Qualsiasi dato fittizio creato accidentalmente deve essere rimosso prima del rilascio o della consegna all'utente.