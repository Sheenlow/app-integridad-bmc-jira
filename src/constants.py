# =============================================================================
# CONSTANTES: Nombres esperados de columnas (referencia por nombre, no por indice)
# Modificar aqui si los nombres de columna cambian en los reportes fuente.
# =============================================================================

# BMC - Work Orders
COL_WO_ID = "WorkOrderID"
COL_WO_SUMMARY = "Titulo de WO"
COL_WO_STATUS = "Status"
COL_WO_PRIORITY = "Priority"

# BMC - Problemas (PBI)
COL_PBI_ID = "ProblemID"
COL_PBI_SUMMARY = "Descripcion"
COL_PBI_STATUS = "Status"

# Jira
COL_JIRA_KEY = "Clave"
COL_JIRA_SUMMARY = "Summary"
COL_JIRA_STATUS = "Status"
COL_JIRA_ISSUE_TYPE = "IssueType"
COL_JIRA_ASSIGNEE = "Persona asignada"
COL_JIRA_INFORMADOR = "Informador"

# BMC - Usuario / Asignado (nombres segun reporte de origen)
COL_BMC_ASIG_WO = "Asignatario Experto"
COL_BMC_ASIG_PBI = "Usuario_Asignado"

# BMC - Grupo Asignado (nombres segun reporte de origen)
# El campo de grupo en WO usa un prefijo select__ seguido de un ID numerico variable.
# Se detecta dinamicamente en tiempo de ejecucion.
COL_BMC_GRUPO_PBI = "Grupo_Asignado"

# --- Filtrado por grupo de trabajo en la ingesta de BMC ---
# Solo se conservan registros cuyo grupo pertenezca a esta lista (tras strip).
GRUPOS_PERMITIDOS = ["GPA ADM - ADM", "GPA ADM - RRHH"]

# Columnas de grupo buscadas por alias/normalizacion (el encabezado puede variar):
# WO evalua "Grupo Experto"; PBI evalua "Grupo_Asignado".
ALIASES_GRUPO_WO = [
    "grupo experto", "grupo de expertos", "grupo asignado",
    "grupo", "support group", "assignee group",
]
ALIASES_GRUPO_PBI = [
    "grupo asignado", "grupo asignado a", "grupo",
    "support group", "assignee group",
]

# --- Fase 2: Transformacion y cruce ---

# Mapeo de IDs originales al campo unificado BMC_ID
COL_WO_SOURCE_ID = "ID Propuesta"
COL_PBI_SOURCE_ID = "Problema"
COL_BMC_ID = "BMC_ID"

# Columna de estado (presente en los 3 reportes)
COL_ESTADO = "Estado"
COL_ESTADO_BMC = "Estado_BMC"
COL_ESTADO_JIRA = "Estado_JIRA"

# Nombres alternativos que puede tener la columna de estado en los reportes
COL_ESTADO_CANDIDATOS = ["Estado", "Status", "state", "estado"]

# Columnas de prioridad (ingesta defensiva con alias; renombradas internamente)
COL_PRIORIDAD_BMC = "Prioridad_BMC"
COL_PRIORIDAD_JIRA = "Prioridad_JIRA"

# Nombres alternativos que puede tener la columna de prioridad en los reportes
COL_PRIORIDAD_CANDIDATOS = ["prioridad", "priority"]

# Trazabilidad de origen BMC
COL_ORIGEN = "Origen_BMC"

# --- Fase 3: Reglas de negocio y exportacion ---

COL_ACCION_SUGERIDA = "ACCION SUGERIDA"
COL_MERGE = "_merge"
COL_CELULA = "CELULA"

# --- Columnas de salida del reporte (todas en mayusculas) ---
COL_TITULO_BMC = "TITULO DE BMC"
COL_TECNICO_ASIGNADO = "TECNICO ASIGNADO"
COL_GRUPO_ASIGNADO = "GRUPO ASIGNADO"
COL_OUT_CLAVE = "CLAVE"
COL_RESUMEN = "RESUMEN"
COL_CATEGORIA_ESTADO = "CATEGORIA DE ESTADO"
COL_PERSONA_ASIGNADA = "PERSONA ASIGNADA"
COL_PROCESO = "PROCESO"
COL_ESTADO_PROPUESTA = "ESTADO PROPUESTA"
COL_OUT_PRIORIDAD_BMC = "Prioridad BMC"
COL_OUT_PRIORIDAD_JIRA = "Prioridad JIRA"

