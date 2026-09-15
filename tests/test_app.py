"""
Test di integrazione per il database e per le funzionalità dell'applicazione.
Verifica:
- Inizializzazione del database
- Calcolo automatico della scadenza delle note caratteristiche a 365 giorni
- Tracciamento patenti, corsi e passaporti
- Integrità delle viste per il calcolo dei giorni mancanti/ritardo
"""

import unittest
import sys
from pathlib import Path
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from database import db

class TestGestionePersonale(unittest.TestCase):

    def setUp(self):
        db.init_db()

    def test_dashboard_stats(self):
        stats = db.get_dashboard_stats()
        self.assertIn("totale_personale", stats)
        self.assertGreater(stats["totale_personale"], 0)
        self.assertIn("note_scadute", stats)
        self.assertIn("note_urgenti_30", stats)

    def test_scadenza_note_365_giorni(self):
        """Verifica che la scadenza della prossima nota sia calcolata a 365 giorni dal termine del periodo valutato."""
        periodo_al = "2025-06-30"
        expected_scadenza = (datetime.strptime(periodo_al, "%Y-%m-%d") + timedelta(days=365)).strftime("%Y-%m-%d")
        
        calc_scadenza = db.calculate_next_deadline(periodo_al, 365)
        self.assertEqual(calc_scadenza, expected_scadenza)
        self.assertEqual(calc_scadenza, "2026-06-30")

    def test_flusso_completo_dipendente(self):
        """Crea un nuovo dipendente, aggiunge patente, passaporto, nota caratteristica e corso."""
        test_cf = "TSTMNR88A01H501K"
        test_mat = "MAT-TEST-99"
        
        # Pulizia preventiva se esiste
        with db.get_db_connection() as conn:
            conn.execute("DELETE FROM personale WHERE matricola = ?", (test_mat,))
            conn.commit()

        # 1. Creazione Personale
        pid = db.create_personale({
            "matricola": test_mat,
            "codice_fiscale": test_cf,
            "cognome": "Test",
            "nome": "Marco",
            "sesso": "M",
            "data_nascita": "1988-01-01",
            "luogo_nascita": "Roma",
            "provincia_nascita": "RM",
            "grado_qualifica": "Tenente",
            "reparto_ufficio": "Ufficio Piani ed Intelligence",
            "incarico": "Addetto Logistico",
            "posto_tabellare": "Pos. Tabellare 04/B",
            "stato_servizio": "In Servizio"
        })
        self.assertIsNotNone(pid)

        # 2. Aggiunta Patente
        pat_id = db.add_patente(pid, {
            "tipo_patente": "Servizio/Militare",
            "categoria": "Mod. 3",
            "numero_patente": "SM-TEST-001",
            "ente_rilascio": "Comando Supporti",
            "data_rilascio": "2020-01-10",
            "data_scadenza": "2030-01-10",
            "limitazioni_abilitazioni": "Guida mezzi operativi"
        })
        self.assertIsNotNone(pat_id)

        # 3. Aggiunta Nota Caratteristica (con calcolo automatico 365 giorni)
        nota_id = db.add_nota_caratteristica(pid, {
            "tipologia_documento": "Note Caratteristiche",
            "motivo_redazione": "Ordinaria Annuale",
            "periodo_dal": "2024-10-01",
            "periodo_al": "2025-09-30",
            "data_firma_interessato": "2025-10-10",
            # Lasciamo data_prossima_scadenza vuoto per testare il calcolo automatico
            "giudizio_finale": "Eccellente",
            "compilatore": "Magg. Valutatore"
        })
        self.assertIsNotNone(nota_id)

        # 4. Aggiunta Passaporto di Servizio
        pass_id = db.add_passaporto(pid, {
            "numero_passaporto": "PS-TEST-9988",
            "tipo_passaporto": "Servizio",
            "autorita_rilascio": "MAECI",
            "data_rilascio": "2023-05-01",
            "data_scadenza": "2028-05-01",
            "stato": "Valido",
            "ubicazione_custodia": "Cassaforte Ufficio"
        })
        self.assertIsNotNone(pass_id)

        # 5. Aggiunta Corso
        corsi = db.get_all_corsi()
        corso_id = corsi[0]["id"]
        partecipazione_id = db.add_partecipazione_corso(pid, {
            "corso_id": corso_id,
            "data_inizio": "2024-05-10",
            "data_fine": "2024-05-12",
            "esito": "Superato",
            "numero_attestato": "ATT-TEST-01"
        })
        self.assertIsNotNone(partecipazione_id)

        # 6. Modifica Dati Operatore (Test Update)
        update_success = db.update_personale(pid, {
            "matricola": test_mat,
            "codice_fiscale": test_cf,
            "cognome": "Test Modificato",
            "nome": "Marco",
            "sesso": "M",
            "data_nascita": "1988-01-01",
            "luogo_nascita": "Roma",
            "provincia_nascita": "RM",
            "grado_qualifica": "Capitano",
            "reparto_ufficio": "Sezione Studi Speciali",
            "incarico": "Responsabile Progetti",
            "posto_tabellare": "Pos. Tabellare 01/A (Direttivo)",
            "stato_servizio": "In Servizio"
        })
        self.assertTrue(update_success)

        # 7. Verifica Scheda Completa con i dati modificati
        scheda = db.get_personale_by_id(pid)
        self.assertEqual(scheda["matricola"], test_mat)
        self.assertEqual(scheda["cognome"], "Test Modificato")
        self.assertEqual(scheda["grado_qualifica"], "Capitano")
        self.assertEqual(scheda["reparto_ufficio"], "Sezione Studi Speciali")
        self.assertEqual(scheda["posto_tabellare"], "Pos. Tabellare 01/A (Direttivo)")
        self.assertEqual(len(scheda["patenti"]), 1)
        self.assertEqual(len(scheda["passaporti"]), 1)
        self.assertEqual(len(scheda["corsi"]), 1)
        self.assertEqual(len(scheda["note_caratteristiche"]), 1)
        
        # Verifica che la scadenza della nota sia fine_periodo + 365 gg
        nota_salvata = scheda["note_caratteristiche"][0]
        self.assertEqual(nota_salvata["data_prossima_scadenza"], "2026-09-30")

        # 8. Pulizia finale
        db.delete_personale(pid)
        self.assertIsNone(db.get_personale_by_id(pid))

if __name__ == "__main__":
    unittest.main()

