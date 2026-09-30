"""
Test de integracion end-to-end del pipeline de conciliacion.
"""
import sys
sys.path.insert(0, ".")

import pandas as pd

from src.transform import (
    normalizar_bmc_wo,
    normalizar_jira,
    cruzar_bmc_jira,
    _agregar_columnas_conciliacion,
    _formatear_output_conciliacion,
)
from src.rules import aplicar_reglas_negocio
from src.constants import COL_ACCION_SUGERIDA


def _run_pipeline(df_bmc, df_jira):
    """Ejecuta la secuencia completa: cruzar -> reglas -> enriquecer -> formatear."""
    df_bmc_norm = normalizar_bmc_wo(df_bmc)
    df_jira_norm = normalizar_jira(df_jira)
    merged = cruzar_bmc_jira(df_bmc_norm, df_jira_norm)
    resultado = aplicar_reglas_negocio(merged)
    resultado = _agregar_columnas_conciliacion(resultado)
    return _formatear_output_conciliacion(resultado)


def test_pipeline_completo_con_tildes_jira():
    """Columnas de Jira con tildes deben quedar pobladas (no NaN)."""
    wo = pd.DataFrame({
        "ID Propuesta": ["WO-001", "WO-002"],
        "Titulo de WO": ["Instalar servidor", "Migrar DB"],
        "Estado": ["Asignado", "Finalizada"],
        "Asignatario Experto": ["user1", "user2"],
        "Estado propuesta": ["Activo", "Activo"],
        "Proceso": ["Pedidos Internos", "Pedidos Internos"],
    })
    jira = pd.DataFrame({
        "Clave": ["J-100", "J-101"],
        "Resumen": ["Instalar servidor", "Migrar DB"],
        "Célula": ["C1", "C2"],
        "Categoría de estado": ["Dev Doing", "Done"],
        "Estado": ["En progreso", "Listo"],
        "Persona asignada": ["user1", "user2"],
        "BMC_ID": ["WO-001", "WO-002"],
    })

    out = _run_pipeline(wo, jira)

    # Columnas provenientes de Jira (con tildes) deben tener valores validos
    assert out["CELULA"].tolist() == ["C1", "C2"]
    assert out["CATEGORIA DE ESTADO"].tolist() == ["Dev Doing", "Done"]
    assert out["RESUMEN"].tolist() == ["Instalar servidor", "Migrar DB"]
    assert not out["CELULA"].isna().any()
    assert not out["CATEGORIA DE ESTADO"].isna().any()
    assert not out["RESUMEN"].isna().any()

    # Reglas aplicadas
    assert COL_ACCION_SUGERIDA in out.columns
    assert out[COL_ACCION_SUGERIDA].tolist() == [
        "OK - Sincronizado",  # WO-001: Pedidos Internos "Asignado" + Jira "En progreso"
        "OK - Sincronizado",  # WO-002: "Finalizada" -> finalizado -> OK
    ]


def test_pipeline_extrae_bmc_id_desde_resumen():
    """Jira sin columna BMC_ID explicita: se extrae del Resumen."""
    wo = pd.DataFrame({
        "ID Propuesta": ["WO-001"],
        "Titulo de WO": ["Instalar servidor"],
        "Estado": ["Asignado"],
        "Proceso": ["Pedidos Internos"],
    })
    jira = pd.DataFrame({
        "Clave": ["J-100"],
        "Resumen": ["Instalar servidor (WO-001)"],
        "Célula": ["C1"],
        "Categoría de estado": ["Dev Doing"],
        "Estado": ["En progreso"],
    })

    out = _run_pipeline(wo, jira)

    assert out["BMC_ID"].tolist() == ["WO-001"]
    assert out["CELULA"].tolist() == ["C1"]
    assert out["CATEGORIA DE ESTADO"].tolist() == ["Dev Doing"]
