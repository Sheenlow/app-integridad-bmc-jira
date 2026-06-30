"""
Tests para transformacion y normalizacion de datos BMC/Jira.
"""
import pytest
import pandas as pd
import sys
sys.path.insert(0, ".")

from src.constants import COL_BMC_ID, COL_ESTADO_BMC, COL_ORIGEN, COL_ESTADO_JIRA
from src.transform import (
    normalizar_bmc_wo,
    normalizar_bmc_pbi,
    unificar_bmc,
    normalizar_jira,
    cruzar_bmc_jira,
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
