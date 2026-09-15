-- ====================================================================
-- DATI INIZIALI DIMOSTRATIVI (SEED DATA)
-- ====================================================================

-- 1. CATALOGO CORSI
INSERT OR IGNORE INTO corso (id, codice_corso, denominazione, ente_erogatore, durata_ore, validita_mesi, prerequisiti, fonte_catalogo, descrizione) VALUES
(1, 'COR-BLSD-01', 'Operatore BLSD (Primo Soccorso e Defibrillatore)', 'Croce Rossa Italiana', 12, 24, 'Idoneità fisica all''impiego operativo; nessun corso propedeutico richiesto.', 'Manuale', 'Abilitazione all''uso del defibrillatore semi-automatico e rianimazione cardio-polmonare di base.'),
(2, 'COR-GUIDA-02', 'Guida Sicura Operativa e Difensiva', 'Centro Addestramento Guida Sicura', 40, NULL, 'Possesso di Patente Civile cat. B da almeno 2 anni o Patente di Servizio Mod. 2.', 'Manuale', 'Tecniche di guida in condizioni estreme, frenata d''emergenza e controllo sbandata.'),
(3, 'COR-ANTINC-03', 'Addetto Antincendio Rischio Elevato', 'Comando Provinciale Vigili del Fuoco', 16, 36, 'Superamento visita medica di idoneità alle mansioni antincendio.', 'Manuale', 'Corso antincendio conforme a normativa di settore, con prova pratica di spegnimento.'),
(4, 'COR-CYBER-04', 'Cyber Security e Tutela Dati Istituzionali', 'Polo Formativo Informatico', 20, NULL, 'Abilitazione di sicurezza (NOS) o mansioni di gestione banche dati e documenti riservati.', 'Manuale', 'Prevenzione minacce informatiche, phishing e sicurezza delle comunicazioni.'),
(5, 'COR-SICUR-05', 'Formazione Generale e Specifica D.Lgs. 81/08', 'Servizio Prevenzione e Protezione', 16, 60, 'Destinato a tutto il personale neo-assegnato al reparto.', 'Manuale', 'Salute e sicurezza nei luoghi di lavoro ad alto rischio.');

-- 2. PERSONALE
INSERT OR IGNORE INTO personale (id, matricola, codice_fiscale, cognome, nome, sesso, data_nascita, luogo_nascita, provincia_nascita, grado_qualifica, reparto_ufficio, incarico, posto_tabellare, data_arruolamento_assunzione, stato_servizio, email_istituzionale, email_personale, telefono, indirizzo_residenza, note_generali) VALUES
(1, 'MAT-10482', 'RSSMRA80A01H501U', 'Rossi', 'Mario', 'M', '1980-01-01', 'Roma', 'RM', 'Capitano', 'Ufficio Piani ed Intelligence', 'Capo Ufficio', 'Pos. Tabellare 01/A (Direttivo)', '2004-10-15', 'In Servizio', 'mario.rossi@personale.gov.it', 'mario.rossi80@email.it', '+39 333 1234567', 'Via Nomentana 120, Roma', 'Specializzato in analisi strategica e piani operativi.'),
(2, 'MAT-11230', 'BNCGPP85E12F205K', 'Bianchi', 'Giuseppe', 'M', '1985-05-12', 'Milano', 'MI', 'Maresciallo Capo', 'Sezione Studi Speciali', 'Responsabile Ricerca e Sviluppo', 'Pos. Tabellare 03/B (Coordinamento)', '2008-03-01', 'In Servizio', 'giuseppe.bianchi@personale.gov.it', 'g.bianchi@email.it', '+39 347 9876543', 'Corso Sempione 45, Milano', 'Abilitato alla gestione di progetti riservati.'),
(3, 'MAT-12591', 'VRDLGU90L20A662X', 'Verdi', 'Luigi', 'M', '1990-07-20', 'Bari', 'BA', 'Sergente Maggiore', 'Sezione Pianificazione Operativa', 'Addetto Pianificazione', 'Pos. Tabellare 05/C (Operativo)', '2012-09-10', 'In Servizio', 'luigi.verdi@personale.gov.it', 'luigi.verdi@email.it', '+39 320 5551234', 'Via Sparano 88, Bari', 'Ottima competenza nelle comunicazioni tattiche.'),
(4, 'MAT-13844', 'FRRFBA94R45H501D', 'Ferrari', 'Francesca', 'F', '1994-10-05', 'Roma', 'RM', 'Tenente', 'Ufficio Piani ed Intelligence', 'Ufficiale Addetto Intelligence', 'Pos. Tabellare 02/A (Analisi)', '2016-04-18', 'In Servizio', 'francesca.ferrari@personale.gov.it', 'francy.ferrari@email.it', '+39 338 7778899', 'Viale Marconi 210, Roma', 'Laurea magistrale, gestione banche dati informative.'),
(5, 'MAT-14102', 'ESPLGI92C15F839Z', 'Esposito', 'Luigi', 'M', '1992-03-15', 'Napoli', 'NA', 'Caporal Maggiore Capo', 'Sezione Pianificazione Operativa', 'Operatore Tecnico di Supporto', 'Pos. Tabellare 08/C (Esecutivo)', '2015-06-01', 'In Servizio', 'luigi.esposito@personale.gov.it', 'esposito.l@email.it', '+39 340 3332211', 'Via Toledo 15, Napoli', 'Conduttore qualificato e supporto logistico.');

