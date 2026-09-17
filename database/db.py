"""
Modulo di gestione del Database SQLite per l'applicazione Gestione Personale.
Fornisce connessioni sicure, migrazioni/inizializzazione automatica e metodi helper per CRUD e scadenze.
"""

import sqlite3
import os
from pathlib import Path
from datetime import datetime, timedelta
from contextlib import contextmanager

DB_DIR = Path(__file__).resolve().parent
DB_FILE = DB_DIR / "personale.db"
SCHEMA_FILE = DB_DIR / "schema.sql"
SEED_FILE = DB_DIR / "seed_data.sql"


@contextmanager
def get_db_connection():
    """Restituisce una connessione al database SQLite configurata con Row factory e foreign keys."""
    conn = sqlite3.connect(str(DB_FILE))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    try:
        yield conn
    finally:
        conn.close()


def init_db(force=False):
    """Inizializza il database se non esiste oppure se richiesto con force=True."""
    if force and DB_FILE.exists():
        DB_FILE.unlink()
    db_exists = DB_FILE.exists()
    if not db_exists:
        print(f"[DB] Inizializzazione database su {DB_FILE}...")
        conn = sqlite3.connect(str(DB_FILE))
        try:
            with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
                conn.executescript(f.read())
            if SEED_FILE.exists():
                with open(SEED_FILE, "r", encoding="utf-8") as f:
                    conn.executescript(f.read())
            conn.commit()
        finally:
            conn.close()
        print("[DB] Inizializzazione completata con successo.")
    else:
        conn = sqlite3.connect(str(DB_FILE))
        try:
            with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
                conn.executescript(f.read())
            # Verifica se la colonna posto_tabellare esiste già in personale
            cursor = conn.execute("PRAGMA table_info(personale);")
            columns = [row[1] for row in cursor.fetchall()]
            if "posto_tabellare" not in columns:
                conn.execute("ALTER TABLE personale ADD COLUMN posto_tabellare TEXT;")

            # Verifica colonne prerequisiti e fonte_catalogo in corso
            cursor = conn.execute("PRAGMA table_info(corso);")
            corso_cols = [row[1] for row in cursor.fetchall()]
            if "prerequisiti" not in corso_cols:
                conn.execute("ALTER TABLE corso ADD COLUMN prerequisiti TEXT;")
            if "fonte_catalogo" not in corso_cols:
                conn.execute("ALTER TABLE corso ADD COLUMN fonte_catalogo TEXT DEFAULT 'Manuale';")
            conn.commit()
        finally:
            conn.close()


def row_to_dict(row):
    """Converte un oggetto sqlite3.Row in un dizionario Python standard."""
    if row is None:
        return None
    return dict(row)


def rows_to_list(rows):
    """Converte una lista di sqlite3.Row in lista di dizionari."""
    return [dict(r) for r in rows]


# ====================================================================
# STATISTICHE DASHBOARD & SCADENZARIO
# ====================================================================

def get_dashboard_stats():
    """Recupera contatori e sintesi per il cruscotto principale."""
    with get_db_connection() as conn:
        totale_personale = conn.execute("SELECT COUNT(*) FROM personale WHERE stato_servizio = 'In Servizio'").fetchone()[0]
        
        # Note caratteristiche scadute o in scadenza
        note_scadute = conn.execute("SELECT COUNT(*) FROM vista_ultima_nota_personale WHERE stato_scadenza = 'SCADUTA'").fetchone()[0]
        note_urgenti_30 = conn.execute("SELECT COUNT(*) FROM vista_ultima_nota_personale WHERE stato_scadenza = 'URGENTE_30GG'").fetchone()[0]
        note_in_scadenza_60 = conn.execute("SELECT COUNT(*) FROM vista_ultima_nota_personale WHERE stato_scadenza = 'IN_SCADENZA_60GG'").fetchone()[0]
        
        # Patenti in scadenza
        patenti_scadute = conn.execute("SELECT COUNT(*) FROM vista_scadenze_patenti WHERE stato_scadenza = 'SCADUTA'").fetchone()[0]
        patenti_in_scadenza = conn.execute("SELECT COUNT(*) FROM vista_scadenze_patenti WHERE stato_scadenza IN ('URGENTE_30GG', 'IN_SCADENZA_60GG')").fetchone()[0]
        
        # Passaporti in scadenza
        passaporti_in_scadenza = conn.execute("SELECT COUNT(*) FROM vista_scadenze_passaporti WHERE stato_scadenza IN ('SCADUTO', 'URGENTE_30GG', 'IN_SCADENZA_90GG')").fetchone()[0]
        
        # Corsi totali a catalogo
        totale_corsi = conn.execute("SELECT COUNT(*) FROM corso").fetchone()[0]
        
        return {
            "totale_personale": totale_personale,
            "note_scadute": note_scadute,
            "note_urgenti_30": note_urgenti_30,
            "note_in_scadenza_60": note_in_scadenza_60,
            "totale_alert_note": note_scadute + note_urgenti_30 + note_in_scadenza_60,
            "patenti_scadute": patenti_scadute,
            "patenti_in_scadenza": patenti_in_scadenza,
            "passaporti_in_scadenza": passaporti_in_scadenza,
            "totale_corsi": totale_corsi
        }


