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


# ====================================================================
# PARSER CATALOGHI CORSI DA PDF (STRUTTURATI E NON STRUTTURATI)
# ====================================================================

# Intestazioni e sezioni amministrative o generali da bypassare
ADMIN_SECTION_PATTERNS = [
    r"^\s*STATO\s+MAGGIORE\s+DELLA\s+DIFESA\b",
    r"^\s*PIANO\s+DELL['\’]OFFERTA\s+FORMATIVA\b",
    r"^\s*PREMESSA\b",
    r"^\s*INTRODUZIONE\b",
    r"^\s*DISPOSIZIONI\s+GENERALI\b",
    r"^\s*PARTE\s+GENERALE\b",
    r"^\s*NORME\s+AMMINISTRATIVE\b",
    r"^\s*CRITERI\s+GENERALI\b",
    r"^\s*ONERI\s+FINANZIARI\b",
    r"^\s*VITTO\s+E\s+ALLOGGIO\b",
    r"^\s*TRASPORTI\b",
    r"^\s*CIRCOLARE\b",
    r"^\s*MODALIT[ÀA]\s+AMMINISTRATIVE\b",
    r"^\s*INDICE\b",
    r"^\s*SOMMARIO\b",
    r"^\s*TAVOLA\s+DEI\s+CONTENUTI\b",
    r"^\s*ALLEGATO\s+[A-Z0-9\”\"\']\b",
    r"^\s*NOTE\s+INTRODUTTIVE\b",
    r"^\s*COMUNICAZIONI\s+VARIE\b",
    r"^\s*QUADRO\s+NORMATIVO\b",
    r"^\s*ATTO\s+DI\s+APPROVAZIONE\b",
    r"^\s*REGISTRAZIONE\s+DELLE\s+AGGIUNTE\b",
    r"^\s*PAGINA\s+LASCIATA\s+INTENZIONALMENTE\b"
]


def is_admin_or_general_section(text_block):
    """Verifica se il blocco è una parte generale o amministrativa (senza corsi specifici)."""
    lines = [l.strip() for l in text_block.splitlines() if l.strip()]
    if not lines:
        return True
    first_line = lines[0].upper()
    for pat in ADMIN_SECTION_PATTERNS:
        if re.search(pat, first_line, re.IGNORECASE):
            if not re.search(r"\bCORSO\s*:", text_block, re.IGNORECASE) and \
               not re.search(r"\b(?:1|8)\.\s*SCOPO\b", text_block, re.IGNORECASE):
                return True
    return False


def parse_course_catalog_text(text):
    """
    Analizza il testo estratto da un catalogo PDF (strutturato o reale interforze/CIFIGE)
    e individua i corsi effettivi, separandoli dalle parti descrittive e generali,
    isolando i rispettivi prerequisiti di ammissione.
    """
    courses = []
    if not text:
        return courses

    # Normalizza ritorni a capo
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 1. Suddivisione preliminare: sfrutta eventuali interruzioni di pagina o macro-sezioni
    pages = re.split(r"\n\s*=== FINE PAGINA ===\s*\n", text)
    if len(pages) <= 1:
        pages = [text]

    extracted_blocks = []

    for page in pages:
        page_clean = page.strip()
        if not page_clean:
            continue

        if is_admin_or_general_section(page_clean):
            continue

        # CASO A: Schede stile CIFIGE (con REQUISITI D'AMMISSIONE e SCOPO)
        has_cifige_req = re.search(r"REQUISITI\s+D[’\']AMMISSIONE", page_clean, re.IGNORECASE)
        has_cifige_scopo = re.search(r"(?:1|8)\.\s*SCOPO", page_clean, re.IGNORECASE)
        if has_cifige_req and has_cifige_scopo:
            extracted_blocks.append(page_clean)
            continue

        # CASO B: Delimitatori espliciti di corso (CORSO:, SCHEDA CORSO, MODULO FORMATIVO)
        split_pattern = re.compile(
            r"(?:^|\n)(?=(?:CORSO(?:\s+DI|\s+PER|\s+IN|\s*[:\-])|SCHEDA\s+CORSO|SCHEDA\s+N\.\s*\d+|MODULO\s*FORMATIVO|(?:[A-Z]{2,6}[-_]\d{2,4}\b))\s+[A-ZÀ-Ú])",
            re.IGNORECASE
        )
        sub_blocks = split_pattern.split(page_clean)
        if len(sub_blocks) > 1:
            for sb in sub_blocks:
                sb_clean = sb.strip()
                if len(sb_clean) >= 30 and not is_admin_or_general_section(sb_clean):
                    extracted_blocks.append(sb_clean)
        else:
            # Prova split su "CORSO:"
            c_blocks = re.split(r"(?=(?:^|\n)\s*CORSO\s*:)", page_clean, flags=re.IGNORECASE)
            if len(c_blocks) > 1:
                for cb in c_blocks:
                    cb_clean = cb.strip()
                    if len(cb_clean) >= 30 and not is_admin_or_general_section(cb_clean):
                        extracted_blocks.append(cb_clean)
            else:
                if len(page_clean) >= 35 and not is_admin_or_general_section(page_clean):
                    if re.search(r"\b(?:CORSO|SCHEDA|MODULO)\b", page_clean, re.IGNORECASE):
                        extracted_blocks.append(page_clean)

    # 2. Parsing e validazione euristica dei singoli blocchi
    for block in extracted_blocks:
        course = parse_single_course_block(block)
        if course:
            # Evita duplicati identici
            if not any(existing["denominazione"].lower() == course["denominazione"].lower() for existing in courses):
                courses.append(course)

    return courses


