"""
Modulo di estrazione e analisi di cataloghi corsi in formato PDF.
Utilizza il framework nativo Apple PDFKit su macOS (zero dipendenze pip)
con fallback a parser di stream zlib per ambienti Linux.
"""

import os
import re
import sys
import tempfile
import subprocess
import zlib


def extract_text_from_pdf(pdf_bytes):
    """Estrae tutto il contenuto testuale da un buffer binario PDF."""
    # 1. Prova estrazione nativa con Apple PDFKit su macOS via osascript JXA
    if sys.platform == "darwin":
        try:
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(pdf_bytes)
                tmp_path = tmp.name

            jxa_script = f"""
            ObjC.import('PDFKit');
            var url = $.NSURL.fileURLWithPath('{tmp_path}');
            var doc = $.PDFDocument.alloc.initWithURL(url);
            if (!doc) {{
                '';
            }} else {{
                var count = doc.pageCount;
                var pages = [];
                for (var i = 0; i < count; i++) {{
                    var p = doc.pageAtIndex(i);
                    if (p) {{
                        var s = p.string;
                        if (s) pages.push(s.js);
                    }}
                }}
                pages.join('\\n\\n=== FINE PAGINA ===\\n\\n');
            }}
            """
            proc = subprocess.run(
                ["osascript", "-l", "JavaScript", "-e", jxa_script],
                capture_output=True,
                text=True,
                timeout=15
            )
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

            if proc.returncode == 0 and proc.stdout.strip():
                return proc.stdout.strip()
        except Exception as e:
            print(f"[PDFParser] Errore estrazione nativa macOS: {e}, provo fallback stream.")

    # 2. Fallback pure-Python (estrazione stream decompressi con zlib)
    return extract_text_pure_python(pdf_bytes)


def extract_text_pure_python(pdf_bytes):
    """Estrazione di fallback da stream PDF compressi o in chiaro in pure-Python."""
    text_chunks = []
    # Cerca tutti i blocchi stream ... endstream
    stream_pattern = re.compile(b"stream[\r\n]+(.*?)[\r\n]+endstream", re.DOTALL)
    for match in stream_pattern.finditer(pdf_bytes):
        raw_stream = match.group(1)
        data = None
        # Prova decompressione Flate/zlib
        try:
            data = zlib.decompress(raw_stream)
        except Exception:
            try:
                data = zlib.decompress(raw_stream, -15)
            except Exception:
                data = raw_stream

        if data:
            # Estrai stringhe tra parentesi (...) o operatori Tj / TJ
            try:
                decoded = data.decode("latin1", errors="ignore")
                # Trova stringhe nei blocchi BT ... ET
                bt_blocks = re.findall(r"BT(.*?)ET", decoded, re.DOTALL)
                for b in bt_blocks:
                    strings = re.findall(r"\((.*?)\)\s*(?:Tj|'|\")", b)
                    if strings:
                        text_chunks.append(" ".join(strings))
                    # Array TJ
                    tj_arrays = re.findall(r"\[(.*?)\]\s*TJ", b)
                    for arr in tj_arrays:
                        arr_strings = re.findall(r"\((.*?)\)", arr)
                        if arr_strings:
                            text_chunks.append(" ".join(arr_strings))
            except Exception:
                pass

    return "\n".join(text_chunks) if text_chunks else ""


def parse_course_catalog_text(text):
    """
    Analizza il testo estratto da un catalogo PDF e individua i corsi,
    con particolare attenzione all'estrazione dei prerequisiti/requisiti di ammissione.
    """
    courses = []
    if not text:
        return courses

    # Normalizza ritorni a capo
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Suddivide il documento in blocchi corso
    # Delimitatori principali: CORSO:, SCHEDA CORSO, CODICE:, o pattern numerati
    pattern = re.compile(
        r"(?:^|\n)(?=(?:CORSO\s*[:\-]|SCHEDA\s+CORSO|MODULO\s*[:\-]|(?:[A-Z]{2,5}-\d{2,4}\b)|(?:\d+\.))\s+[A-ZÀ-Ú])",
        re.IGNORECASE
    )
    raw_sections = pattern.split(text) if pattern.pattern in text else re.split(pattern, text)

    # Se non trova sezioni con quel pattern, prova split su "CORSO"
    if len(raw_sections) <= 1:
        raw_sections = re.split(r"(?=(?:^|\n)\s*CORSO\b)", text, flags=re.IGNORECASE)

    if len(raw_sections) <= 1:
        raw_sections = re.split(r"\n{2,}(?=[A-Z0-9\-\.\s]{4,60}\n)", text)

    for sec in raw_sections:
        sec = sec.strip()
        if len(sec) < 25:
            continue
        # Salta copertine o indici generali
        first_line = sec.splitlines()[0].upper()
        if any(h in first_line for h in ["INDICE", "SOMMARIO", "PREMESSA"]) and "PREREQUISIT" not in sec.upper():
            continue

        course = parse_single_course_block(sec)
        if course and course.get("denominazione"):
            courses.append(course)

    # Se la suddivisione automatica ha trovato pochi corsi, proviamo una scansione alternativa
    if not courses:
        courses = parse_courses_line_by_line(text)

    return courses


