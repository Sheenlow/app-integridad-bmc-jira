"""
Renderizado de la UI de Streamlit (sidebar + areas principales).
Extraido de app.py para reducir la complejidad del modulo de entrada.
"""
import hashlib
from datetime import date

import pandas as pd
import streamlit as st

from .constants import (
    COL_MERGE, COL_ACCION_SUGERIDA, COL_VALIDACION_EPICAS,
    COLUMNAS_PREVIEW_ACCIONES, COLUMNAS_OUTPUT_EPICAS,
    URL_WO_BMC, URL_PBI_BMC, URL_JIRA_FILTER,
    URL_EPICAS_JIRA, URL_TAREAS_JIRA,
    ALIASES_GRUPO_WO, ALIASES_GRUPO_PBI,
    VERSION,
    ACCION_OK, ACCION_FALTA_JIRA, ACCION_SOBRA_JIRA, ACCION_INCONGRUENCIA,
    ACCION_DEBERIA_EN_PROGRESO, ACCION_DEBERIA_BACKLOG,
    ACCION_DEBERIA_BACKLOG_STAND_BY,
)
from .io_utils import leer_archivo_subido
from .transform import (
    _resolver_columnas,
    _agregar_columnas_conciliacion,
    _formatear_output_conciliacion,
    _formatear_output_epicas,
    normalizar_bmc_wo,
    normalizar_bmc_pbi,
    unificar_bmc,
    filtrar_bmc_historico,
    filtrar_bmc_por_grupo,
    normalizar_jira,
    normalizar_epicas_tareas,
    cruzar_bmc_jira,
)
from .rules import aplicar_reglas_negocio, aplicar_validacion_epicas
from .epics import (
    filtrar_epicas,
    filtrar_tareas,
    agrupar_tareas_por_parent,
    cruzar_epicas_con_tareas,
)
from .excel_export import crear_excel
from .styles import obtener_estilo_accion
from .ui import (
    limpiar_datos_conciliacion,
    limpiar_datos_epicas,
    mostrar_resumen,
    badge_cargado,
)


MODO_CONCILIACION = "Conciliacion BMC vs Jira"
MODO_EPICAS = "Validacion Epicas vs Tareas"


# =============================================================================
# CACHE: funciones puras cacheadas para evitar reprocesamiento
# =============================================================================

def _hash_bytes(data: bytes) -> str:
    """Hash SHA-256 de bytes para usar como version en el cache."""
    return hashlib.sha256(data).hexdigest()[:16]


@st.cache_data(show_spinner=False)
def _pipeline_conciliacion(
    _hash_wo: str, df_wo_raw: pd.DataFrame | None,
    _hash_pbi: str, df_pbi_raw: pd.DataFrame | None,
    _hash_jira: str, df_jira_raw: pd.DataFrame | None,
) -> dict:
    """Ejecuta el pipeline de conciliacion y devuelve resultados cacheados."""
    df_wo_norm = normalizar_bmc_wo(df_wo_raw) if df_wo_raw is not None else None
    df_pbi_norm = normalizar_bmc_pbi(df_pbi_raw) if df_pbi_raw is not None else None

    # Filtrado defensivo por grupo de trabajo, inmediatamente tras normalizar
    # cada dataset de BMC y antes de unificar/cruzar con Jira.
    df_wo_norm = filtrar_bmc_por_grupo(df_wo_norm, ALIASES_GRUPO_WO) if df_wo_norm is not None else None
    df_pbi_norm = filtrar_bmc_por_grupo(df_pbi_norm, ALIASES_GRUPO_PBI) if df_pbi_norm is not None else None

    df_bmc_total = unificar_bmc(df_wo_norm, df_pbi_norm)
    df_jira_norm = normalizar_jira(df_jira_raw)

    if df_bmc_total is not None and df_jira_norm is not None:
        df_bmc_total = filtrar_bmc_historico(df_bmc_total, df_jira_norm)
        df_merge = cruzar_bmc_jira(df_bmc_total, df_jira_norm)
    else:
        df_merge = None

    if df_merge is not None:
        df_resultado = aplicar_reglas_negocio(df_merge)
        df_resultado = _agregar_columnas_conciliacion(df_resultado)
    else:
        df_resultado = None

    return {
        "df_bmc_total": df_bmc_total,
        "df_merge": df_merge,
        "df_resultado": df_resultado,
    }


