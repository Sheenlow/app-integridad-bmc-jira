# BMC ↔ Jira — Conciliación

![Python](https://img.shields.io/badge/python-3.14+-blue?logo=python)
![Streamlit](https://img.shields.io/badge/streamlit-1.58.0-FF4B4B?logo=streamlit)
![License](https://img.shields.io/badge/license-MIT-green)
![Tests](https://img.shields.io/badge/tests-55%20passed-brightgreen)

Aplicación Streamlit para conciliar **BMC Remedy** contra **Jira**, con dos modos de operación independientes:

| Modo | Propósito |
|------|-----------|
| **Conciliación BMC vs Jira** | Cruza Work Orders y Problemas (PBI) de BMC con issues de Jira. Clasifica cada registro como `OK - Sincronizado` o `Revisar` según la matriz de reglas de negocio Arcor. |
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
| **Jira** | `Clave`/`Key`, `Resumen`/`Summary`, columna de estado, `Célula`, `Categoría de estado`, `Persona asignada`, `BMC_ID` (opcional — ver normalización) |

#### Validación Épicas vs Tareas

| Fuente | Columnas requeridas |
|--------|-------------------|
| **Épicas (Jira)** | `Tipo de Incidencia` (Epic/Épica/Epica), `Clave`, columna de estado |
| **Tareas (Jira)** | `Tipo de Incidencia`, `parent`, columna de estado |

La columna de estado se detecta automáticamente probando los nombres: `Estado`, `Status`, `state`, `estado`.

### Normalización defensiva de Jira

El export de Jira cambia con frecuencia el nombre de los encabezados (tildes, mayúsculas/minúsculas, prefijos `Custom field`, idioma). Por eso la ingesta de Jira pasa por una capa de normalización que hace robusto el pipeline:

- **Estandarización de encabezados** (`normalizar_columnas_jira` / `normalizar_jira` en `src/transform.py`): limpia cada nombre (quita acentos vía `unicodedata`, pasa a minúsculas y hace `strip`) y lo mapea a un esquema interno fijo mediante alias flexibles (`ALIASES_JIRA` en `src/constants.py`). Por ejemplo, `Célula`, `celula`, `Custom field (Célula)` o `Components` → `CELULA`; `Status` o `Estado` → `Estado_JIRA`.
- **Alias soportados**:
  - `CLAVE`: `clave`, `key`, `issue key`, `clave de la incidencia`
  - `RESUMEN`: `resumen`, `summary`, `resumen de la incidencia`, `titulo`, `title`
  - `CATEGORIA DE ESTADO`: `categoria de estado`, `status category`, `categoria de estado del flujo de trabajo`
  - `Estado_JIRA`: `estado`, `status`, `estado de la incidencia`
  - `PERSONA ASIGNADA`: `persona asignada`, `assignee`, `responsable`, `asignado`
  - `CELULA`: `celula`, `custom field (celula)`, `campo personalizado (celula)`, `componente/s`, `componentes`, `components`
- **Validación y logging**: si una columna crítica (`Clave`, `Estado`, `Celula`) no se detecta tras los alias, se muestra un warning en la UI: `Columna [X] no detectada en el archivo de Jira subido`.
- **Extracción defensiva de `BMC_ID`**: si la columna `BMC_ID` no existe o viene nula, se extrae del `RESUMEN` con una expresión regular (`WO`/`PBI` + número) y se normaliza el ID.
- **Merge robusto**: antes del `.merge()`, los keys `BMC_ID` de ambos lados se normalizan (`str` + `strip` + mayúsculas) para evitar fallos por espacios invisibles o diferencias de caso.
- **Normalización de BMC** (simetría con Jira): `normalizar_bmc_wo` / `normalizar_bmc_pbi` usan `normalizar_texto` + `ALIASES_BMC` (en `src/constants.py`) para resolver `ID Propuesta`/`Problema` → `BMC_ID`, `Estado` → `Estado_BMC` y `Proceso` → `PROCESO`, con warning si no se detecta la columna de ID o estado.

> Nota: `Estado propuesta` y `Proceso` provienen del reporte BMC (WO), no de Jira; se prioriza la fuente BMC y Jira queda como fallback.

### Reglas de negocio Arcor (Conciliación)

La columna `ACCION SUGERIDA` se calcula con la matriz de reglas de Arcor (`src/rules.py`), que normaliza los estados (`strip` + minúsculas + sin tildes) antes de comparar:

- **Ausencia**: si un registro existe en BMC pero no en Jira → `Revisar: Falta en Jira`; si existe en Jira pero no en BMC → `Revisar: Sobra en Jira`.
- **PBIs** (`Origen_BMC == "PBI"`): ignora `ESTADO PROPUESTA`.
  - En curso (`Asignado`, `Assigned`, `Bajo investigación`, `Under Investigation`) → espera `En progreso`/`In Progress`; si no coincide → `Revisar: Deberia estar En progreso en Jira`.
  - No finalizado (fuera de `Terminado`, `Cerrado`, `Finalizado`, `Cancelado`, `Closed`, `Resolved`, `Cancelled`) → espera `Backlog`/`Por hacer`/`To Do`; si no coincide → `Revisar: Deberia estar en Backlog en Jira`.
  - Finalizado → `OK - Sincronizado`.
- **Work Orders** (`Origen_BMC == "WO"`) según `PROCESO`:
  - **Pedidos Internos**: en curso (`Asignado`, `En curso`, `In Progress`, `Planificación`, `Planning`, …) → espera `En progreso`; si no → espera `Backlog`/`Stand By`.
  - **Gestión de la Demanda**: el "en curso" se evalúa sobre `ESTADO PROPUESTA` (`En ejecución`, `Análisis técnico`, `Proyecto creado`, `Cambio creado`) → espera `En progreso`; si no → espera `Backlog`/`Stand By`.
  - Finalizado → `OK - Sincronizado`.
- **Otros procesos / sin origen** (fallback): `OK - Sincronizado` si los estados coinciden; si no → `Revisar: Estado en incongruencia con Jira`.

> Las listas de estados equivalentes están centralizadas en `src/constants.py` (`PBI_ESTADOS_EN_CURSO`, `PBI_ESTADOS_FINALES`, `WO_ESTADOS_EN_CURSO`, `WO_ESTADOS_FINALES`, `GESTION_DEMANDA_ESTADOS_EN_CURSO`, `JIRA_EN_PROGRESO`, `JIRA_BACKLOG`, `JIRA_STAND_BY`).

## Tests

```powershell
python -m pytest tests/ -v
```

## Estructura del proyecto

```
app.py              # Orquestación Streamlit (delgada; renderizado en views.py)
src/
  constants.py      # Columnas, alias BMC/Jira, listas de estados Arcor, URLs, versión
  io_utils.py       # Lectura robusta (Excel, CSV, HTML, ZIP/XML corruptos)
  transform.py      # Normalización defensiva (BMC + Jira), unificación y cruce
  rules.py          # Reglas de negocio Arcor (conciliación + validación de épicas)
  epics.py          # Filtrado, agrupación y cruce de épicas vs tareas
  excel_export.py   # Formateo/generación de Excel (crear_excel)
  styles.py         # Paleta de colores y categorías de acciones centralizadas
  views.py          # Renderizado de la UI (sidebar + pestañas)
  utils.py          # Helpers compartidos (normalizar_texto)
  ui.py             # CSS, session state, componentes UI compartidos
tests/
  conftest.py       # Fixtures de prueba
  test_rules.py     # Tests de reglas de negocio Arcor
  test_transform.py # Tests de normalización (alias/tildes BMC y Jira) y merge
  test_pipeline_integration.py # Test end-to-end del pipeline
  test_epics.py     # Tests de validación de épicas
  test_io.py        # Tests de entrada/salida
```

## Licencia

MIT
