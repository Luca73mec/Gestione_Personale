"""
Modulo di gestione del Database SQLite per l'applicazione Gestione Personale.
Fornisce connessioni sicure, migrazioni/inizializzazione automatica e metodi helper per CRUD e scadenze.
"""

import sqlite3
import os
from pathlib import Path
from datetime import datetime, timedelta
from contextlib import contextmanager

try:
    from .cifige_data import CIFIGE_COURSES
except (ImportError, ValueError):
    from database.cifige_data import CIFIGE_COURSES

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

            # Verifica colonne in personale
            cursor = conn.execute("PRAGMA table_info(personale);")
            columns = [row[1] for row in cursor.fetchall()]
            if "posto_tabellare" not in columns:
                conn.execute("ALTER TABLE personale ADD COLUMN posto_tabellare TEXT;")
            if "livello_nos" not in columns:
                conn.execute("ALTER TABLE personale ADD COLUMN livello_nos TEXT DEFAULT 'Riservato';")
            if "lingua_inglese" not in columns:
                conn.execute("ALTER TABLE personale ADD COLUMN lingua_inglese TEXT DEFAULT 'NATO JFLT 8';")

            # Verifica colonne in corso
            cursor = conn.execute("PRAGMA table_info(corso);")
            corso_cols = [row[1] for row in cursor.fetchall()]
            if "prerequisiti" not in corso_cols:
                conn.execute("ALTER TABLE corso ADD COLUMN prerequisiti TEXT;")
            if "fonte_catalogo" not in corso_cols:
                conn.execute("ALTER TABLE corso ADD COLUMN fonte_catalogo TEXT DEFAULT 'Manuale';")
            if "durata_settimane" not in corso_cols:
                conn.execute("ALTER TABLE corso ADD COLUMN durata_settimane INTEGER;")
            if "requisiti_sicurezza" not in corso_cols:
                conn.execute("ALTER TABLE corso ADD COLUMN requisiti_sicurezza TEXT;")
            if "precedenti_formativi" not in corso_cols:
                conn.execute("ALTER TABLE corso ADD COLUMN precedenti_formativi TEXT;")
            if "precedenti_operativi" not in corso_cols:
                conn.execute("ALTER TABLE corso ADD COLUMN precedenti_operativi TEXT;")
            if "selezioni" not in corso_cols:
                conn.execute("ALTER TABLE corso ADD COLUMN selezioni TEXT;")
            if "conoscenza_lingua" not in corso_cols:
                conn.execute("ALTER TABLE corso ADD COLUMN conoscenza_lingua TEXT;")
            if "altri_requisiti" not in corso_cols:
                conn.execute("ALTER TABLE corso ADD COLUMN altri_requisiti TEXT;")
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
                telefono, indirizzo_residenza, livello_nos, lingua_inglese, note_generali
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            data.get("livello_nos", "Riservato"),
            data.get("lingua_inglese", "NATO JFLT 8"),
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
                livello_nos = COALESCE(?, livello_nos),
                lingua_inglese = COALESCE(?, lingua_inglese),
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
            data.get("livello_nos"),
            data.get("lingua_inglese"),
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
    Analizza in modo strutturato:
    - 1. Stato di Servizio attivo
    - 2. Eventuale frequenza precedente (corso già conseguito / validità rinnovo)
    - 3. Requisiti di Sicurezza (confronto livello NOS militare vs NOS richiesto dal corso)
    - 4. Precedenti Formativi (corsi propedeutici obbligatori o auspicabili)
    - 5. Conoscenza Lingua (NATO JFLT / SLP)
    - 6. Patenti di Guida (Civili o Militari es. Mod. 2 / Mod. 3 e scadenze)
    - 7. Precedenti Operativi (anzianità di impiego specialistico)
    - 8. Selezioni e Idoneità Speciali (prove attitudinali, visite sanitarie SMI / al volo)
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
                "riscontro": f"Corso già superato il {data_fine or '-'} con attestato {stesso_corso.get('numero_attestato') or 'Registrato'}.",
                "esito": "GIA_CONSEGUITO",
                "tipo": "warning"
            })
            has_warning = True
            raccomandazioni.append("Il corso risulta già conseguito a titolo permanente nel fascicolo personale.")

    # 3. REQUISITI DI SICUREZZA (NOS)
    import re
    nos_req = (c.get("requisiti_sicurezza") or "").strip()
    if not nos_req and (c.get("prerequisiti") or ""):
        nos_m = re.search(r"\b(?:NOS\b[^\n,;\.]*|Nulla\s+Osta[^\n,;\.]*|Segretissimo|Segreto|Riservato)", c.get("prerequisiti"), re.IGNORECASE)
        if nos_m:
            nos_req = nos_m.group(0).strip()

    nos_posseduto = (p.get("livello_nos") or "Riservato").strip()

    def nos_rank(text):
        t = (text or "").lower()
        if any(k in t for k in ("cosmic", "segretissimo", "top secret")):
            return 3
        elif any(k in t for k in ("segreto", "nato secret")):
            return 2
        elif any(k in t for k in ("riservato", "confidential")):
            return 1
        elif any(k in t for k in ("adeguato", "in base")):
            return 1
        return 0

    rank_req = nos_rank(nos_req)
    rank_poss = nos_rank(nos_posseduto)

    if not nos_req or "nessun" in nos_req.lower():
        checks.append({
            "categoria": "Sicurezza (NOS)",
            "regola": "Nessun NOS vincolante",
            "riscontro": f"Abilitazione ordinaria (NOS militare: {nos_posseduto})",
            "esito": "SODDISFATTO",
            "tipo": "success"
        })
    elif "adeguato" in nos_req.lower():
        checks.append({
            "categoria": "Sicurezza (NOS)",
            "regola": nos_req,
            "riscontro": f"NOS posseduto: {nos_posseduto}. Verificare congruità formale con l'incarico/designazione.",
            "esito": "DA_VERIFICARE",
            "tipo": "warning"
        })
    elif rank_poss >= rank_req:
        checks.append({
            "categoria": "Sicurezza (NOS)",
            "regola": f"Prescritto {nos_req}",
            "riscontro": f"Abilitazione posseduta: '{nos_posseduto}' (Soddisfa il livello richiesto '{nos_req}')",
            "esito": "SODDISFATTO",
            "tipo": "success"
        })
    else:
        has_blocking = True
        checks.append({
            "categoria": "Sicurezza (NOS)",
            "regola": f"Prescritto {nos_req}",
            "riscontro": f"Abilitazione posseduta: '{nos_posseduto}' INSUFFICIENTE per il livello prescritto ({nos_req})",
            "esito": "BLOCCANTE",
            "tipo": "danger"
        })
        raccomandazioni.append(f"È necessario avviare l'istruttoria di concessione del NOS '{nos_req}' prima dell'invio al corso.")

    # 4. PRECEDENTI FORMATIVI (PROPEDEUTICITÀ)
    form_req = (c.get("precedenti_formativi") or "").strip()
    if not form_req and (c.get("prerequisiti") or ""):
        prop_m = re.search(r"(?:Propedeuticit[àa]|Propedeutico|Corsi\s+propedeutici|Precedenti\s+formativi)\s*[:\-]?\s*([^\n;\.]{4,100})", c.get("prerequisiti"), re.IGNORECASE)
        if prop_m:
            form_req = prop_m.group(1).strip()
        else:
            corsi_trovati = re.findall(r"(?:Corso\s+[A-Z0-9\s/°\-_]{3,40}(?:\([^\)]+\))?)", c.get("prerequisiti"), re.IGNORECASE)
            if corsi_trovati:
                form_req = ", ".join(dict.fromkeys(corsi_trovati))

    if not form_req or form_req.lower().startswith("nessun"):
        checks.append({
            "categoria": "Precedenti Formativi",
            "regola": "Accesso diretto",
            "riscontro": "Nessun corso propedeutico obbligatorio prescritto a catalogo.",
            "esito": "SODDISFATTO",
            "tipo": "success"
        })
    else:
        parti_corsi = re.split(r'[,;\n]+|(?:\s+e\s+Corso\b)', form_req, flags=re.IGNORECASE)
        for part in parti_corsi:
            p_clean = part.strip()
            if not p_clean or len(p_clean) < 4:
                continue
            p_clean = re.sub(r'^(?:propedeutico\s*[:\-])\s*', '', p_clean, flags=re.IGNORECASE).strip()
            is_auspicabile = "auspicabil" in p_clean.lower() or "consigliat" in p_clean.lower()
            clean_titolo = re.sub(r'\s*\((?:obbligatorio|auspicabile|consigliato)[^\)]*\)', '', p_clean, flags=re.IGNORECASE).strip()

            trovato = None
            for ce in corsi_effettuati:
                den_ce = (ce.get("denominazione") or "").lower()
                clean_norm = clean_titolo.lower()
                words = [w.lower() for w in clean_norm.split() if len(w) > 3 and w.lower() not in ("corso", "delle", "degli", "della", "dell", "per")]
                if clean_norm in den_ce or (words and sum(1 for w in words if w in den_ce) >= min(2, len(words))):
                    if ce.get("esito") in ("Superato", "Idoneo", "Qualificato", "Specializzato"):
                        trovato = ce
                        break

            if trovato:
                checks.append({
                    "categoria": "Precedenti Formativi",
                    "regola": p_clean,
                    "riscontro": f"Propedeuticità soddisfatta: '{trovato.get('denominazione')}' superato il {trovato.get('data_fine')} (Attestato: {trovato.get('numero_attestato') or 'Registrato'})",
                    "esito": "SODDISFATTO",
                    "tipo": "success"
                })
            else:
                if is_auspicabile:
                    has_warning = True
                    checks.append({
                        "categoria": "Precedenti Formativi",
                        "regola": p_clean,
                        "riscontro": f"Corso auspicabile '{clean_titolo}' non riscontrato nel fascicolo (requisito non vincolante)",
                        "esito": "DA_VERIFICARE",
                        "tipo": "warning"
                    })
                    raccomandazioni.append(f"La frequenza del corso '{clean_titolo}' è auspicabile sebbene non formalmente bloccante.")
                else:
                    has_blocking = True
                    checks.append({
                        "categoria": "Precedenti Formativi",
                        "regola": p_clean,
                        "riscontro": f"Corso propedeutico obbligatorio '{clean_titolo}' NON presente nello storico corsi del militare",
                        "esito": "BLOCCANTE",
                        "tipo": "danger"
                    })
                    raccomandazioni.append(f"Il militare deve prima conseguire il corso propedeutico obbligatorio: '{clean_titolo}'.")

    # 5. CONOSCENZA LINGUA
    lingua_req = (c.get("conoscenza_lingua") or "").strip()
    if not lingua_req and (c.get("prerequisiti") or ""):
        lingua_m = re.search(r"(?:NATO\s+(?:JFLT|SLP)[^\n,;\.]*|Lingua\s+inglese[^\n,;\.]*|Inglese\s+livello[^\n,;\.]*|Conoscenza\s+Lingua[^\n,;\.]*)", c.get("prerequisiti"), re.IGNORECASE)
        if lingua_m:
            lingua_req = lingua_m.group(0).strip()

    lingua_posseduta = (p.get("lingua_inglese") or "NATO JFLT 8").strip()

    if not lingua_req or lingua_req.lower() in ("standard", "nessuna", "nessun requisito", "-"):
        checks.append({
            "categoria": "Conoscenza Lingua",
            "regola": "Standard istituzionale",
            "riscontro": f"Profilo linguistico ordinario (Registrato: {lingua_posseduta})",
            "esito": "SODDISFATTO",
            "tipo": "success"
        })
    else:
        needs_8 = "8" in lingua_req or "jflt 8" in lingua_req.lower() or "slp 8" in lingua_req.lower()
        has_8 = "8" in lingua_posseduta or "jflt 8" in lingua_posseduta.lower() or "slp 8" in lingua_posseduta.lower() or any(k in lingua_posseduta.lower() for k in ("b2", "c1", "c2"))
        if needs_8:
            if has_8:
                checks.append({
                    "categoria": "Conoscenza Lingua",
                    "regola": lingua_req,
                    "riscontro": f"Livello registrato: '{lingua_posseduta}' (Conforme allo standard richiesto)",
                    "esito": "SODDISFATTO",
                    "tipo": "success"
                })
            else:
                has_blocking = True
                checks.append({
                    "categoria": "Conoscenza Lingua",
                    "regola": lingua_req,
                    "riscontro": f"Livello registrato: '{lingua_posseduta}' INSUFFICIENTE per il livello prescritto ({lingua_req})",
                    "esito": "BLOCCANTE",
                    "tipo": "danger"
                })
                raccomandazioni.append(f"È necessario accertare o conseguire l'attestazione linguistica prescritta: {lingua_req}.")
        else:
            checks.append({
                "categoria": "Conoscenza Lingua",
                "regola": lingua_req,
                "riscontro": f"Profilo linguistico registrato: {lingua_posseduta}",
                "esito": "SODDISFATTO",
                "tipo": "success"
            })

    # 6. PATENTI DI GUIDA (Civili o Militari)
    altri_req = (c.get("altri_requisiti") or "").strip()
    prereq_str = (c.get("prerequisiti") or "").strip()
    req_combined = f"{altri_req} {prereq_str}".lower()
    patenti_militare = p.get("patenti", [])

    if any(k in req_combined for k in ("patente", "mod. 2", "mod. 3", "mod. 4", "mod 2", "mod 3", "cqc")):
        patente_trovata = None
        req_pat_label = "Patente di Guida"
        if "mod. 2" in req_combined or "mod 2" in req_combined:
            req_pat_label = "Patente Militare Mod. 2"
            for pat in patenti_militare:
                cat = (pat.get("categoria") or "").lower()
                if "mod. 2" in cat or "mod 2" in cat:
                    patente_trovata = pat
                    break
        elif "mod. 3" in req_combined or "mod 3" in req_combined:
            req_pat_label = "Patente Militare Mod. 3"
            for pat in patenti_militare:
                cat = (pat.get("categoria") or "").lower()
                if "mod. 3" in cat or "mod 3" in cat:
                    patente_trovata = pat
                    break
        elif "mod. 4" in req_combined or "mod 4" in req_combined:
            req_pat_label = "Patente Militare Mod. 4"
            for pat in patenti_militare:
                cat = (pat.get("categoria") or "").lower()
                if "mod. 4" in cat or "mod 4" in cat:
                    patente_trovata = pat
                    break
        elif "patente b" in req_combined:
            req_pat_label = "Patente cat. B"
            for pat in patenti_militare:
                if "b" in (pat.get("categoria") or "").lower():
                    patente_trovata = pat
                    break

        if patente_trovata:
            stato_scad = patente_trovata.get("stato_scadenza", "REGOLARE")
            scad_str = patente_trovata.get("data_scadenza", "")
            if stato_scad == "SCADUTA":
                has_blocking = True
                checks.append({
                    "categoria": "Patente di Guida",
                    "regola": req_pat_label,
                    "riscontro": f"Patente {patente_trovata.get('categoria')} registrata ma SCADUTA il {scad_str}",
                    "esito": "BLOCCANTE",
                    "tipo": "danger"
                })
                raccomandazioni.append(f"È necessario rinnovare la {patente_trovata.get('categoria')} prima dell'invio al corso.")
            elif stato_scad in ("URGENTE_30GG", "IN_SCADENZA_60GG"):
                has_warning = True
                checks.append({
                    "categoria": "Patente di Guida",
                    "regola": req_pat_label,
                    "riscontro": f"Patente {patente_trovata.get('categoria')} attiva ma in scadenza a breve ({scad_str})",
                    "esito": "IN_SCADENZA",
                    "tipo": "warning"
                })
                raccomandazioni.append("La patente richiesta è in scadenza a breve. Disporre per tempo il rinnovo.")
            else:
                checks.append({
                    "categoria": "Patente di Guida",
                    "regola": req_pat_label,
                    "riscontro": f"Patente {patente_trovata.get('categoria')} valida e attiva fino al {scad_str}",
                    "esito": "SODDISFATTO",
                    "tipo": "success"
                })
        else:
            has_blocking = True
            checks.append({
                "categoria": "Patente di Guida",
                "regola": req_pat_label,
                "riscontro": f"Abilitazione alla guida '{req_pat_label}' NON presente nel fascicolo matricolare",
                "esito": "BLOCCANTE",
                "tipo": "danger"
            })
            raccomandazioni.append(f"Il corso prescrive obbligatoriamente il possesso di: {req_pat_label}.")

    # 7. PRECEDENTI OPERATIVI (ESPERIENZA / IMPIEGO)
    op_req = (c.get("precedenti_operativi") or "").strip()
    if not op_req and (c.get("prerequisiti") or ""):
        op_m = re.search(r"((?:\d+\s*mesi|\d+\s*anni)[^\n,;\.]*(?:impiego|esperienza|servizio)[^\n,;\.]*)", c.get("prerequisiti"), re.IGNORECASE)
        if op_m:
            op_req = op_m.group(0).strip()

    if op_req and not op_req.lower().startswith("nessun"):
        has_warning = True
        checks.append({
            "categoria": "Precedenti Operativi",
            "regola": op_req,
            "riscontro": f"Requisito di impiego operativo da attestare d'ufficio: '{op_req}'. Verificare fascicolo matricolare.",
            "esito": "DA_VERIFICARE",
            "tipo": "warning"
        })
        raccomandazioni.append(f"Accertare il requisito operativo con attestazione del Comando: '{op_req}'.")

    # 8. SELEZIONI & IDONEITÀ SPECIALI
    sel_req = (c.get("selezioni") or "").strip()
    if not sel_req and (c.get("prerequisiti") or ""):
        sel_m = re.search(r"(?:Idoneit[àa][^\n,;\.]*|Prove\s+selettive[^\n,;\.]*|Selezioni[^\n,;\.]*|Test\s+d[’\']ingresso[^\n,;\.]*|Protocollo[^\n,;\.]*)", c.get("prerequisiti"), re.IGNORECASE)
        if sel_m:
            sel_req = sel_m.group(0).strip()

    if sel_req and not any(k in sel_req.lower() for k in ("nessun", "-")):
        has_warning = True
        checks.append({
            "categoria": "Selezioni & Idoneità",
            "regola": sel_req,
            "riscontro": f"Prove selettive / accertamenti sanitari previsti: '{sel_req}'. Richiesto verbale idoneità d'ufficio.",
            "esito": "DA_VERIFICARE",
            "tipo": "warning"
        })
        raccomandazioni.append(f"Verificare superamento prove selettive o attestazione sanitaria prescritta ({sel_req}).")
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
            "stato_servizio": p.get("stato_servizio"),
            "livello_nos": p.get("livello_nos"),
            "lingua_inglese": p.get("lingua_inglese")
        },
        "corso": {
            "id": c["id"],
            "denominazione": c["denominazione"],
            "codice_corso": c.get("codice_corso"),
            "ente_erogatore": c.get("ente_erogatore"),
            "durata_settimane": c.get("durata_settimane"),
            "durata_ore": c.get("durata_ore"),
            "validita_mesi": c.get("validita_mesi"),
            "requisiti_sicurezza": c.get("requisiti_sicurezza"),
            "precedenti_formativi": c.get("precedenti_formativi"),
            "precedenti_operativi": c.get("precedenti_operativi"),
            "selezioni": c.get("selezioni"),
            "conoscenza_lingua": c.get("conoscenza_lingua"),
            "altri_requisiti": c.get("altri_requisiti"),
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
    """Crea un nuovo corso nel catalogo generale con tutte le voci strutturate."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        sett = data.get("durata_settimane")
        ore = data.get("durata_ore")
        if not sett and ore:
            sett = ore // 36 if ore >= 36 else 1
        elif sett and not ore:
            ore = sett * 36

        cursor.execute("""
            INSERT INTO corso (
                codice_corso, denominazione, ente_erogatore,
                durata_settimane, durata_ore, validita_mesi,
                requisiti_sicurezza, precedenti_formativi, precedenti_operativi,
                selezioni, conoscenza_lingua, altri_requisiti,
                prerequisiti, fonte_catalogo, descrizione
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("codice_corso"),
            data.get("denominazione"),
            data.get("ente_erogatore"),
            sett,
            ore,
            data.get("validita_mesi") if data.get("validita_mesi") else None,
            data.get("requisiti_sicurezza", ""),
            data.get("precedenti_formativi", ""),
            data.get("precedenti_operativi", ""),
            data.get("selezioni", ""),
            data.get("conoscenza_lingua", ""),
            data.get("altri_requisiti", ""),
            data.get("prerequisiti", ""),
            data.get("fonte_catalogo", "Manuale"),
            data.get("descrizione", "")
        ))
        conn.commit()
        return cursor.lastrowid


