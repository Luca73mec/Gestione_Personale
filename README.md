# Gestione Personale Web (Sistema Informativo Locale)

Applicazione web e database relazionale locale per la gestione completa del personale, fascicoli matricolari, storico valutazioni e monitoraggio automatico delle scadenze.

---

## 🌟 Funzionalità Principali

1. **Anagrafica Personale Completa**
   - Dati anagrafici (Nome, Cognome, Codice Fiscale, data e luogo di nascita, residenza).
   - Dati di impiego (Matricola, Grado / Qualifica, Reparto / Ufficio, Incarico, data assunzione/arruolamento, stato di servizio).
   - Recapiti completi (Email istituzionale, email personale, telefono/cellulare).

2. **Note Caratteristiche e Documenti di Valutazione**
   - Tracciamento della tipologia (*Note Caratteristiche*, *Scheda Valutativa*, *Rapporto Informativo*).
   - Tracciamento del periodo valutato (`periodo_dal`, `periodo_al`).
   - Tracciamento della **data di firma per presa visione** da parte dell'interessato.
   - **Calcolo automatico della scadenza delle prossime note a 365 giorni** dal termine del periodo valutato (con possibilità di personalizzazione manuale).
   - Alert visivi sullo stato:
     - 🔴 **Scaduta** (oltre i 365 giorni)
     - 🟡 **In scadenza urgente** (entro 30 giorni)
     - 🟠 **In scadenza** (entro 60 giorni)
     - 🟢 **Regolare**

3. **Patenti di Guida (Civili e di Servizio/Militari)**
   - Registrazione di patenti civili (A, B, C, D, CQC) e di servizio/militari (Mod. 2, Mod. 3, Mod. 4).
   - Monitoraggio continuo della data di scadenza e alert dedicati.
   - Tracciamento di prescrizioni (es. *obbligo lenti 01*) e abilitazioni speciali (*guida veloce, mezzi blindati*).

4. **Passaporto di Servizio**
   - Tracciamento del numero libretto, autorità di rilascio (MAECI), tipologia (Servizio / Diplomatico).
   - Date di emissione e scadenza con conteggio giorni rimanenti.
   - Tracciamento dello stato (*Valido, In rinnovo, Restituito, Smarrito*) e della posizione fisica di custodia (*Archivio Ufficio Personale, Cassaforte Comando*).

5. **Corsi Frequentati, Catalogo Formazione & Ingestione PDF con Prerequisiti**
   - **Caricamento Catalogo Corsi da file PDF esterno**: estrazione nativa automatica del testo (senza librerie esterne o dipendenze pip).
   - **Analisi ed estrazione automatica dei prerequisiti**: rilevamento intelligente delle sezioni *Prerequisiti*, *Requisiti di ammissione*, *Condizioni di accesso* e *Propedeuticità*.
   - **Anteprima e modifica pre-importazione**: visualizzazione tabellare con caselle di controllo, campi modificabili e importazione batch immediata.
   - **Iscrizione corsi per il militare flessibile**:
     - *Selezione da catalogo*: mostra immediatamente i prerequisiti richiesti, l'ente erogatore e la durata del corso selezionato.
     - *Inserimento manuale al volo*: consente di registrare un corso non presente a catalogo definendo direttamente ente, ore e prerequisiti.

6. **Pianificazione Corsi & Audit Idoneità Candidatura**
   - **Nuovo modulo "Pianificazione Corsi"**: selezione combinata militare + corso a catalogo con filtri di ricerca in tempo reale.
   - **Motore di audit incrociato automatico**:
     - Verifica immediata di servizio attivo vs congedo/sospensione.
     - Controllo propedeuticità formative superate nel libretto matricolare.
     - Verifica patenti di guida richieste (civili e militari Mod. 2/3/4) con controllo scadenze.
     - Controllo regolarità note caratteristiche e requisiti a vista (lingua, idoneità sanitaria, sicurezza).
   - **Checklist analitica e responso visivo**: semaforo sintetico (🟢 *Candidabile*, 🟡 *Candidabile con Riserva*, 🔴 *Non Candidabile*), percentuale di conformità, raccomandazioni del sistema e pulsante di iscrizione diretta con pre-popolamento.

7. **Cruscotto di Controllo & Scadenzario Unificato**
   - KPI riassuntivi in tempo reale.
   - Vista tabellare ordinata per urgenza per non mancare nessuna scadenza.
   - Funzione di stampa/esportazione scheda fascicolo individuale in formato cartaceo o PDF.

---

## 🛠️ Architettura Tecnica

- **Database**: SQLite 3 (`database/personale.db`) con foreign keys attive (`PRAGMA foreign_keys = ON`), WAL mode (`PRAGMA journal_mode = WAL`), indici di ricerca e viste SQL ottimizzate.
- **Backend**: Python 3.10+ (utilizza esclusivamente la libreria standard di Python: `http.server.ThreadingHTTPServer`, `sqlite3`, `json`, `urllib`, con fallback macOS native PDFKit / pure-Python stream parser). **Zero dipendenze esterne o pip required!**
- **Frontend**: Single Page Application (SPA) reattiva in HTML5, CSS3 moderno e Vanilla JavaScript nativo. Funziona al 100% offline su rete locale protetta, senza connessioni a CDN esterne.

---

## 🚀 Avvio Rapido

Dalla cartella principale del progetto, esegui semplicemente:

```bash
./run.sh
```

Oppure direttamente con Python:

```bash
python3 app/server.py --port 8080
```

Apri quindi il tuo browser preferito su:
👉 **[http://localhost:8080](http://localhost:8080)** (oppure `http://127.0.0.1:8080`)

---

## 📁 Struttura del Progetto

```text
GestionePersonaleWeb/
├── access/
│   └── ModGestionePersonale_Office_v3_3420.bas # Modulo VBA Access di riferimento originario
├── app/
│   ├── api.py                 # Gestore rotte API REST (CRUD, upload PDF, verifica candidatura)
│   ├── pdf_parser.py          # Motore nativo estrazione testo e parsing prerequisiti PDF
│   └── server.py              # Server HTTP locale multi-threaded
├── database/
│   ├── db.py                  # Layer di accesso ai dati e motore audit candidatura
│   ├── schema.sql             # Schema DDL tabelle, vincoli, indici e viste
│   ├── seed_data.sql          # Dati dimostrativi iniziali realistici
│   └── personale.db           # Database SQLite (creato automaticamente all'avvio)
├── static/
│   ├── index.html             # Interfaccia grafica utente (Cruscotto, Schede, Pianificazione)
│   ├── css/
│   │   └── style.css          # Stile moderno, badge semaforici e foglio stampa
│   └── js/
│       └── app.js             # Logica client SPA, audit candidatura e calcolo scadenze
├── tests/
│   ├── test_app.py            # Test automatici database e calcolo 365 giorni
│   ├── test_api.py            # Test automatici rotte API REST
│   ├── test_pdf_courses.py    # Test automatici estrazione PDF, prerequisiti e import batch
│   └── test_pianificazione.py # Test automatici motore verifica idoneità candidatura
├── run.sh                     # Script di avvio rapido con un clic
└── README.md                  # Documentazione del progetto
```

---

## 🧪 Esecuzione dei Test

Per verificare l'integrità del database, delle API, dell'estrazione PDF e del modulo di pianificazione:

```bash
python3 tests/test_app.py
python3 tests/test_api.py
python3 tests/test_pdf_courses.py
python3 tests/test_pianificazione.py
```

