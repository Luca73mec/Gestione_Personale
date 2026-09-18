/**
 * Gestione Personale Web - Client Application Logic
 * Architettura Single Page Application (SPA) in Vanilla JS nativo
 */

const AppState = {
  currentView: 'dashboard',
  currentPersonId: null,
  activeDetailTab: 'anagrafica',
  personaleCache: [],
  corsiCache: [],
  modalCorsoMode: 'catalogo',
  extractedPdfCourses: [],
  extractedPdfFilename: '',
  planMilitariCache: [],
  planCorsiCache: [],
  lastAuditResult: null
};

// ====================================================================
// API UTILITIES
// ====================================================================
async function api(url, method = 'GET', data = null) {
  const options = {
    method,
    headers: { 'Content-Type': 'application/json' }
  };
  if (data && (method === 'POST' || method === 'PUT')) {
    options.body = JSON.stringify(data);
  }

  try {
    const res = await fetch(url, options);
    const json = await res.json();
    if (!res.ok || json.success === false) {
      throw new Error(json.error || `Errore HTTP ${res.status}`);
    }
    return json;
  } catch (err) {
    console.error(`[API Error] ${method} ${url}:`, err);
    showToast(err.message, 'danger');
    throw err;
  }
}

// ====================================================================
// FORMATTERS & HELPERS
// ====================================================================
function formatDate(dateString) {
  if (!dateString) return '-';
  try {
    const parts = dateString.split('-');
    if (parts.length === 3) {
      return `${parts[2]}/${parts[1]}/${parts[0]}`;
    }
    return dateString;
  } catch {
    return dateString;
  }
}

function addDaysToDate(dateStr, days = 365) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return '';
  d.setDate(d.getDate() + days);
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  return `${yyyy}-${mm}-${dd}`;
}

function renderBadgeScadenza(stato, giorni) {
  if (!stato || stato === 'REGOLARE') {
    return `<span class="badge badge-regolare">✓ Regolare (${giorni > 0 ? giorni + ' gg' : 'In corso'})</span>`;
  }
  if (stato === 'SCADUTA' || stato === 'SCADUTO') {
    const ritardo = Math.abs(giorni || 0);
    return `<span class="badge badge-scaduta">⚠️ SCADUTA (${ritardo} gg fa)</span>`;
  }
  if (stato === 'URGENTE_30GG') {
    return `<span class="badge badge-urgente">⏳ Scade tra ${giorni} gg</span>`;
  }
  if (stato === 'IN_SCADENZA_60GG' || stato === 'IN_SCADENZA_90GG') {
    return `<span class="badge badge-urgente">📅 Scade tra ${giorni} gg</span>`;
  }
  return `<span class="badge badge-neutral">${stato}</span>`;
}

function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast ${type === 'danger' ? 'bg-danger' : ''}`;
  toast.innerText = message;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// ====================================================================
// MODAL CONTROLLERS
// ====================================================================
function openModal(id) {
  const modal = document.getElementById(id);
  if (modal) {
    modal.classList.add('active');
  }
}

function closeModal(id) {
  const modal = document.getElementById(id);
  if (modal) {
    modal.classList.remove('active');
  }
}

// ====================================================================
// ROUTING & VIEW NAVIGATION
// ====================================================================
function navigate(viewName, params = {}) {
  AppState.currentView = viewName;

  // Update navigation links
  document.querySelectorAll('.nav-link').forEach(link => {
    link.classList.toggle('active', link.dataset.view === viewName);
  });

  const views = ['dashboard', 'personale', 'dettaglio-personale', 'scadenzario', 'corsi', 'pianificazione'];
  views.forEach(v => {
    const el = document.getElementById(`view-${v}`);
    if (el) el.style.display = (v === viewName) ? 'block' : 'none';
  });

  const pageTitle = document.getElementById('page-title-text');
  const pageSubtitle = document.getElementById('page-subtitle-text');

  if (viewName === 'dashboard') {
    pageTitle.innerText = 'Cruscotto di Controllo';
    pageSubtitle.innerText = 'Panoramica generale del personale e monitoraggio delle scadenze';
    loadDashboard();
  } else if (viewName === 'personale') {
    pageTitle.innerText = 'Ruolo del Personale';
    pageSubtitle.innerText = 'Elenco dipendenti, qualifiche e consultazione rapida fascicoli';
    loadPersonaleList();
  } else if (viewName === 'dettaglio-personale') {
    AppState.currentPersonId = params.id;
    pageTitle.innerText = 'Fascicolo Personale';
    pageSubtitle.innerText = 'Anagrafica completa, storico note caratteristiche, corsi e patenti';
    loadDettaglioPersonale(params.id);
  } else if (viewName === 'scadenzario') {
    pageTitle.innerText = 'Scadenzario Generale';
    pageSubtitle.innerText = 'Riepilogo scadenze imminenti e scadute per note caratteristiche, patenti e passaporti';
    loadScadenzario().then(() => {
      if (params && params.section) {
        setTimeout(() => {
          const sec = document.getElementById(`scadenzario-${params.section}`);
          if (sec) sec.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 60);
      }
    });
  } else if (viewName === 'corsi') {
    pageTitle.innerText = 'Catalogo Formazione e Corsi';
    pageSubtitle.innerText = 'Gestione corsi interni, enti erogatori e abilitazioni periodiche';
    loadCorsiCatalogo();
  } else if (viewName === 'pianificazione') {
    pageTitle.innerText = 'Pianificazione Corsi';
    pageSubtitle.innerText = 'Verifica dei prerequisiti e idoneità alla candidatura corsi per il personale';
    loadPianificazioneCorsi(params);
  }
}

// ====================================================================
// 1. DASHBOARD
// ====================================================================
async function loadDashboard() {
  try {
    const res = await api('/api/dashboard');
    const stats = res.data;

    document.getElementById('stat-totale-personale').innerText = stats.totale_personale;
    document.getElementById('stat-note-scadute').innerText = stats.note_scadute;
    document.getElementById('stat-note-urgenti').innerText = stats.note_urgenti_30;
    document.getElementById('stat-patenti-scadenza').innerText = stats.patenti_in_scadenza + stats.patenti_scadute;
    document.getElementById('stat-passaporti-scadenza').innerText = stats.passaporti_in_scadenza;
    document.getElementById('stat-totale-corsi').innerText = stats.totale_corsi;

    // Badge nel menu laterale
    const alertCount = stats.note_scadute + stats.note_urgenti_30;
    const badgeNote = document.getElementById('nav-badge-note');
    if (badgeNote) {
      if (alertCount > 0) {
        badgeNote.innerText = alertCount;
        badgeNote.style.display = 'inline-block';
      } else {
        badgeNote.style.display = 'none';
      }
    }

    // Carica anteprima scadenze nella dashboard
    const scadenzeRes = await api('/api/scadenzario');
    renderDashboardTables(scadenzeRes.data);
  } catch (err) {
    console.error("Errore caricamento dashboard:", err);
  }
}

function renderDashboardTables(data) {
  const noteTbody = document.getElementById('dash-table-note');
  if (!data.note || data.note.length === 0) {
    noteTbody.innerHTML = `<tr><td colspan="6" class="text-center" style="padding: 24px; color: var(--slate-400);">Tutte le note caratteristiche sono regolari. Nessuna scadenza critica nei prossimi 60 giorni.</td></tr>`;
  } else {
    noteTbody.innerHTML = data.note.map(n => `
      <tr>
        <td><strong>${n.grado_qualifica}</strong> ${n.cognome} ${n.nome}</td>
        <td><code>${n.matricola}</code></td>
        <td>${n.tipologia_documento}</td>
        <td>${formatDate(n.data_prossima_scadenza)}</td>
        <td>${renderBadgeScadenza(n.stato_scadenza, n.giorni_alla_scadenza)}</td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="navigate('dettaglio-personale', {id: ${n.personale_id}})">Fascicolo</button>
        </td>
      </tr>
    `).join('');
  }

  const docTbody = document.getElementById('dash-table-altri-doc');
  const altriDocs = [];
  (data.patenti || []).forEach(p => {
    altriDocs.push({
      persona: `${p.grado_qualifica} ${p.cognome} ${p.nome}`,
      personale_id: p.personale_id,
      tipo: `Patente ${p.tipo_patente} (${p.categoria})`,
      numero: p.numero_patente,
      scadenza: p.data_scadenza,
      stato: p.stato_scadenza,
      giorni: p.giorni_alla_scadenza
    });
  });
  (data.passaporti || []).forEach(ps => {
    altriDocs.push({
      persona: `${ps.grado_qualifica} ${ps.cognome} ${ps.nome}`,
      personale_id: ps.personale_id,
      tipo: `Passaporto ${ps.tipo_passaporto}`,
      numero: ps.numero_passaporto,
      scadenza: ps.data_scadenza,
      stato: ps.stato_scadenza,
      giorni: ps.giorni_alla_scadenza
    });
  });

  if (altriDocs.length === 0) {
    docTbody.innerHTML = `<tr><td colspan="5" class="text-center" style="padding: 24px; color: var(--slate-400);">Nessuna patente o passaporto in scadenza immediata.</td></tr>`;
  } else {
    docTbody.innerHTML = altriDocs.map(d => `
      <tr>
        <td><strong>${d.persona}</strong></td>
        <td>${d.tipo} <br><small style="color: var(--slate-500);">${d.numero}</small></td>
        <td>${formatDate(d.scadenza)}</td>
        <td>${renderBadgeScadenza(d.stato, d.giorni)}</td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="navigate('dettaglio-personale', {id: ${d.personale_id}})">Fascicolo</button>
        </td>
      </tr>
    `).join('');
  }
}

// ====================================================================
// 2. ELENCO PERSONALE
// ====================================================================
async function loadPersonaleList() {
  const search = document.getElementById('search-personale').value;
  const reparto = document.getElementById('filter-reparto').value;
  const stato = document.getElementById('filter-stato').value;

  let url = '/api/personale?';
  if (search) url += `search=${encodeURIComponent(search)}&`;
  if (reparto) url += `reparto=${encodeURIComponent(reparto)}&`;
  if (stato) url += `stato=${encodeURIComponent(stato)}&`;

  try {
    const res = await api(url);
    AppState.personaleCache = res.data;
    renderPersonaleTable(res.data);
  } catch (err) {
    console.error("Errore caricamento lista personale:", err);
  }
}

function renderPersonaleTable(items) {
  const tbody = document.getElementById('table-personale-body');
  if (!items || items.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" class="text-center" style="padding: 32px; color: var(--slate-400);">Nessun dipendente trovato con i criteri selezionati.</td></tr>`;
    return;
  }

  tbody.innerHTML = items.map(p => `
    <tr>
      <td><strong>${p.grado_qualifica}</strong></td>
      <td><strong>${p.cognome}</strong> ${p.nome}</td>
      <td><code>${p.matricola}</code></td>
      <td>${p.reparto_ufficio}</td>
      <td>
        <span class="badge ${p.stato_servizio === 'In Servizio' ? 'badge-regolare' : 'badge-neutral'}">
          ${p.stato_servizio}
        </span>
      </td>
      <td>
        ${p.prossima_scadenza_nota ? `
          <div>${formatDate(p.prossima_scadenza_nota)}</div>
          <div>${renderBadgeScadenza(p.stato_nota, p.giorni_scadenza_nota)}</div>
        ` : '<span style="color: var(--slate-400);">-</span>'}
      </td>
      <td>
        <span class="badge badge-info" title="Patenti possedute">${p.num_patenti} Pat.</span>
        <span class="badge badge-neutral" title="Corsi completati">${p.num_corsi} Corsi</span>
        ${p.num_passaporti > 0 ? '<span class="badge badge-regolare" title="Passaporto di Servizio">PS</span>' : ''}
      </td>
      <td style="white-space: nowrap;">
        <div style="display: flex; gap: 6px; align-items: center;">
          <button class="btn btn-primary btn-sm" onclick="navigate('dettaglio-personale', {id: ${p.id}})" title="Apri Fascicolo">
            Apri Fascicolo
          </button>
          <button class="btn btn-danger btn-sm" onclick="eliminaPersonaleDaRuolo(${p.id})" title="Elimina militare dal ruolo">
            🗑️ Elimina
          </button>
        </div>
      </td>
    </tr>
  `).join('');
}