def get_scadenzario():
    """Recupera tutti gli eventi e documenti in scadenza o scaduti."""
    with get_db_connection() as conn:
        note = rows_to_list(conn.execute("""
            SELECT * FROM vista_ultima_nota_personale 
            WHERE stato_scadenza IN ('SCADUTA', 'URGENTE_30GG', 'IN_SCADENZA_60GG')
            ORDER BY giorni_alla_scadenza ASC
        """).fetchall())
        
        patenti = rows_to_list(conn.execute("""
            SELECT * FROM vista_scadenze_patenti 
            WHERE stato_scadenza IN ('SCADUTA', 'URGENTE_30GG', 'IN_SCADENZA_60GG')
            ORDER BY giorni_alla_scadenza ASC
        """).fetchall())
        
        passaporti = rows_to_list(conn.execute("""
            SELECT * FROM vista_scadenze_passaporti 
            WHERE stato_scadenza IN ('SCADUTO', 'URGENTE_30GG', 'IN_SCADENZA_90GG')
            ORDER BY giorni_alla_scadenza ASC
        """).fetchall())
        
        return {
            "note": note,
            "patenti": patenti,
            "passaporti": passaporti
        }


# ====================================================================
# PERSONALE
# ====================================================================

def get_all_personale(search=None, reparto=None, stato=None):
    """Elenco personale con ricerca per testo e filtri."""
    query = """
        SELECT p.*,
               vun.tipologia_documento AS ultima_nota_tipo,
               vun.periodo_al AS ultima_nota_periodo_al,
               vun.data_prossima_scadenza AS prossima_scadenza_nota,
               vun.giorni_alla_scadenza AS giorni_scadenza_nota,
               vun.stato_scadenza AS stato_nota,
               (SELECT COUNT(*) FROM patente WHERE personale_id = p.id) AS num_patenti,
               (SELECT COUNT(*) FROM partecipazione_corso WHERE personale_id = p.id) AS num_corsi,
               (SELECT COUNT(*) FROM passaporto_servizio WHERE personale_id = p.id) AS num_passaporti
        FROM personale p
        LEFT JOIN vista_ultima_nota_personale vun ON vun.personale_id = p.id
        WHERE 1=1
    """
    params = []
    
    if search:
        s = f"%{search.strip()}%"
        query += " AND (p.cognome LIKE ? OR p.nome LIKE ? OR p.matricola LIKE ? OR p.codice_fiscale LIKE ? OR p.grado_qualifica LIKE ?)"
        params.extend([s, s, s, s, s])
        
    if reparto:
        query += " AND p.reparto_ufficio = ?"
        params.append(reparto)
        
    if stato:
        query += " AND p.stato_servizio = ?"
        params.append(stato)
        
    query += " ORDER BY p.cognome ASC, p.nome ASC"
    
    with get_db_connection() as conn:
        return rows_to_list(conn.execute(query, params).fetchall())


def get_personale_by_matricola(matricola):
    """Restituisce il dettaglio completo di un militare cercandolo per matricola."""
    if not matricola:
        return None
    with get_db_connection() as conn:
        p = conn.execute("SELECT id FROM personale WHERE LOWER(matricola) = LOWER(?)", (str(matricola).strip(),)).fetchone()
        if p:
            return get_personale_by_id(p["id"])
        return None


def get_personale_by_id_or_matricola(identifier):
    """Restituisce il dipendente per ID intero o per matricola."""
    if identifier is None:
        return None
    ident_str = str(identifier).strip()
    if ident_str.isdigit():
        return get_personale_by_id(int(ident_str))
    return get_personale_by_matricola(ident_str)


def get_personale_by_id(personale_id):
    """Scheda anagrafica completa con patenti, corsi, note e passaporti."""
    with get_db_connection() as conn:
        p = conn.execute("SELECT * FROM personale WHERE id = ?", (personale_id,)).fetchone()
        if not p:
            return None
        
        data = row_to_dict(p)
        
        # Patenti
        data["patenti"] = rows_to_list(conn.execute("""
            SELECT *,
                   CAST(julianday(data_scadenza) - julianday('now', 'localtime') AS INTEGER) AS giorni_alla_scadenza,
                   CASE 
                       WHEN julianday(data_scadenza) < julianday('now', 'localtime') THEN 'SCADUTA'
                       WHEN julianday(data_scadenza) - julianday('now', 'localtime') <= 30 THEN 'URGENTE_30GG'
                       WHEN julianday(data_scadenza) - julianday('now', 'localtime') <= 60 THEN 'IN_SCADENZA_60GG'
                       ELSE 'REGOLARE'
                   END AS stato_scadenza
            FROM patente 
            WHERE personale_id = ? 
            ORDER BY data_scadenza ASC
        """, (personale_id,)).fetchall())
        
        # Note Caratteristiche (storico ordinato per data fine)
        data["note_caratteristiche"] = rows_to_list(conn.execute("""
            SELECT *,
                   CAST(julianday(data_prossima_scadenza) - julianday('now', 'localtime') AS INTEGER) AS giorni_alla_scadenza,
                   CASE 
                       WHEN julianday(data_prossima_scadenza) < julianday('now', 'localtime') THEN 'SCADUTA'
                       WHEN julianday(data_prossima_scadenza) - julianday('now', 'localtime') <= 30 THEN 'URGENTE_30GG'
                       WHEN julianday(data_prossima_scadenza) - julianday('now', 'localtime') <= 60 THEN 'IN_SCADENZA_60GG'
                       ELSE 'REGOLARE'
                   END AS stato_scadenza
            FROM nota_caratteristica 
            WHERE personale_id = ? 
            ORDER BY periodo_al DESC
        """, (personale_id,)).fetchall())
        
        # Corsi Frequentati
        data["corsi"] = rows_to_list(conn.execute("""
            SELECT pc.*, c.codice_corso, c.denominazione, c.ente_erogatore, c.durata_ore, c.validita_mesi, c.prerequisiti, c.fonte_catalogo
            FROM partecipazione_corso pc
            JOIN corso c ON c.id = pc.corso_id
            WHERE pc.personale_id = ?
            ORDER BY pc.data_fine DESC
        """, (personale_id,)).fetchall())
        
        # Passaporto di Servizio
        data["passaporti"] = rows_to_list(conn.execute("""
            SELECT *,
                   CAST(julianday(data_scadenza) - julianday('now', 'localtime') AS INTEGER) AS giorni_alla_scadenza,
                   CASE 
                       WHEN julianday(data_scadenza) < julianday('now', 'localtime') THEN 'SCADUTO'
                       WHEN julianday(data_scadenza) - julianday('now', 'localtime') <= 30 THEN 'URGENTE_30GG'
                       WHEN julianday(data_scadenza) - julianday('now', 'localtime') <= 90 THEN 'IN_SCADENZA_90GG'
                       ELSE 'REGOLARE'
                   END AS stato_scadenza
            FROM passaporto_servizio 
            WHERE personale_id = ? 
            ORDER BY data_scadenza DESC
        """, (personale_id,)).fetchall())
        
        return data


