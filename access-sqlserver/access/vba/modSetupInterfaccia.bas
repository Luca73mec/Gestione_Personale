Attribute VB_Name = "modSetupInterfaccia"
Option Compare Database
Option Explicit

Private Const CFG_TABLE As String = "cfg_app"

Public Sub SetupInterfaccia()
    On Error GoTo GestioneErrore

    Dim serverName As String
    Dim databaseName As String
    Dim driverName As String
    Dim connectString As String

    serverName = Trim$(InputBox("Nome o indirizzo del server SQL Server:", "Configurazione SQL Server"))
    If Len(serverName) = 0 Then Exit Sub

    databaseName = Trim$(InputBox("Nome del database SQL Server:", "Configurazione SQL Server"))
    If Len(databaseName) = 0 Then Exit Sub

    driverName = Trim$(InputBox("Nome del driver ODBC SQL Server:", "Driver ODBC", "ODBC Driver 18 for SQL Server"))
    If Len(driverName) = 0 Then Exit Sub

    connectString = "ODBC;DRIVER={" & driverName & "};SERVER=" & serverName & ";DATABASE=" & databaseName & ";Trusted_Connection=Yes;Encrypt=Yes;TrustServerCertificate=No;"

    DoCmd.Hourglass True
    CreaTabellaConfigurazione
    SalvaConfigurazione serverName, databaseName, driverName

    CollegaTabella "personale", connectString
    CollegaTabella "patente", connectString
    CollegaTabella "corso", connectString
    CollegaTabella "partecipazione_corso", connectString
    CollegaTabella "nota_caratteristica", connectString
    CollegaTabella "passaporto_servizio", connectString
    CollegaTabella "vista_ultima_nota_personale", connectString
    CollegaTabella "vista_scadenze_patenti", connectString
    CollegaTabella "vista_scadenze_passaporti", connectString

    CreaQuerySalvate
    CreaMascheraPersonale
    CreaMascheraDettaglio
    CreaMascheraMenu

    DoCmd.Hourglass False
    DoCmd.OpenForm "frmMenu"
    MsgBox "Configurazione completata. Verificare i collegamenti ODBC prima di usare i dati.", vbInformation, "Gestione Personale"
    Exit Sub

GestioneErrore:
    DoCmd.Hourglass False
    MsgBox "Configurazione non completata: " & Err.Description, vbCritical, "Errore configurazione"
End Sub

Private Sub CreaTabellaConfigurazione()
    On Error Resume Next
    CurrentDb.Execute "CREATE TABLE " & CFG_TABLE & " (id COUNTER CONSTRAINT pk_cfg_app PRIMARY KEY, server_name TEXT(255), database_name TEXT(255), driver_name TEXT(255), updated_at DATETIME)", dbFailOnError
    On Error GoTo 0
End Sub

Private Sub SalvaConfigurazione(ByVal serverName As String, ByVal databaseName As String, ByVal driverName As String)
    Dim db As DAO.Database
    Set db = CurrentDb
    db.Execute "DELETE FROM " & CFG_TABLE, dbFailOnError
    db.Execute "INSERT INTO " & CFG_TABLE & " (server_name, database_name, driver_name, updated_at) VALUES (" & _
               StringaSql(serverName) & ", " & StringaSql(databaseName) & ", " & StringaSql(driverName) & ", Now())", dbFailOnError
End Sub

Private Sub CollegaTabella(ByVal tableName As String, ByVal connectString As String)
    Dim db As DAO.Database
    Dim tableDef As DAO.TableDef

    Set db = CurrentDb
    On Error Resume Next
    db.TableDefs.Delete tableName
    On Error GoTo 0

    Set tableDef = db.CreateTableDef(tableName)
    tableDef.Connect = connectString
    tableDef.SourceTableName = "dbo." & tableName
    db.TableDefs.Append tableDef
End Sub