# Nombres de columnas fuente para campos adicionales
COL_SRC_ESTADO_PROPUESTA = "Estado propuesta"
COL_SRC_PROCESO = "Proceso"
COL_SRC_CATEGORIA_ESTADO = "Categoria de estado"
COL_SRC_CELULA = "Celula"

# Orden de columnas del reporte final Resultado_Conciliacion
COLUMNAS_OUTPUT = [
    COL_BMC_ID,
    COL_TITULO_BMC,
    COL_ESTADO_BMC,
    COL_OUT_PRIORIDAD_BMC,
    COL_ESTADO_PROPUESTA,
    COL_TECNICO_ASIGNADO,
    COL_PROCESO,
    COL_GRUPO_ASIGNADO,
    COL_OUT_CLAVE,
    COL_RESUMEN,
    COL_CATEGORIA_ESTADO,
    COL_ESTADO_JIRA,
    COL_OUT_PRIORIDAD_JIRA,
    COL_PERSONA_ASIGNADA,
    COL_CELULA,
    COL_ACCION_SUGERIDA,
]

# Columnas practicas para el preview de Acciones Sugeridas
COLUMNAS_PREVIEW_ACCIONES = [
    COL_BMC_ID,
    COL_OUT_CLAVE,
    COL_ESTADO_BMC,
    COL_OUT_PRIORIDAD_BMC,
    COL_ESTADO_JIRA,
    COL_OUT_PRIORIDAD_JIRA,
    COL_TECNICO_ASIGNADO,
    COL_PERSONA_ASIGNADA,
    COL_GRUPO_ASIGNADO,
    COL_CELULA,
    COL_ACCION_SUGERIDA,
]

# --- Alias flexibles para normalizar encabezados de Jira ---
# Mapea nombres de columna frecuentes (con/sin tilde, otro idioma, o prefijo
# "Custom field") al esquema interno fijo. Las claves son los nombres canonicos
# de salida; los valores se comparan normalizados (sin tilde, minusculas, strip)
# via normalizar_texto() en transform.py.
ALIASES_JIRA = {
    COL_OUT_CLAVE: [
        "clave", "key", "issue key", "clave de la incidencia",
    ],
    COL_RESUMEN: [
        "resumen", "summary", "resumen de la incidencia", "titulo", "title",
    ],
    COL_CATEGORIA_ESTADO: [
        "categoria de estado", "categoria estado", "status category",
        "categoria de estado del flujo de trabajo",
    ],
    COL_ESTADO_JIRA: [
        "estado", "status", "estado de la incidencia",
    ],
    COL_PRIORIDAD_JIRA: [
        "prioridad", "priority",
    ],
    COL_PERSONA_ASIGNADA: [
        "persona asignada", "assignee", "responsable", "asignado",
    ],
    COL_CELULA: [
        "celula", "custom field (celula)", "campo personalizado (celula)",
        "componente/s", "componentes", "components",
    ],
    COL_ESTADO_PROPUESTA: [
        "estado propuesta", "estado de la propuesta",
    ],
    COL_PROCESO: [
        "proceso",
    ],
}

# Columnas criticas de Jira: si no se detectan tras la normalizacion, se emite
# un warning en la UI ("Columna [X] no detectada en el archivo de Jira subido").
COLUMNAS_CRITICAS_JIRA = {
    COL_OUT_CLAVE: "Clave",
    COL_ESTADO_JIRA: "Estado",
    COL_CELULA: "Celula",
}

# --- Alias flexibles para normalizar encabezados de BMC (simetria con Jira) ---
# Se comparan normalizados (sin tilde, minusculas, strip) via normalizar_texto().
# La clave es el nombre canonico interno; los valores son los alias frecuentes.
# El ID (BMC_ID) combina los alias de WO ("ID Propuesta") y PBI ("Problema"):
# cada reporte trae uno solo, asi que la busqueda resuelve el correcto.
ALIASES_BMC = {
    COL_BMC_ID: [
        "id propuesta", "id de la propuesta", "id de propuesta",
        "problema", "problem id", "id problema", "problemid", "problema id",
    ],
    COL_ESTADO_BMC: [
        "estado", "status", "state", "estado de la incidencia", "estado de la wo",
    ],
    COL_PRIORIDAD_BMC: [
        "prioridad", "priority",
    ],
    COL_PROCESO: [
        "proceso", "process",
    ],
}

# --- Reglas de negocio Arcor (estados normalizados: minusculas, sin tildes) ---
# Estos valores se comparan contra cadenas normalizadas via normalizar_texto()
# (src/utils.py): strip + lower + sin tildes.