// ====================================================================
// 3. DETTAGLIO PERSONALE (SCHEDA COMPLETA)
// ====================================================================
async function loadDettaglioPersonale(id) {
  try {
    const res = await api(`/api/personale/${id}`);
    const p = res.data;
    AppState.currentPersonData = p;

    // Aggiorna intestazione hero
    document.getElementById('det-nome-completo').innerText = `${p.grado_qualifica} ${p.cognome} ${p.nome}`;
    document.getElementById('det-sottotitolo').innerText = `Matricola: ${p.matricola} | Reparto: ${p.reparto_ufficio} ${p.posto_tabellare ? ' | Posto Tabellare: ' + p.posto_tabellare : ''} ${p.incarico ? ' | Incarico: ' + p.incarico : ''}`;
    document.getElementById('det-stato-badge').innerHTML = `
      <span class="badge ${p.stato_servizio === 'In Servizio' ? 'badge-regolare' : 'badge-neutral'}">${p.stato_servizio}</span>
      <span class="badge badge-info">CF: ${p.codice_fiscale}</span>
      <span class="badge" style="background:#fee2e2; color:#991b1b; font-weight:700;">🛡️ NOS: ${p.livello_nos || 'Riservato'}</span>
      <span class="badge" style="background:#fef3c7; color:#92400e; font-weight:700;">🗣️ Lingua: ${p.lingua_inglese || 'Standard'}</span>
    `;

    // 1. Tab Anagrafica
    document.getElementById('anag-cf').innerText = p.codice_fiscale;
    document.getElementById('anag-nascita').innerText = `${formatDate(p.data_nascita)} a ${p.luogo_nascita} (${p.provincia_nascita || '-'})`;
    document.getElementById('anag-sesso').innerText = p.sesso === 'M' ? 'Maschile' : (p.sesso === 'F' ? 'Femminile' : p.sesso);
    document.getElementById('anag-arruolamento').innerText = formatDate(p.data_arruolamento_assunzione);
    document.getElementById('anag-reparto').innerText = p.reparto_ufficio || '-';
    document.getElementById('anag-incarico').innerText = p.incarico || '-';
    document.getElementById('anag-posto-tabellare').innerText = p.posto_tabellare || '-';
    document.getElementById('anag-residenza').innerText = p.indirizzo_residenza || '-';
    document.getElementById('anag-email-ist').innerText = p.email_istituzionale || '-';
    document.getElementById('anag-email-pers').innerText = p.email_personale || '-';
    document.getElementById('anag-telefono').innerText = p.telefono || '-';
    const nosEl = document.getElementById('anag-nos');
    if (nosEl) nosEl.innerText = p.livello_nos || 'Riservato';
    const lingEl = document.getElementById('anag-lingua');
    if (lingEl) lingEl.innerText = p.lingua_inglese || 'Standard (NATO JFLT 8)';
    document.getElementById('anag-note').innerText = p.note_generali || 'Nessuna annotazione particolare.';

    // 2. Tab Note Caratteristiche
    renderNoteTab(p.note_caratteristiche, p);

    // 3. Tab Patenti
    renderPatentiTab(p.patenti);

    // 4. Tab Passaporti
    renderPassaportiTab(p.passaporti);

    // 5. Tab Corsi
    renderCorsiTab(p.corsi);

    // Imposta tab attivo predefinito
    switchDetailTab(AppState.activeDetailTab || 'anagrafica');

  } catch (err) {
    console.error("Errore caricamento dettaglio personale:", err);
  }
}

function switchDetailTab(tabName) {
  AppState.activeDetailTab = tabName;
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === tabName);
  });
  const tabs = ['anagrafica', 'note', 'patenti', 'passaporti', 'corsi'];
  tabs.forEach(t => {
    const el = document.getElementById(`tab-content-${t}`);
    if (el) el.style.display = (t === tabName) ? 'block' : 'none';
  });
}

function renderNoteTab(noteList, p) {
  const container = document.getElementById('note-summary-card');
  const tableBody = document.getElementById('table-note-body');

  if (!noteList || noteList.length === 0) {
    container.innerHTML = `
      <div class="alert-banner warning">
        <div>
          <strong>Nessuna nota caratteristica registrata</strong>
          <p>Non risultano ancora documenti caratteristici o schede valutative inserite per questo dipendente.</p>
        </div>
      </div>
    `;
    tableBody.innerHTML = `<tr><td colspan="7" class="text-center" style="padding: 24px; color: var(--slate-400);">Nessun documento caratteristico a fascicolo.</td></tr>`;
    return;
  }

  // Ultima nota (la più recente)
  const ultima = noteList[0];
  container.innerHTML = `
    <div class="card" style="border-left: 4px solid var(--primary); background: var(--slate-50);">
      <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 16px;">
        <div>
          <span style="font-size: 11px; text-transform: uppercase; font-weight: 700; color: var(--slate-500);">Situazione Ultima Valutazione</span>
          <h4 style="font-size: 18px; margin: 4px 0;">${ultima.tipologia_documento} (${ultima.motivo_redazione})</h4>
          <p style="font-size: 13.5px; color: var(--slate-600);">
            Periodo valutato: <strong>${formatDate(ultima.periodo_dal)} - ${formatDate(ultima.periodo_al)}</strong><br>
            Data firma presa visione: <strong>${formatDate(ultima.data_firma_interessato)}</strong> | Giudizio: <strong>${ultima.giudizio_finale || 'N.D.'}</strong>
          </p>
        </div>
        <div style="text-align: right;">
          <div style="font-size: 11px; text-transform: uppercase; font-weight: 700; color: var(--slate-500);">Scadenza Prossima Nota (365 gg)</div>
          <div style="font-size: 20px; font-weight: 700; margin: 4px 0;">${formatDate(ultima.data_prossima_scadenza)}</div>
          <div>${renderBadgeScadenza(ultima.stato_scadenza, ultima.giorni_alla_scadenza)}</div>
        </div>
      </div>
    </div>
  `;

  tableBody.innerHTML = noteList.map(n => `
    <tr>
      <td><strong>${n.tipologia_documento}</strong></td>
      <td>${n.motivo_redazione}</td>
      <td>${formatDate(n.periodo_dal)} - ${formatDate(n.periodo_al)}</td>
      <td>${formatDate(n.data_firma_interessato)}</td>
      <td>
        <strong>${formatDate(n.data_prossima_scadenza)}</strong>
        <div>${renderBadgeScadenza(n.stato_scadenza, n.giorni_alla_scadenza)}</div>
      </td>
      <td><strong>${n.giudizio_finale || '-'}</strong></td>
      <td>
        <button class="btn btn-secondary btn-sm" onclick="eliminaNota(${n.id})">Elimina</button>
      </td>
    </tr>
  `).join('');
}

function renderPatentiTab(patentiList) {
  const tbody = document.getElementById('table-patenti-body');
  if (!patentiList || patentiList.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="text-center" style="padding: 24px; color: var(--slate-400);">Nessuna patente di guida registrata.</td></tr>`;
    return;
  }

  tbody.innerHTML = patentiList.map(p => `
    <tr>
      <td><span class="badge ${p.tipo_patente === 'Civile' ? 'badge-info' : 'badge-neutral'}">${p.tipo_patente}</span></td>
      <td><strong>${p.categoria}</strong></td>
      <td><code>${p.numero_patente}</code></td>
      <td>${p.ente_rilascio}</td>
      <td>${formatDate(p.data_rilascio)}</td>
      <td>
        <strong>${formatDate(p.data_scadenza)}</strong>
        <div>${renderBadgeScadenza(p.stato_scadenza, p.giorni_alla_scadenza)}</div>
      </td>
      <td>${p.limitazioni_abilitazioni || '-'}</td>
      <td>
        <button class="btn btn-secondary btn-sm" onclick="eliminaPatente(${p.id})">Elimina</button>
      </td>
    </tr>
  `).join('');
}

function renderPassaportiTab(passaportiList) {
  const tbody = document.getElementById('table-passaporti-body');
  if (!passaportiList || passaportiList.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" class="text-center" style="padding: 24px; color: var(--slate-400);">Nessun passaporto di servizio registrato.</td></tr>`;
    return;
  }

  tbody.innerHTML = passaportiList.map(ps => `
    <tr>
      <td><code>${ps.numero_passaporto}</code></td>
      <td>${ps.tipo_passaporto}</td>
      <td>${formatDate(ps.data_rilascio)}</td>
      <td>
        <strong>${formatDate(ps.data_scadenza)}</strong>
        <div>${renderBadgeScadenza(ps.stato_scadenza, ps.giorni_alla_scadenza)}</div>
      </td>
      <td><span class="badge ${ps.stato === 'Valido' ? 'badge-regolare' : 'badge-urgente'}">${ps.stato}</span></td>
      <td>${ps.ubicazione_custodia}</td>
      <td>${ps.autorita_rilascio}</td>
      <td>
        <button class="btn btn-secondary btn-sm" onclick="eliminaPassaporto(${ps.id})">Elimina</button>
      </td>
    </tr>
  `).join('');
}

