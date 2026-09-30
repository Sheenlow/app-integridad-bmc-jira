"""
Tests para transformacion y normalizacion de datos BMC/Jira.
"""
import pytest
import pandas as pd
import sys
sys.path.insert(0, ".")

from src.constants import (
    COL_BMC_ID, COL_ESTADO_BMC, COL_ORIGEN, COL_ESTADO_JIRA,
    COL_PRIORIDAD_BMC, COL_PRIORIDAD_JIRA,
    COL_OUT_PRIORIDAD_BMC, COL_OUT_PRIORIDAD_JIRA,
    ALIASES_GRUPO_WO, ALIASES_GRUPO_PBI,
)
from src.transform import (
    normalizar_bmc_wo,
    normalizar_bmc_pbi,
    unificar_bmc,
    filtrar_bmc_historico,
    filtrar_bmc_por_grupo,
    normalizar_jira,
    cruzar_bmc_jira,
    _agregar_columnas_conciliacion,
)


class TestNormalizacion:

    def test_normalizar_wo_ok(self, df_bmc_wo_sample):
        result = normalizar_bmc_wo(df_bmc_wo_sample)
        assert COL_BMC_ID in result.columns
        assert COL_ESTADO_BMC in result.columns
        assert result[COL_ORIGEN].iloc[0] == "WO"
        assert result[COL_BMC_ID].iloc[0] == "WO-001"

    def test_normalizar_wo_sin_id(self):
        """Si falta ID Propuesta, debe retornar None."""
        df = pd.DataFrame({"Otra columna": [1, 2, 3]})
        assert normalizar_bmc_wo(df) is None

    def test_normalizar_pbi_ok(self, df_bmc_pbi_sample):
        result = normalizar_bmc_pbi(df_bmc_pbi_sample)
        assert COL_BMC_ID in result.columns
        assert COL_ESTADO_BMC in result.columns
        assert result[COL_ORIGEN].iloc[0] == "PBI"

    def test_unificar_bmc(self, df_bmc_wo_sample, df_bmc_pbi_sample):
        df_wo = normalizar_bmc_wo(df_bmc_wo_sample)
        df_pbi = normalizar_bmc_pbi(df_bmc_pbi_sample)
        result = unificar_bmc(df_wo, df_pbi)
        assert result.shape[0] == 5  # 3 WO + 2 PBI
        assert set(result[COL_ORIGEN].unique()) == {"WO", "PBI"}

    def test_unificar_solo_uno(self, df_bmc_wo_sample):
        df_wo = normalizar_bmc_wo(df_bmc_wo_sample)
        result = unificar_bmc(df_wo, None)
        assert result.shape[0] == 3

    def test_normalizar_jira_ok(self, df_jira_sample):
        result = normalizar_jira(df_jira_sample)
        assert COL_ESTADO_JIRA in result.columns

    def test_normalizar_jira_none(self):
        assert normalizar_jira(None) is None


class TestMerge:

    def test_cruce_bmc_jira(self, df_bmc_wo_sample, df_jira_sample):
        df_wo = normalizar_bmc_wo(df_bmc_wo_sample)
        df_jira = normalizar_jira(df_jira_sample)
        result = cruzar_bmc_jira(df_wo, df_jira)
        assert "_merge" in result.columns
        assert "both" in result["_merge"].values

    def test_cruce_con_none(self):
        assert cruzar_bmc_jira(None, pd.DataFrame()) is None


