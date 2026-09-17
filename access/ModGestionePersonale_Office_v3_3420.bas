Attribute VB_Name = "ModGestionePersonale_Office_v3_3420"
Option Compare Database
Option Explicit

' Gestione Personale - versione 3.3420
' Compatibile con Access 2007-2016 italiano.
' Non richiede un riferimento DAO esplicito.

Private Const T_LONG As Long = 4
Private Const T_DATE As Long = 8
Private Const T_TEXT As Long = 10
Private Const T_MEMO As Long = 12
Private Const T_AUTONUMBER As Long = 16
Private Const REL_UPDATE As Long = 256
Private Const REL_DELETE_CASCADE As Long = 4096
Private Const REL_DELETE_RESTRICT As Long = 2
Private Const EXEC_FAIL As Long = 128

Public Sub CreaProgettoGestionePersonale()
    On Error GoTo Errore
    Application.Echo False, "Creazione Gestione Personale..."
    CreaTabelle
    CreaRelazioni
    CreaQuery
    CreaDatiDemo
    CreaMaschere
    Application.Echo True
    DoCmd.OpenForm "frmDashboard"
    MsgBox "Gestione Personale v3.3420 creata correttamente.", vbInformation
    Exit Sub
Errore:
    Application.Echo True
    MsgBox "Errore " & Err.Number & ": " & Err.Description, vbCritical
End Sub

Private Sub CreaTabelle()
    Dim db As Object
    Set db = CurrentDb
    EliminaRelazioni db
    EliminaTabella db, "partecipazione_corso"
    EliminaTabella db, "nota_caratteristica"
    EliminaTabella db, "passaporto_servizio"
    EliminaTabella db, "patente"
    EliminaTabella db, "corso"
    EliminaTabella db, "personale"

    CreaPersonale db
    CreaPatente db
    CreaCorso db
    CreaPartecipazione db
    CreaNota db
    CreaPassaporto db
End Sub

Private Sub CreaPersonale(db As Object)
    Dim t As Object
    Set t = db.CreateTableDef("personale")
    AddId t, "id": AddText t, "matricola", 30: AddText t, "codice_fiscale", 20
    AddText t, "cognome", 80: AddText t, "nome", 80: AddText t, "sesso", 10
    AddDate t, "data_nascita": AddText t, "luogo_nascita", 100: AddText t, "provincia_nascita", 5
    AddText t, "grado_qualifica", 100: AddText t, "reparto_ufficio", 120
    AddText t, "incarico", 150: AddText t, "posto_tabellare", 150
    AddDate t, "data_arruolamento_assunzione": AddText t, "stato_servizio", 40
    AddText t, "email_istituzionale", 150: AddText t, "email_personale", 150: AddText t, "telefono", 40
    AddText t, "indirizzo_residenza", 255: AddMemo t, "note_generali"
    AddDate t, "created_at": AddDate t, "updated_at"
    db.TableDefs.Append t
    AddIndex "personale", "pk_personale", "id", True, True
    AddIndex "personale", "ux_personale_matricola", "matricola", True, False
    AddIndex "personale", "ux_personale_cf", "codice_fiscale", True, False
End Sub

Private Sub CreaPatente(db As Object)
    Dim t As Object
    Set t = db.CreateTableDef("patente")
    AddId t, "id": AddLong t, "personale_id": AddText t, "tipo_patente", 30
    AddText t, "categoria", 100: AddText t, "numero_patente", 60: AddText t, "ente_rilascio", 150
    AddDate t, "data_rilascio": AddDate t, "data_scadenza": AddMemo t, "limitazioni_abilitazioni": AddDate t, "created_at"
    db.TableDefs.Append t
    AddIndex "patente", "pk_patente", "id", True, True
    AddIndex "patente", "ix_patente_scadenza", "data_scadenza", False, False
End Sub

Private Sub CreaCorso(db As Object)
    Dim t As Object
    Set t = db.CreateTableDef("corso")
    AddId t, "id": AddText t, "codice_corso", 50: AddText t, "denominazione", 180
    AddText t, "ente_erogatore", 150: AddLong t, "durata_ore": AddLong t, "validita_mesi"
    AddMemo t, "prerequisiti": AddText t, "fonte_catalogo", 255: AddMemo t, "descrizione": AddDate t, "created_at"
    db.TableDefs.Append t
    AddIndex "corso", "pk_corso", "id", True, True
    AddIndex "corso", "ux_corso_codice", "codice_corso", True, False