function renderCorsiTab(corsiList) {
  const tbody = document.getElementById('table-corsi-frequentati-body');
  if (!corsiList || corsiList.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="text-center" style="padding: 24px; color: var(--slate-400);">Nessun corso frequentato registrato.</td></tr>`;
    return;
  }

  tbody.innerHTML = corsiList.map(c => `
    <tr>
      <td><strong>${c.denominazione}</strong> <br><small style="color: var(--slate-500);">Cod: ${c.codice_corso}</small></td>
      <td>${c.ente_erogatore}</td>
      <td>${formatDate(c.data_inizio)} - ${formatDate(c.data_fine)}</td>
      <td><span class="badge badge-regolare">${c.esito}</span></td>
      <td><code>${c.numero_attestato || '-'}</code></td>
      <td>${c.data_scadenza_abilitazione ? formatDate(c.data_scadenza_abilitazione) : 'Permanente'}</td>
      <td>
        <button class="btn btn-secondary btn-sm" onclick="eliminaPartecipazione(${c.id})">Elimina</button>
      </td>
    </tr>
  `).join('');
}

// ====================================================================
// 4. SCADENZARIO GENERALE
// ====================================================================
async function loadScadenzario() {
  try {
    const res = await api('/api/scadenzario');
    const data = res.data;

    // Tabella Note
    const tbodyNote = document.getElementById('scad-table-note');
    if (!data.note || data.note.length === 0) {
      tbodyNote.innerHTML = `<tr><td colspan="6" class="text-center" style="padding: 24px; color: var(--slate-400);">Nessuna nota caratteristica scaduta o in scadenza entro 60 giorni.</td></tr>`;
    } else {
      tbodyNote.innerHTML = data.note.map(n => `
        <tr>
          <td><strong>${n.grado_qualifica}</strong> ${n.cognome} ${n.nome}</td>
          <td><code>${n.matricola}</code></td>
          <td>${n.tipologia_documento}</td>
          <td>${formatDate(n.data_prossima_scadenza)}</td>
          <td>${renderBadgeScadenza(n.stato_scadenza, n.giorni_alla_scadenza)}</td>
          <td>
            <button class="btn btn-primary btn-sm" onclick="navigate('dettaglio-personale', {id: ${n.personale_id}})">Fascicolo</button>
          </td>
        </tr>
      `).join('');
    }

    // Tabella Patenti
    const tbodyPatenti = document.getElementById('scad-table-patenti');
    if (!data.patenti || data.patenti.length === 0) {
      tbodyPatenti.innerHTML = `<tr><td colspan="6" class="text-center" style="padding: 24px; color: var(--slate-400);">Nessuna patente in scadenza.</td></tr>`;
    } else {
      tbodyPatenti.innerHTML = data.patenti.map(p => `
        <tr>
          <td><strong>${p.grado_qualifica}</strong> ${p.cognome} ${p.nome}</td>
          <td><span class="badge ${p.tipo_patente === 'Civile' ? 'badge-info' : 'badge-neutral'}">${p.tipo_patente}</span> (${p.categoria})</td>
          <td><code>${p.numero_patente}</code></td>
          <td>${formatDate(p.data_scadenza)}</td>
          <td>${renderBadgeScadenza(p.stato_scadenza, p.giorni_alla_scadenza)}</td>
          <td>
            <button class="btn btn-secondary btn-sm" onclick="navigate('dettaglio-personale', {id: ${p.personale_id}})">Fascicolo</button>
          </td>
        </tr>
      `).join('');
    }

    // Tabella Passaporti
    const tbodyPassaporti = document.getElementById('scad-table-passaporti');
    if (!data.passaporti || data.passaporti.length === 0) {
      tbodyPassaporti.innerHTML = `<tr><td colspan="6" class="text-center" style="padding: 24px; color: var(--slate-400);">Nessun passaporto di servizio in scadenza.</td></tr>`;
    } else {
      tbodyPassaporti.innerHTML = data.passaporti.map(ps => `
        <tr>
          <td><strong>${ps.grado_qualifica}</strong> ${ps.cognome} ${ps.nome}</td>
          <td><code>${ps.numero_passaporto}</code></td>
          <td>${ps.ubicazione_custodia}</td>
          <td>${formatDate(ps.data_scadenza)}</td>
          <td>${renderBadgeScadenza(ps.stato_scadenza, ps.giorni_alla_scadenza)}</td>
          <td>
            <button class="btn btn-secondary btn-sm" onclick="navigate('dettaglio-personale', {id: ${ps.personale_id}})">Fascicolo</button>
          </td>
        </tr>
      `).join('');
    }

  } catch (err) {
    console.error("Errore caricamento scadenzario:", err);
  }
}

// ====================================================================
// 5. CATALOGO CORSI
// ====================================================================
async function loadCorsiCatalogo() {
  try {
    const res = await api('/api/corsi');
    AppState.corsiCache = res.data;
    const tbody = document.getElementById('table-corsi-catalogo-body');

    if (!res.data || res.data.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center" style="padding: 24px; color: var(--slate-400);">Nessun corso presente a catalogo.</td></tr>`;
      return;
    }

    tbody.innerHTML = res.data.map(c => {
      const durText = (c.durata_settimane ? `<strong>${c.durata_settimane} sett.</strong> ` : '') + (c.durata_ore ? `<span style="color:var(--slate-600);">(${c.durata_ore} h)</span>` : '-');
      
      // Costruzione blocchi requisiti con etichetta posta immediatamente sopra ciascun tag
      const reqBlocks = [];

      // 1. Requisito Sicurezza (NOS)
      const sicVal = c.requisiti_sicurezza ? c.requisiti_sicurezza : 'Nessuno prescritto';
      const sicBg = c.requisiti_sicurezza ? '#fee2e2' : '#f1f5f9';
      const sicColor = c.requisiti_sicurezza ? '#991b1b' : '#64748b';
      reqBlocks.push(`
        <div style="margin-bottom: 7px; line-height: 1.2;">
          <span style="font-size: 10px; font-weight: 700; color: #991b1b; text-transform: uppercase; letter-spacing: 0.3px; display: block; margin-bottom: 2px;">🛡️ Requisito Sicurezza (NOS)</span>
          <span class="badge" style="background:${sicBg}; color:${sicColor}; font-size: 11px; font-weight: 600; display: inline-block;">${sicVal}</span>
        </div>
      `);

      // 2. Precedenti Formativi (Propedeuticità)
      const formVal = c.precedenti_formativi ? c.precedenti_formativi : 'Nessuno (Accesso Diretto)';
      const formBg = c.precedenti_formativi && !c.precedenti_formativi.toLowerCase().startsWith('nessun') ? '#dbeafe' : '#f1f5f9';
      const formColor = c.precedenti_formativi && !c.precedenti_formativi.toLowerCase().startsWith('nessun') ? '#1e40af' : '#64748b';
      reqBlocks.push(`
        <div style="margin-bottom: 7px; line-height: 1.2;">
          <span style="font-size: 10px; font-weight: 700; color: #1e40af; text-transform: uppercase; letter-spacing: 0.3px; display: block; margin-bottom: 2px;">🎓 Precedenti Formativi</span>
          <span class="badge" style="background:${formBg}; color:${formColor}; font-size: 11px; font-weight: 600; display: inline-block;">${formVal}</span>
        </div>
      `);

      // 3. Conoscenza Lingua
      const lingVal = c.conoscenza_lingua ? c.conoscenza_lingua : 'Standard istituzionale';
      const lingBg = c.conoscenza_lingua && !['standard', 'nessuna'].includes(c.conoscenza_lingua.toLowerCase()) ? '#fef3c7' : '#f1f5f9';
      const lingColor = c.conoscenza_lingua && !['standard', 'nessuna'].includes(c.conoscenza_lingua.toLowerCase()) ? '#92400e' : '#64748b';
      reqBlocks.push(`
        <div style="margin-bottom: 7px; line-height: 1.2;">
          <span style="font-size: 10px; font-weight: 700; color: #92400e; text-transform: uppercase; letter-spacing: 0.3px; display: block; margin-bottom: 2px;">🗣️ Conoscenza Lingua</span>
          <span class="badge" style="background:${lingBg}; color:${lingColor}; font-size: 11px; font-weight: 600; display: inline-block;">${lingVal}</span>
        </div>
      `);

      // 4. Altri Requisiti / Patenti
      if (c.altri_requisiti) {
        reqBlocks.push(`
          <div style="margin-bottom: 7px; line-height: 1.2;">
            <span style="font-size: 10px; font-weight: 700; color: #6b21a8; text-transform: uppercase; letter-spacing: 0.3px; display: block; margin-bottom: 2px;">🪪 Altri Requisiti / Patenti</span>
            <span class="badge" style="background:#f3e8ff; color:#6b21a8; font-size: 11px; font-weight: 600; display: inline-block;">${c.altri_requisiti}</span>
          </div>
        `);
      }

      // 5. Precedenti Operativi (se indicati)
      if (c.precedenti_operativi) {
        reqBlocks.push(`
          <div style="margin-bottom: 7px; line-height: 1.2;">
            <span style="font-size: 10px; font-weight: 700; color: #475569; text-transform: uppercase; letter-spacing: 0.3px; display: block; margin-bottom: 2px;">⏱️ Precedenti Operativi</span>
            <span class="badge" style="background:#f1f5f9; color:#475569; font-size: 11px; font-weight: 600; display: inline-block;">${c.precedenti_operativi}</span>
          </div>
        `);
      }

      // 6. Selezioni Speciali (se indicate)
      if (c.selezioni) {
        reqBlocks.push(`
          <div style="margin-bottom: 7px; line-height: 1.2;">
            <span style="font-size: 10px; font-weight: 700; color: #9f1239; text-transform: uppercase; letter-spacing: 0.3px; display: block; margin-bottom: 2px;">🩺 Selezioni Speciali</span>
            <span class="badge" style="background:#fef2f2; color:#b91c1c; font-size: 11px; font-weight: 600; display: inline-block;">${c.selezioni}</span>
          </div>
        `);
      }

      const dataInserimentoStr = formatDateTime(c.created_at);

      return `
      <tr>
        <td><code style="font-size:12px; font-weight:700; color:var(--primary);">${c.codice_corso}</code></td>
        <td>
          <strong style="font-size: 14px; color: var(--slate-900);">${c.denominazione}</strong>
          <div style="font-size: 11.5px; color: var(--slate-500); margin-top: 4px;">
            🕒 Inserito: ${dataInserimentoStr}
          </div>
        </td>
        <td>${c.ente_erogatore}</td>
        <td>
          ${durText}
          ${c.validita_mesi ? '<br><small style="color: var(--slate-500);">' + c.validita_mesi + ' mesi rinnovo</small>' : '<br><small style="color: var(--slate-500);">Permanente</small>'}
        </td>
        <td style="padding: 12px 10px;">
          <div style="font-size: 12px;">
            ${reqBlocks.join('')}
          </div>
        </td>
        <td>
          <span class="badge badge-info">${c.num_partecipanti || 0} part.</span>
          ${c.fonte_catalogo && c.fonte_catalogo !== 'Manuale' ? `<br><small style="color: var(--slate-500); font-size: 11px;" title="Importato da PDF">📄 ${c.fonte_catalogo}</small>` : ''}
        </td>
        <td style="text-align: center; white-space: nowrap;">
          <button class="btn btn-outline-primary btn-sm" onclick="visualizzaSchedaCorso(${c.id})" title="Visualizza Scheda Monografica del Corso" style="margin-right: 4px; font-weight: 600;">
            📋 Scheda Corso
          </button>
          <button class="btn btn-secondary btn-sm" onclick="apriModaleModificaCorso(${c.id})" title="Modifica corso" style="margin-right: 4px;">
            ✏️ Modifica
          </button>
          <button class="btn btn-danger btn-sm" onclick="eliminaCorsoCatalogo(${c.id})" title="Elimina corso dal catalogo">
            🗑️ Elimina
          </button>
        </td>
      </tr>
      `;
    }).join('');
  } catch (err) {
    console.error("Errore caricamento catalogo corsi:", err);
  }
}

