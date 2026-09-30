# AGENTS.md — app-integracion

Proyecto Streamlit local para conciliar BMC Remedy vs Jira. Uso exclusivo local.

## Cómo ejecutar

```powershell
.\venv\Scripts\Activate.ps1
streamlit run app.py
```

## Cómo testear

```powershell
python -m pytest tests/ -v
```

Todos los tests incluyen `sys.path.insert(0, ".")` al inicio. Al crear nuevos tests, seguir ese patrón aunque `pytest.ini` ya declare `pythonpath = ["."]`.

## Arquitectura

Dos pipelines independientes que comparten UI pero no session state:

- **Conciliación BMC vs Jira** → `transform.py` + `rules.py` → state keys: `df_bmc_wo`, `df_bmc_pbi`, `df_jira`, `df_bmc_total`, `df_merge`, `df_resultado`
- **Validación Épicas vs Tareas** → `epics.py` + `rules.py` (validación épicas) → state keys: `df_epicas`, `df_tareas`, `df_epicas_filt`, `df_tareas_filt`, `df_tareas_agg`, `df_epic_merge`, `df_epic_resultado`

Cada pipeline tiene su propia función de limpieza (`limpiar_datos_conciliacion`, `limpiar_datos_epicas`). Al modificar uno, verificar que el otro no se rompa.

El cache de Streamlit (`_pipeline_conciliacion`, `_pipeline_epicas`, en `src/views.py`) usa hashes SHA-256 del contenido de archivos como claves. Los parámetros `_hash_*` (con prefijo `_`) se excluyen del display de la UI pero participan en la clave de cache.

La UI esta modularizada: `app.py` es delgada (config + orquestacion) y el renderizado vive en `src/views.py`. La paleta de colores de acciones esta centralizada en `src/styles.py`.

## Qué no modificar
- No cambiar nombres de columnas en `src/constants.py` sin revisar el impacto en las funciones de normalización y merge.
- Las reglas de negocio en `src/rules.py` usan las listas de estados centralizadas en `src/constants.py` (`PBI_ESTADOS_*`, `WO_ESTADOS_*`, `JIRA_*`, `PROCESO_*`) y los mensajes de acción (`ACCION_*`).
- El parser ZIP/XML en `src/io_utils.py` (`_extraer_datos_xlsx_desde_zip`) es código delicado; modificar solo si hay un test que lo cubra.
- La detección de columna de grupo en WO busca columnas con patrón `select__<número>` (`_detectar_columna_select` en `transform.py`), generado dinámicamente por BMC.

## Convenciones
- Nombres de columnas de salida en mayúsculas con tildes normalizadas.
- Mensajes de estado (toast) con prefijo `✅` o `❌`.
- La versión se define en `src/constants.py` (`VERSION`).
- Usar `st_module` como parámetro opcional para funciones que emiten UI (toast, warning), permitiendo testing sin Streamlit.
- Los encabezados de BMC y Jira se normalizan de forma defensiva (tildes/caso/alias) via `normalizar_texto` (en `src/utils.py`) + `_mapear_alias` (en `src/transform.py`), con `ALIASES_BMC` y `ALIASES_JIRA` centralizados en `src/constants.py`. En `epics.py` la columna de estado se detecta por candidatos: `["Estado", "Status", "state", "estado"]`.

## Lectura de archivos
- `leer_archivo_robusto` intenta Excel → CSV (varios encodings) → HTML en cascada.
- Para `.xlsx` reales (magic bytes `PK`), se deshabilita el fallback CSV/HTML y se usa el parser ZIP/XML como último recurso.
- La carga de Jira en modo Conciliación usa `hoja_preferida="Your Jira Issues"` — no modificar ese valor sin verificar con el reporte real de Jira.
