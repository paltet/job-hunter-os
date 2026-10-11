import os
from datetime import date

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