End Sub

Private Sub CreaPartecipazione(db As Object)
    Dim t As Object
    Set t = db.CreateTableDef("partecipazione_corso")
    AddId t, "id": AddLong t, "personale_id": AddLong t, "corso_id"
    AddDate t, "data_inizio": AddDate t, "data_fine": AddText t, "esito", 40
    AddText t, "numero_attestato", 80: AddDate t, "data_scadenza_abilitazione": AddMemo t, "note": AddDate t, "created_at"
    db.TableDefs.Append t
    AddIndex "partecipazione_corso", "pk_partecipazione", "id", True, True
End Sub

Private Sub CreaNota(db As Object)
    Dim t As Object
    Set t = db.CreateTableDef("nota_caratteristica")
    AddId t, "id": AddLong t, "personale_id": AddText t, "tipologia_documento", 50: AddText t, "motivo_redazione", 50
    AddDate t, "periodo_dal": AddDate t, "periodo_al": AddDate t, "data_firma_interessato": AddDate t, "data_prossima_scadenza"
    AddText t, "giudizio_finale", 60: AddText t, "compilatore", 120: AddText t, "primo_revisore", 120: AddText t, "secondo_revisore", 120
    AddMemo t, "annotazioni": AddDate t, "created_at"
    db.TableDefs.Append t
    AddIndex "nota_caratteristica", "pk_nota", "id", True, True
    AddIndex "nota_caratteristica", "ix_nota_scadenza", "data_prossima_scadenza", False, False
End Sub

Private Sub CreaPassaporto(db As Object)
    Dim t As Object
    Set t = db.CreateTableDef("passaporto_servizio")
    AddId t, "id": AddLong t, "personale_id": AddText t, "numero_passaporto", 50: AddText t, "tipo_passaporto", 30
    AddText t, "autorita_rilascio", 180: AddDate t, "data_rilascio": AddDate t, "data_scadenza": AddText t, "stato", 30
    AddText t, "ubicazione_custodia", 150: AddMemo t, "note": AddDate t, "created_at"
    db.TableDefs.Append t
    AddIndex "passaporto_servizio", "pk_passaporto", "id", True, True
    AddIndex "passaporto_servizio", "ux_passaporto_numero", "numero_passaporto", True, False
    AddIndex "passaporto_servizio", "ix_passaporto_scadenza", "data_scadenza", False, False
End Sub

Private Sub AddId(t As Object, nome As String)
    Dim f As Object
    Set f = t.CreateField(nome, T_LONG)
    f.Attributes = T_AUTONUMBER
    t.Fields.Append f
End Sub

Private Sub AddText(t As Object, nome As String, dimensione As Long)
    Dim f As Object
    Set f = t.CreateField(nome, T_TEXT, dimensione)
    t.Fields.Append f
End Sub

Private Sub AddMemo(t As Object, nome As String)
    Dim f As Object
    Set f = t.CreateField(nome, T_MEMO)
    t.Fields.Append f
End Sub

Private Sub AddLong(t As Object, nome As String)
    Dim f As Object
    Set f = t.CreateField(nome, T_LONG)
    t.Fields.Append f
End Sub

Private Sub AddDate(t As Object, nome As String)
    Dim f As Object
    Set f = t.CreateField(nome, T_DATE)
    t.Fields.Append f
End Sub

Private Sub AddIndex(nomeTabella As String, nomeIndice As String, nomeCampo As String, unico As Boolean, primario As Boolean)
    Dim t As Object, i As Object
    Set t = CurrentDb.TableDefs(nomeTabella)
    Set i = t.CreateIndex(nomeIndice)
    i.Unique = unico
    i.Primary = primario
    Dim f As Object
    Set f = i.CreateField(nomeCampo)
    i.Fields.Append f
    t.Indexes.Append i
End Sub

