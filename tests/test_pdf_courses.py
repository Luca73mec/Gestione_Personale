"""
Test per le funzionalità di caricamento catalogo corsi da PDF,
estrazione automatica dei prerequisiti e iscrizione corsi (manuale e da catalogo).
"""

import unittest
import sys
import json
import io
import base64
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.api import ApiRouter
from app.pdf_parser import parse_course_catalog_text, parse_single_course_block
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


class TestPdfCourseExtraction(unittest.TestCase):

    def setUp(self):
        db.init_db()

    def test_text_parsing_prerequisites(self):
        sample_text = """
        CATALOGO FORMATIVO INTERFORZE 2026

        CORSO: Operatore Intelligence Avanzato
        Codice: OIA-2026
        Ente Erogatore: Scuola Interforze Intelligence
        Durata: 120 ore
        Validità: 36 mesi
        Prerequisiti: Idoneità CS/TS, qualifica analista base, conoscenza lingua inglese B2.
        Descrizione: Tecniche avanzate di analisi informativa e OSINT.

        ---

        CORSO: Scorta e Sicurezza VIP
        Codice: SS-VIP-02
        Ente: Centro Addestramento Speciale
        Durata: 80 ore
        Requisiti di ammissione: Patente Militare Mod. 3, idoneità al maneggio armi, superamento test ginnico.
        Descrizione: Procedure operative per scorte tattiche.
        """

        courses = parse_course_catalog_text(sample_text)
        self.assertEqual(len(courses), 2)

        c1 = courses[0]
        self.assertIn("Intelligence Avanzato", c1["denominazione"])
        self.assertEqual(c1["codice_corso"], "OIA-2026")
        self.assertEqual(c1["durata_ore"], 120)
        self.assertEqual(c1["validita_mesi"], 36)
        self.assertIn("Idoneità CS/TS", c1["prerequisiti"])

        c2 = courses[1]
        self.assertIn("Scorta e Sicurezza VIP", c2["denominazione"])
        self.assertEqual(c2["codice_corso"], "SS-VIP-02")
        self.assertEqual(c2["durata_ore"], 80)
        self.assertIn("Patente Militare Mod. 3", c2["prerequisiti"])

    def test_import_corsi_batch_db(self):
        courses_data = [
            {
                "codice_corso": "TEST-CYB-01",
                "denominazione": "Cyber Security Difensiva Test",
                "ente_erogatore": "Comando Trasmissioni",
                "durata_ore": 60,
                "validita_mesi": 24,
                "prerequisiti": "Diploma tecnico, Corso Base Reti",
                "descrizione": "Corso di monitoraggio SOC"
            },
            {
                "codice_corso": "TEST-CYB-02",
                "denominazione": "Threat Intelligence Applicata Test",
                "ente_erogatore": "Comando C4I",
                "durata_ore": 45,
                "validita_mesi": None,
                "prerequisiti": "Conoscenza architetture TCP/IP",
                "descrizione": "Analisi delle minacce"
            }
        ]

        res_batch = db.import_corsi_batch(courses_data, fonte_catalogo="Test_Catalogo.pdf")
        self.assertEqual(res_batch["total"], 2)

        # Verifica che i corsi siano nel catalogo con i prerequisiti
        all_corsi = db.get_all_corsi()
        imported = [c for c in all_corsi if c["codice_corso"] in ("TEST-CYB-01", "TEST-CYB-02")]
        self.assertEqual(len(imported), 2)
        
        c1 = next(c for c in imported if c["codice_corso"] == "TEST-CYB-01")
        self.assertEqual(c1["prerequisiti"], "Diploma tecnico, Corso Base Reti")
        self.assertEqual(c1["fonte_catalogo"], "Test_Catalogo.pdf")

    def test_api_import_batch(self):
        body = {
            "filename": "Catalogo_2026.pdf",
            "courses": [
                {
                    "codice_corso": "API-CAT-01",
                    "denominazione": "Corso Geoint Speciale",
                    "ente_erogatore": "Centro GEO",
                    "durata_ore": 50,
                    "validita_mesi": 12,
                    "prerequisiti": "Abilitazione cartografica di 2° livello"
                }
            ]
        }
        handler = MockHandler(body)
        ApiRouter.handle_request(handler, "POST", "/api/corsi/import-batch", {})
        self.assertEqual(handler.sent_status, 201)
        res = handler.get_json()
        self.assertTrue(res["success"])
        self.assertEqual(res["imported_count"], 1)

    def test_iscrizione_corso_manuale_e_catalogo(self):
        # 1. Recupera o crea una persona
        handler_list = MockHandler()
        ApiRouter.handle_request(handler_list, "GET", "/api/personale", {})
        persons = handler_list.get_json()["data"]
        self.assertGreater(len(persons), 0)
        person_id = persons[0]["id"]

        # 2. Iscrizione selezionando corso da catalogo
        all_corsi = db.get_all_corsi()
        target_corso = all_corsi[0]

        handler_cat = MockHandler({
            "is_manual": False,
            "corso_id": target_corso["id"],
            "data_inizio": "2026-03-01",
            "data_fine": "2026-03-10",
            "esito": "Superato",
            "numero_attestato": "ATT-CAT-999"
        })
        ApiRouter.handle_request(handler_cat, "POST", f"/api/personale/{person_id}/corso", {})
        self.assertEqual(handler_cat.sent_status, 201)
        res_cat = handler_cat.get_json()
        self.assertTrue(res_cat["success"])

        # 3. Iscrizione manuale (creazione al volo del corso con prerequisiti)
        handler_man = MockHandler({
            "is_manual": True,
            "denominazione": "Corso Riconoscimento Mezzi Corazzati",
            "ente_erogatore": "Scuola Cavalleria",
            "durata_ore": 30,
            "prerequisiti": "Idoneità al servizio operativo",
            "data_inizio": "2026-04-01",
            "data_fine": "2026-04-05",
            "esito": "Superato",
            "numero_attestato": "ATT-MAN-123"
        })
        ApiRouter.handle_request(handler_man, "POST", f"/api/personale/{person_id}/corso", {})
        self.assertEqual(handler_man.sent_status, 201)
        res_man = handler_man.get_json()
        self.assertTrue(res_man["success"])

        # 4. Verifica nel dettaglio persona
        detail = db.get_personale_by_id(person_id)
        partecipazioni = detail["corsi"]
        attestati = [p.get("numero_attestato") for p in partecipazioni]
        self.assertIn("ATT-CAT-999", attestati)
        self.assertIn("ATT-MAN-123", attestati)

        # Verifica che il corso manuale abbia salvato correttamente denominazione e prerequisiti
        manual_entry = next(p for p in partecipazioni if p.get("numero_attestato") == "ATT-MAN-123")
        self.assertEqual(manual_entry["denominazione"], "Corso Riconoscimento Mezzi Corazzati")
        self.assertEqual(manual_entry["prerequisiti"], "Idoneità al servizio operativo")


if __name__ == "__main__":
    unittest.main()