function formatDateTime(dateStr) {
  if (!dateStr) return 'Data non disp.';
  try {
    const d = new Date(dateStr.replace(' ', 'T'));
    if (isNaN(d.getTime())) return dateStr;
    const day = String(d.getDate()).padStart(2, '0');
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const year = d.getFullYear();
    const hours = String(d.getHours()).padStart(2, '0');
    const minutes = String(d.getMinutes()).padStart(2, '0');
    return `${day}/${month}/${year} ore ${hours}:${minutes}`;
  } catch (e) {
    return dateStr;
  }
}

function visualizzaSchedaCorso(id) {
  const c = (AppState.corsiCache || []).find(x => x.id === id);
  if (!c) return;

  document.getElementById('sc-codice').textContent = c.codice_corso || '-';
  document.getElementById('sc-titolo').textContent = c.denominazione || '-';
  document.getElementById('sc-data-inserimento').textContent = `Inserito il ${formatDateTime(c.created_at)}`;
  document.getElementById('sc-fonte').textContent = c.fonte_catalogo || 'Manuale';
  document.getElementById('sc-ente').textContent = c.ente_erogatore || '-';

  const durParts = [];
  if (c.durata_settimane) durParts.push(`${c.durata_settimane} Settimane`);
  if (c.durata_ore) durParts.push(`${c.durata_ore} Ore complessive`);
  document.getElementById('sc-durata').textContent = durParts.length > 0 ? durParts.join(' / ') : 'Non specificata';

  document.getElementById('sc-validita').textContent = c.validita_mesi ? `${c.validita_mesi} mesi (Rinnovo periodico)` : 'Permanente (Senza scadenza)';
  document.getElementById('sc-partecipanti').textContent = `${c.num_partecipanti || 0} militari registrati`;

  document.getElementById('sc-sicurezza').textContent = c.requisiti_sicurezza || 'Nessun vincolo formale';
  document.getElementById('sc-formativi').textContent = c.precedenti_formativi || 'Nessuno (Accesso diretto)';
  document.getElementById('sc-lingua').textContent = c.conoscenza_lingua || 'Standard istituzionale';
  document.getElementById('sc-altri').textContent = c.altri_requisiti || 'Nessun requisito supplementare';

  const boxOp = document.getElementById('sc-box-op');
  if (boxOp) {
    if (c.precedenti_operativi) {
      boxOp.style.display = 'block';
      document.getElementById('sc-operativi').textContent = c.precedenti_operativi;
    } else {
      boxOp.style.display = 'none';
    }
  }

  const boxSel = document.getElementById('sc-box-sel');
  if (boxSel) {
    if (c.selezioni) {
      boxSel.style.display = 'block';
      document.getElementById('sc-selezioni').textContent = c.selezioni;
    } else {
      boxSel.style.display = 'none';
    }
  }

  document.getElementById('sc-descrizione').textContent = c.descrizione || 'Nessuna descrizione o scopo didattico specificato a catalogo.';

  const rawPrereqBox = document.getElementById('sc-box-prereq-raw');
  if (rawPrereqBox) {
    if (c.prerequisiti) {
      rawPrereqBox.style.display = 'block';
      document.getElementById('sc-prerequisiti-raw').textContent = c.prerequisiti;
    } else {
      rawPrereqBox.style.display = 'none';
    }
  }

  openModal('modal-scheda-corso');
}

function stampaSchedaCorso() {
  window.print();
}

async function apriModaleModificaCorso(id) {
  let c = (AppState.corsiCache || []).find(x => x.id === id);
  if (!c) {
    try {
      const res = await api(`/api/corsi/${id}`);
      c = res.data;
    } catch (err) {
      console.error("Errore recupero dati corso:", err);
      return;
    }
  }
  if (!c) return;

  document.getElementById('edit-cat-id').value = c.id;
  document.getElementById('edit-cat-codice').value = c.codice_corso || '';
  document.getElementById('edit-cat-nome').value = c.denominazione || '';
  document.getElementById('edit-cat-ente').value = c.ente_erogatore || '';
  document.getElementById('edit-cat-settimane').value = c.durata_settimane || '';
  document.getElementById('edit-cat-ore').value = c.durata_ore || '';
  document.getElementById('edit-cat-validita').value = c.validita_mesi || '';
  document.getElementById('edit-cat-sicurezza').value = c.requisiti_sicurezza || '';
  document.getElementById('edit-cat-formativi').value = c.precedenti_formativi || '';
  document.getElementById('edit-cat-operativi').value = c.precedenti_operativi || '';
  document.getElementById('edit-cat-selezioni').value = c.selezioni || '';
  document.getElementById('edit-cat-lingua').value = c.conoscenza_lingua || '';
  document.getElementById('edit-cat-altri').value = c.altri_requisiti || '';
  document.getElementById('edit-cat-prerequisiti').value = c.prerequisiti || '';
  document.getElementById('edit-cat-desc').value = c.descrizione || '';

  openModal('modal-modifica-catalogo-corso');
}

async function eliminaCorsoCatalogo(id) {
  const c = (AppState.corsiCache || []).find(x => x.id === id);
  const nomeCorso = c ? `il corso "${c.denominazione}" (${c.codice_corso || 'ID ' + id})` : 'questo corso';
  const numPart = c && c.num_partecipanti ? c.num_partecipanti : 0;

  let msg = `Confermi l'eliminazione definitiva dal catalogo de ${nomeCorso}?`;
  if (numPart > 0) {
    msg = `ATTENZIONE: ${nomeCorso} risulta registrato nello storico di ${numPart} militare/i.\n\nEliminando il corso dal catalogo verranno rimosse anche le relative registrazioni collegate nei fascicoli.\n\nSei sicuro di voler procedere con l'eliminazione definitiva?`;
  }

  if (confirm(msg)) {
    try {
      await api(`/api/corsi/${id}`, 'DELETE');
      showToast('Corso rimosso dal catalogo con successo', 'success');
      loadCorsiCatalogo();
    } catch (err) {
      console.error(err);
    }
  }
}

// Popola il menu a tendina dei corsi nel modale di iscrizione corso
async function popolaSelectCorsi() {
  try {
    setModalCorsoMode('catalogo');
    const res = await api('/api/corsi');
    AppState.corsiCache = res.data;
    const sel = document.getElementById('corso-select-id');
    sel.innerHTML = `<option value="">-- Seleziona un corso a catalogo --</option>` +
      res.data.map(c => `<option value="${c.id}">${c.denominazione} (${c.ente_erogatore})</option>`).join('');

    onCorsoCatalogoSelected();
  } catch (err) {
    console.error("Errore popolamento select corsi:", err);
  }
}

// Quando un corso viene selezionato dal menu a tendina, mostra subito i suoi prerequisiti
function onCorsoCatalogoSelected() {
  const sel = document.getElementById('corso-select-id');
  const box = document.getElementById('box-corso-prerequisiti-selected');
  const txtPrereq = document.getElementById('txt-corso-prerequisiti');
  const txtMeta = document.getElementById('txt-corso-meta');
  if (!sel || !box) return;

  const corsoId = parseInt(sel.value);
  if (!corsoId || !AppState.corsiCache) {
    box.style.display = 'none';
    return;
  }

  const c = AppState.corsiCache.find(x => x.id === corsoId);
  if (c) {
    txtPrereq.innerText = c.prerequisiti || 'Nessun prerequisito specifico indicato.';
    let meta = `Ente: ${c.ente_erogatore}`;
    if (c.durata_ore) meta += ` | Durata: ${c.durata_ore} ore`;
    if (c.validita_mesi) meta += ` | Validità rinnovo: ${c.validita_mesi} mesi`;
    txtMeta.innerText = meta;
    box.style.display = 'block';
  } else {
    box.style.display = 'none';
  }
}

// Switch modalità tra Catalogo Esistente e Inserimento Manuale
function setModalCorsoMode(mode) {
  AppState.modalCorsoMode = mode;
  const btnCat = document.getElementById('btn-mode-corso-cat');
  const btnMan = document.getElementById('btn-mode-corso-man');
  const sezCat = document.getElementById('sezione-corso-catalogo');
  const sezMan = document.getElementById('sezione-corso-manuale');
  const selCat = document.getElementById('corso-select-id');
  const inMan = document.getElementById('man-corso-nome');

  if (mode === 'catalogo') {
    btnCat.classList.add('active');
    btnMan.classList.remove('active');
    sezCat.style.display = 'block';
    sezMan.style.display = 'none';
    selCat.setAttribute('required', 'required');
    inMan.removeAttribute('required');
    onCorsoCatalogoSelected();
  } else {
    btnMan.classList.add('active');
    btnCat.classList.remove('active');
    sezMan.style.display = 'block';
    sezCat.style.display = 'none';
    inMan.setAttribute('required', 'required');
    selCat.removeAttribute('required');
  }
}

// ====================================================================
// 6. PIANIFICAZIONE CORSI & AUDIT PREREQUISITI
// ====================================================================

async function loadPianificazioneCorsi(params = {}) {
  try {
    const [resPers, resCorsi] = await Promise.all([
      api('/api/personale'),
      api('/api/corsi')
    ]);

    AppState.planMilitariCache = resPers.data || [];
    AppState.planCorsiCache = resCorsi.data || [];

    renderPlanMilitariSelect(AppState.planMilitariCache);
    renderPlanCorsiSelect(AppState.planCorsiCache);

    if (params.personale_id) {
      const selM = document.getElementById('plan-select-militare');
      if (selM) {
        selM.value = params.personale_id;
        await onPlanMilitareChange();
      }
    }

    if (params.corso_id) {
      const selC = document.getElementById('plan-select-corso');
      if (selC) {
        selC.value = params.corso_id;
        await onPlanCorsoChange();
      }
    }
  } catch (err) {
    console.error("Errore inizializzazione modulo pianificazione:", err);
  }
}

function renderPlanMilitariSelect(militariList) {
  const sel = document.getElementById('plan-select-militare');
  if (!sel) return;
  const currentVal = sel.value;

  sel.innerHTML = '<option value="">-- Seleziona un militare --</option>' +
    militariList.map(m => {
      const repShort = (m.reparto_ufficio || '').replace('Ufficio ', 'Uff. ').replace('Sezione ', 'Sez. ');
      return `<option value="${m.id}">${m.grado_qualifica} ${m.cognome} ${m.nome} - ${repShort} (${m.matricola})</option>`;
    }).join('');

  if (currentVal && militariList.some(m => m.id == currentVal)) {
    sel.value = currentVal;
  }
}

function renderPlanCorsiSelect(corsiList) {
  const sel = document.getElementById('plan-select-corso');
  if (!sel) return;
  const currentVal = sel.value;

  sel.innerHTML = '<option value="">-- Seleziona un corso a catalogo --</option>' +
    corsiList.map(c => {
      const ore = c.durata_ore ? ` [${c.durata_ore}h]` : '';
      const cod = c.codice_corso ? `[${c.codice_corso}] ` : '';
      return `<option value="${c.id}">${cod}${c.denominazione}${ore} (${c.ente_erogatore})</option>`;
    }).join('');

  if (currentVal && corsiList.some(c => c.id == currentVal)) {
    sel.value = currentVal;
  }
}

