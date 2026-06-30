"""
Funciones de transformacion y cruce de datos BMC <-> Jira.
"""
import pandas as pd
import re

from .constants import (
    COL_BMC_ID, COL_ORIGEN, COL_ESTADO_BMC, COL_ESTADO_JIRA,
    COL_WO_SOURCE_ID, COL_PBI_SOURCE_ID,
    COL_ESTADO, COL_ESTADO_CANDIDATOS,
    COL_WO_SUMMARY, COL_PBI_SUMMARY,
    COL_BMC_ASIG_WO, COL_BMC_ASIG_PBI, COL_BMC_GRUPO_PBI,
    COL_TITULO_BMC, COL_TECNICO_ASIGNADO, COL_GRUPO_ASIGNADO,
    COL_OUT_CLAVE, COL_RESUMEN, COL_CATEGORIA_ESTADO, COL_PERSONA_ASIGNADA,
    COL_PROCESO, COL_ESTADO_PROPUESTA, COL_CELULA,
    COL_JIRA_KEY, COL_JIRA_SUMMARY, COL_JIRA_ASSIGNEE,
    COL_SRC_ESTADO_PROPUESTA, COL_SRC_PROCESO, COL_SRC_CATEGORIA_ESTADO, COL_SRC_CELULA,
    COLUMNAS_OUTPUT, COLUMNAS_OUTPUT_EPICAS,
)


def _resolver_columnas(
    df: pd.DataFrame,
    columnas_deseadas: list[str],
    suffix_prefs: dict[str, str] | None = None,
) -> list[str]:
    """
    Devuelve las columnas de 'columnas_deseadas' que existen en el DataFrame,
    probando con sufijos _BMC / _JIRA si el nombre exacto no se encuentra.
    """
    suffix_prefs = suffix_prefs or {}
    disponibles = []
    for col in columnas_deseadas:
        pref = suffix_prefs.get(col)
        if col in df.columns:
            disponibles.append(col)
        elif pref and f"{col}{pref}" in df.columns:
            disponibles.append(f"{col}{pref}")
        elif f"{col}_BMC" in df.columns:
            disponibles.append(f"{col}_BMC")
        elif f"{col}_JIRA" in df.columns:
            disponibles.append(f"{col}_JIRA")

    return disponibles


def _encontrar_columna_merged(df: pd.DataFrame, nombre_col: str) -> str | None:
    """Busca una columna en el DataFrame post-merge, probando sufijos _BMC / _JIRA."""
    if nombre_col in df.columns:
        return nombre_col
    if f"{nombre_col}_BMC" in df.columns:
        return f"{nombre_col}_BMC"
    if f"{nombre_col}_JIRA" in df.columns:
        return f"{nombre_col}_JIRA"
    return None


def _detectar_columna_select(df: pd.DataFrame) -> str | None:
    """Busca la primera columna que coincida con el patron select__<numero> (admite sufijo _BMC)."""
    for col in df.columns:
        if re.match(r"^select__(\d+)(_BMC)?$", col):
            return re.sub(r"_BMC$", "", col)
    return None


