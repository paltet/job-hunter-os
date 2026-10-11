-- Empresas
CREATE TABLE companies (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,
    website     TEXT,
    notes       TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Candidaturas
CREATE TABLE applications (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    company_id      BIGINT NOT NULL REFERENCES companies(id),
    job_title       TEXT NOT NULL,
    job_url         TEXT,
    source          TEXT,                       -- dónde la encontraste (LinkedIn, web de la empresa...)
    location        TEXT,
    work_mode       TEXT CHECK (work_mode IN ('remote', 'hybrid', 'onsite')),
    status          TEXT NOT NULL DEFAULT 'saved'
                    CHECK (status IN ('saved', 'applied', 'interview', 'offer', 'rejected', 'withdrawn')),
    applied_at      DATE,
    next_action_at  DATE,                       -- cuándo toca hacer algo
    cv_version      TEXT,                       -- qué CV enviaste
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Historial de estados
CREATE TABLE status_history (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    application_id  BIGINT NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    old_status      TEXT,
    new_status      TEXT NOT NULL,
    changed_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    note            TEXT
);

-- Correos detectados
CREATE TABLE email_events (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    application_id  BIGINT REFERENCES applications(id) ON DELETE SET NULL,
    message_id      TEXT NOT NULL UNIQUE,       -- ID único del correo: evita duplicados
    sender          TEXT,
    subject         TEXT,
    received_at     TIMESTAMPTZ,
    detected_type   TEXT CHECK (detected_type IN ('confirmation', 'rejection', 'interview', 'other')),
    confirmed       BOOLEAN NOT NULL DEFAULT false,  -- ¿lo has aprobado tú?
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Recordatorios
CREATE TABLE reminders (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    application_id  BIGINT NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    due_at          TIMESTAMPTZ NOT NULL,
    message         TEXT NOT NULL,
    done            BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Índices para las consultas que haremos más a menudo
CREATE INDEX idx_applications_status ON applications(status);
CREATE INDEX idx_applications_next_action ON applications(next_action_at);
CREATE INDEX idx_reminders_pending ON reminders(due_at) WHERE NOT done;