function filterPlanMilitari(searchTerm) {
  const term = (searchTerm || '').trim().toLowerCase();
  if (!term) {
    renderPlanMilitariSelect(AppState.planMilitariCache);
    return;
  }
  const filtered = AppState.planMilitariCache.filter(m => {
    return (m.cognome && m.cognome.toLowerCase().includes(term)) ||
           (m.nome && m.nome.toLowerCase().includes(term)) ||
           (m.matricola && m.matricola.toLowerCase().includes(term)) ||
           (m.grado_qualifica && m.grado_qualifica.toLowerCase().includes(term)) ||
           (m.reparto_ufficio && m.reparto_ufficio.toLowerCase().includes(term));
  });
  renderPlanMilitariSelect(filtered);
}

function filterPlanCorsi(searchTerm) {
  const term = (searchTerm || '').trim().toLowerCase();
  if (!term) {
    renderPlanCorsiSelect(AppState.planCorsiCache);
    return;
  }
  const filtered = AppState.planCorsiCache.filter(c => {
    return (c.denominazione && c.denominazione.toLowerCase().includes(term)) ||
           (c.codice_corso && c.codice_corso.toLowerCase().includes(term)) ||
           (c.ente_erogatore && c.ente_erogatore.toLowerCase().includes(term)) ||
           (c.prerequisiti && c.prerequisiti.toLowerCase().includes(term));
  });
  renderPlanCorsiSelect(filtered);
}

async function onPlanMilitareChange() {
  const sel = document.getElementById('plan-select-militare');
  const card = document.getElementById('plan-card-militare');
  const auditBox = document.getElementById('plan-audit-container');
  if (!sel || !card) return;

  const pid = (sel.value || '').trim();
  if (!pid || pid === 'undefined' || pid === 'null') {
    card.style.display = 'none';
    if (auditBox) auditBox.style.display = 'none';
    return;
  }

  try {
    const res = await api(`/api/personale/${encodeURIComponent(pid)}`);
    const p = res.data;
    if (!p) return;

    document.getElementById('plan-m-nome').textContent = `${p.cognome} ${p.nome}`;
    document.getElementById('plan-m-grado').textContent = `${p.grado_qualifica} | Matricola: ${p.matricola}`;
    document.getElementById('plan-m-reparto').textContent = p.reparto_ufficio || '-';
    document.getElementById('plan-m-incarico').textContent = p.incarico || '-';
    document.getElementById('plan-m-posto').textContent = p.posto_tabellare || '-';

    const nosEl = document.getElementById('plan-m-nos');
    if (nosEl) nosEl.textContent = p.livello_nos || 'Riservato';
    const linguaEl = document.getElementById('plan-m-lingua');
    if (linguaEl) linguaEl.textContent = p.lingua_inglese || 'NATO JFLT 8';

    const statoBadge = document.getElementById('plan-m-stato-badge');
    if (p.stato_servizio === 'In Servizio') {
      statoBadge.className = 'badge badge-success';
      statoBadge.textContent = 'In Servizio Attivo';
    } else {
      statoBadge.className = 'badge badge-danger';
      statoBadge.textContent = p.stato_servizio || 'Non Attivo';
    }

    const badgesContainer = document.getElementById('plan-m-badges');
    let badgesHtml = '';
    (p.patenti || []).forEach(pat => {
      const isScad = pat.stato_scadenza === 'SCADUTA';
      badgesHtml += `<span class="badge ${isScad ? 'badge-danger' : 'badge-info'}" style="font-size: 11px;">🪪 ${pat.categoria}</span>`;
    });
    const superati = (p.corsi || []).filter(c => ['Superato', 'Idoneo', 'Qualificato', 'Specializzato'].includes(c.esito));
    if (superati.length > 0) {
      badgesHtml += `<span class="badge badge-success" style="font-size: 11px;">🎓 ${superati.length} corsi superati</span>`;
    }
    badgesContainer.innerHTML = badgesHtml;
    card.style.display = 'block';

    checkAndRunPlanAudit();
  } catch (err) {
    console.error("Errore caricamento dettaglio militare per pianificazione:", err);
  }
}

async function onPlanCorsoChange() {
  const sel = document.getElementById('plan-select-corso');
  const card = document.getElementById('plan-card-corso');
  const auditBox = document.getElementById('plan-audit-container');
  if (!sel || !card) return;

  const cid = (sel.value || '').trim();
  if (!cid || cid === 'undefined' || cid === 'null') {
    card.style.display = 'none';
    if (auditBox) auditBox.style.display = 'none';
    return;
  }

  const c = (AppState.planCorsiCache || []).find(x => x.id == cid || (x.codice_corso && x.codice_corso.toLowerCase() === cid.toLowerCase()));
  if (c) {
    renderPlanCorsoCard(c);
  } else {
    try {
      const res = await api(`/api/corsi/${encodeURIComponent(cid)}`);
      renderPlanCorsoCard(res.data);
    } catch (err) {
      console.warn("Corso non reperibile dal catalogo:", err);
      card.style.display = 'none';
    }
  }

  checkAndRunPlanAudit();
}

function renderPlanCorsoCard(c) {
  const card = document.getElementById('plan-card-corso');
  if (!card || !c) return;

  document.getElementById('plan-c-codice').textContent = c.codice_corso || 'COR-GEN';
  document.getElementById('plan-c-nome').textContent = c.denominazione;

  let durText = '';
  if (c.durata_settimane) durText += `${c.durata_settimane} Sett. `;
  if (c.durata_ore) durText += `(${c.durata_ore} Ore)`;
  if (!durText) durText = 'N/D';
  document.getElementById('plan-c-ore-badge').textContent = durText;

  document.getElementById('plan-c-ente').textContent = c.ente_erogatore || '-';
  document.getElementById('plan-c-validita').textContent = c.validita_mesi ? `${c.validita_mesi} mesi` : 'Permanente / Senza Scadenza';

  const elSic = document.getElementById('plan-c-sicurezza');
  if (elSic) elSic.textContent = c.requisiti_sicurezza || 'Standard (Riservato)';

  const elForm = document.getElementById('plan-c-formativi');
  if (elForm) elForm.textContent = c.precedenti_formativi || 'Nessuno prescritto';

  const elLing = document.getElementById('plan-c-lingua');
  if (elLing) elLing.textContent = c.conoscenza_lingua || 'Standard';

  const boxOp = document.getElementById('plan-c-box-op');
  const elOp = document.getElementById('plan-c-operativi');
  if (boxOp && elOp) {
    if (c.precedenti_operativi) {
      boxOp.style.display = 'block';
      elOp.textContent = c.precedenti_operativi;
    } else {
      boxOp.style.display = 'none';
    }
  }

  const boxSel = document.getElementById('plan-c-box-sel');
  const elSel = document.getElementById('plan-c-selezioni');
  if (boxSel && elSel) {
    if (c.selezioni) {
      boxSel.style.display = 'block';
      elSel.textContent = c.selezioni;
    } else {
      boxSel.style.display = 'none';
    }
  }

  const boxAltri = document.getElementById('plan-c-box-altri');
  const elAltri = document.getElementById('plan-c-altri');
  if (boxAltri && elAltri) {
    if (c.altri_requisiti) {
      boxAltri.style.display = 'block';
      elAltri.textContent = c.altri_requisiti;
    } else {
      boxAltri.style.display = 'none';
    }
  }

  card.style.display = 'block';
}

function checkAndRunPlanAudit() {
  const selM = document.getElementById('plan-select-militare');
  const selC = document.getElementById('plan-select-corso');
  const mVal = selM ? (selM.value || '').trim() : '';
  const cVal = selC ? (selC.value || '').trim() : '';

  if (mVal && cVal && mVal !== 'undefined' && cVal !== 'undefined' && mVal !== 'null' && cVal !== 'null') {
    eseguiVerificaCandidatura(mVal, cVal);
  } else {
    const auditBox = document.getElementById('plan-audit-container');
    if (auditBox) auditBox.style.display = 'none';
  }
}

async function eseguiVerificaCandidatura(personaleId, corsoId) {
  const auditBox = document.getElementById('plan-audit-container');
  if (!auditBox) return;

  const pId = (personaleId || '').toString().trim();
  const cId = (corsoId || '').toString().trim();
  if (!pId || !cId || pId === 'undefined' || cId === 'undefined' || pId === 'null' || cId === 'null') {
    auditBox.style.display = 'none';
    return;
  }

  try {
    const res = await api(`/api/corsi/verifica-candidatura?personale_id=${encodeURIComponent(pId)}&corso_id=${encodeURIComponent(cId)}`);
    const data = res.data;
    AppState.lastAuditResult = data;

    // 1. Badge Globale
    const globalBadge = document.getElementById('plan-audit-global-badge');
    let badgeHtml = '';
    if (data.esito_globale === 'IDONEO') {
      badgeHtml = `<span class="badge badge-success" style="font-size: 14px; padding: 6px 14px;">🟢 ${data.badge_label} (${data.percentuale_conformita}%)</span>`;
    } else if (data.esito_globale === 'IDONEO_CON_RISERVA') {
      badgeHtml = `<span class="badge badge-warning" style="font-size: 14px; padding: 6px 14px;">🟡 ${data.badge_label} (${data.percentuale_conformita}%)</span>`;
    } else {
      badgeHtml = `<span class="badge badge-danger" style="font-size: 14px; padding: 6px 14px;">🔴 ${data.badge_label} (${data.percentuale_conformita}%)</span>`;
    }
    globalBadge.innerHTML = badgeHtml;

    // 2. Banner Sintetico
    const banner = document.getElementById('plan-audit-banner');
    const bTitle = document.getElementById('plan-audit-banner-title');
    const bDesc = document.getElementById('plan-audit-banner-desc');

    banner.className = `alert-banner ${data.badge_class === 'success' ? 'success' : (data.badge_class === 'warning' ? 'warning' : 'danger')}`;
    if (data.esito_globale === 'IDONEO') {
      bTitle.textContent = `✅ CANDIDATURA IDONEA: ${data.personale.grado_qualifica} ${data.personale.nominativo}`;
      bDesc.textContent = `Tutti i requisiti per il corso "${data.corso.denominazione}" risultano soddisfatti nel libretto matricolare.`;
    } else if (data.esito_globale === 'IDONEO_CON_RISERVA') {
      bTitle.textContent = `⚠️ CANDIDATURA AMMISSIBILE CON RISERVA: ${data.personale.grado_qualifica} ${data.personale.nominativo}`;
      bDesc.textContent = `Sono presenti prerequisiti qualitativi o scadenze imminenti che richiedono accertamento d'ufficio prima dell'invio al corso.`;
    } else {
      bTitle.textContent = `❌ CANDIDATURA NON IDONEA: ${data.personale.grado_qualifica} ${data.personale.nominativo}`;
      bDesc.textContent = `Sono stati riscontrati requisiti bloccanti non soddisfatti (es. corso propedeutico non effettuato, patente assente o scaduta, stato matricolare non attivo).`;
    }

    // 3. Tabella Checklist Requisiti
    const tbody = document.getElementById('plan-audit-tbody');
    tbody.innerHTML = (data.checks || []).map(chk => {
      let statusBadge = '';
      if (chk.esito === 'SODDISFATTO') {
        statusBadge = '<span class="badge badge-success" style="font-size:12px;">✓ Soddisfatto</span>';
      } else if (chk.esito === 'CONSEGUITO_RINNOVO') {
        statusBadge = '<span class="badge" style="background:#e0f2fe; color:#0369a1; font-size:12px;">Aggiornamento</span>';
      } else if (chk.esito === 'GIA_CONSEGUITO') {
        statusBadge = '<span class="badge badge-warning" style="font-size:12px;">Già Conseguito</span>';
      } else if (chk.esito === 'IN_SCADENZA') {
        statusBadge = '<span class="badge badge-warning" style="font-size:12px;">⚠️ In Scadenza</span>';
      } else if (chk.esito === 'DA_VERIFICARE') {
        statusBadge = '<span class="badge badge-warning" style="font-size:12px;">🔍 Da Verificare</span>';
      } else if (chk.esito === 'AVVISO') {
        statusBadge = '<span class="badge badge-warning" style="font-size:12px;">Avviso</span>';
      } else {
        statusBadge = '<span class="badge badge-danger" style="font-size:12px;">✗ Bloccante</span>';
      }

      return `
        <tr>
          <td><strong style="color: var(--slate-800);">${chk.categoria}</strong></td>
          <td>${chk.regola}</td>
          <td style="color: var(--slate-700);">${chk.riscontro}</td>
          <td style="text-align: center;">${statusBadge}</td>
        </tr>
      `;
    }).join('');

    // 4. Raccomandazioni
    const recoBox = document.getElementById('plan-audit-raccomandazioni-box');
    const recoList = document.getElementById('plan-audit-raccomandazioni-list');
    if (data.raccomandazioni && data.raccomandazioni.length > 0) {
      recoList.innerHTML = data.raccomandazioni.map(r => `<li style="margin-bottom: 4px;">${r}</li>`).join('');
      recoBox.style.display = 'block';
    } else {
      recoBox.style.display = 'none';
    }

    // 5. Pulsante Iscrizione
    const btnIscrivi = document.getElementById('btn-iscrivi-da-pianificazione');
    const footnote = document.getElementById('plan-audit-footnote');
    if (data.esito_globale === 'NON_IDONEO') {
      footnote.textContent = '⚠️ Requisiti bloccanti non soddisfatti: l\'iscrizione è sconsigliata fino a regolarizzazione.';
      btnIscrivi.className = 'btn btn-secondary';
      btnIscrivi.textContent = 'Forza Comunque Iscrizione';
    } else {
      footnote.textContent = 'Tutto pronto: puoi procedere direttamente alla formalizzazione dell\'iscrizione.';
      btnIscrivi.className = 'btn btn-primary';
      btnIscrivi.textContent = '🚀 Procedi con l\'Iscrizione / Candidatura';
    }

    auditBox.style.display = 'block';
    auditBox.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  } catch (err) {
    console.error("Errore durante l'audit di idoneità:", err);
  }
}