def parse_single_course_block(block):
    """Estrae i campi di un singolo blocco di testo corrispondente a un corso."""
    lines = [l.strip() for l in block.splitlines() if l.strip()]
    if not lines:
        return None

    denominazione = ""
    codice_corso = ""
    ente_erogatore = "Ente Istituzionale"
    durata_ore = None
    validita_mesi = None
    prerequisiti = "Nessun prerequisito specifico indicato"
    descrizione = ""

    # Trova titolo ed eventuale codice corso
    for i, line in enumerate(lines[:5]):
        # Codice esplicito (es: Codice: TOP-01)
        cod_match = re.search(r"(?:Cod(?:ice)?\.?|Codice\s+Corso)\s*[:\-]?\s*([A-Z0-9\-_/]+)", line, re.IGNORECASE)
        if cod_match and not codice_corso:
            codice_corso = cod_match.group(1).strip()

        # Se la riga contiene CORSO: Nome
        m_corso = re.search(r"^CORSO(?:\s+DI)?\s*[:\-]?\s*(.+)$", line, re.IGNORECASE)
        if m_corso and not denominazione:
            cand = m_corso.group(1).strip()
            cand = re.sub(r"(?:Cod(?:ice)?\.?|Codice\s+Corso)\s*[:\-]?\s*[A-Z0-9\-_/]+", "", cand, flags=re.IGNORECASE).strip()
            if not any(k in cand.upper() for k in ["CATALOGO", "SOMMARIO", "INDICE"]):
                denominazione = cand
                continue

        # Altro possibile titolo pulito
        if not denominazione:
            clean = re.sub(r"^(?:SCHEDA\s+CORSO|MODULO|N\.\s*\d+)\s*[:\-]?\s*", "", line, flags=re.IGNORECASE).strip()
            clean = re.sub(r"(?:Cod(?:ice)?\.?|Codice\s+Corso)\s*[:\-]?\s*[A-Z0-9\-_/]+", "", clean, flags=re.IGNORECASE).strip()
            if len(clean) >= 4 and not any(k in clean.upper() for k in ["CATALOGO", "SOMMARIO", "INDICE", "PAGINA", "MINISTERO", "COMANDO"]):
                denominazione = clean

    if not denominazione:
        for l in lines:
            if len(l) >= 4 and not any(k in l.lower() for k in ["catalogo", "sommario", "durata:", "ente:", "codice:"]):
                denominazione = l
                break

    # 2. PREREQUISITI / REQUISITI DI AMMISSIONE (Keyword search)
    prereq_pattern = re.compile(
        r"(?:Prerequisit[io]|Requisiti(?:\s+di\s+(?:accesso|ammissione|partecipazione))?|Condizioni\s+di\s+accesso|Propedeuticit[àa]|Titoli\s+richiesti|Requisiti\s+minimi)\s*[:\-\n](.*?)(?=(?:\n\s*(?:Durata|Ente|Validit[àa]|Obiettivi|Descrizione|Periodo|Docenti|Note|Programma|Calendario|CORSO|$)|(?:\s+(?:Descrizione|Durata|Ente|Obiettivi|Validit[àa]))\s*[:\-]))",
        re.IGNORECASE | re.DOTALL
    )
    prereq_match = prereq_pattern.search(block)
    if prereq_match:
        extracted_prereq = prereq_match.group(1).strip()
        extracted_prereq = " ".join(extracted_prereq.split())
        if extracted_prereq:
            prerequisiti = extracted_prereq

    # 3. ENTE EROGATORE
    ente_pattern = re.compile(
        r"(?:Ente(?:\s+erogatore|\s+formativo)?|Svolto\s+presso|Scuola|Comando|Organizzatore)\s*[:\-]?\s*([^\n\r]+)",
        re.IGNORECASE
    )
    ente_match = ente_pattern.search(block)
    if ente_match:
        ente_erogatore = ente_match.group(1).strip()

    # 4. DURATA IN ORE
    durata_match = re.search(r"(?:Durata|Ore)\s*[:\-]?\s*(\d+)\s*(?:ore|h)?", block, re.IGNORECASE)
    if durata_match:
        try:
            durata_ore = int(durata_match.group(1))
        except ValueError:
            pass

    # 5. VALIDITÀ / RINNOVO IN MESI
    validita_match = re.search(r"(?:Validit[àa]|Rinnovo|Scadenza)\s*[:\-]?\s*(\d+)\s*(?:mesi|anni)?", block, re.IGNORECASE)
    if validita_match:
        try:
            num = int(validita_match.group(1))
            if "ann" in block[validita_match.start():validita_match.end() + 10].lower():
                validita_mesi = num * 12
            else:
                validita_mesi = num
        except ValueError:
            pass

    # 6. DESCRIZIONE / OBIETTIVI
    desc_pattern = re.compile(
        r"(?:Descrizione|Obiettivi|Finalit[àa]|Sintesi)\s*[:\-\n](.*?)(?=(?:\n\s*(?:Prerequisiti|Requisiti|Durata|Ente|Validit[àa]|CORSO|$)|(?:\s+(?:Prerequisiti|Requisiti|Durata|Ente|Obiettivi|Validit[àa]))\s*[:\-]))",
        re.IGNORECASE | re.DOTALL
    )
    desc_match = desc_pattern.search(block)
    if desc_match:
        descrizione = " ".join(desc_match.group(1).strip().split())
    else:
        remaining_lines = [l for l in lines[1:] if not any(k in l.lower() for k in ["prerequisit", "requisiti", "durata:", "ente:", "codice:", "validit"])]
        if remaining_lines:
            descrizione = " ".join(remaining_lines[:2])

    if not codice_corso and denominazione:
        clean_name = re.sub(r"[^A-Za-z0-9\s]", "", denominazione)
        words = [w[:3].upper() for w in clean_name.split() if len(w) >= 3][:3]
        prefix = "-".join(words) if words else "COR"
        codice_corso = f"CAT-{prefix}"

    return {
        "codice_corso": codice_corso,
        "denominazione": denominazione,
        "ente_erogatore": ente_erogatore,
        "durata_ore": durata_ore,
        "validita_mesi": validita_mesi,
        "prerequisiti": prerequisiti,
        "descrizione": descrizione
    }