def _agregar_columnas_conciliacion(df_merge: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega las columnas unificadas y detecta las de fuente necesarias
    para el reporte final Resultado_Conciliacion.
    """
    df = df_merge.copy()

    # --- TECNICO ASIGNADO ---
    col_wo_user = _encontrar_columna_merged(df, COL_BMC_ASIG_WO)
    col_pbi_user = _encontrar_columna_merged(df, COL_BMC_ASIG_PBI)

    if col_wo_user and col_pbi_user:
        df[COL_TECNICO_ASIGNADO] = df[col_wo_user].fillna(df[col_pbi_user])
    elif col_wo_user:
        df[COL_TECNICO_ASIGNADO] = df[col_wo_user]
    elif col_pbi_user:
        df[COL_TECNICO_ASIGNADO] = df[col_pbi_user]
    else:
        df[COL_TECNICO_ASIGNADO] = ""

    # --- GRUPO ASIGNADO ---
    col_wo_grupo_select = _detectar_columna_select(df)
    col_wo_grupo = _encontrar_columna_merged(df, col_wo_grupo_select) if col_wo_grupo_select else None
    col_pbi_grupo = _encontrar_columna_merged(df, COL_BMC_GRUPO_PBI)

    if col_wo_grupo and col_pbi_grupo:
        df[COL_GRUPO_ASIGNADO] = df[col_wo_grupo].fillna(df[col_pbi_grupo])
    elif col_wo_grupo:
        df[COL_GRUPO_ASIGNADO] = df[col_wo_grupo]
    elif col_pbi_grupo:
        df[COL_GRUPO_ASIGNADO] = df[col_pbi_grupo]
    else:
        df[COL_GRUPO_ASIGNADO] = ""

    # --- TITULO DE BMC ---
    col_wo_title = _encontrar_columna_merged(df, COL_WO_SUMMARY)
    col_pbi_title = _encontrar_columna_merged(df, COL_PBI_SUMMARY)

    if col_wo_title and col_pbi_title:
        df[COL_TITULO_BMC] = df[col_wo_title].fillna(df[col_pbi_title])
    elif col_wo_title:
        df[COL_TITULO_BMC] = df[col_wo_title]
    elif col_pbi_title:
        df[COL_TITULO_BMC] = df[col_pbi_title]
    else:
        df[COL_TITULO_BMC] = ""

    # --- Columnas fuente adicionales ---
    col_ep = _encontrar_columna_merged(df, COL_SRC_ESTADO_PROPUESTA)
    df[COL_ESTADO_PROPUESTA] = df[col_ep] if col_ep else ""

    col_proc = _encontrar_columna_merged(df, COL_SRC_PROCESO)
    df[COL_PROCESO] = df[col_proc] if col_proc else ""

    col_cat = _encontrar_columna_merged(df, COL_SRC_CATEGORIA_ESTADO)
    df[COL_CATEGORIA_ESTADO] = df[col_cat] if col_cat else ""

    # --- Columnas desde Jira ---
    col_key_jira = _encontrar_columna_merged(df, COL_JIRA_KEY)
    df[COL_OUT_CLAVE] = df[col_key_jira] if col_key_jira else ""

    col_summary_jira = _encontrar_columna_merged(df, COL_JIRA_SUMMARY)
    df[COL_RESUMEN] = df[col_summary_jira] if col_summary_jira else ""

    col_assignee_jira = _encontrar_columna_merged(df, COL_JIRA_ASSIGNEE)
    df[COL_PERSONA_ASIGNADA] = df[col_assignee_jira] if col_assignee_jira else ""

    col_celula = _encontrar_columna_merged(df, COL_SRC_CELULA)
    df[COL_CELULA] = df[col_celula] if col_celula else ""

    return df


def _formatear_output_conciliacion(df: pd.DataFrame) -> pd.DataFrame:
    """Selecciona y ordena unicamente las columnas definidas en COLUMNAS_OUTPUT."""
    resultado = pd.DataFrame()
    for col in COLUMNAS_OUTPUT:
        if col in df.columns:
            resultado[col] = df[col].values
        else:
            resultado[col] = ""
    return resultado


def _formatear_output_epicas(df: pd.DataFrame) -> pd.DataFrame:
    """Selecciona y ordena unicamente las columnas definidas en COLUMNAS_OUTPUT_EPICAS."""
    resultado = pd.DataFrame()
    for col in COLUMNAS_OUTPUT_EPICAS:
        if col in df.columns:
            resultado[col] = df[col].values
        else:
            resultado[col] = ""
    return resultado


def _renombrar_columna_estado(df: pd.DataFrame, nombre_destino: str) -> str | None:
    """
    Busca la columna de estado en 'df' probando varios nombres candidatos
    y la renombra a 'nombre_destino'.
    Retorna el nombre original encontrado, o None si no se encontro ninguna.
    """
    for candidato in COL_ESTADO_CANDIDATOS:
        if candidato in df.columns:
            df.rename(columns={candidato: nombre_destino}, inplace=True)
            return candidato
    return None


def normalizar_bmc_wo(df: pd.DataFrame, st_module=None) -> pd.DataFrame | None:
    """
    Renombra 'ID Propuesta' a 'BMC_ID' y la columna de estado a 'Estado_BMC'.
    Agrega columna 'Origen_BMC' = 'WO'.
    """
    if COL_WO_SOURCE_ID not in df.columns:
        if st_module:
            st_module.warning(
                f"**BMC WO** - No se encontro la columna '{COL_WO_SOURCE_ID}'. "
                f"Columnas disponibles: {df.columns.tolist()}"
            )
        return None

    df = df.copy()
    df.rename(columns={COL_WO_SOURCE_ID: COL_BMC_ID}, inplace=True)
    df[COL_ORIGEN] = "WO"

    original = _renombrar_columna_estado(df, COL_ESTADO_BMC)
    if st_module:
        if original:
            st_module.toast(f"✅ WO — '{original}' → Estado_BMC", icon="✅")
        else:
            st_module.info(f"⚠️ WO — No se detecto columna de estado. Columnas: {df.columns.tolist()}")

    return df


def normalizar_bmc_pbi(df: pd.DataFrame, st_module=None) -> pd.DataFrame | None:
    """
    Renombra 'Problema' a 'BMC_ID' y la columna de estado a 'Estado_BMC'.
    Agrega columna 'Origen_BMC' = 'PBI'.
    """
    if COL_PBI_SOURCE_ID not in df.columns:
        if st_module:
            st_module.warning(
                f"**BMC PBI** - No se encontro la columna '{COL_PBI_SOURCE_ID}'. "
                f"Columnas disponibles: {df.columns.tolist()}"
            )
        return None

    df = df.copy()
    df.rename(columns={COL_PBI_SOURCE_ID: COL_BMC_ID}, inplace=True)
    df[COL_ORIGEN] = "PBI"

    original = _renombrar_columna_estado(df, COL_ESTADO_BMC)
    if st_module:
        if original:
            st_module.toast(f"✅ PBI — '{original}' → Estado_BMC", icon="✅")
        else:
            st_module.info(f"⚠️ PBI — No se detecto columna de estado. Columnas: {df.columns.tolist()}")

    return df


def unificar_bmc(
    df_wo: pd.DataFrame | None,
    df_pbi: pd.DataFrame | None,
) -> pd.DataFrame | None:
    """Concatena los DataFrames normalizados de WO y PBI."""
    partes = []
    if df_wo is not None and not df_wo.empty:
        partes.append(df_wo)
    if df_pbi is not None and not df_pbi.empty:
        partes.append(df_pbi)

    if not partes:
        return None

    return pd.concat(partes, ignore_index=True, sort=False)


def normalizar_jira(df: pd.DataFrame, st_module=None) -> pd.DataFrame | None:
    """
    Renombra la columna de estado a 'Estado_JIRA'.
    """
    if df is None or df.empty:
        return None

    df = df.copy()

    original = _renombrar_columna_estado(df, COL_ESTADO_JIRA)
    if st_module:
        if original:
            st_module.toast(f"✅ Jira — '{original}' → Estado_JIRA", icon="✅")
        else:
            st_module.info(f"⚠️ Jira — No se detecto columna de estado. Columnas: {df.columns.tolist()}")

    return df


def cruzar_bmc_jira(
    df_bmc: pd.DataFrame,
    df_jira: pd.DataFrame,
    st_module=None,
) -> pd.DataFrame | None:
    """
    Outer merge entre BMC y Jira usando 'BMC_ID' como llave.
    """
    if df_bmc is None or df_jira is None:
        return None
    if df_bmc.empty or df_jira.empty:
        return None

    try:
        return pd.merge(
            df_bmc,
            df_jira,
            on=COL_BMC_ID,
            how="outer",
            indicator=True,
            suffixes=("_BMC", "_JIRA"),
        )
    except Exception as e:
        if st_module:
            st_module.error(f"Error al cruzar BMC con Jira: {e}")
        return None