def update_corso(corso_id, data):
    """Aggiorna un corso nel catalogo con tutte le voci strutturate."""
    with get_db_connection() as conn:
        cur = conn.execute("SELECT fonte_catalogo FROM corso WHERE id = ?", (corso_id,)).fetchone()
        fonte = data.get("fonte_catalogo") or (cur["fonte_catalogo"] if cur else "Manuale")
        sett = data.get("durata_settimane")
        ore = data.get("durata_ore")
        if not sett and ore:
            sett = ore // 36 if ore >= 36 else 1
        elif sett and not ore:
            ore = sett * 36

        conn.execute("""
            UPDATE corso SET
                codice_corso = ?,
                denominazione = ?,
                ente_erogatore = ?,
                durata_settimane = ?,
                durata_ore = ?,
                validita_mesi = ?,
                requisiti_sicurezza = ?,
                precedenti_formativi = ?,
                precedenti_operativi = ?,
                selezioni = ?,
                conoscenza_lingua = ?,
                altri_requisiti = ?,
                prerequisiti = ?,
                fonte_catalogo = ?,
                descrizione = ?
            WHERE id = ?
        """, (
            data.get("codice_corso"),
            data.get("denominazione"),
            data.get("ente_erogatore"),
            sett,
            ore,
            data.get("validita_mesi") if data.get("validita_mesi") else None,
            data.get("requisiti_sicurezza", ""),
            data.get("precedenti_formativi", ""),
            data.get("precedenti_operativi", ""),
            data.get("selezioni", ""),
            data.get("conoscenza_lingua", ""),
            data.get("altri_requisiti", ""),
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

            sett = c.get("durata_settimane")
            ore = c.get("durata_ore")
            if not sett and ore:
                sett = ore // 36 if ore >= 36 else 1
            elif sett and not ore:
                ore = sett * 36

            if not codice:
                words = [w[:3].upper() for w in denominazione.split() if len(w) >= 3][:3]
                prefix = "-".join(words) if words else "COR"
                codice = f"PDF-{prefix}-{imported_count + updated_count + 1:03d}"

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
                        durata_settimane = COALESCE(?, durata_settimane),
                        durata_ore = COALESCE(?, durata_ore),
                        validita_mesi = COALESCE(?, validita_mesi),
                        requisiti_sicurezza = COALESCE(?, requisiti_sicurezza),
                        precedenti_formativi = COALESCE(?, precedenti_formativi),
                        precedenti_operativi = COALESCE(?, precedenti_operativi),
                        selezioni = COALESCE(?, selezioni),
                        conoscenza_lingua = COALESCE(?, conoscenza_lingua),
                        altri_requisiti = COALESCE(?, altri_requisiti),
                        prerequisiti = COALESCE(?, prerequisiti),
                        fonte_catalogo = ?,
                        descrizione = COALESCE(?, descrizione)
                    WHERE id = ?
                """, (
                    codice,
                    denominazione,
                    c.get("ente_erogatore"),
                    sett,
                    ore,
                    c.get("validita_mesi"),
                    c.get("requisiti_sicurezza"),
                    c.get("precedenti_formativi"),
                    c.get("precedenti_operativi"),
                    c.get("selezioni"),
                    c.get("conoscenza_lingua"),
                    c.get("altri_requisiti"),
                    c.get("prerequisiti"),
                    fonte_catalogo,
                    c.get("descrizione"),
                    existing["id"]
                ))
                updated_count += 1
            else:
                conn.execute("""
                    INSERT INTO corso (
                        codice_corso, denominazione, ente_erogatore,
                        durata_settimane, durata_ore, validita_mesi,
                        requisiti_sicurezza, precedenti_formativi, precedenti_operativi,
                        selezioni, conoscenza_lingua, altri_requisiti,
                        prerequisiti, fonte_catalogo, descrizione
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    codice,
                    denominazione,
                    c.get("ente_erogatore") or "Centro Interforze di Formazione Intelligence/G.E. (CIFI/GE)",
                    sett,
                    ore,
                    c.get("validita_mesi"),
                    c.get("requisiti_sicurezza"),
                    c.get("precedenti_formativi"),
                    c.get("precedenti_operativi"),
                    c.get("selezioni"),
                    c.get("conoscenza_lingua"),
                    c.get("altri_requisiti"),
                    c.get("prerequisiti") or "Nessun prerequisito specifico indicato",
                    fonte_catalogo,
                    c.get("descrizione") or ""
                ))
                imported_count += 1

        conn.commit()
    return {"imported": imported_count, "updated": updated_count, "total": imported_count + updated_count}


def reset_and_seed_cifige_courses():
    """
    Cancella tutti i corsi precedentemente inseriti e relative partecipazioni collegate,
    e inserisce i 38 corsi ufficiali CIFIGE con tutte le voci strutturate.
    Configura inoltre livelli NOS, lingue e partecipazioni formative per il personale di test.
    """
    with get_db_connection() as conn:
        conn.execute("DELETE FROM partecipazione_corso;")
        conn.execute("DELETE FROM corso;")

        for c in CIFIGE_COURSES:
            conn.execute("""
                INSERT INTO corso (
                    codice_corso, denominazione, ente_erogatore,
                    durata_settimane, durata_ore, validita_mesi,
                    requisiti_sicurezza, precedenti_formativi, precedenti_operativi,
                    selezioni, conoscenza_lingua, altri_requisiti,
                    prerequisiti, fonte_catalogo, descrizione
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                c["codice_corso"],
                c["denominazione"],
                c["ente_erogatore"],
                c.get("durata_settimane"),
                c.get("durata_ore"),
                c.get("validita_mesi"),
                c.get("requisiti_sicurezza"),
                c.get("precedenti_formativi"),
                c.get("precedenti_operativi"),
                c.get("selezioni"),
                c.get("conoscenza_lingua"),
                c.get("altri_requisiti"),
                c.get("prerequisiti"),
                c.get("fonte_catalogo", "CATALOGO_CORSI_CIFIGE_ESTRATTO.pdf"),
                c.get("descrizione", "")
            ))

        # Configura livello NOS e lingua per i militari censiti
        personale_rows = conn.execute("SELECT id, matricola, grado_qualifica, cognome FROM personale").fetchall()
        for p in personale_rows:
            p_id = p["id"]
            cognome = p["cognome"].lower()
            if "rossi" in cognome:
                nos = "Segretissimo / NATO Cosmic Top Secret"
                lingua = "NATO JFLT 8 (2/2/2/2)"
            elif "ferrari" in cognome:
                nos = "Segreto / NATO Secret"
                lingua = "NATO JFLT 8 (2/2/2/2)"
            elif "bianchi" in cognome:
                nos = "Segreto / NATO Secret"
                lingua = "NATO JFLT 8 (2/2/2/2)"
            elif "verdi" in cognome:
                nos = "Riservato"
                lingua = "Livello B1"
            elif "esposito" in cognome:
                nos = "Riservato"
                lingua = "Base / Elementare"
            else:
                nos = "Riservato"
                lingua = "NATO JFLT 8"

            conn.execute("UPDATE personale SET livello_nos = ?, lingua_inglese = ? WHERE id = ?", (nos, lingua, p_id))

        # Inserimento partecipazioni di test collegate ai nuovi corsi CIFIGE
        corso_map = {}
        for row in conn.execute("SELECT id, codice_corso, denominazione FROM corso").fetchall():
            corso_map[row["codice_corso"]] = row["id"]

        m_rossi = conn.execute("SELECT id FROM personale WHERE LOWER(cognome) = 'rossi'").fetchone()
        m_ferrari = conn.execute("SELECT id FROM personale WHERE LOWER(cognome) = 'ferrari'").fetchone()
        m_bianchi = conn.execute("SELECT id FROM personale WHERE LOWER(cognome) = 'bianchi'").fetchone()
        m_verdi = conn.execute("SELECT id FROM personale WHERE LOWER(cognome) = 'verdi'").fetchone()
        m_esposito = conn.execute("SELECT id FROM personale WHERE LOWER(cognome) = 'esposito'").fetchone()

        if m_rossi and "CIFIGE-01" in corso_map and "CIFIGE-05" in corso_map:
            conn.execute("""
                INSERT INTO partecipazione_corso (personale_id, corso_id, data_inizio, data_fine, esito, numero_attestato, note)
                VALUES (?, ?, '2024-02-05', '2024-02-16', 'Superato', 'ATT-CIFIGE-01-2024', 'Corso Intelligence Interforze superato con profitto.')
            """, (m_rossi["id"], corso_map["CIFIGE-01"]))
            conn.execute("""
                INSERT INTO partecipazione_corso (personale_id, corso_id, data_inizio, data_fine, esito, numero_attestato, note)
                VALUES (?, ?, '2024-10-07', '2024-10-18', 'Superato', 'ATT-CIFIGE-05-2024', 'Corso TECHINT 1° Livello completato.')
            """, (m_rossi["id"], corso_map["CIFIGE-05"]))

        if m_ferrari and "CIFIGE-01" in corso_map and "CIFIGE-02" in corso_map:
            conn.execute("""
                INSERT INTO partecipazione_corso (personale_id, corso_id, data_inizio, data_fine, esito, numero_attestato, note)
                VALUES (?, ?, '2024-03-04', '2024-03-15', 'Superato', 'ATT-CIFIGE-01-2024-F', 'Propedeuticità comparto conseguita.')
            """, (m_ferrari["id"], corso_map["CIFIGE-01"]))
            conn.execute("""
                INSERT INTO partecipazione_corso (personale_id, corso_id, data_inizio, data_fine, esito, numero_attestato, note)
                VALUES (?, ?, '2024-11-11', '2024-11-22', 'Superato', 'ATT-CIFIGE-02-2024-F', 'Corso J2 Staff superato con lode.')
            """, (m_ferrari["id"], corso_map["CIFIGE-02"]))

        if m_bianchi and "CIFIGE-25" in corso_map:
            conn.execute("""
                INSERT INTO partecipazione_corso (personale_id, corso_id, data_inizio, data_fine, esito, numero_attestato, note)
                VALUES (?, ?, '2024-05-06', '2024-05-17', 'Superato', 'ATT-CIFIGE-25-2024', 'Acquisizione Forense digitale.')
            """, (m_bianchi["id"], corso_map["CIFIGE-25"]))

        if m_verdi and "CIFIGE-24" in corso_map:
            conn.execute("""
                INSERT INTO partecipazione_corso (personale_id, corso_id, data_inizio, data_fine, esito, numero_attestato, note)
                VALUES (?, ?, '2025-01-13', '2025-01-17', 'Superato', 'ATT-CIFIGE-24-2025', 'Corso propedeutico CNO.')
            """, (m_verdi["id"], corso_map["CIFIGE-24"]))

        if m_esposito and "CIFIGE-01" in corso_map:
            conn.execute("""
                INSERT INTO partecipazione_corso (personale_id, corso_id, data_inizio, data_fine, esito, numero_attestato, note)
                VALUES (?, ?, '2024-04-08', '2024-04-19', 'Superato', 'ATT-CIFIGE-01-2024-E', 'Abilitazione di base comparto.')
            """, (m_esposito["id"], corso_map["CIFIGE-01"]))

        conn.commit()
        return len(CIFIGE_COURSES)


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
