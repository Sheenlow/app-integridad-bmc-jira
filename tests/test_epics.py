"""
Tests para validacion de Epicas vs Tareas.
"""
import pytest
import pandas as pd
import sys
sys.path.insert(0, ".")

from src.constants import COL_VALIDACION_EPICAS, COL_CLAVE_JIRA
from src.rules import aplicar_validacion_epicas
from src.epics import filtrar_epicas, filtrar_tareas, agrupar_tareas_por_parent, cruzar_epicas_con_tareas


class TestEpicValidation:

    def test_epica_sin_tareas(self):
        """Epica sin tareas hijas debe marcarse como tal."""
        df = pd.DataFrame({
            "_merge": ["left_only"],
            "Clave": ["EP-1"],
            "Estado": ["In Progress"],
            "Tareas Totales": [0],
            "Tareas Abiertas": [0],
            "Tareas Cerradas": [0],
        })
        result = aplicar_validacion_epicas(df)
        assert "Epica sin tareas hijas" in result[COL_VALIDACION_EPICAS].iloc[0]

    def test_tarea_huerfana(self):
        """Tarea sin epica padre debe marcarse."""
        df = pd.DataFrame({
            "_merge": ["right_only"],
            "Clave": ["T-1"],
            "Estado": ["En progreso"],
            "Tareas Totales": [0],
            "Tareas Abiertas": [0],
            "Tareas Cerradas": [0],
        })
        result = aplicar_validacion_epicas(df)
        assert "sin epica padre" in result[COL_VALIDACION_EPICAS].iloc[0]

    def test_epica_cerrada_tareas_abiertas(self):
        """Epica Done pero con tareas abiertas -> revisar."""
        df = pd.DataFrame({
            "_merge": ["both"],
            "Clave": ["EP-1"],
            "Estado": ["Done"],
            "Tareas Totales": [3],
            "Tareas Abiertas": [2],
            "Tareas Cerradas": [1],
        })
        result = aplicar_validacion_epicas(df)
        accion = result[COL_VALIDACION_EPICAS].iloc[0]
        assert "Revisar" in accion
        assert "tarea(s) abierta(s)" in accion

    def test_todas_cerradas_sugiere_cierre(self):
        """Todas las tareas cerradas pero epica abierta -> considerar cerrar."""
        df = pd.DataFrame({
            "_merge": ["both"],
            "Clave": ["EP-1"],
            "Estado": ["In Progress"],
            "Tareas Totales": [5],
            "Tareas Abiertas": [0],
            "Tareas Cerradas": [5],
        })
        result = aplicar_validacion_epicas(df)
        accion = result[COL_VALIDACION_EPICAS].iloc[0]
        assert "considera cerrar" in accion

    def test_consistente_ok(self):
        """Epica abierta con tareas en progreso: consistente."""
        df = pd.DataFrame({
            "_merge": ["both"],
            "Clave": ["EP-1"],
            "Estado": ["In Progress"],
            "Tareas Totales": [4],
            "Tareas Abiertas": [2],
            "Tareas Cerradas": [2],
        })
        result = aplicar_validacion_epicas(df)
        assert "OK" in result[COL_VALIDACION_EPICAS].iloc[0]

    def test_sin_tareas_registradas(self):
        """Epica en merge con total NaN -> sin tareas registradas."""
        df = pd.DataFrame({
            "_merge": ["both"],
            "Clave": ["EP-1"],
            "Estado": ["Backlog"],
            "Tareas Totales": [None],
            "Tareas Abiertas": [None],
            "Tareas Cerradas": [None],
        })
        result = aplicar_validacion_epicas(df)
        assert "Sin tareas" in result[COL_VALIDACION_EPICAS].iloc[0]


class TestFiltradoEpicas:

    def test_filtrar_epicas(self, df_epicas_sample):
        result = filtrar_epicas(df_epicas_sample)
        assert len(result) == 3

    def test_filtrar_epicas_sin_columna(self):
        df = pd.DataFrame({"Otra": [1]})
        assert filtrar_epicas(df) is None

    def test_filtrar_tareas(self, df_tareas_sample):
        result = filtrar_tareas(df_tareas_sample)
        assert len(result) == 5  # todas son tasks/stories

    def test_filtrar_mezcla_epicas_y_tareas(self):
        df = pd.DataFrame({
            "Tipo de Incidencia": ["Epic", "Task", "Epic", "Story"],
            "Clave": ["E1", "T1", "E2", "S1"],
        })
        epicas = filtrar_epicas(df)
        tareas = filtrar_tareas(df)
        assert len(epicas) == 2
        assert len(tareas) == 2


class TestAgrupacionTareas:

    def test_agrupar_por_parent(self, df_tareas_sample, df_epicas_sample):
        df_ep = filtrar_epicas(df_epicas_sample)
        df_ta = filtrar_tareas(df_tareas_sample)
        result = agrupar_tareas_por_parent(df_ta, df_ep)
        assert COL_CLAVE_JIRA in result.columns
        assert "Tareas Totales" in result.columns
        # EP-1 tiene 2 tareas
        ep1 = result[result[COL_CLAVE_JIRA] == "EP-1"]
        assert ep1["Tareas Totales"].iloc[0] == 2

    def test_agrupar_sin_columna_parent(self):
        df = pd.DataFrame({"Clave": ["T1"], "Estado": ["Done"]})
        assert agrupar_tareas_por_parent(df) is None