# Estados BMC de un PBI que indican trabajo "en curso"
PBI_ESTADOS_EN_CURSO = [
    "asignado", "assigned", "bajo investigacion", "under investigation",
]

# Estados BMC de un PBI que indican que ya finalizo
PBI_ESTADOS_FINALES = [
    "terminado", "cerrado", "finalizado", "cancelado",
    "closed", "resolved", "cancelled",
]

# Estados BMC de una WO que indican trabajo "en curso"
WO_ESTADOS_EN_CURSO = [
    "asignado", "assigned", "en curso", "in progress",
    "planificacion", "planning",
]

# Estados BMC de una WO que indican que ya finalizo
WO_ESTADOS_FINALES = [
    "finalizada", "finalizado", "cerrado", "abandonado",
    "cancelado", "closed", "resolved", "cancelled",
]

# Estados finales de BMC (WO y PBI) usados para filtrar historial cerrado.
# Normalizados (minusculas, sin tildes). Fuente unica para el filtrado
# historico (transform.py) y la regla de inconsistencia (rules.py).
ESTADOS_FINALES_BMC = {
    "cerrado", "closed", "cancelado", "cancelled",
    "rechazado", "rejected", "finalizado", "finalizada",
    "resolved", "completado", "completed",
    "terminado", "abandonado",
}

# Estados de ESTADO PROPUESTA que indican que una WO de
# "Gestion de la Demanda" esta "en curso"
GESTION_DEMANDA_ESTADOS_EN_CURSO = [
    "en ejecucion", "analisis tecnico", "proyecto creado", "cambio creado",
]

# Estados de Jira considerados equivalentes a cada objetivo
JIRA_EN_PROGRESO = ["en progreso", "in progress"]
JIRA_BACKLOG = ["backlog", "por hacer", "to do"]
JIRA_STAND_BY = ["stand by"]

# Estados de Jira considerados "activos/abiertos" para el filtrado historico
# y la deteccion de inconsistencias (cerrado en BMC pero activo en Jira).
JIRA_ESTADOS_ACTIVOS = [
    "en progreso", "in progress", "en curso",
    "backlog", "tareas por hacer", "to do", "stand by",
]

# Equivalencias de prioridad (ingles <-> espanol) para comparar BMC vs Jira.
# La clave es la categoria canonica; los valores son las variantes que pueden
# llegar de los reportes (se comparan normalizadas: minusculas, sin tildes).
EQUIVALENCIAS_PRIORIDAD = {
    "highest": ["highest", "critico", "critica", "1 - critico", "1 - critica"],
    "high": ["high", "alto", "alta", "2 - alto", "2 - alta"],
    "medium": ["medium", "medio", "media", "3 - medio", "3 - media"],
    "low": ["low", "bajo", "baja", "4 - bajo", "4 - baja"],
}

# Valores normalizados de la columna PROCESO
PROCESO_PEDIDOS_INTERNOS = "pedidos internos"
PROCESO_GESTION_DEMANDA = "gestion de la demanda"

# --- Mensajes de ACCION SUGERIDA (centralizados) ---
# Fuente unica para rules.py, la UI (popover de ayuda), el dashboard y la paleta
# de colores (styles.py), de modo que no se desincronicen.
ACCION_OK = "OK - Sincronizado"
ACCION_FALTA_JIRA = "Revisar: Falta en Jira"
ACCION_SOBRA_JIRA = "Revisar: Sobra en Jira"
ACCION_INCONGRUENCIA = "Revisar: Estado en incongruencia con Jira"
ACCION_DEBERIA_EN_PROGRESO = "Revisar: Deberia estar En progreso en Jira"
ACCION_DEBERIA_BACKLOG = "Revisar: Deberia estar en Backlog en Jira"
ACCION_DEBERIA_BACKLOG_STAND_BY = "Revisar: Deberia estar en Backlog o Stand By en Jira"
ACCION_MODIFICAR_PRIORIDAD_JIRA = "Modificar en Jira prioridad"
ACCION_PRIORIDAD_DESACOPLADA = "Prioridad desincronizada con Jira"
ACCION_INCONSISTENCIA_FINAL_ACTIVO = "Revisar: Inconsistencia - CERRADO/CANCELADO en BMC pero activo en Jira"

# --- Validacion Epicas vs Tareas ---

