# BMC ↔ Jira — Conciliación

![Python](https://img.shields.io/badge/python-3.14+-blue?logo=python)
![Streamlit](https://img.shields.io/badge/streamlit-1.58.0-FF4B4B?logo=streamlit)
![License](https://img.shields.io/badge/license-MIT-green)
![Tests](https://img.shields.io/badge/tests-30%20passed-brightgreen)

Aplicación Streamlit para conciliar **BMC Remedy** contra **Jira**, con dos modos de operación independientes:

| Modo | Propósito |
|------|-----------|
| **Conciliación BMC vs Jira** | Cruza Work Orders y Problemas (PBI) de BMC con issues de Jira. Detecta registros sincronizados, faltantes y sobrantes, y sugiere acciones (crear, actualizar, revisar). |
| **Validación Épicas vs Tareas** | Valida consistencia entre épicas de Jira y sus tareas hijas. Detecta huérfanas, épicas cerradas con tareas abiertas y sugiere cierres. |

## Instalación

Requisitos: **Python 3.14+**.

```powershell
git clone <repo-url>
cd app-integracion
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Uso

```powershell
streamlit run app.py
```

1. Selecciona el modo en la barra lateral: **Conciliación** o **Validación Épicas**.
2. Descarga los reportes desde los enlaces provistos (BMC / Jira).
3. Carga los archivos `.xlsx` o `.csv` en los uploaders.
4. Navega por las pestañas para revisar resultados y exportar.

### Formato esperado de reportes

#### Conciliación BMC vs Jira

| Fuente | Columnas requeridas |
|--------|-------------------|
| **BMC — WO** | `ID Propuesta`, `Titulo de WO`, columna de estado |
| **BMC — PBI** | `Problema`, `Descripcion`, columna de estado |
| **Jira** | `Clave`, `Summary`, `BMC_ID`, columna de estado, `Persona asignada`, `Categoria de estado`, `Celula` |

#### Validación Épicas vs Tareas

| Fuente | Columnas requeridas |
|--------|-------------------|
| **Épicas (Jira)** | `Tipo de Incidencia` (Epic/Épica/Epica), `Clave`, columna de estado |
| **Tareas (Jira)** | `Tipo de Incidencia`, `parent`, columna de estado |

La columna de estado se detecta automáticamente probando los nombres: `Estado`, `Status`, `state`, `estado`.

## Tests

```powershell
python -m pytest tests/ -v
```

## Estructura del proyecto

```
app.py              # Orquestación Streamlit (UI + caché)
src/
  constants.py      # Nombres de columnas, equivalencias, URLs, versión
  io_utils.py       # Lectura robusta (Excel, CSV, HTML, ZIP/XML corruptos)
  transform.py      # Normalización, unificación y cruce BMC ↔ Jira
  rules.py          # Reglas de negocio vectorizadas
  epics.py          # Filtrado, agrupación y cruce de épicas vs tareas
  excel_export.py   # Formateo de Excel para descargas
  ui.py             # CSS, session state, componentes UI compartidos
tests/
  conftest.py       # Fixtures de prueba
  test_rules.py     # Tests de reglas de negocio
  test_transform.py # Tests de normalización y merge
  test_epics.py     # Tests de validación de épicas
  test_io.py        # Tests de entrada/salida
```

## Licencia

MIT
