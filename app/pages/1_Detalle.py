from datetime import date, datetime, time
from zoneinfo import ZoneInfo

import streamlit as st

import db

TZ = ZoneInfo("Europe/Madrid")
KINDS = {
    "recruiter_call": "Llamada con recruiter",
    "technical": "Técnica",
    "hr": "RRHH",
    "final": "Final",
    "other": "Otra",
}

st.set_page_config(page_title="Detalle · Job Hunter OS", layout="wide")
st.title("Detalle de candidatura")

apps = db.list_applications()
if not apps:
    st.info("Aún no hay candidaturas. Crea una en la página principal.")
    st.stop()

options = {f"#{a['id']} · {a['company']} — {a['job_title']}": a for a in apps}
choice = st.selectbox("Candidatura", list(options))
app_id = options[choice]["id"]

meetings = db.list_meetings(app_id)
col_meetings, col_notes = st.columns(2)

# ---------- Reuniones ----------
with col_meetings:
    st.subheader("Reuniones")
    for m in meetings:
        when = m["scheduled_at"].astimezone(TZ).strftime("%d/%m/%Y %H:%M")
        st.markdown(f"**{m['title']}** · {KINDS[m['kind']]} · {when}")
        if m["location_or_link"]:
            st.caption(m["location_or_link"])
    if not meetings:
        st.caption("Sin reuniones todavía.")

    with st.form("new_meeting", clear_on_submit=True):
        st.markdown("**Nueva reunión**")
        title = st.text_input("Título")
        kind = st.selectbox("Tipo", list(KINDS), format_func=KINDS.get)
        day = st.date_input("Fecha", value=date.today())
        hour = st.time_input("Hora", value=time(10, 0))
        place = st.text_input("Enlace o lugar")
        if st.form_submit_button("Guardar reunión"):
            if not title.strip():
                st.error("El título es obligatorio.")
            else:
                # La fecha que escribes es hora de Madrid; en la base se guarda en UTC
                scheduled = datetime.combine(day, hour, tzinfo=TZ)
                db.add_meeting(app_id, kind, title.strip(), scheduled, place.strip())
                st.rerun()

# ---------- Notas ----------
with col_notes:
    st.subheader("Notas")
    targets = {"General (candidatura)": None}
    for m in meetings:
        when = m["scheduled_at"].astimezone(TZ).strftime("%d/%m %H:%M")
        targets[f"#{m['id']} {m['title']} ({when})"] = m["id"]

    with st.form("new_note", clear_on_submit=True):
        target = st.selectbox("Asociar a", list(targets))
        body = st.text_area("Nota")
        if st.form_submit_button("Añadir nota"):
            if not body.strip():
                st.error("La nota está vacía.")
            else:
                db.add_note(app_id, body.strip(), targets[target])
                st.rerun()

    st.markdown("**Cronología (todas las notas)**")
    notes = db.list_notes(app_id)
    if not notes:
        st.caption("Sin notas todavía.")
    for n in notes:
        when = n["created_at"].astimezone(TZ).strftime("%d/%m/%Y %H:%M")
        origin = n["meeting_title"] or "General"
        st.markdown(f"*{when}* · **{origin}**")
        st.markdown(n["body"])
        st.divider()