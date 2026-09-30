"""
Validacion Epicas vs Tareas: filtrado, agrupacion y cruce.
"""
import pandas as pd

from .utils import normalizar_texto
from .constants import (
    COL_TIPO_INCIDENCIA, COL_CLAVE_JIRA, COL_PARENT,
    COL_ESTADO, COL_ESTADO_CANDIDATOS,
    COL_TAREAS_TOTAL, COL_TAREAS_ABIERTAS, COL_TAREAS_CERRADAS,
    COL_ESTADOS_TAREAS, COL_CANT_SPRINTS, COL_ASIGNADO_TAREAS,
    COL_JIRA_ASSIGNEE, COL_SPRINT_CANDIDATOS,
    ESTADOS_FINALES_EPICA,
)


def filtrar_epicas(df: pd.DataFrame, st_module=None) -> pd.DataFrame | None:
    """Filtra solo las filas donde Tipo de Incidencia sea Epic."""
    if COL_TIPO_INCIDENCIA not in df.columns:
        if st_module:
            st_module.warning(
                f"No se encontro la columna '{COL_TIPO_INCIDENCIA}'. "
                f"Columnas disponibles: {df.columns.tolist()}"
            )
        return None
    tipos = df[COL_TIPO_INCIDENCIA].map(normalizar_texto)
    mask = tipos.isin(["epic", "epica"])
    return df[mask].copy()


def filtrar_tareas(df: pd.DataFrame, st_module=None) -> pd.DataFrame | None:
    """Excluye las epicas, dejando solo tareas e historias."""
    if COL_TIPO_INCIDENCIA not in df.columns:
        if st_module:
            st_module.warning(
                f"No se encontro la columna '{COL_TIPO_INCIDENCIA}'. "
                f"Columnas disponibles: {df.columns.tolist()}"
            )
        return None
    tipos = df[COL_TIPO_INCIDENCIA].map(normalizar_texto)
    mask = ~tipos.isin(["epic", "epica"])
    return df[mask].copy()