-- 3. PATENTI
INSERT OR IGNORE INTO patente (id, personale_id, tipo_patente, categoria, numero_patente, ente_rilascio, data_rilascio, data_scadenza, limitazioni_abilitazioni) VALUES
-- Mario Rossi (Patente civile valida, patente di servizio)
(1, 1, 'Civile', 'B', 'U1D883291X', 'M.I.T. - UCO', '2018-02-10', '2028-02-10', 'Obbligo lenti correttive (01)'),
(2, 1, 'Servizio/Militare', 'Mod. 3 (Autovetture e Autocarri)', 'SM-2015-0044', 'Comando Generale', '2015-05-14', '2027-05-14', 'Abilitazione guida veloce e scorta'),
-- Giuseppe Bianchi (Patente civile C + CQC in scadenza tra 25 giorni)
(3, 2, 'Civile', 'C - CQC Merci', 'U1D771120K', 'Motorizzazione Civile Milano', '2021-10-05', '2026-10-06', 'Professionale trasporto cose'),
(4, 2, 'Servizio/Militare', 'Mod. 4 (Mezzi pesanti e speciali)', 'SM-2018-0912', 'Comando Logistico', '2018-11-20', '2028-11-20', 'Abilitazione automezzi pesanti e rimorchi'),
-- Luigi Verdi (Patente civile in scadenza a breve)
(5, 3, 'Civile', 'B', 'U1D445566T', 'M.I.T. - UCO', '2016-09-25', '2026-09-25', 'Nessuna'),
-- Francesca Ferrari (Patente regolare)
(6, 4, 'Civile', 'B', 'U1D998877L', 'M.I.T. - UCO', '2019-06-15', '2029-06-15', 'Nessuna'),
-- Luigi Esposito (Patente civile + di servizio)
(7, 5, 'Civile', 'B', 'U1D332211M', 'Motorizzazione Civile Napoli', '2020-04-10', '2030-04-10', 'Nessuna'),
(8, 5, 'Servizio/Militare', 'Mod. 2 / Guida Operativa', 'SM-2019-1120', 'Reparto Mobile', '2019-07-01', '2026-09-15', 'Guida operativa');

-- 4. PARTECIPAZIONE CORSI
INSERT OR IGNORE INTO partecipazione_corso (id, personale_id, corso_id, data_inizio, data_fine, esito, numero_attestato, data_scadenza_abilitazione, note) VALUES
(1, 1, 1, '2025-02-10', '2025-02-12', 'Superato', 'ATT-BLSD-2025-098', '2027-02-12', 'Rinnovo periodico completato con valutazione ottima.'),
(2, 1, 4, '2024-11-04', '2024-11-08', 'Superato', 'ATT-CYB-2024-441', NULL, 'Formazione per dirigenti e quadri.'),
(3, 2, 2, '2023-05-15', '2023-05-20', 'Specializzato', 'ATT-GSO-2023-019', NULL, 'Abilitato a istruttore di guida operativa interna.'),
(4, 2, 3, '2023-10-02', '2023-10-04', 'Idoneo', 'ATT-ANT-2023-112', '2026-10-04', 'Addetto antincendio del reparto.'),
(5, 3, 1, '2024-04-10', '2024-04-12', 'Superato', 'ATT-BLSD-2024-301', '2026-04-12', 'Abilitazione BLSD in corso di validità.'),
(6, 4, 4, '2025-01-15', '2025-01-18', 'Superato', 'ATT-CYB-2025-012', NULL, 'Trattamento dati sensibili GDPR e fascicolo personale.'),
(7, 5, 2, '2024-03-01', '2024-03-06', 'Superato', 'ATT-GSO-2024-055', NULL, 'Superato con menzione di merito.');

