"""
Tests para funciones de entrada/salida.
"""
import pytest
import pandas as pd
import sys
sys.path.insert(0, ".")

from src.io_utils import detectar_columnas_duplicadas, listar_hojas_excel


class TestDuplicados:

    def test_sin_duplicados_no_warning(self):
        df = pd.DataFrame({"A": [1], "B": [2]})
        # No debe lanzar warning
        detectar_columnas_duplicadas(df, "test", st_module=None)

    def test_con_duplicados_warning(self):
        # Crear DataFrame con columnas duplicadas es raro, pero se puede simular
        # pasando una lista con nombres duplicados a .rename
        df = pd.DataFrame({"A": [1], "B": [2]})
        df.columns = ["X", "X"]
        # Debe llamar a st.warning si se pasa st_module
        class FakeSt:
            warnings = []
            def warning(self, msg):
                self.warnings.append(msg)
        fake_st = FakeSt()
        detectar_columnas_duplicadas(df, "test", st_module=fake_st)
        assert len(fake_st.warnings) == 1
