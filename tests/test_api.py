"""
Test per il modulo API REST (app/api.py).
Verifica che tutte le rotte API restituiscano i codici di stato e i dati corretti.
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


class TestApiRoutes(unittest.TestCase):

    def setUp(self):
        db.init_db()
        if len(db.get_all_personale()) == 0:
            db.create_personale({
                "matricola": "MAT-DEMO-001",
                "codice_fiscale": "RSSMRA85M01H501Z",
                "cognome": "Rossi",
                "nome": "Mario",
                "sesso": "M",
                "data_nascita": "1985-08-01",
                "luogo_nascita": "Roma",
                "grado_qualifica": "Caporal Maggiore Scelto",
                "reparto_ufficio": "Ufficio Piani ed Intelligence",
                "stato_servizio": "In Servizio"
            })

    def test_get_dashboard(self):
        handler = MockHandler()
        ApiRouter.handle_request(handler, "GET", "/api/dashboard", {})
        self.assertEqual(handler.sent_status, 200)
        res = handler.get_json()
        self.assertTrue(res["success"])
        self.assertIn("totale_personale", res["data"])
        self.assertIn("note_scadute", res["data"])

    def test_get_scadenzario(self):
        handler = MockHandler()
        ApiRouter.handle_request(handler, "GET", "/api/scadenzario", {})
        self.assertEqual(handler.sent_status, 200)
        res = handler.get_json()
        self.assertTrue(res["success"])
        self.assertIn("note", res["data"])
        self.assertIn("patenti", res["data"])
        self.assertIn("passaporti", res["data"])

    def test_get_personale_list(self):
        handler = MockHandler()
        ApiRouter.handle_request(handler, "GET", "/api/personale", {})
        self.assertEqual(handler.sent_status, 200)
        res = handler.get_json()
        self.assertTrue(res["success"])
        self.assertIsInstance(res["data"], list)
        self.assertGreater(len(res["data"]), 0)

    def test_get_personale_detail(self):
        # Prendiamo il primo dipendente
        handler_list = MockHandler()
        ApiRouter.handle_request(handler_list, "GET", "/api/personale", {})
        first_id = handler_list.get_json()["data"][0]["id"]

        handler = MockHandler()
        ApiRouter.handle_request(handler, "GET", f"/api/personale/{first_id}", {})
        self.assertEqual(handler.sent_status, 200)
        res = handler.get_json()
        self.assertTrue(res["success"])
        self.assertIn("patenti", res["data"])
        self.assertIn("note_caratteristiche", res["data"])
        self.assertIn("corsi", res["data"])
        self.assertIn("passaporti", res["data"])

    def test_put_personale(self):
        handler_list = MockHandler()
        ApiRouter.handle_request(handler_list, "GET", "/api/personale", {})
        first_p = handler_list.get_json()["data"][0]
        pid = first_p["id"]

        update_payload = dict(first_p)
        update_payload["incarico"] = "Incarico Modificato via API"
        update_payload["posto_tabellare"] = "Pos. Tabellare Aggiornata"
        update_payload["reparto_ufficio"] = "Sezione Pianificazione Operativa"

        handler_put = MockHandler(update_payload)
        ApiRouter.handle_request(handler_put, "PUT", f"/api/personale/{pid}", {})
        self.assertEqual(handler_put.sent_status, 200)

        # Verifica che sia aggiornato
        handler_get = MockHandler()
        ApiRouter.handle_request(handler_get, "GET", f"/api/personale/{pid}", {})
        updated = handler_get.get_json()["data"]
        self.assertEqual(updated["incarico"], "Incarico Modificato via API")
        self.assertEqual(updated["posto_tabellare"], "Pos. Tabellare Aggiornata")
        self.assertEqual(updated["reparto_ufficio"], "Sezione Pianificazione Operativa")

    def test_get_corsi(self):
        handler = MockHandler()
        ApiRouter.handle_request(handler, "GET", "/api/corsi", {})
        self.assertEqual(handler.sent_status, 200)
        res = handler.get_json()
        self.assertTrue(res["success"])
        self.assertIsInstance(res["data"], list)

    def test_delete_corso(self):
        # Crea un corso temporaneo
        cid = db.create_corso({
            "codice_corso": "TEMP-DEL-01",
            "denominazione": "Corso Temporaneo da Eliminare",
            "ente_erogatore": "Centro Sperimentale",
            "durata_ore": 10
        })
        self.assertIsNotNone(cid)

        # Chiamata DELETE via API
        handler_del = MockHandler()
        ApiRouter.handle_request(handler_del, "DELETE", f"/api/corsi/{cid}", {})
        self.assertEqual(handler_del.sent_status, 200)
        self.assertTrue(handler_del.get_json()["success"])

        # Verifica che non esista più
        deleted = db.get_corso_by_id(cid)
        self.assertIsNone(deleted)

    def test_update_corso(self):
        # 1. Crea un corso
        cid = db.create_corso({
            "codice_corso": "COR-TEST-UPD",
            "denominazione": "Corso Originale",
            "ente_erogatore": "Ente Alpha",
            "durata_ore": 20,
            "validita_mesi": 12,
            "prerequisiti": "Nessuno"
        })

        # 2. Aggiorna tramite PUT API
        handler_put = MockHandler({
            "codice_corso": "COR-TEST-UPD",
            "denominazione": "Corso Modificato con Successo",
            "ente_erogatore": "Ente Beta",
            "durata_ore": 45,
            "validita_mesi": 24,
            "prerequisiti": "Patente Mod. 2",
            "descrizione": "Descrizione aggiornata"
        })
        ApiRouter.handle_request(handler_put, "PUT", f"/api/corsi/{cid}", {})
        self.assertEqual(handler_put.sent_status, 200)
        self.assertTrue(handler_put.get_json()["success"])

        # 3. Verifica i dati aggiornati
        updated = db.get_corso_by_id(cid)
        self.assertEqual(updated["denominazione"], "Corso Modificato con Successo")
        self.assertEqual(updated["ente_erogatore"], "Ente Beta")
        self.assertEqual(updated["durata_ore"], 45)
        self.assertEqual(updated["validita_mesi"], 24)
        self.assertEqual(updated["prerequisiti"], "Patente Mod. 2")

        # Pulizia
        db.delete_corso(cid)


if __name__ == "__main__":
    unittest.main()

