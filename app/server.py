#!/usr/bin/env python3
"""
Server HTTP locale multi-threaded per GestionePersonaleWeb.
Non richiede librerie esterne (utilizza esclusivamente la libreria standard di Python).
Supporta API REST JSON e serving file statici (HTML, CSS, JS).
"""

import sys
import os
from pathlib import Path

# Aggiunge la directory radice del progetto al PYTHONPATH
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import mimetypes
import urllib.parse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from database import db
from app.api import ApiRouter, send_error

STATIC_DIR = BASE_DIR / "static"


class AppRequestHandler(BaseHTTPRequestHandler):
    """Gestore delle richieste HTTP per file statici e API REST."""

    def do_OPTIONS(self):
        """Gestione CORS Preflight."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        self._dispatch("GET")

    def do_POST(self):
        self._dispatch("POST")

    def do_PUT(self):
        self._dispatch("PUT")

    def do_DELETE(self):
        self._dispatch("DELETE")

    def _dispatch(self, method):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query_params = urllib.parse.parse_qs(parsed_url.query)

        # Se la richiesta è per una rotta API
        if path.startswith("/api/"):
            ApiRouter.handle_request(self, method, path, query_params)
            return

        # Altrimenti serviamo i file statici
        if method != "GET":
            send_error(self, "Metodo non supportato per file statici", 405)
            return

        self._serve_static(path)

    def _serve_static(self, path):
        if path == "/" or path == "":
            rel_path = "index.html"
        else:
            rel_path = path.lstrip("/")

        target_file = (STATIC_DIR / rel_path).resolve()

        # Protezione path traversal
        try:
            target_file.relative_to(STATIC_DIR.resolve())
        except ValueError:
            send_error(self, "Accesso negato", 403)
            return

        if not target_file.exists() or not target_file.is_file():
            # Fallback SPA su index.html se non è un asset con estensione
            if "." not in target_file.name:
                target_file = STATIC_DIR / "index.html"
            else:
                send_error(self, "File non trovato", 404)
                return

        mime_type, _ = mimetypes.guess_type(str(target_file))
        if not mime_type:
            mime_type = "application/octet-stream"

        try:
            with open(target_file, "rb") as f:
                content = f.read()

            self.send_response(200)
            self.send_header("Content-Type", f"{mime_type}; charset=utf-8" if "text" in mime_type or "javascript" in mime_type else mime_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            send_error(self, f"Errore lettura file: {str(e)}", 500)

    def log_message(self, format, *args):
        """Formattazione personalizzata dei log a video."""
        print(f"[{self.log_date_time_string()}] {self.command} {self.path} - {args[0]}")


def run(host="127.0.0.1", port=8080):
    """Avvia il server web locale."""
    # Assicura inizializzazione DB
    db.init_db()

    server_address = (host, port)
    httpd = ThreadingHTTPServer(server_address, AppRequestHandler)
    print("\n" + "=" * 65)
    print(" 🚀 APPLICAZIONE GESTIONE PERSONALE WEB AVVIATA CON SUCCESSO")
    print("=" * 65)
    print(f" ▸ Indirizzo locale:  http://{host}:{port}")
    print(f" ▸ Documenti:        http://{host}:{port}/")
    print(f" ▸ Database:         {db.DB_FILE}")
    print(" ▸ Premi Ctrl+C per arrestare il server.")
    print("=" * 65 + "\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[INFO] Arresto del server in corso...")
        httpd.server_close()
        print("[INFO] Server terminato correttamente.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Server Web Gestione Personale")
    parser.add_argument("--host", default="127.0.0.1", help="Indirizzo IP di ascolto (default 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8080, help="Porta HTTP (default 8080)")
    args = parser.parse_args()

    run(host=args.host, port=args.port)

