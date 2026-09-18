/*
   Schema SQL Server per Gestione Personale.
   Da eseguire nel database aziendale dopo la verifica dell'amministratore.
*/

IF OBJECT_ID(N'dbo.personale', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.personale (
        id INT IDENTITY(1,1) NOT NULL CONSTRAINT pk_personale PRIMARY KEY,
        matricola NVARCHAR(50) NOT NULL CONSTRAINT uq_personale_matricola UNIQUE,
        codice_fiscale NVARCHAR(16) NOT NULL CONSTRAINT uq_personale_codice_fiscale UNIQUE,
        cognome NVARCHAR(100) NOT NULL,
        nome NVARCHAR(100) NOT NULL,
        sesso NVARCHAR(10) NULL CONSTRAINT ck_personale_sesso CHECK (sesso IN (N'M', N'F', N'Altro')),
        data_nascita DATE NOT NULL,
        luogo_nascita NVARCHAR(150) NOT NULL,
        provincia_nascita NVARCHAR(10) NULL,
        grado_qualifica NVARCHAR(150) NOT NULL,
        reparto_ufficio NVARCHAR(150) NOT NULL,
        incarico NVARCHAR(200) NULL,
        posto_tabellare NVARCHAR(200) NULL,
        data_arruolamento_assunzione DATE NULL,
        stato_servizio NVARCHAR(50) NOT NULL CONSTRAINT df_personale_stato_servizio DEFAULT N'In Servizio',
        email_istituzionale NVARCHAR(254) NULL,
        email_personale NVARCHAR(254) NULL,
        telefono NVARCHAR(50) NULL,
        indirizzo_residenza NVARCHAR(300) NULL,
        livello_nos NVARCHAR(100) NULL CONSTRAINT df_personale_livello_nos DEFAULT N'Riservato',
        lingua_inglese NVARCHAR(100) NULL CONSTRAINT df_personale_lingua DEFAULT N'NATO JFLT 8',
        note_generali NVARCHAR(MAX) NULL,
        created_at DATETIME2(0) NOT NULL CONSTRAINT df_personale_created_at DEFAULT SYSDATETIME(),
        updated_at DATETIME2(0) NOT NULL CONSTRAINT df_personale_updated_at DEFAULT SYSDATETIME(),
        CONSTRAINT ck_personale_stato CHECK (stato_servizio IN (N'In Servizio', N'Congedo', N'Licenza Straordinaria', N'Distaccato', N'Altro'))
    );
END;
GO

IF OBJECT_ID(N'dbo.patente', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.patente (
        id INT IDENTITY(1,1) NOT NULL CONSTRAINT pk_patente PRIMARY KEY,
        personale_id INT NOT NULL,
        tipo_patente NVARCHAR(30) NOT NULL,
        categoria NVARCHAR(100) NOT NULL,
        numero_patente NVARCHAR(100) NOT NULL,
        ente_rilascio NVARCHAR(200) NOT NULL,
        data_rilascio DATE NOT NULL,
        data_scadenza DATE NOT NULL,
        limitazioni_abilitazioni NVARCHAR(500) NULL,
        created_at DATETIME2(0) NOT NULL CONSTRAINT df_patente_created_at DEFAULT SYSDATETIME(),
        CONSTRAINT fk_patente_personale FOREIGN KEY (personale_id) REFERENCES dbo.personale(id) ON DELETE CASCADE,
        CONSTRAINT ck_patente_tipo CHECK (tipo_patente IN (N'Civile', N'Servizio/Militare', N'CQC', N'Altro'))
    );
END;
GO

IF OBJECT_ID(N'dbo.corso', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.corso (
        id INT IDENTITY(1,1) NOT NULL CONSTRAINT pk_corso PRIMARY KEY,
        codice_corso NVARCHAR(100) NOT NULL CONSTRAINT uq_corso_codice UNIQUE,
        denominazione NVARCHAR(300) NOT NULL,
        ente_erogatore NVARCHAR(200) NOT NULL,
        durata_settimane INT NULL,
        durata_ore INT NULL,
        validita_mesi INT NULL,
        requisiti_sicurezza NVARCHAR(500) NULL,
        precedenti_formativi NVARCHAR(MAX) NULL,
        precedenti_operativi NVARCHAR(MAX) NULL,
        selezioni NVARCHAR(MAX) NULL,
        conoscenza_lingua NVARCHAR(500) NULL,
        altri_requisiti NVARCHAR(MAX) NULL,
        prerequisiti NVARCHAR(MAX) NULL,
        fonte_catalogo NVARCHAR(300) NULL CONSTRAINT df_corso_fonte DEFAULT N'Manuale',
        descrizione NVARCHAR(MAX) NULL,
        created_at DATETIME2(0) NOT NULL CONSTRAINT df_corso_created_at DEFAULT SYSDATETIME()
    );
END;
GO

IF OBJECT_ID(N'dbo.partecipazione_corso', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.partecipazione_corso (
        id INT IDENTITY(1,1) NOT NULL CONSTRAINT pk_partecipazione_corso PRIMARY KEY,
        personale_id INT NOT NULL,
        corso_id INT NOT NULL,
        data_inizio DATE NOT NULL,
        data_fine DATE NOT NULL,
        esito NVARCHAR(30) NOT NULL,
        numero_attestato NVARCHAR(100) NULL,
        data_scadenza_abilitazione DATE NULL,
        note NVARCHAR(MAX) NULL,
        created_at DATETIME2(0) NOT NULL CONSTRAINT df_partecipazione_created_at DEFAULT SYSDATETIME(),
        CONSTRAINT fk_partecipazione_personale FOREIGN KEY (personale_id) REFERENCES dbo.personale(id) ON DELETE CASCADE,
        CONSTRAINT fk_partecipazione_corso FOREIGN KEY (corso_id) REFERENCES dbo.corso(id),
        CONSTRAINT ck_partecipazione_esito CHECK (esito IN (N'Superato', N'Idoneo', N'Qualificato', N'Specializzato', N'Non Idoneo', N'Frequentato'))
    );
END;
GO

IF OBJECT_ID(N'dbo.nota_caratteristica', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.nota_caratteristica (
        id INT IDENTITY(1,1) NOT NULL CONSTRAINT pk_nota_caratteristica PRIMARY KEY,
        personale_id INT NOT NULL,
        tipologia_documento NVARCHAR(50) NOT NULL,
        motivo_redazione NVARCHAR(50) NOT NULL,
        periodo_dal DATE NOT NULL,
        periodo_al DATE NOT NULL,
        data_firma_interessato DATE NULL,
        data_prossima_scadenza DATE NOT NULL,
        giudizio_finale NVARCHAR(50) NULL,
        compilatore NVARCHAR(200) NULL,
        primo_revisore NVARCHAR(200) NULL,
        secondo_revisore NVARCHAR(200) NULL,
        annotazioni NVARCHAR(MAX) NULL,
        created_at DATETIME2(0) NOT NULL CONSTRAINT df_nota_created_at DEFAULT SYSDATETIME(),
        CONSTRAINT fk_nota_personale FOREIGN KEY (personale_id) REFERENCES dbo.personale(id) ON DELETE CASCADE
    );
END;
GO

IF OBJECT_ID(N'dbo.passaporto_servizio', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.passaporto_servizio (
        id INT IDENTITY(1,1) NOT NULL CONSTRAINT pk_passaporto_servizio PRIMARY KEY,
        personale_id INT NOT NULL,
        numero_passaporto NVARCHAR(100) NOT NULL CONSTRAINT uq_passaporto_numero UNIQUE,
        tipo_passaporto NVARCHAR(30) NOT NULL CONSTRAINT df_passaporto_tipo DEFAULT N'Servizio',
        autorita_rilascio NVARCHAR(300) NOT NULL CONSTRAINT df_passaporto_autorita DEFAULT N'Ministero Affari Esteri e Cooperazione Internazionale',
        data_rilascio DATE NOT NULL,
        data_scadenza DATE NOT NULL,
        stato NVARCHAR(30) NOT NULL CONSTRAINT df_passaporto_stato DEFAULT N'Valido',
        ubicazione_custodia NVARCHAR(200) NOT NULL CONSTRAINT df_passaporto_ubicazione DEFAULT N'Archivio Ufficio Personale',
        note NVARCHAR(MAX) NULL,
        created_at DATETIME2(0) NOT NULL CONSTRAINT df_passaporto_created_at DEFAULT SYSDATETIME(),
        CONSTRAINT fk_passaporto_personale FOREIGN KEY (personale_id) REFERENCES dbo.personale(id) ON DELETE CASCADE,
        CONSTRAINT ck_passaporto_tipo CHECK (tipo_passaporto IN (N'Servizio', N'Diplomatico', N'Speciale')),
        CONSTRAINT ck_passaporto_stato CHECK (stato IN (N'Valido', N'In Rinnovo', N'Scaduto', N'Restituito', N'Smarrito'))
    );
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'ix_personale_cognome_nome' AND object_id = OBJECT_ID(N'dbo.personale'))
    CREATE INDEX ix_personale_cognome_nome ON dbo.personale(cognome, nome);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'ix_patente_scadenza' AND object_id = OBJECT_ID(N'dbo.patente'))
    CREATE INDEX ix_patente_scadenza ON dbo.patente(data_scadenza);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'ix_nota_scadenza' AND object_id = OBJECT_ID(N'dbo.nota_caratteristica'))
    CREATE INDEX ix_nota_scadenza ON dbo.nota_caratteristica(data_prossima_scadenza);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'ix_passaporto_scadenza' AND object_id = OBJECT_ID(N'dbo.passaporto_servizio'))
    CREATE INDEX ix_passaporto_scadenza ON dbo.passaporto_servizio(data_scadenza);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'ix_partecipazione_personale' AND object_id = OBJECT_ID(N'dbo.partecipazione_corso'))
    CREATE INDEX ix_partecipazione_personale ON dbo.partecipazione_corso(personale_id);
GO

CREATE OR ALTER VIEW dbo.vista_ultima_nota_personale
AS
WITH ultima_nota AS (
    SELECT nc.*, ROW_NUMBER() OVER (
        PARTITION BY nc.personale_id
        ORDER BY nc.periodo_al DESC, nc.id DESC
    ) AS posizione
    FROM dbo.nota_caratteristica AS nc
)
SELECT
    nc.id AS nota_id,
    p.id AS personale_id,
    p.matricola,
    p.grado_qualifica,
    p.cognome,
    p.nome,
    p.reparto_ufficio,
    nc.tipologia_documento,
    nc.motivo_redazione,
    nc.periodo_dal,
    nc.periodo_al,
    nc.data_firma_interessato,
    nc.data_prossima_scadenza,
    nc.giudizio_finale,
    DATEDIFF(DAY, CAST(SYSDATETIME() AS DATE), nc.data_prossima_scadenza) AS giorni_alla_scadenza,
    CASE
        WHEN nc.data_prossima_scadenza < CAST(SYSDATETIME() AS DATE) THEN N'SCADUTA'
        WHEN DATEDIFF(DAY, CAST(SYSDATETIME() AS DATE), nc.data_prossima_scadenza) <= 30 THEN N'URGENTE_30GG'
        WHEN DATEDIFF(DAY, CAST(SYSDATETIME() AS DATE), nc.data_prossima_scadenza) <= 60 THEN N'IN_SCADENZA_60GG'
        ELSE N'REGOLARE'
    END AS stato_scadenza
FROM ultima_nota AS nc
JOIN dbo.personale AS p ON p.id = nc.personale_id
WHERE nc.posizione = 1;
GO

CREATE OR ALTER VIEW dbo.vista_scadenze_patenti
AS
SELECT
    pat.id AS patente_id,
    p.id AS personale_id,
    p.matricola,
    p.grado_qualifica,
    p.cognome,
    p.nome,
    pat.tipo_patente,
    pat.categoria,
    pat.numero_patente,
    pat.data_scadenza,
    DATEDIFF(DAY, CAST(SYSDATETIME() AS DATE), pat.data_scadenza) AS giorni_alla_scadenza,
    CASE
        WHEN pat.data_scadenza < CAST(SYSDATETIME() AS DATE) THEN N'SCADUTA'
        WHEN DATEDIFF(DAY, CAST(SYSDATETIME() AS DATE), pat.data_scadenza) <= 30 THEN N'URGENTE_30GG'
        WHEN DATEDIFF(DAY, CAST(SYSDATETIME() AS DATE), pat.data_scadenza) <= 60 THEN N'IN_SCADENZA_60GG'
        ELSE N'REGOLARE'
    END AS stato_scadenza
FROM dbo.patente AS pat
JOIN dbo.personale AS p ON p.id = pat.personale_id;
GO

CREATE OR ALTER VIEW dbo.vista_scadenze_passaporti
AS
SELECT
    ps.id AS passaporto_id,
    p.id AS personale_id,
    p.matricola,
    p.grado_qualifica,
    p.cognome,
    p.nome,
    ps.numero_passaporto,
    ps.tipo_passaporto,
    ps.data_scadenza,
    ps.stato,
    ps.ubicazione_custodia,
    DATEDIFF(DAY, CAST(SYSDATETIME() AS DATE), ps.data_scadenza) AS giorni_alla_scadenza,
    CASE
        WHEN ps.data_scadenza < CAST(SYSDATETIME() AS DATE) THEN N'SCADUTO'
        WHEN DATEDIFF(DAY, CAST(SYSDATETIME() AS DATE), ps.data_scadenza) <= 30 THEN N'URGENTE_30GG'
        WHEN DATEDIFF(DAY, CAST(SYSDATETIME() AS DATE), ps.data_scadenza) <= 90 THEN N'IN_SCADENZA_90GG'
        ELSE N'REGOLARE'
    END AS stato_scadenza
FROM dbo.passaporto_servizio AS ps
JOIN dbo.personale AS p ON p.id = ps.personale_id;
GO