function resetPianificazione() {
  const selM = document.getElementById('plan-select-militare');
  const selC = document.getElementById('plan-select-corso');
  const searchM = document.getElementById('plan-search-militare');
  const searchC = document.getElementById('plan-search-corso');
  const cardM = document.getElementById('plan-card-militare');
  const cardC = document.getElementById('plan-card-corso');
  const auditBox = document.getElementById('plan-audit-container');

  if (selM) selM.value = '';
  if (selC) selC.value = '';
  if (searchM) searchM.value = '';
  if (searchC) searchC.value = '';
  if (cardM) cardM.style.display = 'none';
  if (cardC) cardC.style.display = 'none';
  if (auditBox) auditBox.style.display = 'none';

  renderPlanMilitariSelect(AppState.planMilitariCache);
  renderPlanCorsiSelect(AppState.planCorsiCache);
  AppState.lastAuditResult = null;
}

async function avviaIscrizioneDaPianificazione() {
  if (!AppState.lastAuditResult) return;
  const { personale, corso } = AppState.lastAuditResult;

  AppState.currentPersonId = personale.id;
  await popolaSelectCorsi();

  const selCorso = document.getElementById('corso-select-id');
  if (selCorso) {
    selCorso.value = corso.id;
    onCorsoCatalogoSelected();
  }

  openModal('modal-nuovo-corso-persona');
}

// ====================================================================
// GESTIONE FORM & MODALI (SUBMISSION & CANCELLAZIONE)
// ====================================================================

// --- Inserimento Personale ---
function setupPersonaleForm() {
  const form = document.getElementById('form-nuovo-personale');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = {
      matricola: document.getElementById('p-matricola').value.trim(),
      codice_fiscale: document.getElementById('p-cf').value.trim(),
      cognome: document.getElementById('p-cognome').value.trim(),
      nome: document.getElementById('p-nome').value.trim(),
      sesso: document.getElementById('p-sesso').value,
      data_nascita: document.getElementById('p-nascita').value,
      luogo_nascita: document.getElementById('p-luogo-nascita').value.trim(),
      provincia_nascita: document.getElementById('p-provincia-nascita').value.trim(),
      grado_qualifica: document.getElementById('p-grado').value.trim(),
      reparto_ufficio: document.getElementById('p-reparto').value,
      incarico: document.getElementById('p-incarico').value.trim(),
      posto_tabellare: document.getElementById('p-posto-tabellare').value.trim(),
      stato_servizio: document.getElementById('p-stato').value,
      livello_nos: document.getElementById('p-nos') ? document.getElementById('p-nos').value : 'Riservato',
      lingua_inglese: document.getElementById('p-lingua') ? document.getElementById('p-lingua').value.trim() : 'NATO JFLT 8',
      data_arruolamento_assunzione: document.getElementById('p-arruolamento').value,
      email_istituzionale: document.getElementById('p-email-ist').value.trim(),
      email_personale: document.getElementById('p-email-pers').value.trim(),
      telefono: document.getElementById('p-telefono').value.trim(),
      indirizzo_residenza: document.getElementById('p-residenza').value.trim(),
      note_generali: document.getElementById('p-note').value.trim()
    };

    try {
      const res = await api('/api/personale', 'POST', data);
      showToast('Nuovo operatore registrato con successo!', 'success');
      closeModal('modal-nuovo-personale');
      form.reset();
      navigate('dettaglio-personale', { id: res.id });
    } catch (err) {
      // Toast già gestito
    }
  });
}

// --- Apertura Modale Modifica Personale ---
function openModificaPersonaleModal() {
  const p = AppState.currentPersonData;
  if (!p) return;
  document.getElementById('edit-p-matricola').value = p.matricola || '';
  document.getElementById('edit-p-cf').value = p.codice_fiscale || '';
  document.getElementById('edit-p-cognome').value = p.cognome || '';
  document.getElementById('edit-p-nome').value = p.nome || '';
  document.getElementById('edit-p-grado').value = p.grado_qualifica || '';
  document.getElementById('edit-p-reparto').value = p.reparto_ufficio || 'Ufficio Piani ed Intelligence';
  document.getElementById('edit-p-incarico').value = p.incarico || '';
  document.getElementById('edit-p-posto-tabellare').value = p.posto_tabellare || '';
  document.getElementById('edit-p-stato').value = p.stato_servizio || 'In Servizio';
  if (document.getElementById('edit-p-nos')) {
    document.getElementById('edit-p-nos').value = p.livello_nos || 'Riservato';
  }
  if (document.getElementById('edit-p-lingua')) {
    document.getElementById('edit-p-lingua').value = p.lingua_inglese || '';
  }
  document.getElementById('edit-p-nascita').value = p.data_nascita || '';
  document.getElementById('edit-p-sesso').value = p.sesso || 'M';
  document.getElementById('edit-p-luogo-nascita').value = p.luogo_nascita || '';
  document.getElementById('edit-p-provincia-nascita').value = p.provincia_nascita || '';
  document.getElementById('edit-p-arruolamento').value = p.data_arruolamento_assunzione || '';
  document.getElementById('edit-p-telefono').value = p.telefono || '';
  document.getElementById('edit-p-email-ist').value = p.email_istituzionale || '';
  document.getElementById('edit-p-email-pers').value = p.email_personale || '';
  document.getElementById('edit-p-residenza').value = p.indirizzo_residenza || '';
  document.getElementById('edit-p-note').value = p.note_generali || '';
  openModal('modal-modifica-personale');
}

// --- Modifica Personale ---
function setupModificaPersonaleForm() {
  const form = document.getElementById('form-modifica-personale');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = {
      matricola: document.getElementById('edit-p-matricola').value.trim(),
      codice_fiscale: document.getElementById('edit-p-cf').value.trim(),
      cognome: document.getElementById('edit-p-cognome').value.trim(),
      nome: document.getElementById('edit-p-nome').value.trim(),
      sesso: document.getElementById('edit-p-sesso').value,
      data_nascita: document.getElementById('edit-p-nascita').value,
      luogo_nascita: document.getElementById('edit-p-luogo-nascita').value.trim(),
      provincia_nascita: document.getElementById('edit-p-provincia-nascita').value.trim(),
      grado_qualifica: document.getElementById('edit-p-grado').value.trim(),
      reparto_ufficio: document.getElementById('edit-p-reparto').value,
      incarico: document.getElementById('edit-p-incarico').value.trim(),
      posto_tabellare: document.getElementById('edit-p-posto-tabellare').value.trim(),
      stato_servizio: document.getElementById('edit-p-stato').value,
      livello_nos: document.getElementById('edit-p-nos') ? document.getElementById('edit-p-nos').value : 'Riservato',
      lingua_inglese: document.getElementById('edit-p-lingua') ? document.getElementById('edit-p-lingua').value.trim() : 'NATO JFLT 8',
      data_arruolamento_assunzione: document.getElementById('edit-p-arruolamento').value,
      email_istituzionale: document.getElementById('edit-p-email-ist').value.trim(),
      email_personale: document.getElementById('edit-p-email-pers').value.trim(),
      telefono: document.getElementById('edit-p-telefono').value.trim(),
      indirizzo_residenza: document.getElementById('edit-p-residenza').value.trim(),
      note_generali: document.getElementById('edit-p-note').value.trim()
    };

    try {
      await api(`/api/personale/${AppState.currentPersonId}`, 'PUT', data);
      showToast('Dati operatore aggiornati con successo!', 'success');
      closeModal('modal-modifica-personale');
      loadDettaglioPersonale(AppState.currentPersonId);
    } catch (err) {
      // Toast già gestito
    }
  });
}

// --- Inserimento Patente ---
function setupPatenteForm() {
  const form = document.getElementById('form-nuova-patente');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = {
      tipo_patente: document.getElementById('pat-tipo').value,
      categoria: document.getElementById('pat-categoria').value,
      numero_patente: document.getElementById('pat-numero').value,
      ente_rilascio: document.getElementById('pat-ente').value,
      data_rilascio: document.getElementById('pat-rilascio').value,
      data_scadenza: document.getElementById('pat-scadenza').value,
      limitazioni_abilitazioni: document.getElementById('pat-limitazioni').value
    };

    try {
      await api(`/api/personale/${AppState.currentPersonId}/patente`, 'POST', data);
      showToast('Patente registrata con successo!', 'success');
      closeModal('modal-nuova-patente');
      form.reset();
      loadDettaglioPersonale(AppState.currentPersonId);
    } catch (err) {}
  });
}