class TestNormalizacionJira:

    def test_normaliza_columnas_con_tildes(self):
        """Columnas con tilde deben mapear al esquema canonico (mayusculas)."""
        df = pd.DataFrame({
            "Clave": ["J-1"],
            "Célula": ["C1"],
            "Categoría de estado": ["Done"],
            "Status": ["Done"],
            "Persona asignada": ["user1"],
        })
        result = normalizar_jira(df)
        assert "CLAVE" in result.columns
        assert "CELULA" in result.columns
        assert "CATEGORIA DE ESTADO" in result.columns
        assert "PERSONA ASIGNADA" in result.columns
        assert "Estado_JIRA" in result.columns

    def test_normaliza_alias_custom_field(self):
        """Alias en ingles / 'Custom field' deben mapear correctamente."""
        df = pd.DataFrame({
            "Issue Key": ["J-1"],
            "Custom field (Célula)": ["C1"],
            "Status Category": ["Done"],
            "Status": ["Done"],
            "Assignee": ["user1"],
        })
        result = normalizar_jira(df)
        assert "CLAVE" in result.columns
        assert "CELULA" in result.columns
        assert "CATEGORIA DE ESTADO" in result.columns
        assert "PERSONA ASIGNADA" in result.columns
        assert "Estado_JIRA" in result.columns

    def test_extrae_bmc_id_desde_resumen(self):
        """Si no hay columna BMC_ID, se extrae del RESUMEN (regex WO/PBI)."""
        df = pd.DataFrame({
            "Clave": ["J-1"],
            "Resumen": ["Instalar servidor WO-001"],
            "Status": ["Done"],
        })
        result = normalizar_jira(df)
        assert "BMC_ID" in result.columns
        assert result["BMC_ID"].iloc[0] == "WO-001"

    def test_preserva_bmc_id_y_rellena_nulos_desde_resumen(self):
        """BMC_ID existente se conserva; los nulos se rellenan desde RESUMEN."""
        df = pd.DataFrame({
            "Clave": ["J-1", "J-2"],
            "Resumen": ["Instalar WO-001", "Migrar DB PBI-002"],
            "Status": ["Done", "Done"],
            "BMC_ID": ["WO-001", None],
        })
        result = normalizar_jira(df)
        assert result["BMC_ID"].iloc[0] == "WO-001"
        assert result["BMC_ID"].iloc[1] == "PBI-002"

    def test_warning_columna_critica_faltante(self):
        """Columnas criticas ausentes deben generar warning en la UI."""
        class FakeSt:
            def __init__(self):
                self.warnings = []

            def warning(self, msg):
                self.warnings.append(msg)

            def toast(self, *args, **kwargs):
                pass

            def info(self, *args, **kwargs):
                pass

        fake = FakeSt()
        df = pd.DataFrame({"Resumen": ["algo"]})
        normalizar_jira(df, st_module=fake)
        assert any("no detectada" in w for w in fake.warnings)


class TestPrioridad:

    def test_normalizar_wo_mapea_priority(self):
        df = pd.DataFrame({
            "ID Propuesta": ["WO-001"],
            "Estado": ["Asignado"],
            "Priority": ["High"],
        })
        result = normalizar_bmc_wo(df)
        assert COL_PRIORIDAD_BMC in result.columns
        assert result[COL_PRIORIDAD_BMC].iloc[0] == "High"

    def test_normalizar_pbi_mapea_prioridad(self):
        df = pd.DataFrame({
            "Problema": ["PBI-001"],
            "Estado": ["Assigned"],
            "Prioridad": ["Alta"],
        })
        result = normalizar_bmc_pbi(df)
        assert COL_PRIORIDAD_BMC in result.columns
        assert result[COL_PRIORIDAD_BMC].iloc[0] == "Alta"

    def test_normalizar_jira_mapea_prioridad(self):
        df = pd.DataFrame({
            "Clave": ["J-1"],
            "Resumen": ["Instalar WO-001"],
            "Status": ["Done"],
            "Priority": ["Medium"],
        })
        result = normalizar_jira(df)
        assert COL_PRIORIDAD_JIRA in result.columns
        assert result[COL_PRIORIDAD_JIRA].iloc[0] == "Medium"

    def test_agregar_columnas_propaga_prioridad(self):
        df = pd.DataFrame({
            "Prioridad_BMC": ["High"],
            "Prioridad_JIRA": ["Low"],
        })
        result = _agregar_columnas_conciliacion(df)
        assert COL_OUT_PRIORIDAD_BMC in result.columns
        assert COL_OUT_PRIORIDAD_JIRA in result.columns
        assert result[COL_OUT_PRIORIDAD_BMC].iloc[0] == "High"
        assert result[COL_OUT_PRIORIDAD_JIRA].iloc[0] == "Low"

    def test_agregar_columnas_prioridad_faltante_vacia(self):
        df = pd.DataFrame({"_merge": ["both"]})
        result = _agregar_columnas_conciliacion(df)
        assert COL_OUT_PRIORIDAD_BMC in result.columns
        assert result[COL_OUT_PRIORIDAD_BMC].iloc[0] == ""


