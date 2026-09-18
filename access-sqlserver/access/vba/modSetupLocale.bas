Option Compare Database
Option Explicit

Public Sub SetupLocale()
    On Error GoTo GestioneErrore

    DoCmd.Hourglass True
    CreaTabelleLocali
    CreaQueryLocali
    CreaMascheraLocalePersonale
    CreaMascheraLocaleDettaglio
    CreaMascheraLocaleMenu
    DoCmd.Hourglass False

    DoCmd.OpenForm "frmLocaleMenu"
    MsgBox "Database locale creato. Non contiene ancora dati personali.", vbInformation, "Gestione Personale"
    Exit Sub

GestioneErrore:
    DoCmd.Hourglass False
    MsgBox "Configurazione locale non completata: " & Err.Description, vbCritical, "Errore configurazione"
End Sub

Private Sub CreaTabelleLocali()
    Dim db As DAO.Database
    Set db = CurrentDb

    CreaTabella db, "personale", _
        "CREATE TABLE personale (id AUTOINCREMENT CONSTRAINT pk_personale PRIMARY KEY, " & _
        "matricola TEXT(50), codice_fiscale TEXT(16), cognome TEXT(100), nome TEXT(100), " & _
        "sesso TEXT(10), data_nascita DATETIME, luogo_nascita TEXT(150), provincia_nascita TEXT(10), " & _
        "grado_qualifica TEXT(150), reparto_ufficio TEXT(150), incarico TEXT(200), posto_tabellare TEXT(200), " & _
        "data_arruolamento_assunzione DATETIME, stato_servizio TEXT(50), email_istituzionale TEXT(254), " & _
        "email_personale TEXT(254), telefono TEXT(50), indirizzo_residenza TEXT(300), livello_nos TEXT(100), " & _
        "lingua_inglese TEXT(100), note_generali MEMO, created_at DATETIME, updated_at DATETIME)"

    CreaTabella db, "patente", _
        "CREATE TABLE patente (id AUTOINCREMENT CONSTRAINT pk_patente PRIMARY KEY, personale_id LONG, " & _
        "tipo_patente TEXT(30), categoria TEXT(100), numero_patente TEXT(100), ente_rilascio TEXT(200), " & _
        "data_rilascio DATETIME, data_scadenza DATETIME, limitazioni_abilitazioni TEXT(500), created_at DATETIME)"

    CreaTabella db, "corso", _
        "CREATE TABLE corso (id AUTOINCREMENT CONSTRAINT pk_corso PRIMARY KEY, codice_corso TEXT(100), " & _
        "denominazione TEXT(300), ente_erogatore TEXT(200), durata_settimane LONG, durata_ore LONG, " & _
        "validita_mesi LONG, requisiti_sicurezza MEMO, precedenti_formativi MEMO, precedenti_operativi MEMO, " & _
        "selezioni MEMO, conoscenza_lingua TEXT(500), altri_requisiti MEMO, prerequisiti MEMO, " & _
        "fonte_catalogo TEXT(300), descrizione MEMO, created_at DATETIME)"

    CreaTabella db, "partecipazione_corso", _
        "CREATE TABLE partecipazione_corso (id AUTOINCREMENT CONSTRAINT pk_partecipazione PRIMARY KEY, " & _
        "personale_id LONG, corso_id LONG, data_inizio DATETIME, data_fine DATETIME, esito TEXT(30), " & _
        "numero_attestato TEXT(100), data_scadenza_abilitazione DATETIME, note MEMO, created_at DATETIME)"

    CreaTabella db, "nota_caratteristica", _
        "CREATE TABLE nota_caratteristica (id AUTOINCREMENT CONSTRAINT pk_nota PRIMARY KEY, personale_id LONG, " & _
        "tipologia_documento TEXT(50), motivo_redazione TEXT(50), periodo_dal DATETIME, periodo_al DATETIME, " & _
        "data_firma_interessato DATETIME, data_prossima_scadenza DATETIME, giudizio_finale TEXT(50), " & _
        "compilatore TEXT(200), primo_revisore TEXT(200), secondo_revisore TEXT(200), annotazioni MEMO, " & _
        "created_at DATETIME)"

    CreaTabella db, "passaporto_servizio", _
        "CREATE TABLE passaporto_servizio (id AUTOINCREMENT CONSTRAINT pk_passaporto PRIMARY KEY, " & _
        "personale_id LONG, numero_passaporto TEXT(100), tipo_passaporto TEXT(30), autorita_rilascio TEXT(300), " & _
        "data_rilascio DATETIME, data_scadenza DATETIME, stato TEXT(30), ubicazione_custodia TEXT(200), " & _
        "note MEMO, created_at DATETIME)"