// --- Inserimento Nota Caratteristica ---
function setupNotaForm() {
  const form = document.getElementById('form-nuova-nota');
  const inputPeriodoAl = document.getElementById('nota-periodo-al');
  const inputScadenza = document.getElementById('nota-scadenza');

  // Calcolo automatico della scadenza prossima nota (+365 giorni dal termine del periodo valutato)
  inputPeriodoAl.addEventListener('change', () => {
    if (inputPeriodoAl.value) {
      inputScadenza.value = addDaysToDate(inputPeriodoAl.value, 365);
    }
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = {
      tipologia_documento: document.getElementById('nota-tipo').value,
      motivo_redazione: document.getElementById('nota-motivo').value,
      periodo_dal: document.getElementById('nota-periodo-dal').value,
      periodo_al: document.getElementById('nota-periodo-al').value,
      data_firma_interessato: document.getElementById('nota-firma').value,
      data_prossima_scadenza: document.getElementById('nota-scadenza').value || addDaysToDate(document.getElementById('nota-periodo-al').value, 365),
      giudizio_finale: document.getElementById('nota-giudizio').value,
      compilatore: document.getElementById('nota-compilatore').value,
      primo_revisore: document.getElementById('nota-revisore1').value,
      secondo_revisore: document.getElementById('nota-revisore2').value,
      annotazioni: document.getElementById('nota-annotazioni').value
    };

    try {
      await api(`/api/personale/${AppState.currentPersonId}/nota`, 'POST', data);
      showToast('Documento caratteristico registrato con successo!', 'success');
      closeModal('modal-nuova-nota');
      form.reset();
      loadDettaglioPersonale(AppState.currentPersonId);
    } catch (err) {}
  });
}

// --- Inserimento Partecipazione Corso ---
function setupPartecipazioneForm() {
  const form = document.getElementById('form-nuovo-corso-persona');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const isManuale = (AppState.modalCorsoMode === 'manuale');
    const data = {
      is_manual: isManuale,
      data_inizio: document.getElementById('part-inizio').value,
      data_fine: document.getElementById('part-fine').value,
      esito: document.getElementById('part-esito').value,
      numero_attestato: document.getElementById('part-attestato').value,
      note: document.getElementById('part-note').value
    };

    if (isManuale) {
      data.denominazione = document.getElementById('man-corso-nome').value.trim();
      data.ente_erogatore = document.getElementById('man-corso-ente').value.trim();
      data.durata_ore = document.getElementById('man-corso-ore').value ? parseInt(document.getElementById('man-corso-ore').value) : null;
      data.prerequisiti = document.getElementById('man-corso-prereq').value.trim();
      if (!data.denominazione) {
        showToast('Inserisci la denominazione del corso.', 'warning');
        return;
      }
    } else {
      data.corso_id = document.getElementById('corso-select-id').value;
      if (!data.corso_id) {
        showToast('Seleziona un corso dal catalogo o passa alla modalità inserimento manuale.', 'warning');
        return;
      }
    }

    try {
      await api(`/api/personale/${AppState.currentPersonId}/corso`, 'POST', data);
      showToast('Partecipazione al corso registrata!', 'success');
      closeModal('modal-nuovo-corso-persona');
      form.reset();
      setModalCorsoMode('catalogo');
      loadDettaglioPersonale(AppState.currentPersonId);
    } catch (err) {}
  });
}

// --- Inserimento Passaporto di Servizio ---
function setupPassaportoForm() {
  const form = document.getElementById('form-nuovo-passaporto');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = {
      numero_passaporto: document.getElementById('pass-numero').value,
      tipo_passaporto: document.getElementById('pass-tipo').value,
      autorita_rilascio: document.getElementById('pass-autorita').value,
      data_rilascio: document.getElementById('pass-rilascio').value,
      data_scadenza: document.getElementById('pass-scadenza').value,
      stato: document.getElementById('pass-stato').value,
      ubicazione_custodia: document.getElementById('pass-ubicazione').value,
      note: document.getElementById('pass-note').value
    };

    try {
      await api(`/api/personale/${AppState.currentPersonId}/passaporto`, 'POST', data);
      showToast('Passaporto registrato con successo!', 'success');
      closeModal('modal-nuovo-passaporto');
      form.reset();
      loadDettaglioPersonale(AppState.currentPersonId);
    } catch (err) {}
  });
}

// --- Sincronizzazione Durata Settimane / Ore ---
function syncDurataOre(prefix) {
  const settEl = document.getElementById(`${prefix}-settimane`);
  const oreEl = document.getElementById(`${prefix}-ore`);
  if (!settEl || !oreEl) return;
  const sett = parseFloat(settEl.value);
  if (!isNaN(sett) && sett > 0) {
    oreEl.value = Math.round(sett * 36);
  }
}

function syncDurataSettimane(prefix) {
  const settEl = document.getElementById(`${prefix}-settimane`);
  const oreEl = document.getElementById(`${prefix}-ore`);
  if (!settEl || !oreEl) return;
  const ore = parseFloat(oreEl.value);
  if (!isNaN(ore) && ore > 0) {
    settEl.value = (ore / 36) % 1 === 0 ? (ore / 36) : (ore / 36).toFixed(1);
  }
}

// --- Inserimento Corso a Catalogo ---
function setupCatalogoForm() {
  const form = document.getElementById('form-nuovo-catalogo-corso');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = {
      codice_corso: document.getElementById('cat-codice').value.trim(),
      denominazione: document.getElementById('cat-nome').value.trim(),
      ente_erogatore: document.getElementById('cat-ente').value.trim(),
      durata_settimane: document.getElementById('cat-settimane').value ? parseFloat(document.getElementById('cat-settimane').value) : null,
      durata_ore: document.getElementById('cat-ore').value ? parseInt(document.getElementById('cat-ore').value) : null,
      validita_mesi: document.getElementById('cat-validita').value ? parseInt(document.getElementById('cat-validita').value) : null,
      requisiti_sicurezza: document.getElementById('cat-sicurezza').value.trim(),
      precedenti_formativi: document.getElementById('cat-formativi').value.trim(),
      precedenti_operativi: document.getElementById('cat-operativi').value.trim(),
      selezioni: document.getElementById('cat-selezioni').value.trim(),
      conoscenza_lingua: document.getElementById('cat-lingua').value.trim(),
      altri_requisiti: document.getElementById('cat-altri').value.trim(),
      prerequisiti: document.getElementById('cat-prerequisiti').value.trim(),
      descrizione: document.getElementById('cat-desc').value.trim()
    };

    try {
      await api('/api/corsi', 'POST', data);
      showToast('Nuovo corso aggiunto al catalogo!', 'success');
      closeModal('modal-nuovo-catalogo-corso');
      form.reset();
      loadCorsiCatalogo();
    } catch (err) {}
  });
}

// --- Modifica Corso a Catalogo ---
function setupModificaCatalogoForm() {
  const form = document.getElementById('form-modifica-catalogo-corso');
  if (!form) return;
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const id = document.getElementById('edit-cat-id').value;
    if (!id) return;

    const data = {
      codice_corso: document.getElementById('edit-cat-codice').value.trim(),
      denominazione: document.getElementById('edit-cat-nome').value.trim(),
      ente_erogatore: document.getElementById('edit-cat-ente').value.trim(),
      durata_settimane: document.getElementById('edit-cat-settimane').value ? parseFloat(document.getElementById('edit-cat-settimane').value) : null,
      durata_ore: document.getElementById('edit-cat-ore').value ? parseInt(document.getElementById('edit-cat-ore').value) : null,
      validita_mesi: document.getElementById('edit-cat-validita').value ? parseInt(document.getElementById('edit-cat-validita').value) : null,
      requisiti_sicurezza: document.getElementById('edit-cat-sicurezza').value.trim(),
      precedenti_formativi: document.getElementById('edit-cat-formativi').value.trim(),
      precedenti_operativi: document.getElementById('edit-cat-operativi').value.trim(),
      selezioni: document.getElementById('edit-cat-selezioni').value.trim(),
      conoscenza_lingua: document.getElementById('edit-cat-lingua').value.trim(),
      altri_requisiti: document.getElementById('edit-cat-altri').value.trim(),
      prerequisiti: document.getElementById('edit-cat-prerequisiti').value.trim(),
      descrizione: document.getElementById('edit-cat-desc').value.trim()
    };

    try {
      await api(`/api/corsi/${id}`, 'PUT', data);
      showToast('Corso aggiornato con successo!', 'success');
      closeModal('modal-modifica-catalogo-corso');
      form.reset();
      loadCorsiCatalogo();
    } catch (err) {
      console.error(err);
    }
  });
}

// ====================================================================
// AZIONI DI CANCELLAZIONE
// ====================================================================
async function eliminaNota(id) {
  if (confirm('Confermi l\'eliminazione definitiva di questo documento caratteristico?')) {
    try {
      await api(`/api/nota/${id}`, 'DELETE');
      showToast('Documento eliminato con successo');
      loadDettaglioPersonale(AppState.currentPersonId);
    } catch (err) {}
  }
}

async function eliminaPatente(id) {
  if (confirm('Confermi l\'eliminazione della patente?')) {
    try {
      await api(`/api/patente/${id}`, 'DELETE');
      showToast('Patente rimossa con successo');
      loadDettaglioPersonale(AppState.currentPersonId);
    } catch (err) {}
  }
}

async function eliminaPassaporto(id) {
  if (confirm('Confermi l\'eliminazione del passaporto?')) {
    try {
      await api(`/api/passaporto/${id}`, 'DELETE');
      showToast('Passaporto rimosso');
      loadDettaglioPersonale(AppState.currentPersonId);
    } catch (err) {}
  }
}

async function eliminaPartecipazione(id) {
  if (confirm('Confermi l\'eliminazione della registrazione al corso?')) {
    try {
      await api(`/api/partecipazione/${id}`, 'DELETE');
      showToast('Corso rimosso dal fascicolo');
      loadDettaglioPersonale(AppState.currentPersonId);
    } catch (err) {}
  }
}

async function eliminaPersonaleCorrente() {
  if (confirm('ATTENZIONE: Stai per eliminare questo dipendente e tutti i dati correlati (patenti, note caratteristiche, corsi, passaporto). Sei sicuro?')) {
    try {
      await api(`/api/personale/${AppState.currentPersonId}`, 'DELETE');
      showToast('Dipendente rimosso dal database', 'success');
      navigate('personale');
    } catch (err) {}
  }
}

async function eliminaPersonaleDaRuolo(id) {
  const p = AppState.personaleCache.find(x => x.id === id);
  const nominativo = p ? `${p.grado_qualifica} ${p.cognome} ${p.nome} (Matr. ${p.matricola})` : 'questo militare';

  if (confirm(`ATTENZIONE: Stai per eliminare definitivamente ${nominativo} dal database, inclusi tutti i dati correlati (patenti, note caratteristiche, corsi, passaporto).\n\nConfermi l'eliminazione definitiva?`)) {
    try {
      await api(`/api/personale/${id}`, 'DELETE');
      showToast(`${nominativo} rimosso dal database`, 'success');
      loadPersonaleList();
    } catch (err) {
      console.error(err);
    }
  }
}

// ====================================================================
// GESTIONE CARICAMENTO CATALOGO CORSI DA PDF ED ESTRAZIONE PREREQUISITI
// ====================================================================