def create_personale(data):
    """Inserisce un nuovo dipendente/militare."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO personale (
                matricola, codice_fiscale, cognome, nome, sesso, data_nascita, luogo_nascita,
                provincia_nascita, grado_qualifica, reparto_ufficio, incarico, posto_tabellare,
                data_arruolamento_assunzione, stato_servizio, email_istituzionale, email_personale,
                telefono, indirizzo_residenza, note_generali
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("matricola"),
            data.get("codice_fiscale", "").upper(),
            data.get("cognome"),
            data.get("nome"),
            data.get("sesso", "M"),
            data.get("data_nascita"),
            data.get("luogo_nascita"),
            data.get("provincia_nascita"),
            data.get("grado_qualifica"),
            data.get("reparto_ufficio"),
            data.get("incarico"),
            data.get("posto_tabellare"),
            data.get("data_arruolamento_assunzione"),
            data.get("stato_servizio", "In Servizio"),
            data.get("email_istituzionale"),
            data.get("email_personale"),
            data.get("telefono"),
            data.get("indirizzo_residenza"),
            data.get("note_generali")
        ))
        conn.commit()
        return cursor.lastrowid


def update_personale(personale_id, data):
    """Aggiorna i dati anagrafici e di servizio di una persona."""
    with get_db_connection() as conn:
        conn.execute("""
            UPDATE personale SET
                matricola = ?,
                codice_fiscale = ?,
                cognome = ?,
                nome = ?,
                sesso = ?,
                data_nascita = ?,
                luogo_nascita = ?,
                provincia_nascita = ?,
                grado_qualifica = ?,
                reparto_ufficio = ?,
                incarico = ?,
                posto_tabellare = ?,
                data_arruolamento_assunzione = ?,
                stato_servizio = ?,
                email_istituzionale = ?,
                email_personale = ?,
                telefono = ?,
                indirizzo_residenza = ?,
                note_generali = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            data.get("matricola"),
            data.get("codice_fiscale", "").upper(),
            data.get("cognome"),
            data.get("nome"),
            data.get("sesso"),
            data.get("data_nascita"),
            data.get("luogo_nascita"),
            data.get("provincia_nascita"),
            data.get("grado_qualifica"),
            data.get("reparto_ufficio"),
            data.get("incarico"),
            data.get("posto_tabellare"),
            data.get("data_arruolamento_assunzione"),
            data.get("stato_servizio"),
            data.get("email_istituzionale"),
            data.get("email_personale"),
            data.get("telefono"),
            data.get("indirizzo_residenza"),
            data.get("note_generali"),
            personale_id
        ))
        conn.commit()
        return True


def delete_personale(personale_id):
    """Elimina una persona e a cascata tutti i suoi record collegati."""
    with get_db_connection() as conn:
        conn.execute("DELETE FROM personale WHERE id = ?", (personale_id,))
        conn.commit()
        return True


# ====================================================================
# PATENTI
# ====================================================================

def add_patente(personale_id, data):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO patente (
                personale_id, tipo_patente, categoria, numero_patente,
                ente_rilascio, data_rilascio, data_scadenza, limitazioni_abilitazioni
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            personale_id,
            data.get("tipo_patente", "Civile"),
            data.get("categoria"),
            data.get("numero_patente"),
            data.get("ente_rilascio"),
            data.get("data_rilascio"),
            data.get("data_scadenza"),
            data.get("limitazioni_abilitazioni")
        ))
        conn.commit()
        return cursor.lastrowid