Private Sub CreaQuerySalvate()
    EliminaQuery "qryPersonaleElenco"
    CreaQuery "qryPersonaleElenco", _
        "SELECT p.id, p.matricola, p.cognome, p.nome, p.grado_qualifica, p.reparto_ufficio, p.stato_servizio, " & _
        "v.data_prossima_scadenza AS prossima_scadenza_nota FROM personale AS p " & _
        "LEFT JOIN vista_ultima_nota_personale AS v ON p.id = v.personale_id"

    EliminaQuery "qryScadenzario"
    CreaQuery "qryScadenzario", _
        "SELECT 'Nota' AS tipo_scadenza, personale_id, cognome, nome, data_prossima_scadenza AS data_scadenza, " & _
        "stato_scadenza FROM vista_ultima_nota_personale WHERE stato_scadenza <> 'REGOLARE' " & _
        "UNION ALL SELECT 'Patente', personale_id, cognome, nome, data_scadenza, stato_scadenza " & _
        "FROM vista_scadenze_patenti WHERE stato_scadenza <> 'REGOLARE' " & _
        "UNION ALL SELECT 'Passaporto', personale_id, cognome, nome, data_scadenza, stato_scadenza " & _
        "FROM vista_scadenze_passaporti WHERE stato_scadenza <> 'REGOLARE'"
End Sub

Private Sub CreaQuery(ByVal queryName As String, ByVal sqlText As String)
    Dim queryDef As DAO.QueryDef
    Set queryDef = CurrentDb.CreateQueryDef(queryName, sqlText)
End Sub

Private Sub EliminaQuery(ByVal queryName As String)
    On Error Resume Next
    CurrentDb.QueryDefs.Delete queryName
    On Error GoTo 0
End Sub

Private Sub CreaMascheraMenu()
    Dim frm As Form
    Dim ctl As Control

    EliminaMaschera "frmMenu"
    Set frm = CreateForm
    frm.Caption = "Gestione Personale"
    frm.NavigationButtons = False
    frm.RecordSelectors = False
    frm.Width = 9000
    frm.Section(acDetail).Height = 5000

    Set ctl = CreateControl(frm.Name, acLabel, acDetail, , , 700, 500, 7600, 600)
    ctl.Caption = "GESTIONE PERSONALE"
    ctl.FontSize = 18
    ctl.FontBold = True

    AggiungiPulsante frm, "Elenco personale", "=ApriPersonale()", 700, 1500, 3500, 600
    AggiungiPulsante frm, "Scadenzario", "=ApriScadenzario()", 4500, 1500, 3500, 600
    AggiungiPulsante frm, "Nuovo personale", "=NuovoPersonale()", 700, 2400, 3500, 600
    AggiungiPulsante frm, "Chiudi applicazione", "=ChiudiApplicazione()", 4500, 2400, 3500, 600

    SalvaMaschera frm, "frmMenu"
End Sub

Private Sub CreaMascheraPersonale()
    Dim frm As Form

    EliminaMaschera "frmPersonale"
    Set frm = CreateForm
    frm.Caption = "Elenco personale"
    frm.RecordSource = "qryPersonaleElenco"
    frm.DefaultView = 1
    frm.AllowAdditions = False
    frm.AllowDeletions = False
    frm.AllowEdits = False
    frm.NavigationButtons = True
    frm.RecordSelectors = True
    frm.Section(acDetail).Height = 950

    Dim hiddenId As Control
    Set hiddenId = CreateControl(frm.Name, acTextBox, acDetail, , , 0, 0, 100, 100)
    hiddenId.Name = "txt_id"
    hiddenId.ControlSource = "id"
    hiddenId.Visible = False

    AggiungiCampo frm, "matricola", "Matricola", 300, 250, 1400
    AggiungiCampo frm, "cognome", "Cognome", 1800, 250, 1800
    AggiungiCampo frm, "nome", "Nome", 3700, 250, 1800
    AggiungiCampo frm, "grado_qualifica", "Grado", 5600, 250, 2200
    AggiungiCampo frm, "stato_servizio", "Stato", 7900, 250, 1800
    AggiungiPulsante frm, "Apri", "=ApriDettaglio()", 9800, 210, 1000, 450

    SalvaMaschera frm, "frmPersonale"
End Sub