@st.cache_data(show_spinner=False)
def _pipeline_epicas(
    _hash_epicas: str, df_epicas_raw: pd.DataFrame | None,
    _hash_tareas: str, df_tareas_raw: pd.DataFrame | None,
) -> dict:
    """Ejecuta el pipeline de validacion de epicas y devuelve resultados cacheados."""
    df_epicas_raw = normalizar_epicas_tareas(df_epicas_raw) if df_epicas_raw is not None else None
    df_tareas_raw = normalizar_epicas_tareas(df_tareas_raw) if df_tareas_raw is not None else None
    df_epicas_filt = filtrar_epicas(df_epicas_raw) if df_epicas_raw is not None else None
    df_tareas_filt = filtrar_tareas(df_tareas_raw) if df_tareas_raw is not None else None
    df_tareas_agg = agrupar_tareas_por_parent(df_tareas_filt, df_epicas_filt)

    if df_epicas_filt is not None and df_tareas_agg is not None:
        df_epic_merge = cruzar_epicas_con_tareas(df_epicas_filt, df_tareas_agg)
    else:
        df_epic_merge = None

    if df_epic_merge is not None:
        df_epic_resultado = aplicar_validacion_epicas(df_epic_merge)
    else:
        df_epic_resultado = None

    return {
        "df_epicas_filt": df_epicas_filt,
        "df_tareas_filt": df_tareas_filt,
        "df_tareas_agg": df_tareas_agg,
        "df_epic_merge": df_epic_merge,
        "df_epic_resultado": df_epic_resultado,
    }


# =============================================================================
# SIDEBAR: carga de archivos
# =============================================================================

