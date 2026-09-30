import streamlit as st

from src.ui import inject_css, init_session_state
from src.views import (
    render_sidebar,
    render_conciliacion,
    render_epicas,
    MODO_CONCILIACION,
)


st.set_page_config(
    page_title="BMC \u2194 Jira | Conciliacion",
    page_icon="\U0001F310",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()
init_session_state()

modo, archivos = render_sidebar()

if modo == MODO_CONCILIACION:
    render_conciliacion(archivos)
else:
    render_epicas(archivos)
