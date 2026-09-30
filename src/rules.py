"""
Reglas de negocio Arcor para conciliacion BMC vs Jira y validacion de epicas.
"""
import numpy as np
import pandas as pd

from .utils import normalizar_texto
from .constants import (
    COL_MERGE, COL_ESTADO_BMC, COL_ESTADO_JIRA,
    COL_PRIORIDAD_BMC, COL_PRIORIDAD_JIRA,
    COL_ACCION_SUGERIDA, COL_ORIGEN,
    COL_PROCESO, COL_SRC_PROCESO,
    COL_ESTADO_PROPUESTA, COL_SRC_ESTADO_PROPUESTA,
    PBI_ESTADOS_EN_CURSO, PBI_ESTADOS_FINALES,
    WO_ESTADOS_EN_CURSO, WO_ESTADOS_FINALES,
    ESTADOS_FINALES_BMC,
    GESTION_DEMANDA_ESTADOS_EN_CURSO,
    JIRA_EN_PROGRESO, JIRA_BACKLOG, JIRA_STAND_BY,
    JIRA_ESTADOS_ACTIVOS,
    PROCESO_PEDIDOS_INTERNOS, PROCESO_GESTION_DEMANDA,
    ACCION_OK, ACCION_FALTA_JIRA, ACCION_SOBRA_JIRA, ACCION_INCONGRUENCIA,
    ACCION_DEBERIA_EN_PROGRESO, ACCION_DEBERIA_BACKLOG,
    ACCION_DEBERIA_BACKLOG_STAND_BY,
    ACCION_MODIFICAR_PRIORIDAD_JIRA, ACCION_PRIORIDAD_DESACOPLADA,
    ACCION_INCONSISTENCIA_FINAL_ACTIVO,
    EQUIVALENCIAS_PRIORIDAD,
    COL_VALIDACION_EPICAS, COL_ESTADO,
    COL_TAREAS_ABIERTAS, COL_TAREAS_CERRADAS, COL_TAREAS_TOTAL,
    ESTADOS_FINALES_EPICA,
)


def _buscar_columna(df: pd.DataFrame, candidatos: list[str]) -> str | None:
    """Devuelve la primera columna candidata presente en el DataFrame, o None."""
    for candidato in candidatos:
        if candidato in df.columns:
            return candidato
    return None


def _valor_normalizado(valor) -> str:
    """Normaliza el valor de una celda; NaN/None -> cadena vacia."""
    if valor is None:
        return ""
    if pd.isna(valor):
        return ""
    return normalizar_texto(valor)


# Equivalencias de prioridad precomputadas: variante normalizada -> categoria
# canonica (highest/high/medium/low).
_EQUIVALENCIAS_PRIORIDAD_NORM = {}
for _categoria, _variantes in EQUIVALENCIAS_PRIORIDAD.items():
    for _variante in _variantes:
        _EQUIVALENCIAS_PRIORIDAD_NORM.setdefault(normalizar_texto(_variante), _categoria)


def _prioridad_canonica(valor: str) -> str:
    """Devuelve la categoria canonica de una prioridad ya normalizada, o el
    propio valor si no coincide con ninguna equivalencia conocida."""
    if not valor:
        return ""
    return _EQUIVALENCIAS_PRIORIDAD_NORM.get(valor, valor)


def _prioridades_coinciden(prioridad_bmc, prioridad_jira) -> bool:
    """Compara prioridades usando EQUIVALENCIAS_PRIORIDAD (ingles/espanol)."""
    prioridad_bmc = _valor_normalizado(prioridad_bmc)
    prioridad_jira = _valor_normalizado(prioridad_jira)
    if not prioridad_bmc and not prioridad_jira:
        return True
    return _prioridad_canonica(prioridad_bmc) == _prioridad_canonica(prioridad_jira)


def _resolver_pbi(estado_bmc: str, estado_jira: str) -> str:
    """Reglas Arcor para PBIs. Ignora ESTADO PROPUESTA (los PBI no la poseen)."""
    if estado_bmc in PBI_ESTADOS_EN_CURSO:
        if estado_jira in JIRA_EN_PROGRESO:
            return ACCION_OK
        return ACCION_DEBERIA_EN_PROGRESO

    if estado_bmc not in PBI_ESTADOS_FINALES:
        # No en curso y no finalizado -> debe estar en Backlog
        if estado_jira in JIRA_BACKLOG:
            return ACCION_OK
        return ACCION_DEBERIA_BACKLOG

    # Finalizado -> sin accion requerida
    return ACCION_OK


