"""
Componentes de UI compartidos: estilos CSS, sidebar, funciones de visualizacion.
"""
import streamlit as st
import pandas as pd


CSS_TECH_THEME = """
<style>
    :root {
        --slate-50:  #f8fafc;
        --slate-100: #f1f5f9;
        --slate-200: #e2e8f0;
        --slate-300: #cbd5e1;
        --slate-400: #94a3b8;
        --slate-500: #64748b;
        --slate-600: #475569;
        --slate-700: #334155;
        --slate-800: #1e293b;
        --slate-900: #0f172a;
        --emerald:   #10b981;
        --amber:     #f59e0b;
        --red:       #ef4444;
        --blue:      #3b82f6;
    }

    /* --- Global --- */
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 1rem;
        max-width: 1400px;
    }

    .stApp {
        background: var(--slate-50);
    }

    /* --- Sidebar --- */
    [data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid var(--slate-200);
    }
    [data-testid="stSidebar"] .block-container {
        padding-top: 1rem;
    }

    /* --- Tabs --- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.25rem;
        border-bottom: 1px solid var(--slate-200);
        padding-bottom: 0;
    }
    .stTabs [data-baseweb="tab"] {
        height: 44px;
        font-size: 15px;
        font-weight: 500;
        color: var(--slate-500);
        border-radius: 8px 8px 0 0;
        padding: 0 20px;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: var(--slate-800);
        background: #ffffff;
        border: 1px solid var(--slate-200);
        border-bottom-color: #ffffff;
    }

    /* --- Metrics --- */
    [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid var(--slate-200);
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    }
    [data-testid="stMetric"] label {
        font-size: 13px;
        color: var(--slate-500) !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: 700;
        color: var(--slate-800);
    }

    /* --- Dataframes --- */
    [data-testid="stDataFrame"] {
        border: 1px solid var(--slate-200);
        border-radius: 10px;
        overflow: hidden;
    }

    /* --- Buttons --- */
    .stDownloadButton button {
        background: var(--blue) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        padding: 0.5rem 1.25rem !important;
        transition: all 0.15s;
    }
    .stDownloadButton button:hover {
        opacity: 0.9;
    }

    /* --- File uploaders --- */
    [data-testid="stFileUploader"] section {
        border-radius: 8px;
        border: 1px dashed var(--slate-300);
    }

    /* --- Containers (border=True cards) --- */
    [data-testid="stNotification"] {
        border-radius: 10px;
    }

    /* --- Hide Streamlit branding --- */
    #MainMenu, footer, header[data-testid="stHeader"] {
        display: none;
    }

    /* --- Info / Warning spacing --- */
    .stAlert {
        border-radius: 8px;
    }
</style>
"""


def inject_css():
    """Inyecta el CSS del tema tech minimalista."""
    st.markdown(CSS_TECH_THEME, unsafe_allow_html=True)


def init_session_state():
    """Inicializa las claves de session state para DataFrames."""
    for key in [
        "df_bmc_wo", "df_bmc_pbi", "df_jira",
        "df_bmc_total", "df_merge", "df_resultado",
        "df_epicas", "df_tareas",
        "df_epicas_filt", "df_tareas_filt", "df_tareas_agg",
        "df_epic_merge", "df_epic_resultado",
    ]:
        if key not in st.session_state:
            st.session_state[key] = None


def limpiar_datos_conciliacion():
    """Limpia solo las claves de datos del modo Conciliacion."""
    for key in ["df_bmc_wo", "df_bmc_pbi", "df_jira",
                "df_bmc_total", "df_merge", "df_resultado"]:
        if key in st.session_state:
            del st.session_state[key]


def limpiar_datos_epicas():
    """Limpia solo las claves de datos del modo Epicas."""
    for key in ["df_epicas", "df_tareas", "df_epicas_filt",
                "df_tareas_filt", "df_tareas_agg",
                "df_epic_merge", "df_epic_resultado"]:
        if key in st.session_state:
            del st.session_state[key]


def mostrar_resumen(df: pd.DataFrame, label: str) -> None:
    """Muestra shape, columnas y primeras filas de un DataFrame."""
    if df is None or df.empty:
        return

    st.subheader(f"{label}")
    shape_col, cols_col = st.columns([1, 3])
    shape_col.metric("Dimensiones", f"{df.shape[0]:,} filas x {df.shape[1]:,} columnas")
    with cols_col.expander("Columnas detectadas"):
        st.write(df.columns.tolist())

    st.dataframe(df.head(5), use_container_width=True)
    st.markdown("---")


def badge_cargado(label: str, df_key: str) -> None:
    """Muestra un badge de estado de carga en el sidebar."""
    df = st.session_state.get(df_key)
    if df is not None:
        filas = df.shape[0]
        cols = df.shape[1]
        st.markdown(
            f'<p style="font-size:11px;color:#10b981;margin:0 0 0.25rem 0.5rem;">'
            f'\u2705 {label} — {filas:,} filas, {cols} cols'
            f'</p>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<p style="font-size:11px;color:#94a3b8;margin:0 0 0.25rem 0.5rem;">'
            f'\u25CB {label} — Pendiente'
            f'</p>',
            unsafe_allow_html=True,
        )