def parse_courses_line_by_line(text):
    """Parser secondario per documenti a elenco o tabellari compatti."""
    courses = []
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    current_course = None
    for line in lines:
        # Identifica inizio corso
        is_title = re.match(r"^(?:[0-9]+\.|\-|\*|[A-Z]{2,4}-\d+)\s+([A-ZÀ-Ú\s]{5,60})", line)
        if is_title:
            if current_course and current_course.get("denominazione"):
                courses.append(current_course)
            title = is_title.group(1).strip()
            current_course = {
                "codice_corso": "",
                "denominazione": title,
                "ente_erogatore": "Ente Istituzionale",
                "durata_ore": None,
                "validita_mesi": None,
                "prerequisiti": "Nessun prerequisito specifico indicato",
                "descrizione": ""
            }
            continue

        if current_course:
            # Check prerequisiti
            p_match = re.search(r"(?:Prerequisit[io]|Requisiti):\s*(.*)", line, re.IGNORECASE)
            if p_match:
                current_course["prerequisiti"] = p_match.group(1).strip()
                continue
            # Check durata
            d_match = re.search(r"Durata:\s*(\d+)\s*ore?", line, re.IGNORECASE)
            if d_match:
                try:
                    current_course["durata_ore"] = int(d_match.group(1))
                except ValueError:
                    pass
                continue
            # Check ente
            e_match = re.search(r"Ente:\s*(.*)", line, re.IGNORECASE)
            if e_match:
                current_course["ente_erogatore"] = e_match.group(1).strip()
                continue

    if current_course and current_course.get("denominazione"):
        courses.append(current_course)

    return courses