Private Sub CreaRelazioni()
    Dim db As Object
    Set db = CurrentDb
    CreaRelazione db, "rel_personale_patente", "personale", "patente", "id", "personale_id", REL_UPDATE Or REL_DELETE_CASCADE
    CreaRelazione db, "rel_personale_note", "personale", "nota_caratteristica", "id", "personale_id", REL_UPDATE Or REL_DELETE_CASCADE
    CreaRelazione db, "rel_personale_passaporto", "personale", "passaporto_servizio", "id", "personale_id", REL_UPDATE Or REL_DELETE_CASCADE
    CreaRelazione db, "rel_personale_partecipazione", "personale", "partecipazione_corso", "id", "personale_id", REL_UPDATE Or REL_DELETE_CASCADE
    CreaRelazione db, "rel_corso_partecipazione", "corso", "partecipazione_corso", "id", "corso_id", REL_UPDATE Or REL_DELETE_RESTRICT
End Sub

Private Sub CreaRelazione(db As Object, nome As String, tabellaPadre As String, tabellaFiglia As String, campoPadre As String, campoFiglio As String, attributi As Long)
    Dim r As Object, f As Object
    Set r = db.CreateRelation(nome, tabellaPadre, tabellaFiglia, attributi)
    Set f = r.CreateField(campoPadre)
    f.ForeignName = campoFiglio
    r.Fields.Append f
    db.Relations.Append r
End Sub

Private Sub CreaQuery()
    SalvaQuery "qryScadenzePatenti", "SELECT p.cognome,p.nome,pat.*,DateDiff('d',Date(),pat.data_scadenza) AS giorni_alla_scadenza,IIf(pat.data_scadenza<Date(),'SCADUTA',IIf(pat.data_scadenza<=Date()+30,'URGENTE_30GG',IIf(pat.data_scadenza<=Date()+60,'IN_SCADENZA_60GG','REGOLARE'))) AS stato_scadenza FROM personale AS p INNER JOIN patente AS pat ON p.id=pat.personale_id"
    SalvaQuery "qryScadenzePassaporti", "SELECT p.cognome,p.nome,ps.*,DateDiff('d',Date(),ps.data_scadenza) AS giorni_alla_scadenza,IIf(ps.data_scadenza<Date(),'SCADUTO',IIf(ps.data_scadenza<=Date()+30,'URGENTE_30GG',IIf(ps.data_scadenza<=Date()+90,'IN_SCADENZA_90GG','REGOLARE'))) AS stato_scadenza FROM personale AS p INNER JOIN passaporto_servizio AS ps ON p.id=ps.personale_id"
    SalvaQuery "qryDashboard", "SELECT (SELECT Count(*) FROM personale WHERE stato_servizio='In Servizio') AS totale_personale,(SELECT Count(*) FROM corso) AS totale_corsi,(SELECT Count(*) FROM qryScadenzePatenti WHERE stato_scadenza<>'REGOLARE') AS patenti_alert,(SELECT Count(*) FROM qryScadenzePassaporti WHERE stato_scadenza<>'REGOLARE') AS passaporti_alert"
End Sub

Private Sub CreaDatiDemo()
    If DCount("*", "personale") > 0 Then Exit Sub
    Esegui "INSERT INTO corso(codice_corso,denominazione,ente_erogatore,durata_ore,validita_mesi,prerequisiti,fonte_catalogo,created_at) VALUES ('COR-BLSD-01','Operatore BLSD','Croce Rossa Italiana',12,24,'Idoneita fisica','Manuale',Now())"
    Esegui "INSERT INTO corso(codice_corso,denominazione,ente_erogatore,durata_ore,prerequisiti,fonte_catalogo,created_at) VALUES ('COR-GUIDA-02','Guida Sicura Operativa','Centro Addestramento',40,'Patente civile B','Manuale',Now())"
    Persona "MAT-10482", "RSSMRA80A01H501U", "Rossi", "Mario", 1980, 1, 1, "Roma", "Capitano", "Ufficio Piani ed Intelligence"
    Persona "MAT-11230", "BNCGPP85E12F205K", "Bianchi", "Giuseppe", 1985, 5, 12, "Milano", "Maresciallo Capo", "Sezione Studi Speciali"
End Sub

Private Sub Persona(matricola As String, cf As String, cognome As String, nome As String, anno As Long, mese As Long, giorno As Long, luogo As String, grado As String, reparto As String)
    Esegui "INSERT INTO personale(matricola,codice_fiscale,cognome,nome,sesso,data_nascita,luogo_nascita,grado_qualifica,reparto_ufficio,stato_servizio,created_at,updated_at) VALUES ('" & matricola & "','" & cf & "','" & cognome & "','" & nome & "','M',DateSerial(" & anno & "," & mese & "," & giorno & "),'" & luogo & "','" & grado & "','" & reparto & "','In Servizio',Now(),Now())"
