"""
Tests para reglas de negocio Arcor de conciliacion BMC vs Jira.
"""
import pytest
import pandas as pd
import sys
sys.path.insert(0, ".")

from src.constants import COL_ACCION_SUGERIDA
from src.rules import aplicar_reglas_negocio


def _accion(df):
    """Aplica las reglas a un DataFrame y devuelve la primera accion sugerida."""
    result = aplicar_reglas_negocio(df)
    return result[COL_ACCION_SUGERIDA].iloc[0]


def _pbi(estado_bmc, estado_jira):
    return pd.DataFrame([{
        "_merge": "both",
        "Origen_BMC": "PBI",
        "Estado_BMC": estado_bmc,
        "Estado_JIRA": estado_jira,
    }])


def _wo(estado_bmc, estado_jira, proceso, estado_propuesta=None, col_proceso="PROCESO"):
    row = {
        "_merge": "both",
        "Origen_BMC": "WO",
        "Estado_BMC": estado_bmc,
        "Estado_JIRA": estado_jira,
        col_proceso: proceso,
    }
    if estado_propuesta is not None:
        row["ESTADO PROPUESTA"] = estado_propuesta
    return pd.DataFrame([row])


class TestReglaAusencia:

    def test_left_only_es_falta_en_jira(self):
        df = pd.DataFrame([{
            "_merge": "left_only",
            "Origen_BMC": "WO",
            "Estado_BMC": "Asignado",
        }])
        assert _accion(df) == "Revisar: Falta en Jira"

    def test_right_only_es_sobra_en_jira(self):
        df = pd.DataFrame([{
            "_merge": "right_only",
            "Estado_JIRA": "En progreso",
        }])
        assert _accion(df) == "Revisar: Sobra en Jira"


class TestReglasPBI:

    def test_en_curso_sincronizado(self):
        assert _accion(_pbi("Assigned", "En progreso")) == "OK - Sincronizado"

    def test_en_curso_in_progress_sincronizado(self):
        assert _accion(_pbi("Under Investigation", "In Progress")) == "OK - Sincronizado"

    def test_en_curso_mal_estado(self):
        assert (
            _accion(_pbi("Assigned", "Backlog"))
            == "Revisar: Deberia estar En progreso en Jira"
        )

    def test_no_en_curso_backlog_sincronizado(self):
        assert _accion(_pbi("Draft", "Backlog")) == "OK - Sincronizado"

    def test_no_en_curso_mal_estado(self):
        assert (
            _accion(_pbi("Draft", "En progreso"))
            == "Revisar: Deberia estar en Backlog en Jira"
        )

    def test_finalizado_con_jira_activo_inconsistencia(self):
        # Regla nueva: cerrado en BMC pero activo en Jira -> inconsistencia
        assert (
            _accion(_pbi("Closed", "En progreso"))
            == "Revisar: Inconsistencia - CERRADO/CANCELADO en BMC pero activo en Jira"
        )

    def test_finalizado_sin_jira_activo_ok(self):
        # PBI finalizado y Jira no activo -> sin accion requerida
        assert _accion(_pbi("Closed", "Cerrado")) == "OK - Sincronizado"

    def test_ignora_estado_propuesta(self):
        df = _pbi("Assigned", "Backlog")
        df["ESTADO PROPUESTA"] = "En ejecucion"
        assert _accion(df) == "Revisar: Deberia estar En progreso en Jira"


class TestReglasWOPedidosInternos:

    def test_en_curso_sincronizado(self):
        df = _wo("Asignado", "En progreso", "Pedidos Internos")
        assert _accion(df) == "OK - Sincronizado"

    def test_en_curso_mal_estado(self):
        df = _wo("En curso", "Backlog", "Pedidos Internos")
        assert _accion(df) == "Revisar: Deberia estar En progreso en Jira"

    def test_no_en_curso_stand_by_sincronizado(self):
        df = _wo("Pendiente Aprobacion del negocio", "Stand By", "Pedidos Internos")
        assert _accion(df) == "OK - Sincronizado"

    def test_no_en_curso_backlog_sincronizado(self):
        df = _wo("Pendiente Aprobacion del negocio", "Backlog", "Pedidos Internos")
        assert _accion(df) == "OK - Sincronizado"

    def test_no_en_curso_mal_estado(self):
        df = _wo("Pendiente Aprobacion del negocio", "En progreso", "Pedidos Internos")
        assert _accion(df) == "Revisar: Deberia estar en Backlog o Stand By en Jira"

    def test_finalizada_con_jira_activo_inconsistencia(self):
        # "finalizada" ahora es estado final: + Jira activo -> inconsistencia
        df = _wo("Finalizada", "En progreso", "Pedidos Internos")
        assert (
            _accion(df)
            == "Revisar: Inconsistencia - CERRADO/CANCELADO en BMC pero activo en Jira"
        )

    def test_finalizada_sin_jira_activo_ok(self):
        df = _wo("Finalizada", "Cerrado", "Pedidos Internos")
        assert _accion(df) == "OK - Sincronizado"