class TestFiltradoHistorico:

    def test_cerrado_sin_tarjeta_activa_se_elimina(self):
        """BMC cerrado SIN tarjeta activa en Jira -> se descarta."""
        df_bmc = pd.DataFrame({
            "BMC_ID": ["WO-001", "WO-002"],
            "Estado_BMC": ["Cerrado", "Asignado"],
        })
        df_jira = pd.DataFrame({
            "BMC_ID": ["WO-999"],
            "Estado_JIRA": ["En progreso"],
        })
        result = filtrar_bmc_historico(df_bmc, df_jira)
        ids = result["BMC_ID"].tolist()
        assert "WO-001" not in ids  # cerrado y sin activa -> eliminado
        assert "WO-002" in ids      # no final -> mantenido

    def test_cerrado_con_tarjeta_activa_se_mantiene(self):
        """BMC cerrado CON tarjeta activa en Jira -> se mantiene."""
        df_bmc = pd.DataFrame({
            "BMC_ID": ["WO-001"],
            "Estado_BMC": ["Cerrado"],
        })
        df_jira = pd.DataFrame({
            "BMC_ID": ["WO-001"],
            "Estado_JIRA": ["En progreso"],
        })
        result = filtrar_bmc_historico(df_bmc, df_jira)
        assert "WO-001" in result["BMC_ID"].tolist()

    def test_estado_no_final_siempre_se_mantiene(self):
        """Un registro no final se mantiene aunque no este en Jira."""
        df_bmc = pd.DataFrame({
            "BMC_ID": ["WO-002"],
            "Estado_BMC": ["Asignado"],
        })
        result = filtrar_bmc_historico(df_bmc, pd.DataFrame())
        assert "WO-002" in result["BMC_ID"].tolist()


class TestFiltradoPorGrupo:

    def test_filtra_grupos_no_permitidos_wo(self):
        df = pd.DataFrame({
            "BMC_ID": ["WO-001", "WO-002", "WO-003"],
            "Grupo Experto": ["GPA ADM - ADM", "GPA LCI COMEX", "WEB"],
        })
        result = filtrar_bmc_por_grupo(df, ALIASES_GRUPO_WO)
        assert result["BMC_ID"].tolist() == ["WO-001"]

    def test_filtra_grupo_asignado_pbi(self):
        df = pd.DataFrame({
            "BMC_ID": ["PBI-001", "PBI-002", "PBI-003"],
            "Grupo_Asignado": ["GPA ADM - RRHH", "GPA LCI COMEX", "GPA ADM - ADM"],
        })
        result = filtrar_bmc_por_grupo(df, ALIASES_GRUPO_PBI)
        assert result["BMC_ID"].tolist() == ["PBI-001", "PBI-003"]

    def test_normaliza_encabezado_y_strip(self):
        """Encabezado con variacion de caso y valores con espacios."""
        df = pd.DataFrame({
            "BMC_ID": ["WO-001", "WO-002"],
            "GRUPO EXPERTO": ["  GPA ADM - ADM  ", "WEB"],
        })
        result = filtrar_bmc_por_grupo(df, ALIASES_GRUPO_WO)
        assert result["BMC_ID"].tolist() == ["WO-001"]

    def test_sin_columna_grupo_no_filtra(self):
        df = pd.DataFrame({
            "BMC_ID": ["WO-001", "WO-002"],
            "Estado_BMC": ["Asignado", "Asignado"],
        })
        result = filtrar_bmc_por_grupo(df, ALIASES_GRUPO_WO)
        assert result["BMC_ID"].tolist() == ["WO-001", "WO-002"]