def update_patente(patente_id, data):
    with get_db_connection() as conn:
        conn.execute("""
            UPDATE patente SET
                tipo_patente = ?,
                categoria = ?,
                numero_patente = ?,
                ente_rilascio = ?,
                data_rilascio = ?,
                data_scadenza = ?,
                limitazioni_abilitazioni = ?
            WHERE id = ?
        """, (
            data.get("tipo_patente"),
            data.get("categoria"),
            data.get("numero_patente"),
            data.get("ente_rilascio"),
            data.get("data_rilascio"),
            data.get("data_scadenza"),
            data.get("limitazioni_abilitazioni"),
            patente_id
        ))
        conn.commit()
        return True


def delete_patente(patente_id):
    with get_db_connection() as conn:
        conn.execute("DELETE FROM patente WHERE id = ?", (patente_id,))
        conn.commit()
        return True


# ====================================================================
# NOTE CARATTERISTICHE (Calcolo automatico scadenza = periodo_al + 365 gg)
# ====================================================================

def calculate_next_deadline(periodo_al_str, days=365):
    """Calcola la data della prossima scadenza sommando 365 giorni alla data di fine periodo."""
    try:
        dt = datetime.strptime(periodo_al_str, "%Y-%m-%d")
        deadline = dt + timedelta(days=days)
        return deadline.strftime("%Y-%m-%d")
    except Exception:
        return periodo_al_str


def add_nota_caratteristica(personale_id, data):
    periodo_al = data.get("periodo_al")
    scadenza = data.get("data_prossima_scadenza")
    if not scadenza and periodo_al:
        scadenza = calculate_next_deadline(periodo_al, 365)
        
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO nota_caratteristica (
                personale_id, tipologia_documento, motivo_redazione,
                periodo_dal, periodo_al, data_firma_interessato, data_prossima_scadenza,
                giudizio_finale, compilatore, primo_revisore, secondo_revisore, annotazioni
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            personale_id,
            data.get("tipologia_documento", "Note Caratteristiche"),
            data.get("motivo_redazione", "Ordinaria Annuale"),
            data.get("periodo_dal"),
            periodo_al,
            data.get("data_firma_interessato"),
            scadenza,
            data.get("giudizio_finale"),
            data.get("compilatore"),
            data.get("primo_revisore"),
            data.get("secondo_revisore"),
            data.get("annotazioni")
        ))
        conn.commit()
        return cursor.lastrowid


def update_nota_caratteristica(nota_id, data):
    periodo_al = data.get("periodo_al")
    scadenza = data.get("data_prossima_scadenza")
    if not scadenza and periodo_al:
        scadenza = calculate_next_deadline(periodo_al, 365)

    with get_db_connection() as conn:
        conn.execute("""
            UPDATE nota_caratteristica SET
                tipologia_documento = ?,
                motivo_redazione = ?,
                periodo_dal = ?,
                periodo_al = ?,
                data_firma_interessato = ?,
                data_prossima_scadenza = ?,
                giudizio_finale = ?,
                compilatore = ?,
                primo_revisore = ?,
                secondo_revisore = ?,
                annotazioni = ?
            WHERE id = ?
        """, (
            data.get("tipologia_documento"),
            data.get("motivo_redazione"),
            data.get("periodo_dal"),
            periodo_al,
            data.get("data_firma_interessato"),
            scadenza,
            data.get("giudizio_finale"),
            data.get("compilatore"),
            data.get("primo_revisore"),
            data.get("secondo_revisore"),
            data.get("annotazioni"),
            nota_id
        ))
        conn.commit()
        return True


def delete_nota_caratteristica(nota_id):
    with get_db_connection() as conn:
        conn.execute("DELETE FROM nota_caratteristica WHERE id = ?", (nota_id,))
        conn.commit()
        return True


# ====================================================================
# CORSI & PARTECIPAZIONI
# ====================================================================

def get_all_corsi():
    """Restituisce l'elenco dei corsi a catalogo con il conteggio partecipanti."""
    with get_db_connection() as conn:
        return rows_to_list(conn.execute("""
            SELECT c.*, 
                   (SELECT COUNT(*) FROM partecipazione_corso WHERE corso_id = c.id) AS num_partecipanti
            FROM corso c 
            ORDER BY c.denominazione ASC
        """).fetchall())


def get_corso_by_id(corso_id):
    """Restituisce il dettaglio completo di un corso dal catalogo per ID numerico."""
    if corso_id is None:
        return None
    try:
        cid = int(corso_id)
    except (ValueError, TypeError):
        return None
    with get_db_connection() as conn:
        row = conn.execute("SELECT * FROM corso WHERE id = ?", (cid,)).fetchone()
        return row_to_dict(row) if row else None


def get_corso_by_id_or_code(identifier):
    """Restituisce un corso dal catalogo cercandolo per ID numerico o per codice_corso."""
    if identifier is None:
        return None
    ident_str = str(identifier).strip()
    if ident_str.isdigit():
        item = get_corso_by_id(int(ident_str))
        if item:
            return item
    with get_db_connection() as conn:
        row = conn.execute("SELECT * FROM corso WHERE LOWER(codice_corso) = LOWER(?)", (ident_str,)).fetchone()
        if not row:
            # Fallback ricerca per denominazione esatta
            row = conn.execute("SELECT * FROM corso WHERE LOWER(denominazione) = LOWER(?)", (ident_str,)).fetchone()
        return row_to_dict(row) if row else None


