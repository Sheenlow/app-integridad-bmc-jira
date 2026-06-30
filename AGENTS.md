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

## Qué no modificar
- No cambiar nombres de columnas en `src/constants.py` sin revisar el impacto en las funciones de normalización y merge.
- Las reglas de negocio en `src/rules.py` dependen del diccionario `EQUIVALENCIAS`.
- El parser ZIP/XML en `src/io_utils.py` (`_extraer_datos_xlsx_desde_zip`) es código delicado; modificar solo si hay un test que lo cubra.

## Convenciones
- Nombres de columnas de salida en mayúsculas con tildes normalizadas.
- Mensajes de estado (toast) con prefijo `✅` o `❌`.
- La versión se define en `src/constants.py` (`VERSION`).
- Usar `st_module` como parámetro opcional para funciones que emiten UI (toast, warning), permitiendo testing sin Streamlit.