class TestReglasWOGestionDemanda:

    def test_en_curso_sincronizado(self):
        df = _wo(
            "Pendiente Aprobacion del negocio", "En progreso",
            "Gestión de la Demanda", estado_propuesta="En ejecución",
        )
        assert _accion(df) == "OK - Sincronizado"

    def test_en_curso_mal_estado(self):
        df = _wo(
            "Pendiente Aprobacion del negocio", "Backlog",
            "Gestion de la Demanda", estado_propuesta="Proyecto creado",
        )
        assert _accion(df) == "Revisar: Deberia estar En progreso en Jira"

    def test_no_en_curso_backlog_sincronizado(self):
        df = _wo(
            "Pendiente Aprobacion del negocio", "Backlog",
            "Gestión de la Demanda", estado_propuesta="Pendiente Aprobacion",
        )
        assert _accion(df) == "OK - Sincronizado"

    def test_no_en_curso_mal_estado(self):
        df = _wo(
            "Pendiente Aprobacion del negocio", "En progreso",
            "Gestión de la Demanda", estado_propuesta="Pendiente Aprobacion",
        )
        assert _accion(df) == "Revisar: Deberia estar en Backlog o Stand By en Jira"


class TestRobustez:

    def test_proceso_con_nombre_fuente(self):
        # La columna fuente "Proceso" (sin mayusculas) tambien se resuelve
        df = _wo("Asignado", "En progreso", "Pedidos Internos", col_proceso="Proceso")
        assert _accion(df) == "OK - Sincronizado"

    def test_estados_iguales_sin_origen_ok(self):
        df = pd.DataFrame([{
            "_merge": "both",
            "Estado_BMC": "En progreso",
            "Estado_JIRA": "En progreso",
        }])
        assert _accion(df) == "OK - Sincronizado"

    def test_estados_distintos_sin_origen_incongruencia(self):
        df = pd.DataFrame([{
            "_merge": "both",
            "Estado_BMC": "Asignado",
            "Estado_JIRA": "En progreso",
        }])
        assert _accion(df) == "Revisar: Estado en incongruencia con Jira"

    def test_normaliza_tildes_y_caso(self):
        # "Bajo Investigación" (con tilde) debe tratarse como "bajo investigacion"
        assert _accion(_pbi("Bajo Investigación", "En progreso")) == "OK - Sincronizado"

    def test_df_none_retorna_none(self):
        assert aplicar_reglas_negocio(None) is None

    def test_df_vacio_retorna_none(self):
        assert aplicar_reglas_negocio(pd.DataFrame()) is None


class TestReglasPrioridad:

    def test_estado_ok_prioridad_descalzada(self):
        """Estados sincronizados pero prioridad distinta -> modificar en Jira."""
        df = _wo("Asignado", "En progreso", "Pedidos Internos")
        df["Prioridad_BMC"] = "High"
        df["Prioridad_JIRA"] = "Low"
        assert _accion(df) == "Modificar en Jira prioridad"

    def test_estado_ok_prioridad_equivalente_espanol(self):
        """'High' (BMC) y 'Alto' (Jira) son equivalentes -> OK."""
        df = _wo("Asignado", "En progreso", "Pedidos Internos")
        df["Prioridad_BMC"] = "High"
        df["Prioridad_JIRA"] = "Alto"
        assert _accion(df) == "OK - Sincronizado"

    def test_estado_desfasado_y_prioridad_descalzada(self):
        """Estado desfasado + prioridad distinta -> notifica la discrepancia."""
        df = _wo("Asignado", "Backlog", "Pedidos Internos")
        df["Prioridad_BMC"] = "1 - Critico"
        df["Prioridad_JIRA"] = "Low"
        accion = _accion(df)
        assert accion.startswith("Revisar: Deberia estar En progreso en Jira")
        assert "Prioridad desincronizada con Jira" in accion

    def test_prioridad_ausente_no_cambia_accion(self):
        """Sin columnas de prioridad no debe alterarse la accion base."""
        df = _wo("Asignado", "Backlog", "Pedidos Internos")
        assert _accion(df) == "Revisar: Deberia estar En progreso en Jira"


class TestReglaInconsistenciaFinalActivo:

    def test_bmc_final_jira_activo_inconsistencia(self):
        """Cerrado en BMC + activo en Jira -> inconsistencia."""
        df = _wo("Cancelado", "En progreso", "Pedidos Internos")
        assert (
            _accion(df)
            == "Revisar: Inconsistencia - CERRADO/CANCELADO en BMC pero activo en Jira"
        )

    def test_bmc_final_jira_final_ok(self):
        """Cerrado en BMC + no activo en Jira -> sin inconsistencia (OK)."""
        df = _wo("Cancelado", "Cerrado", "Pedidos Internos")
        assert _accion(df) == "OK - Sincronizado"