def valuta_candidatura_corso(personale_id, corso_id):
    """
    Esegue l'audit e la verifica di idoneità per la candidatura di un militare a un corso.
    Supporta ID numerici, matricola o codice corso.
    Analizza:
    - Stato di servizio attivo
    - Eventuale corso già conseguito (e se con validità periodica per eventuale rinnovo)
    - Prerequisiti formativi (corsi propedeutici superati)
    - Prerequisiti di abilitazione alla guida (patenti civili e militari con stato di scadenza)
    - Note caratteristiche (regolarità ultimi 365 giorni)
    - Idoneità speciali (NOS, sicurezza, idoneità sanitaria, lingua)
    """
    p = get_personale_by_id_or_matricola(personale_id)
    c = get_corso_by_id_or_code(corso_id)
    if not p:
        raise ValueError(f"Militare con riferimento '{personale_id}' non trovato")
    if not c:
        raise ValueError(f"Corso con riferimento '{corso_id}' non trovato")

    checks = []
    raccomandazioni = []
    has_blocking = False
    has_warning = False

    # 1. Verifica Stato di Servizio
    stato_serv = (p.get("stato_servizio") or "In Servizio").strip()
    if stato_serv.lower() == "in servizio":
        checks.append({
            "categoria": "Stato di Servizio",
            "regola": "Servizio attivo",
            "riscontro": f"Militare regolarmente in servizio ({p.get('grado_qualifica')} presso {p.get('reparto_ufficio')})",
            "esito": "SODDISFATTO",
            "tipo": "success"
        })
    else:
        has_blocking = True
        checks.append({
            "categoria": "Stato di Servizio",
            "regola": "Servizio attivo",
            "riscontro": f"Militare non in servizio attivo (Attuale: {stato_serv})",
            "esito": "BLOCCANTE",
            "tipo": "danger"
        })
        raccomandazioni.append("La candidatura non può procedere fino al rientro in servizio attivo.")

    # 2. Verifica se il corso è già stato conseguito dal militare
    corsi_effettuati = p.get("corsi", [])
    stesso_corso = None
    for pc in corsi_effettuati:
        if pc.get("corso_id") == c["id"] or (pc.get("denominazione") and pc.get("denominazione").strip().lower() == c["denominazione"].strip().lower()):
            if pc.get("esito") in ("Superato", "Idoneo", "Qualificato", "Specializzato"):
                stesso_corso = pc
                break

    if stesso_corso:
        validita = c.get("validita_mesi")
        data_fine = stesso_corso.get("data_fine")
        if validita and data_fine:
            checks.append({
                "categoria": "Frequenza Precedente",
                "regola": f"Validità corso ({validita} mesi)",
                "riscontro": f"Corso già conseguito il {data_fine} (Esito: {stesso_corso.get('esito')}). Candidatura utile come rinnovo/aggiornamento periodico.",
                "esito": "CONSEGUITO_RINNOVO",
                "tipo": "info"
            })
            raccomandazioni.append("Il militare ha già superato questo corso. La partecipazione è intesa come aggiornamento / rinnovo validità.")
        else:
            checks.append({
                "categoria": "Frequenza Precedente",
                "regola": "Abilitazione già in possesso",
                "riscontro": f"Corso già superato il {data_fine or '-'} con attestato {stesso_corso.get('numero_attestato') or 'N/D'}.",
                "esito": "GIA_CONSEGUITO",
                "tipo": "warning"
            })
            has_warning = True
            raccomandazioni.append("Il corso risulta già conseguito a titolo permanente nel fascicolo personale.")

    # 3. Analisi dei Prerequisiti del corso
    prereq_raw = (c.get("prerequisiti") or "").strip()
    patenti_militare = p.get("patenti", [])
    note_militare = p.get("note_caratteristiche", [])

    if not prereq_raw or prereq_raw.lower() in ("nessun prerequisito specifico indicato", "nessuno", "nessun prerequisito", "-"):
        checks.append({
            "categoria": "Prerequisiti di Accesso",
            "regola": "Nessun prerequisito vincolante",
            "riscontro": "Il corso è ad accesso diretto senza propedeuticità o abilitazioni obbligatorie.",
            "esito": "SODDISFATTO",
            "tipo": "success"
        })
    else:
        import re
        parts = re.split(r'[;,\n]+', prereq_raw)
        for part in parts:
            req = part.strip()
            req = re.sub(r'^[-\*\•\d\.\)\s]+', '', req).strip()
            if not req or len(req) < 3:
                continue

            req_lower = req.lower()

            # A) Requisito di Patente di Guida
            if any(k in req_lower for k in ("patente", "mod.", "modello", "cqc")):
                patente_trovata = None
                for pat in patenti_militare:
                    cat = (pat.get("categoria") or "").lower()
                    if ("mod. 3" in req_lower or "mod 3" in req_lower) and ("mod. 3" in cat or "mod 3" in cat):
                        patente_trovata = pat
                        break
                    elif ("mod. 2" in req_lower or "mod 2" in req_lower) and ("mod. 2" in cat or "mod 2" in cat):
                        patente_trovata = pat
                        break
                    elif ("mod. 4" in req_lower or "mod 4" in req_lower) and ("mod. 4" in cat or "mod 4" in cat):
                        patente_trovata = pat
                        break
                    elif "patente b" in req_lower and "b" in cat:
                        patente_trovata = pat
                        break
                    elif "patente c" in req_lower and "c" in cat:
                        patente_trovata = pat
                        break
                    elif cat in req_lower:
                        patente_trovata = pat
                        break

                if patente_trovata:
                    stato_scad = patente_trovata.get("stato_scadenza", "REGOLARE")
                    scad_str = patente_trovata.get("data_scadenza", "")
                    if stato_scad == "SCADUTA":
                        has_blocking = True
                        checks.append({
                            "categoria": "Patente di Guida",
                            "regola": req,
                            "riscontro": f"Patente {patente_trovata.get('categoria')} registrata ma SCADUTA il {scad_str}",
                            "esito": "BLOCCANTE",
                            "tipo": "danger"
                        })
                        raccomandazioni.append(f"È necessario procedere al rinnovo della {patente_trovata.get('categoria')} prima della candidatura.")
                    elif stato_scad in ("URGENTE_30GG", "IN_SCADENZA_60GG"):
                        has_warning = True
                        checks.append({
                            "categoria": "Patente di Guida",
                            "regola": req,
                            "riscontro": f"Patente {patente_trovata.get('categoria')} presente ma IN SCADENZA a breve ({scad_str})",
                            "esito": "IN_SCADENZA",
                            "tipo": "warning"
                        })
                        raccomandazioni.append("La patente richiesta scadrà a breve. Verificare il rinnovo in concomitanza del corso.")
                    else:
                        checks.append({
                            "categoria": "Patente di Guida",
                            "regola": req,
                            "riscontro": f"Patente {patente_trovata.get('categoria')} attiva e valida (Scadenza: {scad_str})",
                            "esito": "SODDISFATTO",
                            "tipo": "success"
                        })
                else:
                    has_blocking = True
                    checks.append({
                        "categoria": "Patente di Guida",
                        "regola": req,
                        "riscontro": "Nessuna patente corrispondente rilevata nel fascicolo del militare",
                        "esito": "BLOCCANTE",
                        "tipo": "danger"
                    })
                    raccomandazioni.append(f"Il militare deve prima conseguire la patente richiesta: '{req}'.")

            # B) Requisito di Corso Propedeutico o Qualifica
            elif any(k in req_lower for k in ("corso", "qualifica", "abilitazione", "analista base", "osint base", "cartografica", "base reti")):
                corso_trovato = None
                for c_eff in corsi_effettuati:
                    den_c = (c_eff.get("denominazione") or "").lower()
                    if (den_c in req_lower or any(word in den_c for word in req_lower.split() if len(word) > 4)) and c_eff.get("esito") in ("Superato", "Idoneo", "Qualificato", "Specializzato"):
                        corso_trovato = c_eff
                        break

                if corso_trovato:
                    checks.append({
                        "categoria": "Propedeuticità Formativa",
                        "regola": req,
                        "riscontro": f"Corso propedeutico superato: '{corso_trovato.get('denominazione')}' (Attestato: {corso_trovato.get('numero_attestato') or 'Registrato'})",
                        "esito": "SODDISFATTO",
                        "tipo": "success"
                    })
                else:
                    has_blocking = True
                    checks.append({
                        "categoria": "Propedeuticità Formativa",
                        "regola": req,
                        "riscontro": "Requisito formativo non riscontrato nello storico dei corsi superati",
                        "esito": "BLOCCANTE",
                        "tipo": "danger"
                    })
                    raccomandazioni.append(f"Verificare o iscrivere il militare al corso propedeutico '{req}'.")

            # C) Altri requisiti specifici (Sicurezza, Lingua, Idoneità Sanitaria, Armi, ecc.)
            else:
                has_warning = True
                checks.append({
                    "categoria": "Requisito da Accertare",
                    "regola": req,
                    "riscontro": "Accertamento d'ufficio richiesto (verificare attestazione del Comando o idoneità specifica)",
                    "esito": "DA_VERIFICARE",
                    "tipo": "warning"
                })
                raccomandazioni.append(f"Accertare il requisito '{req}' a vista tramite documentazione matricolare o idoneità medica/di sicurezza.")

    # 4. Verifica Note Caratteristiche (regolarità generale del fascicolo)
    if note_militare:
        ultima_nota = note_militare[0]
        stato_nota = ultima_nota.get("stato_scadenza", "REGOLARE")
        if stato_nota == "SCADUTA":
            has_warning = True
            checks.append({
                "categoria": "Documenti di Valutazione",
                "regola": "Documento caratteristico in corso di validità (≤ 365 gg)",
                "riscontro": f"Ultima nota caratteristica del {ultima_nota.get('periodo_al')} risultante SCADUTA",
                "esito": "AVVISO",
                "tipo": "warning"
            })
            raccomandazioni.append("Si raccomanda l'aggiornamento della scheda valutativa prima della missione/corso.")
        else:
            checks.append({
                "categoria": "Documenti di Valutazione",
                "regola": "Regolarità note caratteristiche",
                "riscontro": f"Nota valida fino al {ultima_nota.get('data_prossima_scadenza')} (Giudizio: {ultima_nota.get('giudizio_finale') or 'Favorevole'})",
                "esito": "SODDISFATTO",
                "tipo": "success"
            })
    else:
        checks.append({
            "categoria": "Documenti di Valutazione",
            "regola": "Note caratteristiche",
            "riscontro": "Nessuna nota caratteristica registrata nel fascicolo (personale neo-assegnato o in attesa di prima valutazione)",
            "esito": "INFO",
            "tipo": "info"
        })

    # Calcolo Esito Globale
    if has_blocking:
        esito_globale = "NON_IDONEO"
        badge_label = "Non Candidabile"
        badge_class = "danger"
    elif has_warning:
        esito_globale = "IDONEO_CON_RISERVA"
        badge_label = "Candidabile con Riserva"
        badge_class = "warning"
    else:
        esito_globale = "IDONEO"
        badge_label = "Pienamente Candidabile"
        badge_class = "success"

    # Percentuale di conformità (esclude note puramente informative)
    totali_valutabili = [chk for chk in checks if chk["esito"] != "INFO"]
    soddisfatti = sum(1 for chk in totali_valutabili if chk["esito"] in ("SODDISFATTO", "CONSEGUITO_RINNOVO"))
    percentuale = int((soddisfatti / len(totali_valutabili)) * 100) if totali_valutabili else 100

    return {
        "personale": {
            "id": p["id"],
            "nominativo": f"{p['cognome']} {p['nome']}",
            "grado_qualifica": p.get("grado_qualifica"),
            "matricola": p.get("matricola"),
            "reparto_ufficio": p.get("reparto_ufficio"),
            "incarico": p.get("incarico"),
            "posto_tabellare": p.get("posto_tabellare"),
            "stato_servizio": p.get("stato_servizio")
        },
        "corso": {
            "id": c["id"],
            "denominazione": c["denominazione"],
            "codice_corso": c.get("codice_corso"),
            "ente_erogatore": c.get("ente_erogatore"),
            "durata_ore": c.get("durata_ore"),
            "validita_mesi": c.get("validita_mesi"),
            "prerequisiti": c.get("prerequisiti")
        },
        "esito_globale": esito_globale,
        "badge_label": badge_label,
        "badge_class": badge_class,
        "percentuale_conformita": percentuale,
        "checks": checks,
        "raccomandazioni": raccomandazioni
    }


