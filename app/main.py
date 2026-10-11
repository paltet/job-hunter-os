import streamlit as st

import db

STATUSES = ["saved", "applied", "interview", "offer", "rejected", "withdrawn"]
WORK_MODES = ["", "remote", "hybrid", "onsite"]

st.set_page_config(page_title="Job Hunter OS", layout="wide")
st.title("Job Hunter OS")

# --- Formulario para añadir una oferta ---
with st.form("new_application", clear_on_submit=True):
    st.subheader("Nueva candidatura")
    company = st.text_input("Empresa")
    title = st.text_input("Puesto")
    url = st.text_input("Enlace de la oferta")
    source = st.text_input("Fuente (LinkedIn, web de la empresa...)")
    work_mode = st.selectbox("Modalidad", WORK_MODES)
    status = st.selectbox("Estado", STATUSES)
    submitted = st.form_submit_button("Guardar")

if submitted:
    if not company.strip() or not title.strip():
        st.error("Empresa y puesto son obligatorios.")
    else:
        db.add_application(
            company.strip(), title.strip(), url.strip(),
            source.strip(), work_mode or None, status,
        )
        st.success("Candidatura guardada.")

# --- Tabla de candidaturas ---
st.subheader("Candidaturas")
rows = db.list_applications()
if rows:
    st.dataframe(rows, use_container_width=True, hide_index=True)
else:
    st.info("Todavía no hay candidaturas. Añade la primera arriba.")

# --- Cambiar el estado de una candidatura ---
if rows:
    st.subheader("Cambiar estado")
    options = {f"#{r['id']} · {r['company']} — {r['job_title']}": r for r in rows}
    choice = st.selectbox("Candidatura", list(options))
    new_status = st.selectbox("Nuevo estado", STATUSES, key="new_status")
    if st.button("Actualizar"):
        db.update_status(options[choice]["id"], new_status)
        st.rerun()