def _resolver_wo_en_curso_o_backlog(en_curso: bool, estado_jira: str) -> str:
    """Regla comun de WO: en curso -> 'En progreso'; si no -> 'Backlog'/'Stand By'."""
    if en_curso:
        if estado_jira in JIRA_EN_PROGRESO:
            return ACCION_OK
        return ACCION_DEBERIA_EN_PROGRESO

    if estado_jira in JIRA_BACKLOG or estado_jira in JIRA_STAND_BY:
        return ACCION_OK
    return ACCION_DEBERIA_BACKLOG_STAND_BY


def _resolver_wo(
    estado_bmc: str, estado_jira: str, proceso: str, estado_propuesta: str,
) -> str:
    """Reglas Arcor para Work Orders, segun PROCESO."""
    if estado_bmc in WO_ESTADOS_FINALES:
        return ACCION_OK

    if proceso == PROCESO_PEDIDOS_INTERNOS:
        en_curso = estado_bmc in WO_ESTADOS_EN_CURSO
        return _resolver_wo_en_curso_o_backlog(en_curso, estado_jira)

    if proceso == PROCESO_GESTION_DEMANDA:
        en_curso = estado_propuesta in GESTION_DEMANDA_ESTADOS_EN_CURSO
        return _resolver_wo_en_curso_o_backlog(en_curso, estado_jira)

    # Proceso sin regla especifica -> comparacion simple de estados
    return _resolver_generico(estado_bmc, estado_jira)


def _resolver_generico(estado_bmc: str, estado_jira: str) -> str:
    """Fallback: OK si los estados coinciden; si no, incongruencia con Jira."""
    if estado_bmc and estado_jira and estado_bmc == estado_jira:
        return ACCION_OK
    return ACCION_INCONGRUENCIA


def _aplicar_regla_prioridad(
    accion: str, row, col_prioridad_bmc, col_prioridad_jira,
) -> str:
    """
    Ajusta la accion segun la prioridad (BMC es la fuente de la verdad):
    - Estados OK + prioridad descalzada -> 'Modificar en Jira prioridad'.
    - Estados desfasados + prioridad descalzada -> notifica la discrepancia.
    Solo se aplica si ambas columnas de prioridad estan presentes.
    """
    if not col_prioridad_bmc or not col_prioridad_jira:
        return accion

    prioridad_bmc = row.get(col_prioridad_bmc)
    prioridad_jira = row.get(col_prioridad_jira)

    if _prioridades_coinciden(prioridad_bmc, prioridad_jira):
        return accion

    if accion == ACCION_OK:
        return ACCION_MODIFICAR_PRIORIDAD_JIRA
    return f"{accion} — {ACCION_PRIORIDAD_DESACOPLADA}"


def _resolver_accion_both(
    row, col_proceso, col_estado_propuesta,
    col_prioridad_bmc=None, col_prioridad_jira=None,
) -> str:
    """Resuelve la accion para una fila con merge=both (via apply)."""
    origen = _valor_normalizado(row.get(COL_ORIGEN))
    estado_bmc = _valor_normalizado(row.get(COL_ESTADO_BMC))
    estado_jira = _valor_normalizado(row.get(COL_ESTADO_JIRA))

    # Regla de inconsistencia: cerrado/cancelado en BMC pero activo en Jira.
    if estado_bmc in ESTADOS_FINALES_BMC and estado_jira in JIRA_ESTADOS_ACTIVOS:
        return ACCION_INCONSISTENCIA_FINAL_ACTIVO

    if origen == "pbi":
        accion = _resolver_pbi(estado_bmc, estado_jira)
    elif origen == "wo":
        proceso = (
            _valor_normalizado(row.get(col_proceso)) if col_proceso else ""
        )
        estado_propuesta = (
            _valor_normalizado(row.get(col_estado_propuesta))
            if col_estado_propuesta else ""
        )
        accion = _resolver_wo(estado_bmc, estado_jira, proceso, estado_propuesta)
    else:
        # Origen desconocido -> comparacion generica
        accion = _resolver_generico(estado_bmc, estado_jira)

    return _aplicar_regla_prioridad(
        accion, row, col_prioridad_bmc, col_prioridad_jira
    )