COL_TIPO_INCIDENCIA = "Tipo de Incidencia"
COL_CLAVE_JIRA = "Clave"
COL_PARENT = "parent"
COL_TAREAS_TOTAL = "Tareas Totales"
COL_TAREAS_ABIERTAS = "Tareas Abiertas"
COL_TAREAS_CERRADAS = "Tareas Cerradas"
COL_ESTADOS_TAREAS = "Estados Tareas"
COL_VALIDACION_EPICAS = "Validacion Epica"
COL_CANT_SPRINTS = "Cantidad de Sprints"
COL_ASIGNADO_TAREAS = "Asignado tareas"

COL_SPRINT_CANDIDATOS = ["Sprint", "Sprints", "Sprint ID", "Iteracion"]

ESTADOS_FINALES_EPICA = [
    "Done", "Closed", "Finalizada", "Finalizado",
    "Cancelado", "Cancelada", "Cancelled", "Listo",
]

# --- Alias flexibles para normalizar encabezados de los reportes Epicas/Tareas ---
# Los reportes de Jira exportan encabezados en ingles o con distinto caso/tilde.
# Mapea a los nombres canonicos usados por epics.py (Tipo de Incidencia, Clave,
# Estado, parent, ...). Simetrico a ALIASES_JIRA para el pipeline de conciliacion.
ALIASES_EPICAS = {
    COL_TIPO_INCIDENCIA: [
        "tipo de incidencia", "tipo de incidente", "tipo de issue",
        "issue type", "issuetype", "tipo",
    ],
    COL_CLAVE_JIRA: [
        "clave", "key", "issue key", "clave de la incidencia",
        "clave de incidencia",
    ],
    COL_ESTADO: [
        "estado", "status", "state", "estado de la incidencia",
    ],
    "Resumen": [
        "resumen", "summary", "titulo", "title", "descripcion",
    ],
    "Prioridad": [
        "prioridad", "priority",
    ],
    "Componentes": [
        "componente/s", "componentes", "components", "componente",
    ],
    "Creada": [
        "creada", "created", "fecha de creacion", "fecha creacion",
    ],
    "Resuelta": [
        "resuelta", "resolved", "fecha de resolucion", "resolution date",
    ],
    "Celula": [
        "celula", "custom field (celula)", "campo personalizado (celula)",
        "celulas",
    ],
    COL_BMC_ID: [
        "bmc id", "bmc_id", "bmcid", "id bmc", "bmc",
    ],
    COL_JIRA_ASSIGNEE: [
        "persona asignada", "assignee", "responsable", "asignado",
        "asignado a",
    ],
    COL_PARENT: [
        "parent", "parent link", "epic link", "epic", "padre", "epica",
    ],
}

# Orden de columnas del reporte final validacion_epicas
COLUMNAS_OUTPUT_EPICAS = [
    COL_TIPO_INCIDENCIA,
    COL_CLAVE_JIRA,
    "Resumen",
    "Prioridad",
    "Componentes",
    COL_ESTADO,
    "Creada",
    "Resuelta",
    "Celula",
    COL_BMC_ID,
    COL_JIRA_ASSIGNEE,
    COL_ASIGNADO_TAREAS,
    COL_TAREAS_TOTAL,
    COL_TAREAS_ABIERTAS,
    COL_TAREAS_CERRADAS,
    COL_ESTADOS_TAREAS,
    COL_CANT_SPRINTS,
    COL_VALIDACION_EPICAS,
]

# --- URLs de descarga de reportes ---
URL_WO_BMC = "https://portaltiarcor-or1.onbmc.com/dashboards/d/Q0z63zu7z/wo-panel-general?orgId=622379620&from=now-6h&to=now&timezone=browser"
URL_PBI_BMC = "https://portaltiarcor-or1.onbmc.com/dashboards/d/uEZ87-z4z/pbi-panel-general?orgId=622379620&from=2022-01-01T04:14:39.000Z&to=2026-12-31T10:02:23.000Z&timezone=browser&var-ID=$__all"
URL_JIRA_FILTER = "https://arcor-saic.atlassian.net/issues/?filter=23700&atlOrigin=eyJpIjoiYmQwZWY0MDUzMzQ4NDFhMWFkMzc5ZDE4ZjVkOTYzYmEiLCJwIjoiaiJ9"
URL_EPICAS_JIRA = "https://arcor-saic.atlassian.net/issues/?filter=23612&atlOrigin=eyJpIjoiYTE5YjA4ZTFjMWViNDA4MjlhNTQxZTdjMjZlZDBiMWUiLCJwIjoiaiJ9"
URL_TAREAS_JIRA = "https://arcor-saic.atlassian.net/issues/?filter=14116"

# --- Version ---
VERSION = "v1.3"
