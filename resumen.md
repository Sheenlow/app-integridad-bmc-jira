# BMC ↔ Jira — App de Conciliación (Streamlit)

## Qué es

Aplicación **Streamlit local** (uso exclusivo interno, empresa **Arcor**) que automatiza dos tareas de control de gestión de incidencias, hoy hechas a mano en planillas:

1. **Conciliación BMC Remedy ↔ Jira**: cruza los reportes de *Work Orders* (WO) y *Problemas* (PBI) de BMC contra los issues de Jira, y devuelve por cada registro una **"ACCION SUGERIDA"** (OK, Revisar, Falta en Jira, Sobra en Jira, Actualizar estado).
2. **Validación Épicas ↔ Tareas (Jira)**: valida consistencia entre épicas y sus tareas hijas (huérfanas, épicas cerradas con tareas abiertas, épicas listas para cerrar).

El usuario descarga reportes desde los paneles (hay botones con URLs directas de los dashboards BMC y filtros Jira de Arcor), los sube como `.csv`/`.xlsx`, y la app procesa y exporta un Excel final formateado.

## Stack

- **Python 3.14+**, **Streamlit 1.58**, **pandas 3.0**, **openpyxl 3.1** (`requirements.txt`).
- **30 tests con pytest** (README declara "30 passed").

## Arquitectura

Dos pipelines **independientes** que comparten UI pero no session state. Cada uno con su propia función de limpieza (`limpiar_datos_conciliacion` vs `limpiar_datos_epicas`).

- **Pipeline Conciliación** → state keys: `df_bmc_wo`, `df_bmc_pbi`, `df_jira`, `df_bmc_total`, `df_merge`, `df_resultado`
- **Pipeline Épicas** → state keys: `df_epicas`, `df_tareas`, `df_epicas_filt`, `df_tareas_filt`, `df_tareas_agg`, `df_epic_merge`, `df_epic_resultado`

Cada pipeline está cacheado con `@st.cache_data` (`_pipeline_conciliacion`, `_pipeline_epicas`) usando hashes **SHA-256** del contenido de los archivos como clave. Los parámetros `_hash_*` no se muestran en UI pero forman parte de la clave de cache → al re-subir el mismo archivo, no reprocesa.

## Pipeline 1 — Conciliación BMC vs Jira (`transform.py` + `rules.py`)

1. **Ingesta** (sidebar): 3 uploaders (WO, PBI, Jira) con enlaces de descarga de reportes.
2. **Normalización**:
   - `normalizar_bmc_wo`: renombra `ID Propuesta` → `BMC_ID`, detecta la columna de estado (`Estado`/`Status`/`state`/`estado`) → `Estado_BMC`, agrega `Origen_BMC="WO"`.
   - `normalizar_bmc_pbi`: ídem con `Problema` → `BMC_ID`, `Origen_BMC="PBI"`.
   - `normalizar_jira`: renombra estado → `Estado_JIRA`.
3. **Unificación** (`unificar_bmc`): concatena WO + PBI en un solo dataframe con la columna `Origen_BMC`.
4. **Cruce** (`cruzar_bmc_jira`): `pd.merge(how="outer", indicator=True)` sobre `BMC_ID`, con sufijos `_BMC`/`_JIRA`. El indicador `_merge` clasifica: `both` / `left_only` / `right_only`.
5. **Reglas de negocio** (`aplicar_reglas_negocio`, vectorizada con `np.select`):
   - `left_only` → `"Falta en Jira - Crear"` (existe en BMC, no en Jira)
   - `right_only` → `"Sobra en Jira - Revisar/Eliminar"` (existe en Jira, no en BMC)
   - `both` → se resuelve fila a fila con `_resolver_accion_both`:
     - Estado coincide → `OK - Sincronizado`
     - Jira ya avanzó a un estado compatible con otro estado BMC → `Revisar: ... Avanzar BMC a: [...]` (usa lookup inverso `_JIRA_A_BMC` precomputado)
     - Estado BMC sin equivalencia conocida o desfasado → `Actualizar estado: ...`
   - Los estados se comparan vía el diccionario `EQUIVALENCIAS` (BMC → lista de estados Jira aceptables).
6. **Enriquecimiento** (`_agregar_columnas_conciliacion`): arma columnas finales unificando WO/PBI con `fillna` (TECNICO ASIGNADO, GRUPO ASIGNADO, TITULO DE BMC) y copia campos de Jira (CLAVE, RESUMEN, PERSONA ASIGNADA, CELULA, CATEGORIA DE ESTADO, PROCESO, ESTADO PROPUESTA).
7. **Salida**: columnas en mayúsculas definidas en `COLUMNAS_OUTPUT`, exportadas a Excel con formato (`formatear_excel`).

