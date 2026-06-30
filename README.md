# BMC ↔ Jira — Conciliación

Aplicación Streamlit para conciliar Work Orders y Problemas de BMC Remedy contra issues de Jira, aplicando reglas de negocio y validación de épicas.

## Funcionalidades

| Modo | Descripción |
|------|-------------|
| **Conciliación BMC vs Jira** | Cruza WO y PBI de BMC con issues de Jira, detecta sincronizados, faltantes, sobrantes y sugiere acciones (crear, actualizar, revisar). |
| **Validación Épicas vs Tareas** | Valida consistencia entre épicas de Jira y sus tareas hijas: huérfanas, épicas cerradas con tareas abiertas, sugiere cierres. |

## Requisitos

- Python 3.14+
- Dependencias: `streamlit==1.58.0`, `pandas==3.0.3`, `openpyxl==3.1.5`

## Instalación

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Ejecución

```powershell
streamlit run app.py
```

## Tests

```powershell
python -m pytest tests/ -v
```

## Formato esperado de reportes

### BMC — Work Orders (WO)
Columnas requeridas: `ID Propuesta`, `Titulo de WO`, una columna de estado (`Estado`, `Status`, `state` o `estado`)

### BMC — Problemas (PBI)
Columnas requeridas: `Problema`, `Descripcion`, una columna de estado

### Jira (conciliación)
Columnas requeridas: `Clave`, `Summary`, `BMC_ID`, una columna de estado, `Persona asignada`, `Categoria de estado`, `Celula`

### Jira — Épicas y Tareas
Columnas requeridas: `Tipo de Incidencia` (con valores `Epic`/`Épica`/`Epica`), `Clave`, `parent`, una columna de estado

## Estructura del proyecto

```
app.py              # Orquestación Streamlit
src/
  constants.py      # Nombres de columnas, equivalencias, URLs, versión
  io_utils.py       # Lectura robusta de archivos (Excel, CSV, HTML, ZIP/XML)
  transform.py      # Normalización, merge, columnas de salida
  rules.py          # Reglas de negocio (vectorizadas)
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