-- 5. NOTE CARATTERISTICHE (Con data prossima scadenza = fine periodo + 365 giorni)
INSERT OR IGNORE INTO nota_caratteristica (id, personale_id, tipologia_documento, motivo_redazione, periodo_dal, periodo_al, data_firma_interessato, data_prossima_scadenza, giudizio_finale, compilatore, primo_revisore, secondo_revisore, annotazioni) VALUES
-- Mario Rossi: Ultima nota redatta per il periodo fino al 2025-10-31. Prossima scadenza: 2026-10-31 (entro ~50 giorni)
(1, 1, 'Note Caratteristiche', 'Ordinaria Annuale', '2024-11-01', '2025-10-31', '2025-11-15', '2026-10-31', 'Eccellente con Lode', 'Col. A. Mancini', 'Gen. B. De Luca', NULL, 'Ufficiale di spiccate doti organizzative e grande spirito di servizio.'),
-- Mario Rossi (anno precedente)
(2, 1, 'Note Caratteristiche', 'Ordinaria Annuale', '2023-11-01', '2024-10-31', '2024-11-10', '2025-10-31', 'Eccellente', 'Col. A. Mancini', 'Gen. B. De Luca', NULL, 'Conferma costante rendimento di massimo livello.'),

-- Giuseppe Bianchi: Ultima nota al 2025-08-15 -> Scaduta il 2026-08-15 (URGENTE/SCADUTA!)
(3, 2, 'Note Caratteristiche', 'Ordinaria Annuale', '2024-08-16', '2025-08-15', '2025-08-28', '2026-08-15', 'Eccellente', 'Magg. S. Neri', 'Col. A. Mancini', NULL, 'Nota caratteristica scaduta, da compilare urgentemente.'),

-- Luigi Verdi: Ultima nota al 2025-09-30 -> Scadenza 2026-09-30 (entro ~19 giorni! URGENTE!)
(4, 3, 'Scheda Valutativa', 'Ordinaria Annuale', '2024-10-01', '2025-09-30', '2025-10-05', '2026-09-30', 'Superiore alla Media', 'Cap. M. Rossi', 'Magg. S. Neri', NULL, 'In preparazione la nuova scheda per l''anno in corso.'),

-- Francesca Ferrari: Ultima nota al 2026-02-28 -> Prossima scadenza 2027-02-28 (REGOLARE)
(5, 4, 'Note Caratteristiche', 'Ordinaria Annuale', '2025-03-01', '2026-02-28', '2026-03-10', '2027-02-28', 'Eccellente', 'Magg. S. Neri', 'Col. A. Mancini', NULL, 'Rendimento esemplare nella gestione dell''ufficio.'),

-- Luigi Esposito: Cambio incarico al 2025-12-15 -> Prossima scadenza 2026-12-15 (REGOLARE)
(6, 5, 'Rapporto Informativo', 'Cambio Incarico', '2025-06-01', '2025-12-15', '2025-12-20', '2026-12-15', 'Superiore alla Media', 'Ten. F. Ferrari', 'Cap. M. Rossi', NULL, 'Redatto per cambio mansione da scorta a radiomobile.');

-- 6. PASSAPORTO DI SERVIZIO
INSERT OR IGNORE INTO passaporto_servizio (id, personale_id, numero_passaporto, tipo_passaporto, autorita_rilascio, data_rilascio, data_scadenza, stato, ubicazione_custodia, note) VALUES
(1, 1, 'PS-889901A', 'Servizio', 'Ministero Affari Esteri e Cooperazione Internazionale', '2022-04-10', '2027-04-10', 'Valido', 'Cassaforte Comando', 'Rilasciato per missioni internazionali di cooperazione.'),
(2, 2, 'PS-672190B', 'Servizio', 'Ministero Affari Esteri e Cooperazione Internazionale', '2021-09-20', '2026-09-20', 'In Rinnovo', 'Archivio Ufficio Personale', 'Pratica di rinnovo avviata presso il MAECI.'),
(3, 4, 'PS-991023C', 'Servizio', 'Ministero Affari Esteri e Cooperazione Internazionale', '2023-01-15', '2028-01-15', 'Valido', 'Archivio Ufficio Personale', 'Titolare di passaporto per trasferte istituzionali UE.');