End Sub

Private Sub CreaTabella(ByVal db As DAO.Database, ByVal tableName As String, ByVal sqlText As String)
    If Not TabellaEsiste(tableName) Then db.Execute sqlText, dbFailOnError
End Sub

Private Function TabellaEsiste(ByVal tableName As String) As Boolean
    Dim tableDef As DAO.TableDef
    On Error Resume Next
    Set tableDef = CurrentDb.TableDefs(tableName)
    TabellaEsiste = (Err.Number = 0)
    Err.Clear
    On Error GoTo 0
End Function

Private Sub CreaQueryLocali()
    EliminaQueryLocale "qryLocalePersonale"
    CreaQueryLocale "qryLocalePersonale", _
        "SELECT id, matricola, cognome, nome, grado_qualifica, reparto_ufficio, stato_servizio FROM personale"

    EliminaQueryLocale "qryLocaleScadenzario"
    CreaQueryLocale "qryLocaleScadenzario", _
        "SELECT 'Nota' AS tipo_scadenza, p.id AS personale_id, p.cognome, p.nome, " & _
        "n.data_prossima_scadenza AS data_scadenza FROM personale AS p INNER JOIN " & _
        "nota_caratteristica AS n ON p.id = n.personale_id WHERE n.data_prossima_scadenza <= Date()+60 " & _
        "UNION ALL SELECT 'Patente', p.id, p.cognome, p.nome, pa.data_scadenza FROM personale AS p INNER JOIN " & _
        "patente AS pa ON p.id = pa.personale_id WHERE pa.data_scadenza <= Date()+60 " & _
        "UNION ALL SELECT 'Passaporto', p.id, p.cognome, p.nome, ps.data_scadenza FROM personale AS p INNER JOIN " & _
        "passaporto_servizio AS ps ON p.id = ps.personale_id WHERE ps.data_scadenza <= Date()+90 " & _
        "ORDER BY data_scadenza"
End Sub

Private Sub CreaQueryLocale(ByVal queryName As String, ByVal sqlText As String)
    Dim queryDef As DAO.QueryDef
    Set queryDef = CurrentDb.CreateQueryDef(queryName, sqlText)
End Sub

Private Sub EliminaQueryLocale(ByVal queryName As String)
    On Error Resume Next
    CurrentDb.QueryDefs.Delete queryName
    On Error GoTo 0
End Sub

Private Sub CreaMascheraLocaleMenu()
    Dim frm As Form
    Dim titolo As Control

    EliminaMascheraLocale "frmLocaleMenu"
    Set frm = CreateForm
    frm.Caption = "Gestione Personale - Database locale"
    frm.NavigationButtons = False
    frm.RecordSelectors = False
    frm.Width = 9000
    frm.Section(acDetail).Height = 4300

    Set titolo = CreateControl(frm.Name, acLabel, acDetail, , , 700, 500, 7600, 600)
    titolo.Caption = "GESTIONE PERSONALE - DATABASE LOCALE"
    titolo.FontSize = 16
    titolo.FontBold = True

    AggiungiPulsanteLocale frm, "Elenco personale", "=LocaleApriPersonale()", 700, 1500, 3500, 600
    AggiungiPulsanteLocale frm, "Scadenzario", "=LocaleApriScadenzario()", 4500, 1500, 3500, 600
    AggiungiPulsanteLocale frm, "Nuovo personale", "=LocaleNuovoPersonale()", 700, 2400, 3500, 600
    AggiungiPulsanteLocale frm, "Chiudi", "=LocaleChiudi()", 4500, 2400, 3500, 600
    SalvaMascheraLocale frm, "frmLocaleMenu"
End Sub

Private Sub CreaMascheraLocalePersonale()
    Dim frm As Form
    Dim hiddenId As Control

    EliminaMascheraLocale "frmLocalePersonale"
    Set frm = CreateForm
    frm.Caption = "Elenco personale locale"
    frm.RecordSource = "qryLocalePersonale"
    frm.DefaultView = 1
    frm.AllowAdditions = False
    frm.AllowDeletions = False
    frm.AllowEdits = False
    frm.Section(acDetail).Height = 950

    Set hiddenId = CreateControl(frm.Name, acTextBox, acDetail, , , 0, 0, 100, 100)
    hiddenId.Name = "txt_id"
    hiddenId.ControlSource = "id"
    hiddenId.Visible = False

    AggiungiCampoLocale frm, "matricola", "Matricola", 300, 250, 1400
    AggiungiCampoLocale frm, "cognome", "Cognome", 1800, 250, 1800
    AggiungiCampoLocale frm, "nome", "Nome", 3700, 250, 1800
    AggiungiCampoLocale frm, "grado_qualifica", "Grado", 5600, 250, 2200
    AggiungiCampoLocale frm, "stato_servizio", "Stato", 7900, 250, 1800
    AggiungiPulsanteLocale frm, "Apri", "=LocaleApriDettaglio()", 9800, 210, 1000, 450
    SalvaMascheraLocale frm, "frmLocalePersonale"