def create_corso(data):
    """Crea un nuovo corso nel catalogo generale."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO corso (
                codice_corso, denominazione, ente_erogatore, durata_ore, validita_mesi, prerequisiti, fonte_catalogo, descrizione
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("codice_corso"),
            data.get("denominazione"),
            data.get("ente_erogatore"),
            data.get("durata_ore"),
            data.get("validita_mesi") if data.get("validita_mesi") else None,
            data.get("prerequisiti", ""),
            data.get("fonte_catalogo", "Manuale"),
            data.get("descrizione", "")
        ))
        conn.commit()
        return cursor.lastrowid


def update_corso(corso_id, data):
    with get_db_connection() as conn:
        cur = conn.execute("SELECT fonte_catalogo FROM corso WHERE id = ?", (corso_id,)).fetchone()
        fonte = data.get("fonte_catalogo") or (cur["fonte_catalogo"] if cur else "Manuale")
        conn.execute("""
            UPDATE corso SET
                codice_corso = ?,
                denominazione = ?,
                ente_erogatore = ?,
                durata_ore = ?,
                validita_mesi = ?,
                prerequisiti = ?,
                fonte_catalogo = ?,
                descrizione = ?
            WHERE id = ?
        """, (
            data.get("codice_corso"),
            data.get("denominazione"),
            data.get("ente_erogatore"),
            data.get("durata_ore"),
            data.get("validita_mesi") if data.get("validita_mesi") else None,
            data.get("prerequisiti", ""),
            fonte,
            data.get("descrizione", ""),
            corso_id
        ))
        conn.commit()
        return True


def import_corsi_batch(courses_list, fonte_catalogo="Catalogo PDF"):
    """Importa o aggiorna una lista di corsi estratti da PDF o file esterno."""
    imported_count = 0
    updated_count = 0

    with get_db_connection() as conn:
        for c in courses_list:
            codice = (c.get("codice_corso") or "").strip()
            denominazione = (c.get("denominazione") or "").strip()
            if not denominazione:
                continue

            if not codice:
                # Genera codice univoco basato sul titolo
                words = [w[:3].upper() for w in denominazione.split() if len(w) >= 3][:3]
                prefix = "-".join(words) if words else "COR"
                codice = f"PDF-{prefix}-{imported_count + updated_count + 1:03d}"

            # Verifica se il corso esiste già (per codice o per denominazione esatta)
            existing = conn.execute(
                "SELECT id FROM corso WHERE codice_corso = ? OR LOWER(denominazione) = LOWER(?)",
                (codice, denominazione)
            ).fetchone()

            if existing:
                conn.execute("""
                    UPDATE corso SET
                        codice_corso = ?,
                        denominazione = ?,
                        ente_erogatore = COALESCE(?, ente_erogatore),
                        durata_ore = COALESCE(?, durata_ore),
                        validita_mesi = COALESCE(?, validita_mesi),
                        prerequisiti = COALESCE(?, prerequisiti),
                        fonte_catalogo = ?,
                        descrizione = COALESCE(?, descrizione)
                    WHERE id = ?
                """, (
                    codice,
                    denominazione,
                    c.get("ente_erogatore"),
                    c.get("durata_ore"),
                    c.get("validita_mesi"),
                    c.get("prerequisiti"),
                    fonte_catalogo,
                    c.get("descrizione"),
                    existing["id"]
                ))
                updated_count += 1
            else:
                conn.execute("""
                    INSERT INTO corso (
                        codice_corso, denominazione, ente_erogatore, durata_ore, validita_mesi, prerequisiti, fonte_catalogo, descrizione
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    codice,
                    denominazione,
                    c.get("ente_erogatore") or "Ente Istituzionale",
                    c.get("durata_ore"),
                    c.get("validita_mesi"),
                    c.get("prerequisiti") or "Nessun prerequisito specifico indicato",
                    fonte_catalogo,
                    c.get("descrizione") or ""
                ))
                imported_count += 1

        conn.commit()
    return {"imported": imported_count, "updated": updated_count, "total": imported_count + updated_count}