function handlePdfSelected(files) {
  if (!files || !files.length) return;
  const file = files[0];
  if (!file.name.toLowerCase().endsWith('.pdf')) {
    showToast('Seleziona un file valido in formato PDF.', 'warning');
    return;
  }

  const indicator = document.getElementById('pdf-loading-indicator');
  const dropzone = document.getElementById('pdf-dropzone');
  if (indicator) indicator.style.display = 'block';
  if (dropzone) dropzone.style.opacity = '0.5';

  const reader = new FileReader();
  reader.onload = async function(e) {
    try {
      const base64Content = e.target.result.split(',')[1];
      const res = await api('/api/corsi/upload-pdf', 'POST', {
        filename: file.name,
        file_base64: base64Content
      });

      if (!res.courses || res.courses.length === 0) {
        showToast('Nessun corso rilevato nel PDF caricato.', 'warning');
        return;
      }

      AppState.extractedPdfCourses = res.courses;
      AppState.extractedPdfFilename = file.name;
      closeModal('modal-upload-catalogo-pdf');
      renderAnteprimaCorsi(res.courses, file.name);
      openModal('modal-anteprima-catalogo-pdf');
      showToast(`Analisi completata: trovati ${res.courses.length} corsi nel PDF!`, 'success');
    } catch (err) {
      console.error(err);
    } finally {
      if (indicator) indicator.style.display = 'none';
      if (dropzone) dropzone.style.opacity = '1';
      const fileInput = document.getElementById('pdf-file-input');
      if (fileInput) fileInput.value = '';
    }
  };
  reader.onerror = function() {
    showToast('Errore durante la lettura del file PDF locale.', 'danger');
    if (indicator) indicator.style.display = 'none';
    if (dropzone) dropzone.style.opacity = '1';
  };
  reader.readAsDataURL(file);
}

function renderAnteprimaCorsi(courses, filename) {
  const lblNome = document.getElementById('anteprima-pdf-nome');
  const lblCount = document.getElementById('anteprima-pdf-count');
  const tbody = document.getElementById('anteprima-corsi-tbody');
  const chkAll = document.getElementById('check-all-anteprima');

  if (lblNome) lblNome.textContent = filename || AppState.extractedPdfFilename || '-';
  if (lblCount) lblCount.textContent = courses.length;
  if (chkAll) chkAll.checked = true;

  if (!tbody) return;
  tbody.innerHTML = courses.map((c, index) => {
    const codiceVal = (c.codice_corso || '').replace(/"/g, '&quot;');
    const nomeVal = (c.denominazione || '').replace(/"/g, '&quot;');
    const enteVal = (c.ente_erogatore || '').replace(/"/g, '&quot;');
    const settVal = c.durata_settimane || '';
    const oreVal = c.durata_ore || '';
    const sicVal = (c.requisiti_sicurezza || '').replace(/"/g, '&quot;');
    const formVal = (c.precedenti_formativi || '').replace(/"/g, '&quot;');
    const lingVal = (c.conoscenza_lingua || '').replace(/"/g, '&quot;');
    const opVal = (c.precedenti_operativi || '').replace(/"/g, '&quot;');
    const selVal = (c.selezioni || '').replace(/"/g, '&quot;');
    const altriVal = (c.altri_requisiti || '').replace(/"/g, '&quot;');

    return `
      <tr data-index="${index}">
        <td style="vertical-align: top; padding-top: 12px; text-align: center;">
          <input type="checkbox" class="check-anteprima-item" data-index="${index}" checked>
        </td>
        <td style="vertical-align: top;">
          <div style="margin-bottom: 6px;">
            <input type="text" class="form-control form-control-sm anteprima-codice" value="${codiceVal}" placeholder="Codice (es. CIFIGE-01)" style="font-family:monospace; font-weight:700; width:130px; display:inline-block; margin-bottom:4px;">
          </div>
          <input type="text" class="form-control form-control-sm anteprima-nome" value="${nomeVal}" placeholder="Denominazione corso" style="font-weight:600; width: 100%;">
        </td>
        <td style="vertical-align: top; font-size: 13px;">
          <div style="display:flex; gap:6px; margin-bottom:6px;">
            <div>
              <label style="font-size:10.5px; color:var(--slate-500); display:block;">Settimane</label>
              <input type="number" class="form-control form-control-sm anteprima-settimane" value="${settVal}" style="width:70px;">
            </div>
            <div>
              <label style="font-size:10.5px; color:var(--slate-500); display:block;">Ore</label>
              <input type="number" class="form-control form-control-sm anteprima-ore" value="${oreVal}" style="width:70px;">
            </div>
          </div>
          <div>
            <label style="font-size:10.5px; color:var(--slate-500); display:block;">Ente Erogatore</label>
            <input type="text" class="form-control form-control-sm anteprima-ente" value="${enteVal}" style="width:100%; font-size:12px;">
          </div>
        </td>
        <td style="vertical-align: top;">
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px; font-size: 12px;">
            <div>
              <label style="font-size:10.5px; font-weight:600; color:#991b1b; display:block;">🛡️ Sicurezza (NOS):</label>
              <input type="text" class="form-control form-control-sm anteprima-sicurezza" value="${sicVal}" placeholder="es. Riservato / Segreto">
            </div>
            <div>
              <label style="font-size:10.5px; font-weight:600; color:#1e40af; display:block;">🎓 Formativi:</label>
              <input type="text" class="form-control form-control-sm anteprima-formativi" value="${formVal}" placeholder="es. Corso propedeutico">
            </div>
            <div>
              <label style="font-size:10.5px; font-weight:600; color:#92400e; display:block;">🗣️ Lingua:</label>
              <input type="text" class="form-control form-control-sm anteprima-lingua" value="${lingVal}" placeholder="es. NATO JFLT 8">
            </div>
            <div>
              <label style="font-size:10.5px; font-weight:600; color:#6b21a8; display:block;">🪪 Altri / Patenti:</label>
              <input type="text" class="form-control form-control-sm anteprima-altri" value="${altriVal}" placeholder="es. Patente Mod. 2">
            </div>
            ${opVal ? `
            <div>
              <label style="font-size:10.5px; font-weight:600; color:#475569; display:block;">⏱️ Operativi:</label>
              <input type="text" class="form-control form-control-sm anteprima-operativi" value="${opVal}">
            </div>` : ''}
            ${selVal ? `
            <div>
              <label style="font-size:10.5px; font-weight:600; color:#b91c1c; display:block;">🩺 Selezioni:</label>
              <input type="text" class="form-control form-control-sm anteprima-selezioni" value="${selVal}">
            </div>` : ''}
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

function toggleSelectAllAnteprima(checked) {
  document.querySelectorAll('.check-anteprima-item').forEach(cb => {
    cb.checked = checked;
  });
}

async function confermaImportazioneBatch() {
  const rows = document.querySelectorAll('#anteprima-corsi-tbody tr');
  const toImport = [];

  rows.forEach(tr => {
    const chk = tr.querySelector('.check-anteprima-item');
    if (chk && chk.checked) {
      const idx = parseInt(chk.getAttribute('data-index'));
      const orig = AppState.extractedPdfCourses[idx] || {};
      const codInput = tr.querySelector('.anteprima-codice');
      const nomeInput = tr.querySelector('.anteprima-nome');
      const enteInput = tr.querySelector('.anteprima-ente');
      const settInput = tr.querySelector('.anteprima-settimane');
      const oreInput = tr.querySelector('.anteprima-ore');
      const sicInput = tr.querySelector('.anteprima-sicurezza');
      const formInput = tr.querySelector('.anteprima-formativi');
      const lingInput = tr.querySelector('.anteprima-lingua');
      const opInput = tr.querySelector('.anteprima-operativi');
      const selInput = tr.querySelector('.anteprima-selezioni');
      const altriInput = tr.querySelector('.anteprima-altri');

      toImport.push({
        ...orig,
        codice_corso: codInput ? codInput.value.trim() : orig.codice_corso,
        denominazione: nomeInput ? nomeInput.value.trim() : orig.denominazione,
        ente_erogatore: enteInput ? enteInput.value.trim() : orig.ente_erogatore,
        durata_settimane: settInput && settInput.value ? parseFloat(settInput.value) : orig.durata_settimane,
        durata_ore: oreInput && oreInput.value ? parseInt(oreInput.value) : orig.durata_ore,
        requisiti_sicurezza: sicInput ? sicInput.value.trim() : orig.requisiti_sicurezza,
        precedenti_formativi: formInput ? formInput.value.trim() : orig.precedenti_formativi,
        precedenti_operativi: opInput ? opInput.value.trim() : orig.precedenti_operativi,
        selezioni: selInput ? selInput.value.trim() : orig.selezioni,
        conoscenza_lingua: lingInput ? lingInput.value.trim() : orig.conoscenza_lingua,
        altri_requisiti: altriInput ? altriInput.value.trim() : orig.altri_requisiti
      });
    }
  });

  if (toImport.length === 0) {
    showToast('Nessun corso selezionato per l\'importazione.', 'warning');
    return;
  }

  try {
    const res = await api('/api/corsi/import-batch', 'POST', {
      courses: toImport,
      filename: AppState.extractedPdfFilename || 'catalogo.pdf'
    });

    showToast(`Catalogo aggiornato: ${res.imported_count} corsi importati con successo!`, 'success');
    closeModal('modal-anteprima-catalogo-pdf');
    AppState.extractedPdfCourses = [];
    AppState.extractedPdfFilename = '';
    loadCorsiCatalogo();
  } catch (err) {}
}

function setupPdfDropzone() {
  const dropzone = document.getElementById('pdf-dropzone');
  if (!dropzone) return;

  ['dragenter', 'dragover'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add('dragover');
    }, false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove('dragover');
    }, false);
  });

  dropzone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    handlePdfSelected(files);
  }, false);
}

// ====================================================================
// INIZIALIZZAZIONE APPLICATIVO
// ====================================================================
document.addEventListener('DOMContentLoaded', () => {
  // Setup forms
  setupPersonaleForm();
  setupModificaPersonaleForm();
  setupPatenteForm();
  setupNotaForm();
  setupPartecipazioneForm();
  setupPassaportoForm();
  setupCatalogoForm();
  setupModificaCatalogoForm();
  setupPdfDropzone();

  // Search filter triggers
  const searchInput = document.getElementById('search-personale');
  if (searchInput) {
    searchInput.addEventListener('input', () => {
      clearTimeout(window.searchTimeout);
      window.searchTimeout = setTimeout(loadPersonaleList, 250);
    });
  }

  const filterReparto = document.getElementById('filter-reparto');
  if (filterReparto) filterReparto.addEventListener('change', loadPersonaleList);

  const filterStato = document.getElementById('filter-stato');
  if (filterStato) filterStato.addEventListener('change', loadPersonaleList);

  // Close modals on clicking outside or ESC
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal-backdrop.active').forEach(m => m.classList.remove('active'));
    }
  });

  // Allow keyboard interaction (Enter / Space) on stat-cards
  document.addEventListener('keydown', (e) => {
    if ((e.key === 'Enter' || e.key === ' ') && e.target && e.target.classList && e.target.classList.contains('stat-card')) {
      e.preventDefault();
      e.target.click();
    }
  });

  // Start with Dashboard
  navigate('dashboard');
});

