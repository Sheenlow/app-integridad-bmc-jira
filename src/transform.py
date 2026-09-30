"""
Funciones de transformacion y cruce de datos BMC <-> Jira.
"""
import pandas as pd
import re

from .utils import normalizar_texto
from .constants import (
    COL_BMC_ID, COL_ORIGEN, COL_ESTADO_BMC, COL_ESTADO_JIRA,
    COL_PRIORIDAD_BMC, COL_PRIORIDAD_JIRA,
    ESTADOS_FINALES_BMC, JIRA_ESTADOS_ACTIVOS,
    COL_WO_SUMMARY, COL_PBI_SUMMARY,
    COL_BMC_ASIG_WO, COL_BMC_ASIG_PBI, COL_BMC_GRUPO_PBI,
    GRUPOS_PERMITIDOS, ALIASES_GRUPO_WO, ALIASES_GRUPO_PBI,
    COL_TITULO_BMC, COL_TECNICO_ASIGNADO, COL_GRUPO_ASIGNADO,
    COL_OUT_CLAVE, COL_RESUMEN, COL_CATEGORIA_ESTADO, COL_PERSONA_ASIGNADA,
    COL_OUT_PRIORIDAD_BMC, COL_OUT_PRIORIDAD_JIRA,
    COL_PROCESO, COL_ESTADO_PROPUESTA, COL_CELULA,
    COL_JIRA_KEY, COL_JIRA_SUMMARY, COL_JIRA_ASSIGNEE,
    COL_SRC_ESTADO_PROPUESTA, COL_SRC_PROCESO, COL_SRC_CATEGORIA_ESTADO, COL_SRC_CELULA,
    COLUMNAS_OUTPUT, COLUMNAS_OUTPUT_EPICAS,
    ALIASES_JIRA, ALIASES_BMC, ALIASES_EPICAS, COLUMNAS_CRITICAS_JIRA,
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


def _encontrar_columna_candidatos(df: pd.DataFrame, candidatos: list[str]) -> str | None:
    """Prueba varias columnas candidatas (con sufijos _BMC/_JIRA) y devuelve la primera."""
    for candidato in candidatos:
        col = _encontrar_columna_merged(df, candidato)
        if col:
            return col
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

    # --- Columnas fuente adicionales (BMC y Jira, con fallback) ---
    col_ep = _encontrar_columna_candidatos(
        df, [COL_SRC_ESTADO_PROPUESTA, COL_ESTADO_PROPUESTA]
    )
    df[COL_ESTADO_PROPUESTA] = df[col_ep] if col_ep else ""

    col_proc = _encontrar_columna_candidatos(
        df, [COL_SRC_PROCESO, COL_PROCESO]
    )
    df[COL_PROCESO] = df[col_proc] if col_proc else ""

    col_cat = _encontrar_columna_candidatos(
        df, [COL_CATEGORIA_ESTADO, COL_SRC_CATEGORIA_ESTADO]
    )
    df[COL_CATEGORIA_ESTADO] = df[col_cat] if col_cat else ""

    # --- Columnas desde Jira ---
    col_key_jira = _encontrar_columna_candidatos(
        df, [COL_OUT_CLAVE, COL_JIRA_KEY]
    )
    df[COL_OUT_CLAVE] = df[col_key_jira] if col_key_jira else ""

    col_summary_jira = _encontrar_columna_candidatos(
        df, [COL_RESUMEN, COL_JIRA_SUMMARY]
    )
    df[COL_RESUMEN] = df[col_summary_jira] if col_summary_jira else ""

    col_assignee_jira = _encontrar_columna_candidatos(
        df, [COL_PERSONA_ASIGNADA, COL_JIRA_ASSIGNEE]
    )
    df[COL_PERSONA_ASIGNADA] = df[col_assignee_jira] if col_assignee_jira else ""

    col_celula = _encontrar_columna_candidatos(
        df, [COL_CELULA, COL_SRC_CELULA]
    )
    df[COL_CELULA] = df[col_celula] if col_celula else ""

    # --- Prioridad (BMC y Jira, con fallback) ---
    col_prioridad_bmc = _encontrar_columna_candidatos(df, [COL_PRIORIDAD_BMC])
    df[COL_OUT_PRIORIDAD_BMC] = df[col_prioridad_bmc] if col_prioridad_bmc else ""

    col_prioridad_jira = _encontrar_columna_candidatos(df, [COL_PRIORIDAD_JIRA])
    df[COL_OUT_PRIORIDAD_JIRA] = df[col_prioridad_jira] if col_prioridad_jira else ""

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


def _mapear_alias(df: pd.DataFrame, aliases: dict) -> tuple[pd.DataFrame, set]:
    """
    Renombra columnas segun un mapeo {canonico: [aliases]}, comparando nombres
    normalizados (acentos/caso/strip). Devuelve (df_renombrado, canonicos_encontrados).
    """
    norm_to_orig: dict[str, str] = {}
    for col in df.columns:
        n = normalizar_texto(col)
        if n and n not in norm_to_orig:
            norm_to_orig[n] = col

    renombres: dict[str, str] = {}
    encontrados: set = set()
    for canonico, lista_aliases in aliases.items():
        for alias in lista_aliases:
            na = normalizar_texto(alias)
            if na in norm_to_orig:
                renombres[norm_to_orig[na]] = canonico
                encontrados.add(canonico)
                break

    return df.rename(columns=renombres), encontrados


def normalizar_bmc_wo(df: pd.DataFrame, st_module=None) -> pd.DataFrame | None:
    """
    Normaliza encabezados de BMC WO via alias (ID Propuesta -> BMC_ID,
    estado -> Estado_BMC, Proceso -> PROCESO). Agrega 'Origen_BMC' = 'WO'.
    """
    if df is None or df.empty:
        return None

    df = df.copy()
    df, encontrados = _mapear_alias(df, ALIASES_BMC)

    if COL_BMC_ID not in encontrados:
        if st_module:
            st_module.warning(
                "Columna [ID Propuesta] no detectada en el archivo de BMC WO subido. "
                f"Columnas disponibles: {df.columns.tolist()}"
            )
        return None

    df[COL_ORIGEN] = "WO"

    if st_module:
        if COL_ESTADO_BMC in encontrados:
            st_module.toast("✅ WO — columna de estado normalizada → Estado_BMC", icon="✅")
        else:
            st_module.info(
                f"⚠️ WO — No se detecto columna de estado. Columnas: {df.columns.tolist()}"
            )

    return df


def normalizar_bmc_pbi(df: pd.DataFrame, st_module=None) -> pd.DataFrame | None:
    """
    Normaliza encabezados de BMC PBI via alias (Problema -> BMC_ID,
    estado -> Estado_BMC). Agrega 'Origen_BMC' = 'PBI'.
    """
    if df is None or df.empty:
        return None

    df = df.copy()
    df, encontrados = _mapear_alias(df, ALIASES_BMC)

    if COL_BMC_ID not in encontrados:
        if st_module:
            st_module.warning(
                "Columna [Problema] no detectada en el archivo de BMC PBI subido. "
                f"Columnas disponibles: {df.columns.tolist()}"
            )
        return None

    df[COL_ORIGEN] = "PBI"

    if st_module:
        if COL_ESTADO_BMC in encontrados:
            st_module.toast("✅ PBI — columna de estado normalizada → Estado_BMC", icon="✅")
        else:
            st_module.info(
                f"⚠️ PBI — No se detecto columna de estado. Columnas: {df.columns.tolist()}"
            )

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


def _normalizar_id_bmc(valor):
    """
    Normaliza un BMC_ID para el cruce: str + strip + mayusculas.
    Retorna None para valores vacios/NaN para que el merge no invente llaves.
    """
    if valor is None:
        return None
    s = str(valor).strip().upper()
    if s in ("", "NAN", "NONE", "NAT", "NULL", "<NA>"):
        return None
    return s


def _normalizar_estado(valor) -> str:
    """Normaliza un valor de estado: NaN/None -> cadena vacia."""
    if valor is None or pd.isna(valor):
        return ""
    return normalizar_texto(valor)


def _bmc_ids_activos_jira(df_jira: pd.DataFrame) -> set:
    """Conjunto de BMC_IDs de incidencias activas/abiertas en Jira."""
    if df_jira is None or df_jira.empty:
        return set()
    col_estado = _encontrar_columna_merged(df_jira, COL_ESTADO_JIRA)
    col_bmc_id = _encontrar_columna_merged(df_jira, COL_BMC_ID)
    if not col_estado or not col_bmc_id:
        return set()

    estados = df_jira[col_estado].map(_normalizar_estado)
    ids = df_jira[col_bmc_id].map(_normalizar_id_bmc)
    mask_activo = estados.isin(JIRA_ESTADOS_ACTIVOS)
    return set(ids[mask_activo].dropna())


def filtrar_bmc_historico(
    df_bmc: pd.DataFrame, df_jira: pd.DataFrame,
) -> pd.DataFrame:
    """
    Filtra registros historicos de BMC (WO/PBI) ya cerrados y sin tarjeta
    activa en Jira. Mantiene:
      - registros cuyo Estado_BMC (normalizado) NO esta en ESTADOS_FINALES_BMC;
      - registros en estado final pero cuyo BMC_ID sigue activo en Jira.
    """
    if df_bmc is None or df_bmc.empty:
        return df_bmc

    df = df_bmc.copy()
    col_estado_bmc = _encontrar_columna_merged(df, COL_ESTADO_BMC)
    col_bmc_id = _encontrar_columna_merged(df, COL_BMC_ID)

    if col_estado_bmc is None:
        # Sin columna de estado no es posible clasificar finales: no filtrar.
        return df

    bmc_ids_activos = _bmc_ids_activos_jira(df_jira)

    estados = df[col_estado_bmc].map(_normalizar_estado)
    es_final = estados.isin(ESTADOS_FINALES_BMC)

    if col_bmc_id is not None and bmc_ids_activos:
        ids = df[col_bmc_id].map(_normalizar_id_bmc)
        activo_en_jira = ids.isin(bmc_ids_activos)
    else:
        activo_en_jira = pd.Series(False, index=df.index)

    mask = (~es_final) | activo_en_jira
    return df[mask].reset_index(drop=True)


def _encontrar_columna_por_alias(df: pd.DataFrame, candidatos: list[str]) -> str | None:
    """Busca la primera columna cuyo nombre normalizado coincida con un candidato."""
    def _norm(cadena: str) -> str:
        return normalizar_texto(cadena).replace("_", " ")

    norm_to_orig: dict[str, str] = {}
    for col in df.columns:
        n = _norm(col)
        if n and n not in norm_to_orig:
            norm_to_orig[n] = col
    for candidato in candidatos:
        n = _norm(candidato)
        if n in norm_to_orig:
            return norm_to_orig[n]
    return None


def filtrar_bmc_por_grupo(
    df: pd.DataFrame, candidatos_grupo: list[str], st_module=None,
) -> pd.DataFrame | None:
    """
    Conserva solo los registros cuyo grupo (columna detectada por alias o
    normalizacion) este en GRUPOS_PERMITIDOS. Si la columna de grupo no se
    detecta, no filtra (comportamiento defensivo).
    """
    if df is None or df.empty:
        return df

    col_grupo = _encontrar_columna_por_alias(df, candidatos_grupo)
    if col_grupo is None:
        if st_module:
            st_module.warning(
                "Columna de grupo no detectada en el reporte BMC; "
                "no se filtra por grupo."
            )
        return df

    valores = df[col_grupo].astype(str).str.strip()
    mask = valores.isin(GRUPOS_PERMITIDOS)
    return df[mask].reset_index(drop=True)


def normalizar_columnas_jira(df: pd.DataFrame, st_module=None) -> pd.DataFrame:
    """
    Capa de estandarizacion de encabezados de Jira.
    Normaliza nombres de columna (acentos/caso) y mapea alias frecuentes a un
    esquema interno fijo, de modo que las reglas de negocio no dependan del
    nombre exacto que exporte Jira.
    """
    df = df.copy()
    df, _ = _mapear_alias(df, ALIASES_JIRA)

    # Warning por columnas criticas ausentes
    if st_module:
        for col, label in COLUMNAS_CRITICAS_JIRA.items():
            if col not in df.columns:
                st_module.warning(
                    f"Columna [{label}] no detectada en el archivo de Jira subido."
                )

    return df


def _asegurar_bmc_id(df: pd.DataFrame, st_module=None) -> pd.DataFrame:
    """
    Garantiza la columna BMC_ID: usa la existente (normalizada) o, si falta o
    viene nula, la extrae del RESUMEN con una regex (WO/PBI + numero).
    """
    # Resolver BMC_ID si viene con casing/alias distinto
    if COL_BMC_ID not in df.columns:
        for col in df.columns:
            if normalizar_texto(col) in ("bmc id", "bmc_id", "bmcid", "id bmc", "bmc"):
                df = df.rename(columns={col: COL_BMC_ID})
                break

    patron = re.compile(r"((?:WO|PBI)[\s\-_]?\d+)", re.IGNORECASE)

    if COL_BMC_ID in df.columns:
        serie_actual = df[COL_BMC_ID].map(_normalizar_id_bmc)
        if COL_RESUMEN in df.columns:
            extraidos = df[COL_RESUMEN].astype(str).str.extract(patron, expand=False)
            df[COL_BMC_ID] = serie_actual.where(serie_actual.notna(), extraidos)
        else:
            df[COL_BMC_ID] = serie_actual
    elif COL_RESUMEN in df.columns:
        df[COL_BMC_ID] = (
            df[COL_RESUMEN].astype(str).str.extract(patron, expand=False)
            .map(_normalizar_id_bmc)
        )
    else:
        if st_module:
            st_module.warning(
                "Columna [BMC_ID] no detectada en el archivo de Jira subido "
                "y no se pudo extraer desde el RESUMEN."
            )

    return df


def normalizar_jira(df: pd.DataFrame, st_module=None) -> pd.DataFrame | None:
    """
    Normaliza el reporte de Jira al esquema interno:
    - Estandariza encabezados (acentos/caso/alias).
    - Garantiza la columna BMC_ID (existente o extraida del RESUMEN).
    - Renombra el estado a 'Estado_JIRA'.
    """
    if df is None or df.empty:
        return None

    df = normalizar_columnas_jira(df, st_module)
    df = _asegurar_bmc_id(df, st_module)

    if st_module:
        if COL_ESTADO_JIRA in df.columns:
            st_module.toast(
                "✅ Jira — columnas normalizadas (estado → Estado_JIRA)", icon="✅"
            )
        else:
            st_module.info(
                f"⚠️ Jira — No se detecto columna de estado. Columnas: {df.columns.tolist()}"
            )

    return df


def normalizar_epicas_tareas(df: pd.DataFrame, st_module=None) -> pd.DataFrame | None:
    """
    Normaliza encabezados de los reportes de Epicas y Tareas de Jira al
    esquema interno de epics.py (Tipo de Incidencia, Clave, Estado, parent,
    Resumen, etc.) de forma defensiva (tildes/caso/alias), simetrico a como
    normalizar_jira() estandariza el reporte de conciliacion.
    """
    if df is None or df.empty:
        return None

    df = df.copy()
    df, _ = _mapear_alias(df, ALIASES_EPICAS)
    return df


def cruzar_bmc_jira(
    df_bmc: pd.DataFrame,
    df_jira: pd.DataFrame,
    st_module=None,
) -> pd.DataFrame | None:
    """
    Outer merge entre BMC y Jira usando 'BMC_ID' como llave.
    Normaliza los keys de cruce (str + strip + mayusculas) para evitar
    fallos por espacios invisibles o diferencias de caso.
    """
    if df_bmc is None or df_jira is None:
        return None
    if df_bmc.empty or df_jira.empty:
        return None

    try:
        df_bmc = df_bmc.copy()
        df_jira = df_jira.copy()
        if COL_BMC_ID in df_bmc.columns:
            df_bmc[COL_BMC_ID] = df_bmc[COL_BMC_ID].map(_normalizar_id_bmc)
        if COL_BMC_ID in df_jira.columns:
            df_jira[COL_BMC_ID] = df_jira[COL_BMC_ID].map(_normalizar_id_bmc)

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