def delete_corso(corso_id):
    """Elimina un corso dal catalogo e rimuove eventuali partecipazioni collegate."""
    with get_db_connection() as conn:
        conn.execute("DELETE FROM partecipazione_corso WHERE corso_id = ?", (corso_id,))
        conn.execute("DELETE FROM corso WHERE id = ?", (corso_id,))
        conn.commit()
        return True


def add_partecipazione_corso(personale_id, data):
    """Registra la frequenza di un corso da parte di un dipendente (da catalogo o con inserimento manuale)."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        corso_id = data.get("corso_id")

        # Se inserimento manuale o corso_id non fornito
        if not corso_id and data.get("denominazione"):
            denom = data.get("denominazione").strip()
            # Controlla se già presente a catalogo
            c_exist = conn.execute("SELECT id FROM corso WHERE LOWER(denominazione) = LOWER(?)", (denom,)).fetchone()
            if c_exist:
                corso_id = c_exist["id"]
            else:
                # Crea nuovo corso al volo a catalogo
                codice = data.get("codice_corso") or f"COR-MAN-{int(datetime.now().timestamp())}"
                cursor.execute("""
                    INSERT INTO corso (codice_corso, denominazione, ente_erogatore, durata_ore, validita_mesi, prerequisiti, fonte_catalogo, descrizione)
                    VALUES (?, ?, ?, ?, ?, ?, 'Inserimento Manuale', ?)
                """, (
                    codice,
                    denom,
                    data.get("ente_erogatore", "Ente Non Specificato"),
                    data.get("durata_ore"),
                    data.get("validita_mesi"),
                    data.get("prerequisiti", ""),
                    data.get("descrizione", "Inserito manualmente dal fascicolo operatore")
                ))
                corso_id = cursor.lastrowid

        if not corso_id:
            raise ValueError("ID corso o denominazione obbligatoria")

        # Calcolo eventuale scadenza se il corso ha validita_mesi
        scadenza = data.get("data_scadenza_abilitazione")
        if not scadenza and data.get("data_fine"):
            c = conn.execute("SELECT validita_mesi FROM corso WHERE id = ?", (corso_id,)).fetchone()
            if c and c["validita_mesi"]:
                dt_fine = datetime.strptime(data.get("data_fine"), "%Y-%m-%d")
                scadenza = (dt_fine + timedelta(days=c["validita_mesi"] * 30)).strftime("%Y-%m-%d")

        cursor.execute("""
            INSERT INTO partecipazione_corso (
                personale_id, corso_id, data_inizio, data_fine,
                esito, numero_attestato, data_scadenza_abilitazione, note
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            personale_id,
            corso_id,
            data.get("data_inizio"),
            data.get("data_fine"),
            data.get("esito", "Superato"),
            data.get("numero_attestato"),
            scadenza,
            data.get("note")
        ))
        conn.commit()
        return cursor.lastrowid