def render_sidebar() -> tuple[str, dict]:
    """Renderiza el sidebar y devuelve (modo, archivos) con los uploaders."""
    archivo_bmc_wo = None
    archivo_bmc_pbi = None
    archivo_jira = None
    archivo_epicas = None
    archivo_tareas = None

    with st.sidebar:
        # Branding
        st.markdown(
            f"""
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:0.5rem;">
                <div style="background:var(--blue);width:36px;height:36px;border-radius:8px;
                            display:flex;align-items:center;justify-content:center;font-size:18px;">
                    \U0001F310
                </div>
                <div>
                    <div style="font-weight:700;font-size:15px;color:#0f172a;">BMC \u2194 Jira</div>
                    <div style="font-size:11px;color:#64748b;">Conciliacion {VERSION}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")

        modo = st.radio(
            "Navegacion",
            [MODO_CONCILIACION, MODO_EPICAS],
            key="nav_modo",
            label_visibility="collapsed",
        )

        st.markdown("---")

        if modo == MODO_CONCILIACION:

            st.markdown(
                '<p style="font-size:12px;font-weight:600;color:#64748b;'
                'text-transform:uppercase;letter-spacing:0.5px;margin-bottom:0.5rem;">'
                '\U0001F517 Descargar reportes</p>',
                unsafe_allow_html=True,
            )

            st.link_button("\U0001F4E4 WO BMC", URL_WO_BMC, use_container_width=True)
            st.link_button("\U0001F4E4 PBI BMC", URL_PBI_BMC, use_container_width=True)
            st.link_button("\U0001F4E4 Jira", URL_JIRA_FILTER, use_container_width=True)

            st.markdown("---")

            st.markdown(
                '<p style="font-size:12px;font-weight:600;color:#64748b;'
                'text-transform:uppercase;letter-spacing:0.5px;margin-bottom:0.5rem;">'
                '\U0001F4C2 Reportes</p>',
                unsafe_allow_html=True,
            )

            archivo_bmc_wo = st.file_uploader(
                "BMC \u2014 Work Orders (WO)",
                type=["csv", "xlsx"],
                key="upload_bmc_wo",
            )

            archivo_bmc_pbi = st.file_uploader(
                "BMC \u2014 Problemas (PBI)",
                type=["csv", "xlsx"],
                key="upload_bmc_pbi",
            )

            archivo_jira = st.file_uploader(
                "Jira",
                type=["csv", "xlsx"],
                key="upload_jira",
            )

            badge_cargado("WO", "df_bmc_wo")
            badge_cargado("PBI", "df_bmc_pbi")
            badge_cargado("Jira", "df_jira")

            st.markdown("---")

            cargados = sum(
                1 for key in ["df_bmc_wo", "df_bmc_pbi", "df_jira"]
                if st.session_state.get(key) is not None
            )
            st.progress(cargados / 3, text=f"Progreso: {cargados}/3 reportes")

            if st.button("\U0001F5D1\uFE0F Limpiar todo", use_container_width=True):
                limpiar_datos_conciliacion()
                st.rerun()

            st.markdown("---")
            st.caption("Formatos: **.csv** y **.xlsx**  \nColumnas referenciadas por nombre")

        elif modo == MODO_EPICAS:

            st.markdown(
                '<p style="font-size:12px;font-weight:600;color:#64748b;'
                'text-transform:uppercase;letter-spacing:0.5px;margin-bottom:0.5rem;">'
                '\U0001F517 Descargar reportes</p>',
                unsafe_allow_html=True,
            )

            st.link_button("\U0001F4E4 Epicas (Jira)", URL_EPICAS_JIRA, use_container_width=True)
            st.link_button("\U0001F4E4 Tareas e Historias (Jira)", URL_TAREAS_JIRA, use_container_width=True)

            st.markdown("---")

            st.markdown(
                '<p style="font-size:12px;font-weight:600;color:#64748b;'
                'text-transform:uppercase;letter-spacing:0.5px;margin-bottom:0.5rem;">'
                '\U0001F4C2 Reportes Jira</p>',
                unsafe_allow_html=True,
            )

            archivo_epicas = st.file_uploader(
                "Reporte de Epicas (Jira)",
                type=["csv", "xlsx"],
                key="upload_epicas",
            )

            archivo_tareas = st.file_uploader(
                "Reporte de Tareas e Historias (Jira)",
                type=["csv", "xlsx"],
                key="upload_tareas",
            )

            badge_cargado("Epicas", "df_epicas")
            badge_cargado("Tareas", "df_tareas")

            st.markdown("---")

            cargados_epicas = sum(
                1 for key in ["df_epicas", "df_tareas"]
                if st.session_state.get(key) is not None
            )
            st.progress(cargados_epicas / 2, text=f"Progreso: {cargados_epicas}/2 reportes")

            if st.button("\U0001F5D1\uFE0F Limpiar", use_container_width=True, key="limpiar_epicas"):
                limpiar_datos_epicas()
                st.rerun()

            st.markdown("---")
            st.caption("Formatos: **.csv** y **.xlsx**")

    archivos = {
        "wo": archivo_bmc_wo,
        "pbi": archivo_bmc_pbi,
        "jira": archivo_jira,
        "epicas": archivo_epicas,
        "tareas": archivo_tareas,
    }
    return modo, archivos


# =============================================================================
# CONCILIACION BMC vs Jira
# =============================================================================

def _dashboard_conciliacion() -> None:
    """Bloque de cabecera con el resumen ejecutivo de acciones."""
    acc = st.session_state.df_resultado[COL_ACCION_SUGERIDA].astype(str)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("\U0001F7E2 OK", int(acc.str.startswith(ACCION_OK).sum()))
    c2.metric("\U0001F7E1 Falta en Jira", int(acc.str.startswith(ACCION_FALTA_JIRA).sum()))
    c3.metric("\U0001F534 Sobra en Jira", int(acc.str.startswith(ACCION_SOBRA_JIRA).sum()))
    c4.metric(
        "\U0001F7E0 Incongruencias",
        int(
            (
                acc.str.startswith(ACCION_INCONGRUENCIA)
                | acc.str.startswith(ACCION_DEBERIA_EN_PROGRESO)
                | acc.str.startswith(ACCION_DEBERIA_BACKLOG)
                | acc.str.startswith(ACCION_DEBERIA_BACKLOG_STAND_BY)
            ).sum()
        ),
    )


def render_conciliacion(archivos: dict) -> None:
    """Area principal del modo Conciliacion BMC vs Jira."""
    archivo_bmc_wo = archivos["wo"]
    archivo_bmc_pbi = archivos["pbi"]
    archivo_jira = archivos["jira"]

    # --- Lectura de archivos ---
    if archivo_bmc_wo is not None:
        st.session_state.df_bmc_wo = leer_archivo_subido(
            archivo_bmc_wo, "BMC - Work Orders", st
        )
    else:
        st.session_state.df_bmc_wo = None

    if archivo_bmc_pbi is not None:
        st.session_state.df_bmc_pbi = leer_archivo_subido(
            archivo_bmc_pbi, "BMC - Problemas", st
        )
    else:
        st.session_state.df_bmc_pbi = None

    if archivo_jira is not None:
        st.session_state.df_jira = leer_archivo_subido(
            archivo_jira, "Jira", st, hoja_preferida="Your Jira Issues"
        )
    else:
        st.session_state.df_jira = None

    # --- Pipeline cacheado ---
    if any([
        st.session_state.df_bmc_wo is not None,
        st.session_state.df_bmc_pbi is not None,
        st.session_state.df_jira is not None,
    ]):
        with st.spinner("Procesando pipeline de conciliacion..."):
            resultado = _pipeline_conciliacion(
                _hash_wo="0" if st.session_state.df_bmc_wo is None else _hash_bytes(
                    archivo_bmc_wo.getvalue() if archivo_bmc_wo else b""
                ),
                df_wo_raw=st.session_state.df_bmc_wo,
                _hash_pbi="0" if st.session_state.df_bmc_pbi is None else _hash_bytes(
                    archivo_bmc_pbi.getvalue() if archivo_bmc_pbi else b""
                ),
                df_pbi_raw=st.session_state.df_bmc_pbi,
                _hash_jira="0" if st.session_state.df_jira is None else _hash_bytes(
                    archivo_jira.getvalue() if archivo_jira else b""
                ),
                df_jira_raw=st.session_state.df_jira,
            )
        st.session_state.df_bmc_total = resultado["df_bmc_total"]
        st.session_state.df_merge = resultado["df_merge"]
        st.session_state.df_resultado = resultado["df_resultado"]
    else:
        st.session_state.df_bmc_total = None
        st.session_state.df_merge = None
        st.session_state.df_resultado = None

    tab1, tab2, tab3 = st.tabs([
        "\U0001F4E5 Ingesta de Datos",
        "\U0001F504 Cruce y Reglas de Negocio",
        "\U0001F4CA Resultados y Exportacion",
    ])

    # --- TAB 1: Ingesta ---
    with tab1:
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.session_state.df_bmc_wo is not None:
                mostrar_resumen(st.session_state.df_bmc_wo, "BMC \u2014 Work Orders (WO)")
            else:
                with st.container(border=True):
                    st.markdown(
                        '<p style="color:#94a3b8;text-align:center;padding:2rem 0;">'
                        '\U0001F4E4 Carga el reporte de Work Orders en el sidebar</p>',
                        unsafe_allow_html=True,
                    )

        with col2:
            if st.session_state.df_bmc_pbi is not None:
                mostrar_resumen(st.session_state.df_bmc_pbi, "BMC \u2014 Problemas (PBI)")
            else:
                with st.container(border=True):
                    st.markdown(
                        '<p style="color:#94a3b8;text-align:center;padding:2rem 0;">'
                        '\U0001F4E4 Carga el reporte de Problemas en el sidebar</p>',
                        unsafe_allow_html=True,
                    )

        with col3:
            if st.session_state.df_jira is not None:
                mostrar_resumen(st.session_state.df_jira, "Jira")
            else:
                with st.container(border=True):
                    st.markdown(
                        '<p style="color:#94a3b8;text-align:center;padding:2rem 0;">'
                        '\U0001F4E4 Carga el reporte de Jira en el sidebar</p>',
                        unsafe_allow_html=True,
                    )

    # --- TAB 2: Cruce y Reglas ---
    with tab2:
        if st.session_state.df_bmc_total is not None:
            st.subheader(
                f"\U0001F4E6 BMC Unificado "
                f"({st.session_state.df_bmc_total.shape[0]:,} registros)"
            )
            st.dataframe(
                st.session_state.df_bmc_total.head(10), use_container_width=True
            )
            st.caption(
                "Work Orders (WO) + Problemas (PBI). "
                "Columna `Origen_BMC` indica la fuente."
            )
        else:
            with st.container(border=True):
                st.info(
                    "\U0001F4E4 Carga al menos un reporte BMC (WO o PBI) "
                    "en el sidebar para ver la unificacion."
                )

        if st.session_state.df_merge is not None:
            st.markdown("---")
            st.subheader("\U0001F91D Cruce BMC \u2194 Jira")

            conteo = st.session_state.df_merge[COL_MERGE].value_counts()
            m1, m2, m3 = st.columns(3)
            m1.metric("\U0001F7E2 Sincronizados (both)", conteo.get("both", 0))
            m2.metric("\U0001F7E1 Solo BMC (left_only)", conteo.get("left_only", 0))
            m3.metric("\U0001F534 Solo Jira (right_only)", conteo.get("right_only", 0))

            st.markdown("---")
            st.subheader("\U0001F9E0 Acciones Sugeridas")

            if st.session_state.df_resultado is not None:
                cols_preview = _resolver_columnas(
                    st.session_state.df_resultado,
                    COLUMNAS_PREVIEW_ACCIONES,
                )
                df_preview = st.session_state.df_resultado[cols_preview]

                df_no_ok = df_preview[~df_preview[COL_ACCION_SUGERIDA].str.startswith("OK", na=False)]
                if df_no_ok.empty:
                    st.success("Todas las acciones estan OK \u2014 sin correcciones requeridas.")
                else:
                    styled = df_no_ok.style.map(
                        obtener_estilo_accion, subset=[COL_ACCION_SUGERIDA]
                    )
                    st.dataframe(styled, use_container_width=True, height=400)
                    st.caption(
                        f"{df_no_ok.shape[0]:,} registros con acciones requeridas. "
                        "Usa la pestana **Resultados** para el detalle completo."
                    )

                    data = crear_excel(
                        df_no_ok, "Acciones_Pendientes", columna_color=COL_ACCION_SUGERIDA
                    )
                    st.download_button(
                        label="\U0001F4E5 Descargar acciones pendientes (.xlsx)",
                        data=data,
                        file_name=f"acciones_pendientes_conciliacion_{date.today():%Y%m%d}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="dl_acciones_tab2",
                    )
        else:
            if st.session_state.df_bmc_total is None:
                pass
            elif st.session_state.df_jira is None:
                with st.container(border=True):
                    st.info(
                        "\U0001F4E4 Carga el reporte de Jira en el sidebar "
                        "para realizar el cruce."
                    )

    # --- TAB 3: Resultados y Exportacion ---
    with tab3:
        if st.session_state.df_resultado is not None:
            _dashboard_conciliacion()
            st.markdown("---")

            col_filtro, col_info = st.columns([3, 1])
            with col_filtro:
                acciones_unicas = sorted(
                    st.session_state.df_resultado[COL_ACCION_SUGERIDA].unique()
                )
                seleccion = st.multiselect(
                    "Filtrar por Accion Sugerida",
                    options=acciones_unicas,
                    default=acciones_unicas,
                    key="filtro_accion",
                )

            with col_info:
                with st.popover("\U00002139 Ayuda"):
                    st.markdown(
                        f"""
                        **Categorias de Accion Sugerida:**
                        - **{ACCION_OK}**: el estado coincide entre sistemas
                        - **{ACCION_FALTA_JIRA}**: el registro existe en BMC pero no en Jira
                        - **{ACCION_SOBRA_JIRA}**: el registro existe en Jira pero no en BMC
                        - **Revisar: Deberia estar ... en Jira**: el estado de Jira no coincide con la regla Arcor esperada
                        - **{ACCION_INCONGRUENCIA}**: origen/proceso sin regla especifica y estados distintos
                        """
                    )

            if seleccion:
                df_filtrado = st.session_state.df_resultado[
                    st.session_state.df_resultado[COL_ACCION_SUGERIDA].isin(seleccion)
                ]
            else:
                df_filtrado = st.session_state.df_resultado

            total = st.session_state.df_resultado.shape[0]
            mostrados = df_filtrado.shape[0]
            st.caption(f"Mostrando **{mostrados:,}** de **{total:,}** registros")

            df_output = _formatear_output_conciliacion(df_filtrado)

            styled_full = df_output.style.map(
                obtener_estilo_accion, subset=[COL_ACCION_SUGERIDA]
            ).format(precision=0, na_rep="\u2014")

            st.dataframe(
                styled_full,
                use_container_width=True,
                height=520,
                hide_index=True,
            )

            st.markdown("---")
            data = crear_excel(
                df_output, "Conciliacion", columna_color=COL_ACCION_SUGERIDA
            )

            dl_col, _ = st.columns([1, 3])
            with dl_col:
                st.download_button(
                    label="\U0001F4E5 Descargar resultado_conciliacion.xlsx",
                    data=data,
                    file_name=f"resultado_conciliacion_{date.today():%Y%m%d}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )
        else:
            with st.container(border=True):
                st.info(
                    "\U0001F4CA Carga los 3 reportes en el sidebar y ve a la pestana "
                    "**Cruce y Reglas** para generar los resultados de conciliacion."
                )


# =============================================================================
# VALIDACION EPICAS vs TAREAS
# =============================================================================

def render_epicas(archivos: dict) -> None:
    """Area principal del modo Validacion Epicas vs Tareas."""
    archivo_epicas = archivos["epicas"]
    archivo_tareas = archivos["tareas"]

    st.title("\U0001F4CB Validacion Epicas vs Tareas")
    st.caption("Motor de validacion \u2014 Epicas e Historias de Jira")

    # Lectura
    if archivo_epicas is not None:
        st.session_state.df_epicas = leer_archivo_subido(
            archivo_epicas, "Epicas (Jira)", st
        )
    else:
        st.session_state.df_epicas = None

    if archivo_tareas is not None:
        st.session_state.df_tareas = leer_archivo_subido(
            archivo_tareas, "Tareas e Historias (Jira)", st
        )
    else:
        st.session_state.df_tareas = None

    # Pipeline cacheado
    if any([
        st.session_state.df_epicas is not None,
        st.session_state.df_tareas is not None,
    ]):
        with st.spinner("Procesando pipeline de validacion de epicas..."):
            resultado_epic = _pipeline_epicas(
                _hash_epicas="0" if st.session_state.df_epicas is None else _hash_bytes(
                    archivo_epicas.getvalue() if archivo_epicas else b""
                ),
                df_epicas_raw=st.session_state.df_epicas,
                _hash_tareas="0" if st.session_state.df_tareas is None else _hash_bytes(
                    archivo_tareas.getvalue() if archivo_tareas else b""
                ),
                df_tareas_raw=st.session_state.df_tareas,
            )
        st.session_state.df_epicas_filt = resultado_epic["df_epicas_filt"]
        st.session_state.df_tareas_filt = resultado_epic["df_tareas_filt"]
        st.session_state.df_tareas_agg = resultado_epic["df_tareas_agg"]
        st.session_state.df_epic_merge = resultado_epic["df_epic_merge"]
        st.session_state.df_epic_resultado = resultado_epic["df_epic_resultado"]
    else:
        st.session_state.df_epicas_filt = None
        st.session_state.df_tareas_filt = None
        st.session_state.df_tareas_agg = None
        st.session_state.df_epic_merge = None
        st.session_state.df_epic_resultado = None

    tab1, tab2, tab3 = st.tabs([
        "\U0001F4E5 Ingesta",
        "\U0001F504 Cruce y Validacion",
        "\U0001F4CA Resultados",
    ])

    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            if st.session_state.df_epicas is not None:
                mostrar_resumen(st.session_state.df_epicas, "Epicas (Jira)")
            else:
                with st.container(border=True):
                    st.markdown(
                        '<p style="color:#94a3b8;text-align:center;padding:2rem 0;">'
                        '\U0001F4E4 Carga el reporte de Epicas en el sidebar</p>',
                        unsafe_allow_html=True,
                    )
            if st.session_state.df_epicas_filt is not None:
                st.caption(
                    f"Epicas filtradas: {st.session_state.df_epicas_filt.shape[0]:,} "
                    f"(original: {st.session_state.df_epicas.shape[0]:,})"
                )

        with col2:
            if st.session_state.df_tareas is not None:
                mostrar_resumen(st.session_state.df_tareas, "Tareas e Historias (Jira)")
            else:
                with st.container(border=True):
                    st.markdown(
                        '<p style="color:#94a3b8;text-align:center;padding:2rem 0;">'
                        '\U0001F4E4 Carga el reporte de Tareas en el sidebar</p>',
                        unsafe_allow_html=True,
                    )
            if st.session_state.df_tareas_filt is not None:
                st.caption(
                    f"Tareas filtradas: {st.session_state.df_tareas_filt.shape[0]:,} "
                    f"(original: {st.session_state.df_tareas.shape[0]:,})"
                )

    with tab2:
        if st.session_state.df_epic_merge is not None:
            conteo = st.session_state.df_epic_merge[COL_MERGE].value_counts()
            m1, m2, m3 = st.columns(3)
            m1.metric("\U0001F7E2 Vinculadas (both)", conteo.get("both", 0))
            m2.metric("\U0001F7E1 Solo Epicas (left_only)", conteo.get("left_only", 0))
            m3.metric("\U0001F534 Solo Tareas (right_only)", conteo.get("right_only", 0))

            st.markdown("---")
            st.subheader("\U0001F9E0 Validacion de Epicas")

            if st.session_state.df_epic_resultado is not None:
                cols_ok = [c for c in COLUMNAS_OUTPUT_EPICAS if c in st.session_state.df_epic_resultado.columns]
                df_view = st.session_state.df_epic_resultado[cols_ok]

                df_no_ok = df_view[~df_view[COL_VALIDACION_EPICAS].str.startswith("OK", na=False)]
                if df_no_ok.empty:
                    st.success("Todas las epicas estan OK \u2014 sin acciones requeridas.")
                else:
                    styled = df_no_ok.style.map(
                        obtener_estilo_accion, subset=[COL_VALIDACION_EPICAS]
                    ).format(precision=0, na_rep="\u2014")
                    st.dataframe(styled, use_container_width=True, height=400)
                    st.caption(
                        f"{df_no_ok.shape[0]:,} registros con acciones requeridas. "
                        "Usa la pestana **Resultados** para el detalle completo."
                    )

                    data = crear_excel(
                        df_no_ok, "Validacion_Epicas", columna_color=COL_VALIDACION_EPICAS
                    )
                    st.download_button(
                        label="\U0001F4E5 Descargar solo pendientes (.xlsx)",
                        data=data,
                        file_name=f"validacion_epicas_pendientes_{date.today():%Y%m%d}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="dl_epic_tab2",
                    )
        else:
            with st.container(border=True):
                st.info(
                    "\U0001F4E4 Carga ambos reportes (Epicas y Tareas) en el sidebar "
                    "para ver la validacion."
                )

    with tab3:
        if st.session_state.df_epic_resultado is not None:
            vals_unicas = sorted(
                st.session_state.df_epic_resultado[COL_VALIDACION_EPICAS].unique()
            )
            sel = st.multiselect(
                "Filtrar por Validacion de Epica",
                options=vals_unicas,
                default=vals_unicas,
                key="filtro_epic",
            )
            df_filt = (
                st.session_state.df_epic_resultado
                if not sel
                else st.session_state.df_epic_resultado[
                    st.session_state.df_epic_resultado[COL_VALIDACION_EPICAS].isin(sel)
                ]
            )
            st.caption(
                f"Mostrando **{df_filt.shape[0]:,}** de "
                f"**{st.session_state.df_epic_resultado.shape[0]:,}** registros"
            )

            df_output = _formatear_output_epicas(df_filt)

            styled_full = df_output.style.map(
                obtener_estilo_accion, subset=[COL_VALIDACION_EPICAS]
            ).format(precision=0, na_rep="\u2014")

            st.dataframe(
                styled_full, use_container_width=True, height=520, hide_index=True
            )

            st.markdown("---")
            data = crear_excel(
                df_output, "Validacion_Epicas", columna_color=COL_VALIDACION_EPICAS
            )

            dl_col, _ = st.columns([1, 3])
            with dl_col:
                st.download_button(
                    label="\U0001F4E5 Descargar validacion_epicas.xlsx",
                    data=data,
                    file_name=f"validacion_epicas_{date.today():%Y%m%d}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )
        else:
            with st.container(border=True):
                st.info(
                    "\U0001F4CA Carga ambos reportes en el sidebar y ve a la pestana "
                    "**Cruce y Validacion** para generar los resultados."
                )
