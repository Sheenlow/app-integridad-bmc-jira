"""
Fixtures compartidos para los tests.
"""
import pytest
import pandas as pd
import numpy as np


@pytest.fixture
def df_bmc_wo_sample():
    """DataFrame simulado de Work Orders BMC."""
    return pd.DataFrame({
        "ID Propuesta": ["WO-001", "WO-002", "WO-003"],
        "Titulo de WO": ["Instalar servidor", "Migrar DB", "Configurar red"],
        "Estado": ["En ejecucion", "Finalizada", "Asignado"],
        "Asignatario Experto": ["user1", "user2", "user3"],
        "Estado propuesta": ["Activo", "Activo", "Pendiente"],
        "Proceso": ["IT", "IT", "Redes"],
    })


@pytest.fixture
def df_bmc_pbi_sample():
    """DataFrame simulado de Problemas BMC."""
    return pd.DataFrame({
        "Problema": ["PBI-001", "PBI-002"],
        "Descripcion": ["Error en login", "Rendimiento bajo"],
        "Estado": ["Assigned", "Under Investigation"],
        "Usuario_Asignado": ["user4", "user5"],
    })


@pytest.fixture
def df_jira_sample():
    """DataFrame simulado de Jira."""
    return pd.DataFrame({
        "Clave": ["JIRA-100", "JIRA-101", "JIRA-102", "JIRA-999"],
        "Summary": ["Instalar servidor", "Migrar DB", "Configurar red", "Tarea extra"],
        "Status": ["En progreso", "Listo", "Por hacer", "En progreso"],
        "IssueType": ["Task", "Task", "Task", "Task"],
        "Persona asignada": ["user1", "user2", "user3", "user6"],
        "Categoria de estado": ["Dev Doing", "Done", "To Do", "Dev Doing"],
        "Celula": ["C1", "C2", "C3", "C4"],
        "BMC_ID": ["WO-001", "WO-002", "WO-003", "WO-999"],
    })


@pytest.fixture
def df_epicas_sample():
    """DataFrame simulado de Epicas Jira."""
    return pd.DataFrame({
        "Tipo de Incidencia": ["Epic", "Epic", "Epic"],
        "Clave": ["EP-1", "EP-2", "EP-3"],
        "Resumen": ["Login SSO", "Reportes", "Notificaciones"],
        "Estado": ["In Progress", "Done", "In Progress"],
        "Persona asignada": ["user1", "user2", "user3"],
        "Celula": ["C1", "C2", "C3"],
        "BMC_ID": ["BMC-1", "BMC-2", "BMC-3"],
    })


@pytest.fixture
def df_tareas_sample():
    """DataFrame simulado de Tareas Jira."""
    return pd.DataFrame({
        "Tipo de Incidencia": ["Task", "Task", "Task", "Task", "Story"],
        "Clave": ["T-1", "T-2", "T-3", "T-4", "T-5"],
        "parent": ["EP-1", "EP-1", "EP-2", "EP-2", "EP-2"],
        "Estado": ["En progreso", "Finalizada", "Finalizada", "Finalizada", "Cancelado"],
        "Persona asignada": ["user1", "user1", "user2", "user2", "user2"],
    })


@pytest.fixture
def df_merge_sample(df_bmc_wo_sample, df_jira_sample):
    """DataFrame merge de BMC y Jira para tests de reglas."""
    from src.transform import normalizar_bmc_wo, normalizar_jira, cruzar_bmc_jira
    df_wo_norm = normalizar_bmc_wo(df_bmc_wo_sample)
    df_jira_norm = normalizar_jira(df_jira_sample)
    return cruzar_bmc_jira(df_wo_norm, df_jira_norm)


@pytest.fixture
def df_epic_merge_sample(df_epicas_sample, df_tareas_sample):
    """DataFrame merge de Epicas y Tareas para tests de validacion."""
    from src.epics import filtrar_epicas, filtrar_tareas, agrupar_tareas_por_parent, cruzar_epicas_con_tareas
    df_ep = filtrar_epicas(df_epicas_sample)
    df_ta = agrupar_tareas_por_parent(filtrar_tareas(df_tareas_sample), df_ep)
    return cruzar_epicas_con_tareas(df_ep, df_ta)