## Pipeline 2 — Validación Épicas vs Tareas (`epics.py` + `rules.py`)

1. **Filtrado**: `filtrar_epicas` (tipo `Epic`/`Epica`) y `filtrar_tareas` (todo lo que no sea épica).
2. **Agrupación** (`agrupar_tareas_por_parent`): agrupa tareas por `parent`, calculando:
   - `Tareas Totales` / `Abiertas` (estado no final) / `Cerradas` (estado final — ver `ESTADOS_FINALES_EPICA`)
   - lista de estados únicos
   - `Cantidad de Sprints` (unión deduplicada de sprints de tareas + sprints de la épica)
   - `Asignado tareas` (asignado más frecuente)
3. **Cruce** (`cruzar_epicas_con_tareas`): outer merge épicas ↔ tareas agregadas por `Clave`.
4. **Validación** (`aplicar_validacion_epicas`):
   - Épica sin tareas hijas → `Epica sin tareas hijas`
   - Tarea sin épica padre → `Tarea sin epica padre en el reporte`
   - Épica en estado final con tareas abiertas → `Revisar: Epica cerrada pero tiene N tarea(s) abierta(s)`
   - Todas las tareas cerradas y épica abierta → `Todas las tareas cerradas — considera cerrar la epica`
   - Coherente → `OK — Consistente`
   - Sin tareas → `OK — Sin tareas registradas`

## Módulos del paquete `src/`

| Archivo | Responsabilidad |
|---|---|
| `constants.py` | Todos los nombres de columnas, `EQUIVALENCIAS`, `ESTADOS_FINALES_EPICA`, columnas de salida, URLs de reportes, `VERSION = "v1.1"` |
| `io_utils.py` | Lectura robusta en cascada (Excel → CSV multi-encoding → HTML), detección de columnas duplicadas, elección de hoja, y parser **ZIP/XML** para `.xlsx` corruptos |
| `transform.py` | Normalización, unificación y cruce BMC↔Jira; detección dinámica de columna de grupo `select__<n>` generada por BMC |
| `rules.py` | Reglas de negocio vectorizadas para ambos pipelines; lookup inverso `_JIRA_A_BMC` |
| `epics.py` | Filtrado, agrupación por parent y cruce de épicas |
| `excel_export.py` | Formato Excel: ancho de columnas, header oscuro, freeze, bordes, color condicional por acción |
| `ui.py` | CSS tema tech (slate/emerald), init de session state, badges de carga, resúmenes |

## Detalles técnicos destacables

- **`leer_archivo_robusto`**: cascada Excel → CSV (utf-8/latin-1/cp1252, separador autodetectado) → HTML. Para `.xlsx` reales (magic bytes `PK`), deshabilita el fallback y usa el **parser ZIP/XML** como último recurso (lee `sharedStrings.xml`, `workbook.xml` + relaciones para resolver hojas, y las celdas de la hoja; soporta shared strings, rich text, inlineStr y fórmulas). Es código marcado como delicado en AGENTS.md — no tocar sin test.
- **Jira en modo Conciliación** usa `hoja_preferida="Your Jira Issues"` (configuración que no hay que cambiar).
- **Columna de grupo en WO**: BMC la genera dinámicamente con patrón `select__<número>` → `_detectar_columna_select` la busca por regex.
- **Detección de estado**: candidatos `["Estado", "Status", "state", "estado"]` en ambos pipelines (`_renombrar_columna_estado` en transform, y manual en `epics.py`).
- **Convención `st_module`**: las funciones que emiten UI reciben `st_module` opcional para poder testear sin Streamlit.
- **Toasts**: `✅` éxito / `❌` error.
- **UI**: 3 tabs por modo (Ingesta → Cruce y Reglas → Resultados y Exportación), filtros por acción sugerida, métricas de sincronizados/left_only/right_only, y descargas de Excel con fecha en el nombre (`resultado_conciliacion_YYYYMMDD.xlsx`).
- **Tests** (`tests/`): `conftest.py` con fixtures de DataFrames simulados (WO, PBI, Jira, épicas, tareas, merges); 30 tests cubren normalización, unificación, cruce, reglas de negocio, validación de épicas y advertencia de duplicados. Todos incluyen `sys.path.insert(0, ".")` al inicio.
- **Empresa/contexto**: Arcor; BMC Remedy (`portaltiarcor-or1.onbmc.com`) y Jira (`arcor-saic.atlassian.net`). Uso estrictamente local, sin servicios en la nube.

## Estructura raíz

```
app.py            # Orquestación Streamlit (UI + caché + exportación)
src/              # Lógica (ver tabla)
tests/            # conftest + 4 archivos de tests
AGENTS.md         # Guía de convenciones para el agente
README.md         # Docs (badges: 30 tests OK)
requirements.txt, pytest.ini, .gitignore
```