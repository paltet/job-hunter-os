import os
from datetime import date, datetime, timedelta, timezone

import psycopg
from psycopg.rows import dict_row


def get_conn():
    # Los datos de conexión vienen de variables de entorno (de tu .env),
    # nunca escritos en el código.
    return psycopg.connect(
        host=os.environ["POSTGRES_HOST"],
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        row_factory=dict_row,  # cada fila llega como diccionario
    )


def add_application(company, title, url, source, work_mode, status):
    # "with" abre una transacción: si todo va bien se confirma (commit) al salir;
    # si algo falla, se deshace entero. Así no quedan datos a medias.
    with get_conn() as conn:
        # Crea la empresa o, si ya existe, reutiliza su id (upsert)
        company_id = conn.execute(
            """INSERT INTO companies (name) VALUES (%s)
               ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
               RETURNING id""",
            (company,),
        ).fetchone()["id"]

        applied_at = date.today() if status == "applied" else None
        app_id = conn.execute(
            """INSERT INTO applications
                   (company_id, job_title, job_url, source, work_mode, status, applied_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s)
               RETURNING id""",
            (company_id, title, url or None, source or None,
             work_mode, status, applied_at),
        ).fetchone()["id"]

        conn.execute(
            "INSERT INTO status_history (application_id, old_status, new_status) "
            "VALUES (%s, NULL, %s)",
            (app_id, status),
        )


def list_applications():
    with get_conn() as conn:
        return conn.execute(
            """SELECT a.id, c.name AS company, a.job_title, a.status,
                      a.work_mode, a.source, a.applied_at, a.job_url
               FROM applications a
               JOIN companies c ON c.id = a.company_id
               ORDER BY a.updated_at DESC"""
        ).fetchall()


def update_status(app_id, new_status):
    with get_conn() as conn:
        # FOR UPDATE bloquea la fila mientras dura la transacción
        old = conn.execute(
            "SELECT status FROM applications WHERE id = %s FOR UPDATE", (app_id,)
        ).fetchone()["status"]
        if old == new_status:
            return

        applied_date = date.today() if new_status == "applied" else None
        conn.execute(
            """UPDATE applications
               SET status = %s, updated_at = now(),
                   applied_at = COALESCE(applied_at, %s)
               WHERE id = %s""",
            (new_status, applied_date, app_id),
        )
        conn.execute(
            "INSERT INTO status_history (application_id, old_status, new_status) "
            "VALUES (%s, %s, %s)",
            (app_id, old, new_status),
        )

def add_meeting(application_id, kind, title, scheduled_at, location_or_link):
    # Todo en una sola transacción: la reunión y sus recordatorios se guardan
    # juntos o no se guarda nada.
    with get_conn() as conn:
        meeting_id = conn.execute(
            """INSERT INTO meetings (application_id, kind, title, scheduled_at, location_or_link)
               VALUES (%s, %s, %s, %s, %s) RETURNING id""",
            (application_id, kind, title, scheduled_at, location_or_link or None),
        ).fetchone()["id"]

        info = conn.execute(
            """SELECT c.name AS company, a.job_title
               FROM applications a JOIN companies c ON c.id = a.company_id
               WHERE a.id = %s""",
            (application_id,),
        ).fetchone()

        # Dos avisos automáticos: un día antes y una hora antes.
        # Si la hora del aviso ya pasó, no se crea.
        now = datetime.now(timezone.utc)
        for delta, label in ((timedelta(days=1), "mañana"), (timedelta(hours=1), "en 1 hora")):
            due_at = scheduled_at - delta
            if due_at > now:
                conn.execute(
                    """INSERT INTO reminders (application_id, meeting_id, due_at, message)
                       VALUES (%s, %s, %s, %s)""",
                    (application_id, meeting_id, due_at,
                     f"{info['company']} · {info['job_title']}: {title} {label}"),
                )
        return meeting_id


def list_meetings(application_id):
    with get_conn() as conn:
        return conn.execute(
            """SELECT id, kind, title, scheduled_at, location_or_link
               FROM meetings WHERE application_id = %s ORDER BY scheduled_at""",
            (application_id,),
        ).fetchall()


def add_note(application_id, body, meeting_id=None):
    with get_conn() as conn:
        if meeting_id is not None:
            # La reunión debe pertenecer a esta candidatura
            ok = conn.execute(
                "SELECT 1 FROM meetings WHERE id = %s AND application_id = %s",
                (meeting_id, application_id),
            ).fetchone()
            if not ok:
                raise ValueError("La reunión no pertenece a esta candidatura")
        conn.execute(
            "INSERT INTO notes (application_id, meeting_id, body) VALUES (%s, %s, %s)",
            (application_id, meeting_id, body),
        )


def list_notes(application_id):
    # LEFT JOIN: las notas sin reunión también aparecen (meeting_title queda vacío)
    with get_conn() as conn:
        return conn.execute(
            """SELECT n.id, n.body, n.created_at, m.title AS meeting_title
               FROM notes n LEFT JOIN meetings m ON m.id = n.meeting_id
               WHERE n.application_id = %s
               ORDER BY n.created_at DESC""",
            (application_id,),
        ).fetchall()

def related_counts(application_id):
    # Cuántas cosas colgadas de la candidatura se borrarían con ella.
    # %(id)s es un parámetro con nombre: sirve para repetir el mismo valor.
    with get_conn() as conn:
        return conn.execute(
            """SELECT
                 (SELECT COUNT(*) FROM meetings       WHERE application_id = %(id)s) AS meetings,
                 (SELECT COUNT(*) FROM notes          WHERE application_id = %(id)s) AS notes,
                 (SELECT COUNT(*) FROM reminders      WHERE application_id = %(id)s) AS reminders,
                 (SELECT COUNT(*) FROM status_history WHERE application_id = %(id)s) AS history""",
            {"id": application_id},
        ).fetchone()


def delete_application(application_id):
    with get_conn() as conn:
        row = conn.execute(
            "DELETE FROM applications WHERE id = %s RETURNING id", (application_id,)
        ).fetchone()
        return row is not None   # False si no existía