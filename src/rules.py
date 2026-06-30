"""
Reglas de negocio para conciliacion BMC vs Jira.
"""
import pandas as pd

from .constants import (
    COL_MERGE, COL_ESTADO_BMC, COL_ESTADO_JIRA,
    COL_ACCION_SUGERIDA, EQUIVALENCIAS,
    COL_VALIDACION_EPICAS, COL_ESTADO,
    COL_TAREAS_ABIERTAS, COL_TAREAS_CERRADAS, COL_TAREAS_TOTAL,
    ESTADOS_FINALES_EPICA,
)


def aplicar_reglas_negocio(df_merge: pd.DataFrame, st_module=None) -> pd.DataFrame | None:
    """
    Agrega la columna 'ACCION SUGERIDA' al DataFrame del merge,
    aplicando reglas de conciliacion fila por fila.
    """
    if df_merge is None or df_merge.empty:
        return None

    try:
        df = df_merge.copy()
        acciones = []

        for _, fila in df.iterrows():
            merge_val = fila.get(COL_MERGE, "")

            if merge_val == "left_only":
                acciones.append("Falta en Jira - Crear")

            elif merge_val == "right_only":
                acciones.append("Sobra en Jira - Revisar/Eliminar")

            elif merge_val == "both":
                estado_bmc = fila.get(COL_ESTADO_BMC)
                estado_jira = fila.get(COL_ESTADO_JIRA)

                if pd.isna(estado_bmc):
                    acciones.append("Actualizar estado: BMC sin estado registrado")
                elif pd.isna(estado_jira):
                    acciones.append(f"Actualizar estado: Jira sin estado, BMC esta en '{estado_bmc}'")
                else:
                    estados_validos = EQUIVALENCIAS.get(estado_bmc)
                    if estados_validos is None:
                        acciones.append(
                            f"Actualizar estado: BMC en '{estado_bmc}', "
                            f"sin equivalencia conocida para '{estado_jira}'"
                        )
                    elif estado_jira in estados_validos:
                        acciones.append("OK - Sincronizado")
                    else:
                        bmc_compatibles = [
                            bmc_s
                            for bmc_s, jira_list in EQUIVALENCIAS.items()
                            if estado_jira in jira_list and bmc_s != estado_bmc
                        ]
                        if bmc_compatibles:
                            sugeridos = ", ".join(bmc_compatibles[:3])
                            acciones.append(
                                f"Revisar: BMC en '{estado_bmc}', "
                                f"Jira ya esta en '{estado_jira}'. "
                                f"Avanzar BMC a: {sugeridos}"
                            )
                        else:
                            lista_str = ", ".join(estados_validos)
                            acciones.append(
                                f"Actualizar estado: BMC en '{estado_bmc}', "
                                f"Jira debe pasar a uno de: [{lista_str}]"
                            )
            else:
                acciones.append("Sin clasificar")

        df[COL_ACCION_SUGERIDA] = acciones
        return df

    except Exception as e:
        if st_module:
            st_module.error(f"Error al aplicar reglas de negocio: {e}")
        return None


def aplicar_validacion_epicas(df_merged: pd.DataFrame, st_module=None) -> pd.DataFrame | None:
    """
    Agrega columna 'Validacion Epica' al merge Epicas vs Tareas.
    """
    if df_merged is None or df_merged.empty:
        return None

    try:
        df = df_merged.copy()
        validaciones = []

        for _, fila in df.iterrows():
            merge_val = fila.get(COL_MERGE, "")

            if merge_val == "left_only":
                validaciones.append("Epica sin tareas hijas")

            elif merge_val == "right_only":
                validaciones.append("Tarea sin epica padre en el reporte")

            elif merge_val == "both":
                estado_epica = fila.get(COL_ESTADO)
                abiertas = fila.get(COL_TAREAS_ABIERTAS, 0)
                cerradas = fila.get(COL_TAREAS_CERRADAS, 0)
                total = fila.get(COL_TAREAS_TOTAL, 0)

                if pd.isna(total) or total == 0:
                    validaciones.append("OK — Sin tareas registradas")
                else:
                    epica_final = (
                        isinstance(estado_epica, str)
                        and estado_epica in ESTADOS_FINALES_EPICA
                    )
                    if epica_final and abiertas > 0:
                        validaciones.append(
                            f"Revisar: Epica cerrada ({estado_epica}) "
                            f"pero tiene {int(abiertas)} tarea(s) abierta(s)"
                        )
                    elif not epica_final and cerradas == total:
                        validaciones.append(
                            f"Todas las tareas cerradas ({int(total)}) "
                            f"— considera cerrar la epica ({estado_epica})"
                        )
                    else:
                        validaciones.append("OK — Consistente")
            else:
                validaciones.append("Sin clasificar")

        df[COL_VALIDACION_EPICAS] = validaciones
        return df

    except Exception as e:
        if st_module:
            st_module.error(f"Error al aplicar validacion de Epicas: {e}")
        return None
