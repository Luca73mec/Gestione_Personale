-- ====================================================================
-- SCHEMA DATABASE: GESTIONE PERSONALE
-- Supporto completo: Anagrafica, Corsi, Patenti, Note Caratteristiche, Passaporti
-- ====================================================================

PRAGMA foreign_keys = ON;

-- 1. TABELLA PERSONALE (Anagrafica completa e dati di servizio)
CREATE TABLE IF NOT EXISTS personale (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    matricola TEXT UNIQUE NOT NULL,
    codice_fiscale TEXT UNIQUE NOT NULL,
    cognome TEXT NOT NULL,
    nome TEXT NOT NULL,
    sesso TEXT CHECK(sesso IN ('M', 'F', 'Altro')) DEFAULT 'M',
    data_nascita DATE NOT NULL,
    luogo_nascita TEXT NOT NULL,
    provincia_nascita TEXT,
    grado_qualifica TEXT NOT NULL,
    reparto_ufficio TEXT NOT NULL CHECK(reparto_ufficio IN ('Ufficio Piani ed Intelligence', 'Sezione Studi Speciali', 'Sezione Pianificazione Operativa')),
    incarico TEXT,
    posto_tabellare TEXT,
    data_arruolamento_assunzione DATE,
    stato_servizio TEXT DEFAULT 'In Servizio' CHECK(stato_servizio IN ('In Servizio', 'Congedo', 'Licenza Straordinaria', 'Distaccato', 'Altro')),
    email_istituzionale TEXT,
    email_personale TEXT,
    telefono TEXT,
    indirizzo_residenza TEXT,
    livello_nos TEXT DEFAULT 'Riservato', -- Es: Nessuno, Riservato, Segreto / NATO Secret, Segretissimo / COSMIC Top Secret
    lingua_inglese TEXT DEFAULT 'NATO JFLT 8', -- Es: NATO JFLT 8 (2/2/2/2), NATO SLP 8, Livello B2, ecc.
    note_generali TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. TABELLA PATENTI (Civili e di Servizio/Militari)
CREATE TABLE IF NOT EXISTS patente (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    personale_id INTEGER NOT NULL,
    tipo_patente TEXT NOT NULL CHECK(tipo_patente IN ('Civile', 'Servizio/Militare', 'CQC', 'Altro')),
    categoria TEXT NOT NULL, -- Es: A, B, C, D, CE, Mod. 2, Mod. 3, ecc.
    numero_patente TEXT NOT NULL,
    ente_rilascio TEXT NOT NULL, -- Es: M.I.T. - UCO, Prefettura, Comando Militare
    data_rilascio DATE NOT NULL,
    data_scadenza DATE NOT NULL,
    limitazioni_abilitazioni TEXT, -- Es: Guida veloce, Mezzi corazzati, Obbligo lenti 01
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (personale_id) REFERENCES personale(id) ON DELETE CASCADE
);

-- 3. TABELLA CATALOGO CORSI
CREATE TABLE IF NOT EXISTS corso (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codice_corso TEXT UNIQUE NOT NULL,
    denominazione TEXT NOT NULL,
    ente_erogatore TEXT NOT NULL,
    durata_settimane INTEGER, -- Durata temporale in settimane (es. 1, 2, 4, 5, 6, 7)
    durata_ore INTEGER, -- Durata totale in ore (es. settimane * 36)
    validita_mesi INTEGER DEFAULT NULL, -- NULL se senza scadenza periodica (permanente)
    requisiti_sicurezza TEXT, -- Es. NOS Riservato, Segreto / NATO Secret, Segretissimo / COSMIC Top Secret
    precedenti_formativi TEXT, -- Es. Corsi propedeutici obbligatori o auspicabili
    precedenti_operativi TEXT, -- Es. 12 mesi impiego operativo OSINT, 3 anni CII, ecc.
    selezioni TEXT, -- Es. Prove selettive protocollo fonti umane 2021, idoneità volo IMAS, test ingresso
    conoscenza_lingua TEXT, -- Es. NATO JFLT non inferiore a 8 (2/2/2/2), NATO SLP 8
    altri_requisiti TEXT, -- Es. Patente Militare Mod. 2, giudizio note caratteristiche >= Superiore alla Media
    prerequisiti TEXT, -- Sintesi generale dei requisiti per compatibilità retroattiva
    fonte_catalogo TEXT DEFAULT 'Manuale', -- Nome file PDF o 'Manuale'
    descrizione TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. TABELLA PARTECIPAZIONE CORSI (Corsi frequentati da ciascun dipendente)
CREATE TABLE IF NOT EXISTS partecipazione_corso (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    personale_id INTEGER NOT NULL,
    corso_id INTEGER NOT NULL,
    data_inizio DATE NOT NULL,
    data_fine DATE NOT NULL,
    esito TEXT NOT NULL CHECK(esito IN ('Superato', 'Idoneo', 'Qualificato', 'Specializzato', 'Non Idoneo', 'Frequentato')),
    numero_attestato TEXT,
    data_scadenza_abilitazione DATE, -- Calcolata o indicata esplicitamente
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (personale_id) REFERENCES personale(id) ON DELETE CASCADE,
    FOREIGN KEY (corso_id) REFERENCES corso(id) ON DELETE RESTRICT
);

-- 5. TABELLA NOTE CARATTERISTICHE (Documenti di valutazione e scadenze)
CREATE TABLE IF NOT EXISTS nota_caratteristica (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    personale_id INTEGER NOT NULL,
    tipologia_documento TEXT NOT NULL CHECK(tipologia_documento IN ('Note Caratteristiche', 'Scheda Valutativa', 'Rapporto Informativo', 'Altro')),
    motivo_redazione TEXT NOT NULL CHECK(motivo_redazione IN ('Ordinaria Annuale', 'Cambio Incarico', 'Cambio Superiore', 'Avanzamento', 'Straordinaria', 'Fine Servizio', 'Altro')),
    periodo_dal DATE NOT NULL,
    periodo_al DATE NOT NULL,
    data_firma_interessato DATE, -- Data in cui il dipendente ha firmato per presa visione
    data_prossima_scadenza DATE NOT NULL, -- Di regola data fine periodo + 365 giorni
    giudizio_finale TEXT CHECK(giudizio_finale IN ('Eccellente con Lode', 'Eccellente', 'Superiore alla Media', 'Nella Media', 'Inferiore alla Media', 'Insufficiente')),
    compilatore TEXT,
    primo_revisore TEXT,
    secondo_revisore TEXT,
    annotazioni TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (personale_id) REFERENCES personale(id) ON DELETE CASCADE
);

-- 6. TABELLA PASSAPORTO DI SERVIZIO
CREATE TABLE IF NOT EXISTS passaporto_servizio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    personale_id INTEGER NOT NULL,
    numero_passaporto TEXT UNIQUE NOT NULL,
    tipo_passaporto TEXT DEFAULT 'Servizio' CHECK(tipo_passaporto IN ('Servizio', 'Diplomatico', 'Speciale')),
    autorita_rilascio TEXT DEFAULT 'Ministero Affari Esteri e Cooperazione Internazionale',
    data_rilascio DATE NOT NULL,
    data_scadenza DATE NOT NULL,
    stato TEXT DEFAULT 'Valido' CHECK(stato IN ('Valido', 'In Rinnovo', 'Scaduto', 'Restituito', 'Smarrito')),
    ubicazione_custodia TEXT DEFAULT 'Archivio Ufficio Personale', -- Dove si trova fisicamente il libretto
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (personale_id) REFERENCES personale(id) ON DELETE CASCADE
);

-- INDICI DI PERFORMANCE
CREATE INDEX IF NOT EXISTS idx_personale_cognome_nome ON personale(cognome, nome);
CREATE INDEX IF NOT EXISTS idx_personale_matricola ON personale(matricola);
CREATE INDEX IF NOT EXISTS idx_patente_scadenza ON patente(data_scadenza);
CREATE INDEX IF NOT EXISTS idx_note_scadenza ON nota_caratteristica(data_prossima_scadenza);
CREATE INDEX IF NOT EXISTS idx_passaporto_scadenza ON passaporto_servizio(data_scadenza);
CREATE INDEX IF NOT EXISTS idx_partecipazione_persona ON partecipazione_corso(personale_id);

-- VISTE PER IL CRUSCOTTO DELLE SCADENZE

-- Vista per individuare l'ultima nota caratteristica per ciascun dipendente
CREATE VIEW IF NOT EXISTS vista_ultima_nota_personale AS
SELECT 
    nc.id AS nota_id,
    p.id AS personale_id,
    p.matricola,
    p.grado_qualifica,
    p.cognome,
    p.nome,
    p.reparto_ufficio,
    nc.tipologia_documento,
    nc.motivo_redazione,
    nc.periodo_dal,
    nc.periodo_al,
    nc.data_firma_interessato,
    nc.data_prossima_scadenza,
    nc.giudizio_finale,
    CAST(julianday(nc.data_prossima_scadenza) - julianday('now', 'localtime') AS INTEGER) AS giorni_alla_scadenza,
    CASE 
        WHEN julianday(nc.data_prossima_scadenza) < julianday('now', 'localtime') THEN 'SCADUTA'
        WHEN julianday(nc.data_prossima_scadenza) - julianday('now', 'localtime') <= 30 THEN 'URGENTE_30GG'
        WHEN julianday(nc.data_prossima_scadenza) - julianday('now', 'localtime') <= 60 THEN 'IN_SCADENZA_60GG'
        ELSE 'REGOLARE'
    END AS stato_scadenza
FROM nota_caratteristica nc
JOIN personale p ON p.id = nc.personale_id
WHERE nc.id = (
    SELECT nc2.id 
    FROM nota_caratteristica nc2 
    WHERE nc2.personale_id = nc.personale_id 
    ORDER BY nc2.periodo_al DESC, nc2.id DESC 
    LIMIT 1
);

-- Vista scadenze patenti
CREATE VIEW IF NOT EXISTS vista_scadenze_patenti AS
SELECT 
    pat.id AS patente_id,
    p.id AS personale_id,
    p.matricola,
    p.grado_qualifica,
    p.cognome,
    p.nome,
    pat.tipo_patente,
    pat.categoria,
    pat.numero_patente,
    pat.data_scadenza,
    CAST(julianday(pat.data_scadenza) - julianday('now', 'localtime') AS INTEGER) AS giorni_alla_scadenza,
    CASE 
        WHEN julianday(pat.data_scadenza) < julianday('now', 'localtime') THEN 'SCADUTA'
        WHEN julianday(pat.data_scadenza) - julianday('now', 'localtime') <= 30 THEN 'URGENTE_30GG'
        WHEN julianday(pat.data_scadenza) - julianday('now', 'localtime') <= 60 THEN 'IN_SCADENZA_60GG'
        ELSE 'REGOLARE'
    END AS stato_scadenza
FROM patente pat
JOIN personale p ON p.id = pat.personale_id;

-- Vista scadenze passaporti
CREATE VIEW IF NOT EXISTS vista_scadenze_passaporti AS
SELECT 
    ps.id AS passaporto_id,
    p.id AS personale_id,
    p.matricola,
    p.grado_qualifica,
    p.cognome,
    p.nome,
    ps.numero_passaporto,
    ps.tipo_passaporto,
    ps.data_scadenza,
    ps.stato,
    ps.ubicazione_custodia,
    CAST(julianday(ps.data_scadenza) - julianday('now', 'localtime') AS INTEGER) AS giorni_alla_scadenza,
    CASE 
        WHEN julianday(ps.data_scadenza) < julianday('now', 'localtime') THEN 'SCADUTO'
        WHEN julianday(ps.data_scadenza) - julianday('now', 'localtime') <= 30 THEN 'URGENTE_30GG'
        WHEN julianday(ps.data_scadenza) - julianday('now', 'localtime') <= 90 THEN 'IN_SCADENZA_90GG'
        ELSE 'REGOLARE'
    END AS stato_scadenza
FROM passaporto_servizio ps
JOIN personale p ON p.id = ps.personale_id;

