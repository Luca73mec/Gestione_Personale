"""
Test per il modulo di Pianificazione Corsi e Verifica Prerequisiti di Candidatura.
"""

import unittest
import sys
import json
import io
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.api import ApiRouter
from database import db


class MockHandler:
    def __init__(self, body_dict=None):
        self.headers = {}
        if body_dict is not None:
            raw = json.dumps(body_dict).encode("utf-8")
            self.rfile = io.BytesIO(raw)
            self.headers["Content-Length"] = str(len(raw))
        else:
            self.rfile = io.BytesIO(b"")
            self.headers["Content-Length"] = "0"
            
        self.wfile = io.BytesIO()
        self.sent_status = None
        self.sent_headers = {}

    def send_response(self, status):
        self.sent_status = status

    def send_header(self, key, value):
        self.sent_headers[key] = value

    def end_headers(self):
        pass

    def get_json(self):
        return json.loads(self.wfile.getvalue().decode("utf-8"))


class TestPianificazioneCorsi(unittest.TestCase):

    def setUp(self):
        db.init_db()
        self._cleanup()

    def tearDown(self):
        self._cleanup()

    def _cleanup(self):
        with db.get_db_connection() as conn:
            conn.execute("DELETE FROM partecipazione_corso WHERE personale_id IN (SELECT id FROM personale WHERE matricola LIKE 'MAT-PLAN-%')")
            conn.execute("DELETE FROM patente WHERE personale_id IN (SELECT id FROM personale WHERE matricola LIKE 'MAT-PLAN-%')")
            conn.execute("DELETE FROM personale WHERE matricola LIKE 'MAT-PLAN-%'")
            conn.execute("DELETE FROM corso WHERE codice_corso LIKE 'PLAN-TEST-%'")
            conn.commit()

    def test_valutazione_candidatura_idoneo(self):
        # 1. Crea corso con prerequisito di Patente Mod. 3
        cid = db.create_corso({
            "codice_corso": "PLAN-TEST-01",
            "denominazione": "Corso Conduzione Tattica",
            "ente_erogatore": "Scuola Trasporti",
            "durata_ore": 40,
            "validita_mesi": 24,
            "prerequisiti": "Patente Militare Mod. 3"
        })

        # 2. Crea operatore con Patente Militare Mod. 3 valida
        pid = db.create_personale({
            "matricola": "MAT-PLAN-01",
            "codice_fiscale": "PLNIDO80A01H501Z",
            "cognome": "Verdi",
            "nome": "Giuseppe",
            "sesso": "M",
            "data_nascita": "1985-05-10",
            "luogo_nascita": "Roma",
            "grado_qualifica": "Sergente Maggiore",
            "reparto_ufficio": "Sezione Pianificazione Operativa",
            "stato_servizio": "In Servizio"
        })
        db.add_patente(pid, {
            "categoria": "Patente Militare Mod. 3",
            "numero_patente": "PAT-MIL-999",
            "ente_rilascio": "Comando Trasporti",
            "data_rilascio": "2020-01-01",
            "data_scadenza": "2028-01-01"
        })

        # 3. Valutazione
        audit = db.valuta_candidatura_corso(pid, cid)
        self.assertEqual(audit["esito_globale"], "IDONEO")
        self.assertEqual(audit["badge_class"], "success")
        self.assertGreaterEqual(audit["percentuale_conformita"], 90)

    def test_valutazione_candidatura_non_idoneo_mancanza_patente(self):
        # 1. Corso che richiede Patente Militare Mod. 4
        cid = db.create_corso({
            "codice_corso": "PLAN-TEST-02",
            "denominazione": "Corso Mezzi Corazzati Pesanti",
            "ente_erogatore": "Scuola Cavalleria",
            "durata_ore": 80,
            "prerequisiti": "Patente Militare Mod. 4"
        })

        # 2. Operatore senza patente Mod. 4
        pid = db.create_personale({
            "matricola": "MAT-PLAN-02",
            "codice_fiscale": "PLNNOI80A01H501W",
            "cognome": "Rossi",
            "nome": "Mario",
            "sesso": "M",
            "data_nascita": "1990-03-15",
            "luogo_nascita": "Milano",
            "grado_qualifica": "Caporal Maggiore",
            "reparto_ufficio": "Ufficio Piani ed Intelligence",
            "stato_servizio": "In Servizio"
        })

        # 3. Valutazione
        audit = db.valuta_candidatura_corso(pid, cid)
        self.assertEqual(audit["esito_globale"], "NON_IDONEO")
        self.assertEqual(audit["badge_class"], "danger")
        # Verifica presenza motivo bloccante
        has_pat_block = any(chk["esito"] == "BLOCCANTE" and "Patente" in chk["categoria"] for chk in audit["checks"])
        self.assertTrue(has_pat_block)

    def test_valutazione_candidatura_fuori_servizio(self):
        # Operatore in congedo o sospeso
        pid = db.create_personale({
            "matricola": "MAT-PLAN-03",
            "codice_fiscale": "PLNSOS80A01H501X",
            "cognome": "Bianchi",
            "nome": "Luigi",
            "sesso": "M",
            "data_nascita": "1988-11-20",
            "luogo_nascita": "Napoli",
            "grado_qualifica": "Maresciallo",
            "reparto_ufficio": "Sezione Studi Speciali",
            "stato_servizio": "Congedo"
        })

        cid = db.create_corso({
            "codice_corso": "PLAN-TEST-03",
            "denominazione": "Corso Base Standard",
            "ente_erogatore": "Centro Addestramento",
            "prerequisiti": "Nessun prerequisito specifico"
        })

        audit = db.valuta_candidatura_corso(pid, cid)
        self.assertEqual(audit["esito_globale"], "NON_IDONEO")
        has_serv_block = any(chk["esito"] == "BLOCCANTE" and "Stato di Servizio" in chk["categoria"] for chk in audit["checks"])
        self.assertTrue(has_serv_block)

    def test_valutazione_candidatura_riserva(self):
        # Corso con requisito speciale qualitativo ("Idoneità CS/TS, lingua inglese B2")
        cid = db.create_corso({
            "codice_corso": "PLAN-TEST-04",
            "denominazione": "Corso Operazioni Internazionali",
            "ente_erogatore": "Scuola Interforze",
            "prerequisiti": "Idoneità CS/TS, Conoscenza Lingua Inglese B2"
        })

        pid = db.create_personale({
            "matricola": "MAT-PLAN-04",
            "codice_fiscale": "PLNRIS80A01H501Y",
            "cognome": "Neri",
            "nome": "Marco",
            "sesso": "M",
            "data_nascita": "1986-07-25",
            "luogo_nascita": "Torino",
            "grado_qualifica": "Tenente",
            "reparto_ufficio": "Ufficio Piani ed Intelligence",
            "stato_servizio": "In Servizio"
        })

        audit = db.valuta_candidatura_corso(pid, cid)
        self.assertEqual(audit["esito_globale"], "IDONEO_CON_RISERVA")
        self.assertEqual(audit["badge_class"], "warning")
        has_to_verify = any(chk["esito"] == "DA_VERIFICARE" for chk in audit["checks"])
        self.assertTrue(has_to_verify)

    def test_api_verifica_candidatura(self):
        all_p = db.get_all_personale()
        all_c = db.get_all_corsi()
        self.assertGreater(len(all_p), 0)
        self.assertGreater(len(all_c), 0)
        pid = all_p[0]["id"]
        cid = all_c[0]["id"]

        # Test GET
        handler_get = MockHandler()
        ApiRouter.handle_request(handler_get, "GET", "/api/corsi/verifica-candidatura", {
            "personale_id": [str(pid)],
            "corso_id": [str(cid)]
        })
        self.assertEqual(handler_get.sent_status, 200)
        res_get = handler_get.get_json()
        self.assertTrue(res_get["success"])
        self.assertIn("esito_globale", res_get["data"])
        self.assertIn("checks", res_get["data"])

        # Test POST
        handler_post = MockHandler({
            "personale_id": pid,
            "corso_id": cid
        })
        ApiRouter.handle_request(handler_post, "POST", "/api/corsi/verifica-candidatura", {})
        self.assertEqual(handler_post.sent_status, 200)
        res_post = handler_post.get_json()
        self.assertTrue(res_post["success"])
        self.assertEqual(res_post["data"]["esito_globale"], res_get["data"]["esito_globale"])

    def test_non_integer_resilience(self):
        """Verifica che valori non interi (es. 'undefined', codici o matricole) non causino crash 500 con ValueError."""
        # 1. Verifica candidatura con parametri 'undefined'
        h_undef = MockHandler()
        ApiRouter.handle_request(h_undef, "GET", "/api/corsi/verifica-candidatura", {
            "personale_id": ["undefined"],
            "corso_id": ["undefined"]
        })
        self.assertEqual(h_undef.sent_status, 400)
        self.assertFalse(h_undef.get_json()["success"])

        # 2. GET corso con 'undefined'
        h_corso_undef = MockHandler()
        ApiRouter.handle_request(h_corso_undef, "GET", "/api/corsi/undefined", {})
        self.assertEqual(h_corso_undef.sent_status, 404)

        # 3. GET personale con 'undefined'
        h_pers_undef = MockHandler()
        ApiRouter.handle_request(h_pers_undef, "GET", "/api/personale/undefined", {})
        self.assertEqual(h_pers_undef.sent_status, 404)

        # 4. Valutazione tramite codice_corso e matricola
        cid = db.create_corso({
            "codice_corso": "PLAN-TEST-STR",
            "denominazione": "Corso Test String",
            "ente_erogatore": "Ente Test",
            "prerequisiti": ""
        })
        pid = db.create_personale({
            "matricola": "MAT-PLAN-STR",
            "codice_fiscale": "PLNSTR80A01H501Z",
            "cognome": "Bianchi",
            "nome": "Mario",
            "sesso": "M",
            "data_nascita": "1980-01-01",
            "luogo_nascita": "Roma",
            "grado_qualifica": "Capitano",
            "reparto_ufficio": "Ufficio Piani ed Intelligence",
            "stato_servizio": "In Servizio"
        })

        # Deve funzionare passando i codici alfanumerici senza sollevare ValueError (invalid literal)
        audit_by_codes = db.valuta_candidatura_corso("MAT-PLAN-STR", "PLAN-TEST-STR")
        self.assertIn("esito_globale", audit_by_codes)
        self.assertEqual(audit_by_codes["esito_globale"], "IDONEO")


if __name__ == "__main__":
    unittest.main()