Private Sub CreaMascheraDettaglio()
    Dim frm As Form

    EliminaMaschera "frmPersonaleDettaglio"
    Set frm = CreateForm
    frm.Caption = "Scheda personale"
    frm.RecordSource = "personale"
    frm.DefaultView = 0
    frm.AllowAdditions = True
    frm.AllowDeletions = False
    frm.AllowEdits = True
    frm.NavigationButtons = True
    frm.Section(acDetail).Height = 6200

    AggiungiCampo frm, "matricola", "Matricola", 500, 400, 2500
    AggiungiCampo frm, "codice_fiscale", "Codice fiscale", 3500, 400, 3000
    AggiungiCampo frm, "cognome", "Cognome", 500, 1100, 2500
    AggiungiCampo frm, "nome", "Nome", 3500, 1100, 3000
    AggiungiCampo frm, "grado_qualifica", "Grado / qualifica", 500, 1800, 4000
    AggiungiCampo frm, "reparto_ufficio", "Reparto / ufficio", 500, 2500, 5000
    AggiungiCampo frm, "incarico", "Incarico", 500, 3200, 5000
    AggiungiCampo frm, "stato_servizio", "Stato di servizio", 500, 3900, 3000
    AggiungiCampo frm, "email_istituzionale", "Email istituzionale", 500, 4600, 5000
    AggiungiCampo frm, "note_generali", "Note", 500, 5300, 7000, 500)

    SalvaMaschera frm, "frmPersonaleDettaglio"
End Sub

Private Sub AggiungiCampo(ByVal frm As Form, ByVal fieldName As String, ByVal caption As String, ByVal leftPos As Long, ByVal topPos As Long, ByVal width As Long, Optional ByVal height As Long = 350)
    Dim labelCtl As Control
    Dim textCtl As Control

    Set labelCtl = CreateControl(frm.Name, acLabel, acDetail, , , leftPos, topPos - 250, 1900, 250)
    labelCtl.Caption = caption
    Set textCtl = CreateControl(frm.Name, acTextBox, acDetail, , , leftPos + 1900, topPos, width, height)
    textCtl.Name = "txt_" & fieldName
    textCtl.ControlSource = fieldName
End Sub

Private Sub AggiungiPulsante(ByVal frm As Form, ByVal caption As String, ByVal expression As String, ByVal leftPos As Long, ByVal topPos As Long, ByVal width As Long, ByVal height As Long)
    Dim buttonCtl As Control
    Set buttonCtl = CreateControl(frm.Name, acCommandButton, acDetail, , , leftPos, topPos, width, height)
    buttonCtl.Caption = caption
    buttonCtl.OnClick = expression
End Sub

Private Sub SalvaMaschera(ByVal frm As Form, ByVal formName As String)
    DoCmd.Save acForm, frm.Name
    DoCmd.Close acForm, frm.Name, acSaveYes
    DoCmd.Rename formName, acForm, frm.Name
End Sub

Private Sub EliminaMaschera(ByVal formName As String)
    On Error Resume Next
    DoCmd.Close acForm, formName, acSaveNo
    DoCmd.DeleteObject acForm, formName
    On Error GoTo 0
End Sub

Private Function StringaSql(ByVal value As String) As String
    StringaSql = "'" & Replace(value, "'", "''") & "'"
End Function

Public Function ApriPersonale() As Boolean
    DoCmd.OpenForm "frmPersonale"
    ApriPersonale = True
End Function

Public Function ApriScadenzario() As Boolean
    DoCmd.OpenQuery "qryScadenzario"
    ApriScadenzario = True
End Function

Public Function NuovoPersonale() As Boolean
    DoCmd.OpenForm "frmPersonaleDettaglio", , , , acFormAdd
    NuovoPersonale = True
End Function

Public Function ApriDettaglio() As Boolean
    Dim personaleId As Variant
    personaleId = Screen.ActiveControl.Parent.Controls("id").Value
    If Not IsNull(personaleId) Then
        DoCmd.OpenForm "frmPersonaleDettaglio", , , "id=" & CLng(personaleId)
    End If
    ApriDettaglio = True
End Function

Public Function ChiudiApplicazione() As Boolean
    DoCmd.Quit acQuitSaveAll
    ChiudiApplicazione = True
End Function