def agrupar_tareas_por_parent(
    df_tareas: pd.DataFrame,
    df_epicas: pd.DataFrame | None = None,
    st_module=None,
) -> pd.DataFrame | None:
    """
    Agrupa tareas por la columna 'parent' y calcula:
    - total de tareas
    - tareas abiertas (estado no final)
    - tareas cerradas (estado final)
    - lista de estados unicos
    - cantidad de sprints
    - asignado mas frecuente
    """
    if df_tareas is None or df_tareas.empty:
        return None
    if COL_PARENT not in df_tareas.columns:
        if st_module:
            st_module.warning(f"No se encontro la columna '{COL_PARENT}' en el reporte de Tareas.")
        return None

    # Detectar columna de estado
    estado_col = None
    if COL_ESTADO not in df_tareas.columns:
        for cand in COL_ESTADO_CANDIDATOS:
            if cand in df_tareas.columns:
                estado_col = cand
                break
        if estado_col is None:
            if st_module:
                st_module.warning(
                    f"No se encontro columna de estado en Tareas. "
                    f"Columnas: {df_tareas.columns.tolist()}"
                )
            return None
    else:
        estado_col = COL_ESTADO

    # Detectar columna de sprint en tareas
    sprint_col = None
    for cand in COL_SPRINT_CANDIDATOS:
        if cand in df_tareas.columns:
            sprint_col = cand
            break

    # Detectar columna de sprint en epicas y construir lookup
    sprint_col_epicas = None
    sprints_epicas_lookup = {}
    if df_epicas is not None and not df_epicas.empty:
        for cand in COL_SPRINT_CANDIDATOS:
            if cand in df_epicas.columns:
                sprint_col_epicas = cand
                break
        if sprint_col_epicas and COL_CLAVE_JIRA in df_epicas.columns:
            for _, row in df_epicas.iterrows():
                clave = row[COL_CLAVE_JIRA]
                valor = row[sprint_col_epicas]
                if pd.notna(valor) and str(valor).strip():
                    sprints = {s.strip() for s in str(valor).split(";") if s.strip()}
                    sprints_epicas_lookup[clave] = sprints

    # Detectar columna de asignado
    asignado_col = None
    if COL_JIRA_ASSIGNEE in df_tareas.columns:
        asignado_col = COL_JIRA_ASSIGNEE

    # --- Agregacion de estados ---
    def _agregar_estados(series):
        total = len(series)
        cerradas = series.isin(ESTADOS_FINALES_EPICA).sum()
        abiertas = total - cerradas
        unicos = series.dropna().unique().tolist()
        return pd.Series({
            COL_TAREAS_TOTAL: total,
            COL_TAREAS_ABIERTAS: abiertas,
            COL_TAREAS_CERRADAS: cerradas,
            COL_ESTADOS_TAREAS: ", ".join(sorted(set(str(s) for s in unicos))),
        })

    grouped = df_tareas.groupby(COL_PARENT)[estado_col].apply(_agregar_estados).unstack()
    grouped = grouped.reset_index()
    grouped.rename(columns={COL_PARENT: COL_CLAVE_JIRA}, inplace=True)

    # --- Conteo de sprints (union epica + tareas, deduplicado) ---
    if sprint_col:
        def _contar_sprints(series):
            sprints_union = set()
            for val in series.dropna():
                for s in str(val).split(";"):
                    s = s.strip()
                    if s:
                        sprints_union.add(s)
            return len(sprints_union) if sprints_union else 0

        sprints_count = (
            df_tareas.groupby(COL_PARENT)[sprint_col]
            .apply(_contar_sprints)
            .reset_index()
        )
        sprints_count.rename(
            columns={COL_PARENT: COL_CLAVE_JIRA, sprint_col: COL_CANT_SPRINTS},
            inplace=True,
        )

        # Incorporar sprints de epicas al conteo (union deduplicada)
        if sprints_epicas_lookup:
            for idx, row in sprints_count.iterrows():
                clave = row[COL_CLAVE_JIRA]
                sprints_epica = sprints_epicas_lookup.get(clave, set())
                if sprints_epica:
                    sprints_tareas = set()
                    tareas_sprint_vals = df_tareas[df_tareas[COL_PARENT] == clave][sprint_col].dropna()
                    for val in tareas_sprint_vals:
                        for s in str(val).split(";"):
                            s = s.strip()
                            if s:
                                sprints_tareas.add(s)
                    total = len(sprints_tareas.union(sprints_epica))
                    sprints_count.at[idx, COL_CANT_SPRINTS] = total

        grouped = pd.merge(grouped, sprints_count, on=COL_CLAVE_JIRA, how="left")
        grouped[COL_CANT_SPRINTS] = grouped[COL_CANT_SPRINTS].fillna(0).astype(int)

    # --- Asignado mas frecuente por parent ---
    if asignado_col:
        def _asignado_frecuente(series):
            counts = series.dropna().value_counts()
            return counts.index[0] if len(counts) > 0 else ""

        asignado_count = (
            df_tareas.groupby(COL_PARENT)[asignado_col]
            .apply(_asignado_frecuente)
            .reset_index()
        )
        asignado_count.rename(
            columns={COL_PARENT: COL_CLAVE_JIRA, asignado_col: COL_ASIGNADO_TAREAS},
            inplace=True,
        )
        grouped = pd.merge(grouped, asignado_count, on=COL_CLAVE_JIRA, how="left")
        grouped[COL_ASIGNADO_TAREAS] = grouped[COL_ASIGNADO_TAREAS].fillna("")

    return grouped


def cruzar_epicas_con_tareas(
    df_epicas: pd.DataFrame,
    df_tareas_agg: pd.DataFrame,
    st_module=None,
) -> pd.DataFrame | None:
    """Outer merge entre epicas y tareas agrupadas, con indicador."""
    if df_epicas is None or df_tareas_agg is None:
        return None
    try:
        return pd.merge(
            df_epicas,
            df_tareas_agg,
            on=COL_CLAVE_JIRA,
            how="outer",
            indicator=True,
        )
    except Exception as e:
        if st_module:
            st_module.error(f"Error al cruzar Epicas con Tareas: {e}")
        return None