End Sub

Private Sub CreaMaschere()
    CreaMaschera "frmDashboard", "qryDashboard", "Cruscotto", Array("totale_personale", "totale_corsi", "patenti_alert", "passaporti_alert")
    CreaMaschera "frmPersonale", "personale", "Personale", Array("matricola", "codice_fiscale", "cognome", "nome", "sesso", "data_nascita", "grado_qualifica", "reparto_ufficio", "stato_servizio", "telefono", "note_generali")
    CreaMaschera "frmCorsi", "corso", "Catalogo Corsi", Array("codice_corso", "denominazione", "ente_erogatore", "durata_ore", "validita_mesi", "prerequisiti", "descrizione")
    CreaMaschera "frmScadenzario", "qryScadenzePatenti", "Scadenzario", Array("cognome", "nome", "tipo_patente", "categoria", "numero_patente", "data_scadenza", "giorni_alla_scadenza", "stato_scadenza")
    CreaMaschera "frmNote", "nota_caratteristica", "Note Caratteristiche", Array("personale_id", "tipologia_documento", "motivo_redazione", "periodo_dal", "periodo_al", "data_prossima_scadenza", "giudizio_finale", "annotazioni")
    CreaMaschera "frmPassaporti", "passaporto_servizio", "Passaporti", Array("personale_id", "numero_passaporto", "tipo_passaporto", "data_rilascio", "data_scadenza", "stato", "ubicazione_custodia", "note")
End Sub

Private Sub CreaMaschera(nome As String, origine As String, titolo As String, campi As Variant)
    Dim f As Object, c As Object, i As Long, y As Long, temporaneo As String
    On Error Resume Next
    DoCmd.DeleteObject acForm, nome
    On Error GoTo 0
    Set f = CreateForm
    temporaneo = f.Name
    f.RecordSource = origine
    f.Caption = titolo
    f.Width = 11000
    y = 300
    For i = LBound(campi) To UBound(campi)
        Set c = CreateControl(temporaneo, acTextBox, acDetail, , CStr(campi(i)), 300, y, 6500, 360)
        c.Name = "txt_" & CStr(campi(i))
        c.ControlSource = CStr(campi(i))
        Set c = CreateControl(temporaneo, acLabel, acDetail, , , 7000, y, 3000, 360)
        c.Caption = Replace(CStr(campi(i)), "_", " ")
        y = y + 430
    Next i
    Set c = CreateControl(temporaneo, acCommandButton, acDetail, , , 300, y, 2200, 450)
    c.Caption = "Nuovo record"
    c.OnClick = "=NuovoRecord()"
    Set c = CreateControl(temporaneo, acCommandButton, acDetail, , , 2700, y, 2200, 450)
    c.Caption = "Elimina record"
    c.OnClick = "=EliminaRecord()"
    DoCmd.Save acForm, temporaneo
    DoCmd.Close acForm, temporaneo, acSaveYes
    DoCmd.Rename nome, acForm, temporaneo
End Sub

Public Function NuovoRecord() As Boolean
    DoCmd.GoToRecord , , acNewRec
    NuovoRecord = True
End Function

Public Function EliminaRecord() As Boolean
    If MsgBox("Eliminare il record corrente?", vbYesNo + vbQuestion) = vbYes Then DoCmd.RunCommand acCmdDeleteRecord
    EliminaRecord = True
End Function

Private Sub Esegui(sqlText As String)
    CurrentDb.Execute sqlText, EXEC_FAIL
End Sub

Private Sub SalvaQuery(nome As String, sqlText As String)
    On Error Resume Next
    CurrentDb.QueryDefs.Delete nome
    On Error GoTo 0
    CurrentDb.CreateQueryDef nome, sqlText
End Sub

Private Sub EliminaTabella(db As Object, nome As String)
    On Error Resume Next
    db.TableDefs.Delete nome
    On Error GoTo 0
End Sub

Private Sub EliminaRelazioni(db As Object)
    On Error Resume Next
    db.Relations.Delete "rel_personale_patente"
    db.Relations.Delete "rel_personale_note"
    db.Relations.Delete "rel_personale_passaporto"
    db.Relations.Delete "rel_personale_partecipazione"
    db.Relations.Delete "rel_corso_partecipazione"
    On Error GoTo 0
End Sub