def parse_single_course_block(block):
    """Estrae e valida i campi di un singolo blocco di testo corrispondente a un corso."""
    lines = [l.strip() for l in block.splitlines() if l.strip()]
    if not lines:
        return None

    denominazione = ""
    codice_corso = ""
    ente_erogatore = "Centro Interforze di Formazione Intelligence/G.E. (CIFI/GE)"
    durata_ore = None
    validita_mesi = None
    prerequisiti = ""
    descrizione = ""

    # Creazione snippet originale pulito (primi 300 caratteri del blocco)
    clean_snippet = " ".join(" ".join(lines).split())
    if len(clean_snippet) > 320:
        snippet_origine = clean_snippet[:317] + "..."
    else:
        snippet_origine = clean_snippet

    # 1. VERIFICA SCHEMA CIFIGE (Titolo prima di 1. SCOPO o 8. SCOPO)
    scopo_match = re.search(r"(?:1|8)\.\s*SCOPO", block, re.IGNORECASE)
    req_cifige_match = re.search(r"(?:(?:5|12)\.\s*)?REQUISITI\s+D[’\']AMMISSIONE(.*?)(?=(?:(?:6|13)\.\s*CARATTERISTICHE|\Z))", block, re.IGNORECASE | re.DOTALL)
    if scopo_match and req_cifige_match:
        pre_scopo = block[:scopo_match.start()].strip()
        pre_lines = [l.strip() for l in pre_scopo.splitlines() if l.strip()]
        title_lines = [l for l in pre_lines if not re.match(r"^(?:PAGINA|AREA\s+|PARTE\s+|II\s*[\-\–]|I\s*[\-\–]|\d+$)", l, re.IGNORECASE)]
        raw_tit = " ".join(title_lines) if title_lines else pre_lines[-1]
        raw_tit = re.sub(r"^(?:CORSO\s+DI\s+|CORSO\s+PER\s+|CORSO\s+)", "", raw_tit, flags=re.IGNORECASE).strip()
        denominazione = "Corso " + raw_tit.title()
        denominazione = denominazione.replace("Cno", "CNO").replace("Osint", "OSINT").replace("Aid", "AID").replace("Sigint", "SIGINT").replace("Comint", "COMINT").replace("Elint", "ELINT").replace("Acint", "ACINT").replace("Rme", "RME").replace("Techint", "TECHINT").replace("Iftna", "IFTNA").replace("Humint", "HUMINT").replace("J2", "J2")
        prerequisiti = " ".join([l.strip() for l in req_cifige_match.group(1).splitlines() if l.strip()])

    # 2. TITOLO IN FORMATO STANDARD (es. CORSO: Nome)
    if not denominazione:
        for line in lines[:6]:
            cod_match = re.search(r"(?:Cod(?:ice)?\.?|Codice\s+Corso)\s*[:\-]?\s*([A-Z0-9\-_/]{2,20})", line, re.IGNORECASE)
            if cod_match and not codice_corso:
                codice_corso = cod_match.group(1).strip()

            m_corso = re.search(r"^CORSO(?:\s*[:\-])\s*(.+)$", line, re.IGNORECASE)
            if m_corso and not denominazione:
                denominazione = m_corso.group(1).strip()
                continue

            m_scheda = re.search(r"^(?:SCHEDA\s+CORSO|SCHEDA\s+N\.\s*\d+|MODULO\s+FORMATIVO|DENOMINAZIONE(?:\s+CORSO)?)\s*[:\-]?\s*(.+)$", line, re.IGNORECASE)
            if m_scheda and not denominazione:
                denominazione = m_scheda.group(1).strip()
                continue

    if not denominazione:
        for line in lines[:4]:
            if line.upper().startswith("CORSO ") and len(line) < 90:
                denominazione = line
                break

    if not denominazione or len(denominazione) < 4:
        return None

    # Escludi eventuali frasi burocratiche finite nel titolo
    for pat in ADMIN_SECTION_PATTERNS:
        if re.search(pat, denominazione, re.IGNORECASE):
            return None

    # Codice esplicito nel testo
    if not codice_corso:
        m_cod = re.search(r"(?:Codice|Codice\s+Corso)\s*[:\-]?\s*([A-Z0-9\-_/]{2,20})", block, re.IGNORECASE)
        if m_cod:
            codice_corso = m_cod.group(1).strip()

    # 3. PREREQUISITI / REQUISITI
    if not prerequisiti:
        prereq_pattern = re.compile(
            r"(?:REQUISITI\s+DI\s+ACCESSO(?:\s*/\s*PREREQUISITI)?|REQUISITI\s+D[’\']AMMISSIONE|Prerequisit[io]|Requisiti(?:\s+di\s+(?:accesso|ammissione|partecipazione))?|Condizioni\s+di\s+accesso|Titoli\s+richiesti|Propedeuticit[àa]|Requisiti\s+minimi)\s*[:\-\n]\s*(.*?)(?=(?:\n\s*(?:Durata|Ente|Sede|Validit[àa]|Obiettivi|Finalit[àa]|Scopo|Descrizione|Periodo|Docenti|Note|Programma|Calendario|CORSO|SCHEDA)[^\n\r:]*[:\-]|\Z))",
            re.IGNORECASE | re.DOTALL
        )
        prereq_match = prereq_pattern.search(block)
        if prereq_match:
            prerequisiti = " ".join(prereq_match.group(1).split()).strip()

    if not prerequisiti:
        prerequisiti = "Nessun prerequisito specifico indicato nel catalogo"

    # 4. ENTE EROGATORE
    ente_match = re.search(r"(?:Ente(?:\s+Erogatore|\s+formativo)?|Svolto\s+presso|Sede)\s*[:\-]?\s*([^\n\r]+)", block, re.IGNORECASE)
    if ente_match:
        cand_ente = ente_match.group(1).strip()
        if len(cand_ente) > 2 and not cand_ente.startswith("Pagina"):
            ente_erogatore = cand_ente

    # 5. DURATA IN ORE O SETTIMANE
    durata_settimane = None
    sett_match = re.search(r"(\d+)\s*settiman[ea]\b", block, re.IGNORECASE)
    if sett_match:
        try:
            durata_settimane = int(sett_match.group(1))
        except ValueError:
            pass

    durata_ore_match = re.search(r"(?:Durata|Ore\s+complessive|Ore)\s*[:\-]?\s*(\d+)\s*(?:ore|h)\b", block, re.IGNORECASE)
    if durata_ore_match:
        try:
            durata_ore = int(durata_ore_match.group(1))
        except ValueError:
            pass
    elif durata_settimane:
        durata_ore = durata_settimane * 36
    else:
        giorni_match = re.search(r"(\d+)\s*giorn[io]\b", block, re.IGNORECASE)
        if giorni_match:
            try:
                durata_ore = int(giorni_match.group(1)) * 6
            except ValueError:
                pass
        else:
            gen_match = re.search(r"(?:Durata)\s*[:\-]?\s*(\d+)\b", block, re.IGNORECASE)
            if gen_match:
                try:
                    durata_ore = int(gen_match.group(1))
                except ValueError:
                    pass

    if not durata_ore:
        durata_ore = 72

    if not durata_settimane:
        durata_settimane = max(1, durata_ore // 36)

    # 5.1 VALIDITÀ MESI
    val_match = re.search(r"(?:Validit[àa]|Scadenza)\s*[:\-]?\s*(\d+)\s*(?:mesi|mese|anni|anno)?", block, re.IGNORECASE)
    if val_match:
        try:
            num = int(val_match.group(1))
            ctx = block[val_match.start():val_match.end()+10].lower()
            if "ann" in ctx:
                validita_mesi = num * 12
            else:
                validita_mesi = num
        except ValueError:
            pass

    # 5.2 ESTRAZIONE VOCI STRUTTURATE DEI REQUISITI
    requisiti_sicurezza = ""
    precedenti_formativi = ""
    precedenti_operativi = ""
    selezioni = ""
    conoscenza_lingua = ""
    altri_requisiti = ""

    # Requisiti Sicurezza (NOS)
    nos_m = re.search(r"\b(?:NOS|Nulla\s+Osta\s+di\s+Sicurezza)\b\s*[:\-]?\s*([A-Za-z0-9\s/’'\-]{3,40})", block, re.IGNORECASE)
    if nos_m:
        raw_nos = nos_m.group(1).strip()
        raw_nos = re.split(r'[\n;,\.]|(?:\s+Lingua\b)|(?:\s+Propedeutic\b)', raw_nos, flags=re.IGNORECASE)[0].strip()
        requisiti_sicurezza = f"NOS {raw_nos}" if not raw_nos.upper().startswith("NOS") else raw_nos
    elif "segretissimo" in block.lower() or "cosmic" in block.lower():
        requisiti_sicurezza = "NOS Segretissimo / NATO Cosmic Top Secret"
    elif "segreto" in block.lower() or "nato secret" in block.lower():
        requisiti_sicurezza = "NOS Segreto / NATO Secret"
    elif "riservato" in block.lower():
        requisiti_sicurezza = "NOS Riservato"

    # Precedenti Formativi (Propedeuticità)
    prop_m = re.search(r"(?:Propedeuticit[àa]|Propedeutico|Corsi\s+propedeutici|Precedenti\s+formativi)\s*[:\-]?\s*([^\n;\.]{4,100})", block, re.IGNORECASE)
    if prop_m:
        precedenti_formativi = prop_m.group(1).strip()
    else:
        corsi_trovati = re.findall(r"(?:Corso\s+[A-Z0-9\s/°\-_]{3,40}(?:\([^\)]+\))?)", prerequisiti, re.IGNORECASE)
        if corsi_trovati:
            corsi_filtrati = [ct.strip() for ct in corsi_trovati if ct.strip().lower() != denominazione.lower()]
            if corsi_filtrati:
                precedenti_formativi = ", ".join(dict.fromkeys(corsi_filtrati))

    # Precedenti Operativi
    op_m = re.search(r"((?:\d+\s*mesi|\d+\s*anni)[^\n;\.]{3,70}(?:impiego|esperienza|servizio)[^\n;\.]*)", block, re.IGNORECASE)
    if op_m:
        precedenti_operativi = op_m.group(1).strip()

    # Selezioni
    sel_m = re.search(r"(?:Prove\s+selettive|Selezioni|Idoneit[àa]\s+psicofisica|Idoneit[àa]\s+al\s+volo|Test\s+d[’\']ingresso|Protocollo\s+fonti\s+umane)[^\n;\.]{0,80}", block, re.IGNORECASE)
    if sel_m:
        selezioni = sel_m.group(0).strip()

    # Conoscenza Lingua
    lingua_m = re.search(r"(?:NATO\s+(?:JFLT|SLP)[^\n;\.]{0,35}|Lingua\s+inglese[^\n;\.]{0,40}|Inglese\s+livello[^\n;\.]{0,20})", block, re.IGNORECASE)
    if lingua_m:
        conoscenza_lingua = lingua_m.group(0).strip()

    # Altri Requisiti (Patenti, note caratteristiche)
    altri_list = []
    pat_m = re.search(r"(?:Patente\s+(?:Militare\s+)?(?:Mod\.?\s*\d+|cat\.?\s*[A-Z0-9]+))", block, re.IGNORECASE)
    if pat_m:
        altri_list.append(pat_m.group(0).strip())
    if "superiore alla media" in block.lower():
        altri_list.append("Valutazione caratteristica non inferiore a 'Superiore alla Media'")
    if "sanzioni di rigore" in block.lower():
        altri_list.append("Assenza di sanzioni disciplinari di rigore o procedimenti penali")
    if altri_list:
        altri_requisiti = "; ".join(altri_list)

    # 6. DESCRIZIONE / SCOPO
    desc_match = re.search(r"(?:SCOPO(?:\s+E\s+DESCRIZIONE)?|Descrizione|Obiettivi(?:\s+didattici)?|Finalit[àa]|Scopo(?:\s+del\s+corso)?)\s*[:\-\n]\s*(.*?)(?=(?:\n\s*(?:Prerequisiti|Requisiti|Durata|Ente|Sede|Validit[àa]|Destinatari|Programma|CORSO|SCHEDA|2\.\s*PROFILO)[^\n\r:]*[:\-]|\Z))", block, re.IGNORECASE | re.DOTALL)
    if desc_match:
        descrizione = " ".join(desc_match.group(1).split()).strip()

    # Genera codice se assente
    if not codice_corso:
        clean_name = re.sub(r"[^A-Za-z0-9\s]", "", denominazione)
        words = [w[:3].upper() for w in clean_name.split() if len(w) >= 3][:3]
        prefix = "-".join(words) if words else "COR"
        codice_corso = f"CAT-{prefix}"

    return {
        "codice_corso": codice_corso,
        "denominazione": denominazione,
        "ente_erogatore": ente_erogatore,
        "durata_settimane": durata_settimane,
        "durata_ore": durata_ore,
        "validita_mesi": validita_mesi,
        "requisiti_sicurezza": requisiti_sicurezza,
        "precedenti_formativi": precedenti_formativi,
        "precedenti_operativi": precedenti_operativi,
        "selezioni": selezioni,
        "conoscenza_lingua": conoscenza_lingua,
        "altri_requisiti": altri_requisiti,
        "prerequisiti": prerequisiti,
        "descrizione": descrizione,
        "snippet_origine": snippet_origine
    }

