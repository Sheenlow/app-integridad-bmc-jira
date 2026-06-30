"""
Reglas de negocio para conciliacion BMC vs Jira.
"""
import numpy as np
import pandas as pd

from .constants import (
    COL_MERGE, COL_ESTADO_BMC, COL_ESTADO_JIRA,
    COL_ACCION_SUGERIDA, EQUIVALENCIAS,
    COL_VALIDACION_EPICAS, COL_ESTADO,
    COL_TAREAS_ABIERTAS, COL_TAREAS_CERRADAS, COL_TAREAS_TOTAL,
    ESTADOS_FINALES_EPICA,
)

# Precomputo: reverse lookup de estado_jira -> lista de estados_bmc que lo contienen
_JIRA_A_BMC: dict[str, list[str]] = {}
for _bmc_state, _jira_states in EQUIVALENCIAS.items():
    for _js in _jira_states:
        _JIRA_A_BMC.setdefault(_js, []).append(_bmc_state)


def _resolver_accion_both(row) -> str:
    """Resuelve la accion para una fila con merge=both (vectorizada via apply)."""
    estado_bmc = row[COL_ESTADO_BMC]
    estado_jira = row[COL_ESTADO_JIRA]

    if pd.isna(estado_bmc):
        return "Actualizar estado: BMC sin estado registrado"
    if pd.isna(estado_jira):
        return f"Actualizar estado: Jira sin estado, BMC esta en '{estado_bmc}'"

    estados_validos = EQUIVALENCIAS.get(estado_bmc)
    if estados_validos is None:
        return (
            f"Actualizar estado: BMC en '{estado_bmc}', "
            f"sin equivalencia conocida para '{estado_jira}'"
        )

    if estado_jira in estados_validos:
        return "OK - Sincronizado"

    # Buscar si Jira ya avanzo -> sugerir avanzar BMC
    bmc_compatibles = [
        s for s in _JIRA_A_BMC.get(estado_jira, [])
        if s != estado_bmc
    ]
    if bmc_compatibles:
        sugeridos = ", ".join(bmc_compatibles[:3])
        return (
            f"Revisar: BMC en '{estado_bmc}', "
            f"Jira ya esta en '{estado_jira}'. "
            f"Avanzar BMC a: {sugeridos}"
        )

    lista_str = ", ".join(estados_validos)
    return (
        f"Actualizar estado: BMC en '{estado_bmc}', "
        f"Jira debe pasar a uno de: [{lista_str}]"
    )


def aplicar_reglas_negocio(df_merge: pd.DataFrame, st_module=None) -> pd.DataFrame | None:
    """
    Agrega la columna 'ACCION SUGERIDA' al DataFrame del merge,
    aplicando reglas de conciliacion vectorizadas.
    """
    if df_merge is None or df_merge.empty:
        return None

    try:
        df = df_merge.copy()
        merge_vals = df[COL_MERGE].values

        condiciones = [
            merge_vals == "left_only",
            merge_vals == "right_only",
            merge_vals == "both",
        ]
        opciones = [
            "Falta en Jira - Crear",
            "Sobra en Jira - Revisar/Eliminar",
            None,  # se resuelve abajo para filas "both"
        ]

        acciones = np.select(condiciones, opciones, default="Sin clasificar").astype(object)

        # Resolver solo filas "both" con apply (mas rapido que iterrows)
        mask_both = merge_vals == "both"
        if mask_both.any():
            acciones[mask_both] = df.loc[mask_both].apply(_resolver_accion_both, axis=1)

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
