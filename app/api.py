"""
Router e gestore delle chiamate API REST in formato JSON per l'applicazione Gestione Personale.
"""

import json
import urllib.parse
import base64
from datetime import datetime
from database import db
from app import pdf_parser

def parse_body(handler):
    """Legge e deserializza il payload JSON da una richiesta HTTP."""
    content_length = int(handler.headers.get("Content-Length", 0))
    if content_length == 0:
        return {}
    raw_data = handler.rfile.read(content_length).decode("utf-8")
    try:
        return json.loads(raw_data)
    except Exception:
        return {}

def send_json(handler, data, status=200):
    """Invia una risposta HTTP in formato JSON con intestazioni CORS e codifica UTF-8."""
    body = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.end_headers()
    handler.wfile.write(body)

def send_error(handler, message, status=400):
    """Invia un errore JSON strutturato."""
    send_json(handler, {"success": False, "error": message}, status=status)


class ApiRouter:
    """Gestore del routing delle richieste API REST."""

    @staticmethod
    def handle_request(handler, method, path, query_params):
        parts = [p for p in path.strip("/").split("/") if p]
        # parts[0] è 'api'
        if len(parts) < 2:
            send_error(handler, "Endpoint non valido", 404)
            return

        resource = parts[1]

        try:
            # DASHBOARD & SCADENZE
            if resource == "dashboard" and method == "GET":
                data = db.get_dashboard_stats()
                send_json(handler, {"success": True, "data": data})
                return

            if resource == "scadenzario" and method == "GET":
                data = db.get_scadenzario()
                send_json(handler, {"success": True, "data": data})
                return

            # PERSONALE
            if resource == "personale":
                # GET /api/personale
                if len(parts) == 2 and method == "GET":
                    search = query_params.get("search", [None])[0]
                    reparto = query_params.get("reparto", [None])[0]
                    stato = query_params.get("stato", [None])[0]
                    items = db.get_all_personale(search=search, reparto=reparto, stato=stato)
                    send_json(handler, {"success": True, "data": items})
                    return

                # POST /api/personale
                if len(parts) == 2 and method == "POST":
                    body = parse_body(handler)
                    new_id = db.create_personale(body)
                    send_json(handler, {"success": True, "id": new_id, "message": "Dipendente creato con successo"}, 201)
                    return

                # Rotte su specifico dipendente: /api/personale/<id>
                if len(parts) >= 3:
                    ident = parts[2].strip()
                    if ident.isdigit():
                        personale_id = int(ident)
                    else:
                        p_match = db.get_personale_by_matricola(ident)
                        if p_match:
                            personale_id = p_match["id"]
                        else:
                            send_error(handler, f"Dipendente non trovato: {ident}", 404)
                            return

                    if len(parts) == 3:
                        if method == "GET":
                            item = db.get_personale_by_id(personale_id)
                            if item:
                                send_json(handler, {"success": True, "data": item})
                            else:
                                send_error(handler, "Dipendente non trovato", 404)
                            return
                        elif method == "PUT":
                            body = parse_body(handler)
                            db.update_personale(personale_id, body)
                            send_json(handler, {"success": True, "message": "Dati dipendente aggiornati"})
                            return
                        elif method == "DELETE":
                            db.delete_personale(personale_id)
                            send_json(handler, {"success": True, "message": "Dipendente eliminato"})
                            return

                    # Sottorisorse del dipendente: /api/personale/<id>/patente
                    subresource = parts[3]
                    body = parse_body(handler)

                    if subresource == "patente" and method == "POST":
                        new_id = db.add_patente(personale_id, body)
                        send_json(handler, {"success": True, "id": new_id, "message": "Patente registrata con successo"}, 201)
                        return

                    if subresource == "nota" and method == "POST":
                        new_id = db.add_nota_caratteristica(personale_id, body)
                        send_json(handler, {"success": True, "id": new_id, "message": "Documento caratteristico registrato"}, 201)
                        return

                    if subresource == "corso" and method == "POST":
                        new_id = db.add_partecipazione_corso(personale_id, body)
                        send_json(handler, {"success": True, "id": new_id, "message": "Frequenza corso registrata"}, 201)
                        return

                    if subresource == "passaporto" and method == "POST":
                        new_id = db.add_passaporto(personale_id, body)
                        send_json(handler, {"success": True, "id": new_id, "message": "Passaporto di servizio salvato"}, 201)
                        return

            # PATENTI DIRETTE: /api/patente/<id>
            if resource == "patente" and len(parts) == 3:
                if not parts[2].strip().isdigit():
                    send_error(handler, "ID patente non valido", 400)
                    return
                patente_id = int(parts[2].strip())
                if method == "PUT":
                    body = parse_body(handler)
                    db.update_patente(patente_id, body)
                    send_json(handler, {"success": True, "message": "Patente aggiornata"})
                    return
                elif method == "DELETE":
                    db.delete_patente(patente_id)
                    send_json(handler, {"success": True, "message": "Patente rimossa"})
                    return

            # NOTE CARATTERISTICHE DIRETTE: /api/nota/<id>
            if resource == "nota" and len(parts) == 3:
                if not parts[2].strip().isdigit():
                    send_error(handler, "ID nota non valido", 400)
                    return
                nota_id = int(parts[2].strip())
                if method == "PUT":
                    body = parse_body(handler)
                    db.update_nota_caratteristica(nota_id, body)
                    send_json(handler, {"success": True, "message": "Nota caratteristica aggiornata"})
                    return
                elif method == "DELETE":
                    db.delete_nota_caratteristica(nota_id)
                    send_json(handler, {"success": True, "message": "Nota rimossa"})
                    return

            # CATALOGO CORSI: /api/corsi
            if resource == "corsi":
                # POST /api/corsi/upload-pdf (analizza il PDF senza salvarlo ancora nel DB)
                if len(parts) == 3 and parts[2] == "upload-pdf" and method == "POST":
                    body = parse_body(handler)
                    file_b64 = body.get("file_base64", "")
                    filename = body.get("filename", "Catalogo_Corsi.pdf")

                    # Se c'è il prefisso data:application/pdf;base64,...
                    if "," in file_b64:
                        file_b64 = file_b64.split(",", 1)[1]

                    try:
                        pdf_bytes = base64.b64decode(file_b64)
                    except Exception as e:
                        send_error(handler, f"File PDF non valido o corrotto: {str(e)}", 400)
                        return

                    raw_text = pdf_parser.extract_text_from_pdf(pdf_bytes)
                    if not raw_text:
                        send_error(handler, "Impossibile estrarre testo dal file PDF (potrebbe essere una scansione immagine o protetto da password).", 422)
                        return

                    parsed_courses = pdf_parser.parse_course_catalog_text(raw_text)
                    send_json(handler, {
                        "success": True,
                        "filename": filename,
                        "total_extracted": len(parsed_courses),
                        "courses": parsed_courses
                    })
                    return

                # POST /api/corsi/import-batch (conferma e salva i corsi nel DB)
                if len(parts) == 3 and parts[2] == "import-batch" and method == "POST":
                    body = parse_body(handler)
                    courses = body.get("courses", [])
                    filename = body.get("filename", "Catalogo PDF")
                    if not courses or not isinstance(courses, list):
                        send_error(handler, "Nessun corso fornito per l'importazione", 400)
                        return

                    res_import = db.import_corsi_batch(courses, fonte_catalogo=filename)
                    send_json(handler, {
                        "success": True,
                        "result": res_import,
                        "imported_count": res_import["total"],
                        "message": f"Importazione completata con successo ({res_import['total']} corsi elaborati)."
                    }, 201)
                    return

                # GET o POST /api/corsi/verifica-candidatura (verifica idoneità e prerequisiti)
                if len(parts) == 3 and parts[2] == "verifica-candidatura":
                    if method == "GET":
                        personale_id = query_params.get("personale_id", [None])[0]
                        corso_id = query_params.get("corso_id", [None])[0]
                    elif method == "POST":
                        body = parse_body(handler)
                        personale_id = body.get("personale_id")
                        corso_id = body.get("corso_id")
                    else:
                        send_error(handler, "Metodo non consentito", 405)
                        return

                    if not personale_id or not corso_id or str(personale_id).lower() in ("undefined", "null", "") or str(corso_id).lower() in ("undefined", "null", ""):
                        send_error(handler, "Parametri 'personale_id' e 'corso_id' obbligatori e validi", 400)
                        return

                    try:
                        valutazione = db.valuta_candidatura_corso(personale_id, corso_id)
                        send_json(handler, {"success": True, "data": valutazione})
                    except ValueError as ve:
                        send_error(handler, str(ve), 404)
                    return

                if len(parts) == 2 and method == "GET":
                    items = db.get_all_corsi()
                    send_json(handler, {"success": True, "data": items})
                    return
                elif len(parts) == 2 and method == "POST":
                    body = parse_body(handler)
                    new_id = db.create_corso(body)
                    send_json(handler, {"success": True, "id": new_id, "message": "Nuovo corso inserito a catalogo"}, 201)
                    return
                elif len(parts) == 3:
                    ident = parts[2].strip()
                    item = db.get_corso_by_id_or_code(ident)
                    if not item:
                        send_error(handler, f"Corso non trovato: {ident}", 404)
                        return
                    corso_id = item["id"]

                    if method == "GET":
                        send_json(handler, {"success": True, "data": item})
                        return
                    elif method == "PUT":
                        body = parse_body(handler)
                        db.update_corso(corso_id, body)
                        send_json(handler, {"success": True, "message": "Corso aggiornato"})
                        return
                    elif method == "DELETE":
                        db.delete_corso(corso_id)
                        send_json(handler, {"success": True, "message": "Corso eliminato"})
                        return

            # PARTECIPAZIONI CORSI DIRETTE: /api/partecipazione/<id>
            if resource == "partecipazione" and len(parts) == 3:
                if not parts[2].strip().isdigit():
                    send_error(handler, "ID partecipazione non valido", 400)
                    return
                partecipazione_id = int(parts[2].strip())
                if method == "DELETE":
                    db.delete_partecipazione_corso(partecipazione_id)
                    send_json(handler, {"success": True, "message": "Partecipazione eliminata"})
                    return

            # PASSAPORTO DIRETTO: /api/passaporto/<id>
            if resource == "passaporto" and len(parts) == 3:
                if not parts[2].strip().isdigit():
                    send_error(handler, "ID passaporto non valido", 400)
                    return
                passaporto_id = int(parts[2].strip())
                if method == "PUT":
                    body = parse_body(handler)
                    db.update_passaporto(passaporto_id, body)
                    send_json(handler, {"success": True, "message": "Passaporto aggiornato"})
                    return
                elif method == "DELETE":
                    db.delete_passaporto(passaporto_id)
                    send_json(handler, {"success": True, "message": "Passaporto eliminato"})
                    return

            # Se nessun route corrisponde
            send_error(handler, f"Rotta non trovata: {method} {path}", 404)

        except Exception as e:
            import traceback
            traceback.print_exc()
            send_error(handler, f"Errore interno del server: {str(e)}", 500)