def aplicar_reglas_negocio(df_merge: pd.DataFrame, st_module=None) -> pd.DataFrame | None:
    """
    Agrega la columna 'ACCION SUGERIDA' aplicando la matriz de reglas Arcor:
    - Ausencia: left_only -> 'Falta en Jira'; right_only -> 'Sobra en Jira'.
    - PBIs: En Curso -> 'En progreso'; no finalizado -> 'Backlog'.
    - WOs: segun PROCESO (Pedidos Internos / Gestion de la Demanda).
    """
    if df_merge is None or df_merge.empty:
        return None

    try:
        df = df_merge.copy()

        col_proceso = _buscar_columna(df, [COL_PROCESO, COL_SRC_PROCESO])
        col_estado_propuesta = _buscar_columna(
            df, [COL_ESTADO_PROPUESTA, COL_SRC_ESTADO_PROPUESTA]
        )
        col_prioridad_bmc = _buscar_columna(df, [COL_PRIORIDAD_BMC])
        col_prioridad_jira = _buscar_columna(df, [COL_PRIORIDAD_JIRA])

        merge_vals = df[COL_MERGE].values

        condiciones = [
            merge_vals == "left_only",
            merge_vals == "right_only",
            merge_vals == "both",
        ]
        opciones = [
            ACCION_FALTA_JIRA,   # left_only: el registro BMC no tiene issue en Jira
            ACCION_SOBRA_JIRA,   # right_only: el issue de Jira no tiene registro en BMC
            None,                # se resuelve abajo para filas "both"
        ]

        acciones = np.select(
            condiciones, opciones, default=ACCION_INCONGRUENCIA
        ).astype(object)

        mask_both = merge_vals == "both"
        if mask_both.any():
            acciones[mask_both] = df.loc[mask_both].apply(
                lambda row: _resolver_accion_both(
                    row, col_proceso, col_estado_propuesta,
                    col_prioridad_bmc, col_prioridad_jira,
                ),
                axis=1,
            )

        df[COL_ACCION_SUGERIDA] = acciones
        return df

    except Exception as e:
        if st_module:
            st_module.error(f"Error al aplicar reglas de negocio: {e}")
        return None


def _resolver_validacion_both(row) -> str:
    """Resuelve la validacion para una fila de epicas con merge=both."""
    estado_epica = row.get(COL_ESTADO)
    abiertas = row.get(COL_TAREAS_ABIERTAS, 0)
    cerradas = row.get(COL_TAREAS_CERRADAS, 0)
    total = row.get(COL_TAREAS_TOTAL, 0)

    if pd.isna(total) or total == 0:
        return "OK — Sin tareas registradas"

    epica_final = (
        isinstance(estado_epica, str)
        and estado_epica in ESTADOS_FINALES_EPICA
    )
    if epica_final and abiertas > 0:
        return (
            f"Revisar: Epica cerrada ({estado_epica}) "
            f"pero tiene {int(abiertas)} tarea(s) abierta(s)"
        )
    if not epica_final and cerradas == total:
        return (
            f"Todas las tareas cerradas ({int(total)}) "
            f"— considera cerrar la epica ({estado_epica})"
        )
    return "OK — Consistente"


def aplicar_validacion_epicas(df_merged: pd.DataFrame, st_module=None) -> pd.DataFrame | None:
    """
    Agrega columna 'Validacion Epica' al merge Epicas vs Tareas (vectorizada).
    """
    if df_merged is None or df_merged.empty:
        return None

    try:
        df = df_merged.copy()
        merge_vals = df[COL_MERGE].values

        condiciones = [
            merge_vals == "left_only",
            merge_vals == "right_only",
        ]
        opciones = [
            "Epica sin tareas hijas",
            "Tarea sin epica padre en el reporte",
        ]

        validaciones = np.select(condiciones, opciones, default=None).astype(object)

        # Filas "both" resueltas con apply (mas rapido que iterrows)
        mask_both = merge_vals == "both"
        if mask_both.any():
            validaciones[mask_both] = df.loc[mask_both].apply(_resolver_validacion_both, axis=1)

        validaciones[validaciones == None] = "Sin clasificar"

        df[COL_VALIDACION_EPICAS] = validaciones
        return df

    except Exception as e:
        if st_module:
            st_module.error(f"Error al aplicar validacion de Epicas: {e}")
        return None