End Sub

Private Sub CreaMascheraLocaleDettaglio()
    Dim frm As Form

    EliminaMascheraLocale "frmLocaleDettaglio"
    Set frm = CreateForm
    frm.Caption = "Scheda personale locale"
    frm.RecordSource = "personale"
    frm.DefaultView = 0
    frm.AllowAdditions = True
    frm.AllowDeletions = False
    frm.AllowEdits = True
    frm.Section(acDetail).Height = 6200

    AggiungiCampoLocale frm, "matricola", "Matricola", 500, 400, 2500
    AggiungiCampoLocale frm, "codice_fiscale", "Codice fiscale", 3500, 400, 3000
    AggiungiCampoLocale frm, "cognome", "Cognome", 500, 1100, 2500
    AggiungiCampoLocale frm, "nome", "Nome", 3500, 1100, 3000
    AggiungiCampoLocale frm, "grado_qualifica", "Grado / qualifica", 500, 1800, 4000
    AggiungiCampoLocale frm, "reparto_ufficio", "Reparto / ufficio", 500, 2500, 5000
    AggiungiCampoLocale frm, "incarico", "Incarico", 500, 3200, 5000
    AggiungiCampoLocale frm, "stato_servizio", "Stato di servizio", 500, 3900, 3000
    AggiungiCampoLocale frm, "email_istituzionale", "Email istituzionale", 500, 4600, 5000
    AggiungiCampoLocale frm, "note_generali", "Note", 500, 5300, 7000, 500
    SalvaMascheraLocale frm, "frmLocaleDettaglio"
End Sub

Private Sub AggiungiCampoLocale(ByVal frm As Form, ByVal fieldName As String, ByVal caption As String, ByVal leftPos As Long, ByVal topPos As Long, ByVal width As Long, Optional ByVal height As Long = 350)
    Dim labelCtl As Control
    Dim textCtl As Control

    Set labelCtl = CreateControl(frm.Name, acLabel, acDetail, , , leftPos, topPos - 250, 1900, 250)
    labelCtl.Caption = caption
    Set textCtl = CreateControl(frm.Name, acTextBox, acDetail, , , leftPos + 1900, topPos, width, height)
    textCtl.Name = "txtLocale_" & fieldName
    textCtl.ControlSource = fieldName
End Sub

Private Sub AggiungiPulsanteLocale(ByVal frm As Form, ByVal caption As String, ByVal expression As String, ByVal leftPos As Long, ByVal topPos As Long, ByVal width As Long, ByVal height As Long)
    Dim buttonCtl As Control
    Set buttonCtl = CreateControl(frm.Name, acCommandButton, acDetail, , , leftPos, topPos, width, height)
    buttonCtl.Caption = caption
    buttonCtl.OnClick = expression
End Sub

Private Sub SalvaMascheraLocale(ByVal frm As Form, ByVal formName As String)
    DoCmd.Save acForm, frm.Name
    DoCmd.Close acForm, frm.Name, acSaveYes
    DoCmd.Rename formName, acForm, frm.Name
End Sub

Private Sub EliminaMascheraLocale(ByVal formName As String)
    On Error Resume Next
    DoCmd.Close acForm, formName, acSaveNo
    DoCmd.DeleteObject acForm, formName
    On Error GoTo 0
End Sub

Public Function LocaleApriPersonale() As Boolean
    DoCmd.OpenForm "frmLocalePersonale"
    LocaleApriPersonale = True
End Function

Public Function LocaleApriScadenzario() As Boolean
    DoCmd.OpenQuery "qryLocaleScadenzario"
    LocaleApriScadenzario = True
End Function

Public Function LocaleNuovoPersonale() As Boolean
    DoCmd.OpenForm "frmLocaleDettaglio", , , , acFormAdd
    LocaleNuovoPersonale = True
End Function

Public Function LocaleApriDettaglio() As Boolean
    Dim personaleId As Variant
    personaleId = Screen.ActiveControl.Parent.Controls("txt_id").Value
    If Not IsNull(personaleId) Then
        DoCmd.OpenForm "frmLocaleDettaglio", , , "id=" & CLng(personaleId)
    End If
    LocaleApriDettaglio = True
End Function

Public Function LocaleChiudi() As Boolean
    DoCmd.Quit acQuitSaveAll
    LocaleChiudi = True
End Function