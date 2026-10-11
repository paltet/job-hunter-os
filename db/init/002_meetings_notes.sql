-- Reuniones de cada candidatura
CREATE TABLE IF NOT EXISTS meetings (
    id               BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    application_id   BIGINT NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    kind             TEXT NOT NULL DEFAULT 'other'
                     CHECK (kind IN ('recruiter_call', 'technical', 'hr', 'final', 'other')),
    title            TEXT NOT NULL,
    scheduled_at     TIMESTAMPTZ NOT NULL,
    location_or_link TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Notas: de la candidatura (meeting_id vacío) o de una reunión concreta
CREATE TABLE IF NOT EXISTS notes (
    id               BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    application_id   BIGINT NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    meeting_id       BIGINT REFERENCES meetings(id) ON DELETE CASCADE,
    body             TEXT NOT NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Los recordatorios pueden venir de una reunión y recordar si ya se enviaron
ALTER TABLE reminders
    ADD COLUMN IF NOT EXISTS meeting_id BIGINT REFERENCES meetings(id) ON DELETE CASCADE,
    ADD COLUMN IF NOT EXISTS sent_at    TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_meetings_application ON meetings(application_id, scheduled_at);
CREATE INDEX IF NOT EXISTS idx_notes_application ON notes(application_id, created_at);