def delete_partecipazione_corso(partecipazione_id):
    with get_db_connection() as conn:
        conn.execute("DELETE FROM partecipazione_corso WHERE id = ?", (partecipazione_id,))
        conn.commit()
        return True


# ====================================================================
# PASSAPORTO DI SERVIZIO
# ====================================================================

def add_passaporto(personale_id, data):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO passaporto_servizio (
                personale_id, numero_passaporto, tipo_passaporto,
                autorita_rilascio, data_rilascio, data_scadenza, stato, ubicazione_custodia, note
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            personale_id,
            data.get("numero_passaporto"),
            data.get("tipo_passaporto", "Servizio"),
            data.get("autorita_rilascio", "Ministero Affari Esteri e Cooperazione Internazionale"),
            data.get("data_rilascio"),
            data.get("data_scadenza"),
            data.get("stato", "Valido"),
            data.get("ubicazione_custodia", "Archivio Ufficio Personale"),
            data.get("note")
        ))
        conn.commit()
        return cursor.lastrowid


def update_passaporto(passaporto_id, data):
    with get_db_connection() as conn:
        conn.execute("""
            UPDATE passaporto_servizio SET
                numero_passaporto = ?,
                tipo_passaporto = ?,
                autorita_rilascio = ?,
                data_rilascio = ?,
                data_scadenza = ?,
                stato = ?,
                ubicazione_custodia = ?,
                note = ?
            WHERE id = ?
        """, (
            data.get("numero_passaporto"),
            data.get("tipo_passaporto"),
            data.get("autorita_rilascio"),
            data.get("data_rilascio"),
            data.get("data_scadenza"),
            data.get("stato"),
            data.get("ubicazione_custodia"),
            data.get("note"),
            passaporto_id
        ))
        conn.commit()
        return True


def delete_passaporto(passaporto_id):
    with get_db_connection() as conn:
        conn.execute("DELETE FROM passaporto_servizio WHERE id = ?", (passaporto_id,))
        conn.commit()
        return True
