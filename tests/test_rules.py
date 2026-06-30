"""
Tests para reglas de negocio de conciliacion BMC vs Jira.
"""
import pytest
import pandas as pd
import sys
sys.path.insert(0, ".")

from src.constants import COL_ACCION_SUGERIDA
from src.rules import aplicar_reglas_negocio


class TestReglasNegocio:

    def test_left_only_falta_crear(self, df_merge_sample):
        """WO que no existe en Jira debe sugerir 'Falta en Jira - Crear'."""
        result = aplicar_reglas_negocio(df_merge_sample)
        left_rows = result[result["_merge"] == "left_only"]
        for accion in left_rows[COL_ACCION_SUGERIDA]:
            assert accion == "Falta en Jira - Crear"

    def test_right_only_sobra_revisar(self, df_merge_sample):
        """Issue en Jira que no existe en BMC debe sugerir 'Sobra en Jira'."""
        result = aplicar_reglas_negocio(df_merge_sample)
        right_rows = result[result["_merge"] == "right_only"]
        for accion in right_rows[COL_ACCION_SUGERIDA]:
            assert accion == "Sobra en Jira - Revisar/Eliminar"

    def test_both_sincronizado(self, df_merge_sample):
        """WO y Jira con estados equivalentes deben ser 'OK - Sincronizado'."""
        result = aplicar_reglas_negocio(df_merge_sample)
        both_rows = result[result["_merge"] == "both"]
        # WO "Finalizada" -> Jira "Listo" deberian ser equivalentes
        assert any("OK" in str(a) for a in both_rows[COL_ACCION_SUGERIDA])

    def test_both_no_equivalencia(self):
        """Estado BMC sin equivalencia conocida debe generar advertencia."""
        import pandas as pd
        df = pd.DataFrame({
            "_merge": ["both"],
            "Estado_BMC": ["EstadoInventado"],
            "Estado_JIRA": ["In Progress"],
        })
        result = aplicar_reglas_negocio(df)
        assert "sin equivalencia" in str(result[COL_ACCION_SUGERIDA].iloc[0])

    def test_bmc_atrasado(self):
        """BMC en estado anterior, Jira avanzo: sugerir avanzar BMC."""
        import pandas as pd
        df = pd.DataFrame({
            "_merge": ["both"],
            "Estado_BMC": ["Asignado"],
            "Estado_JIRA": ["En progreso"],
        })
        result = aplicar_reglas_negocio(df)
        accion = str(result[COL_ACCION_SUGERIDA].iloc[0])
        assert "Revisar" in accion
        assert "Avanzar BMC" in accion

    def test_df_none_retorna_none(self):
        assert aplicar_reglas_negocio(None) is None

    def test_df_vacio_retorna_none(self):
        assert aplicar_reglas_negocio(pd.DataFrame()) is None
