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
    COL_ESTADO_PROPUESTA,
    COL_TECNICO_ASIGNADO,
    COL_PROCESO,
    COL_GRUPO_ASIGNADO,
    COL_OUT_CLAVE,
    COL_RESUMEN,
    COL_CATEGORIA_ESTADO,
    COL_ESTADO_JIRA,
    COL_PERSONA_ASIGNADA,
    COL_CELULA,
    COL_ACCION_SUGERIDA,
]

# Columnas practicas para el preview de Acciones Sugeridas
COLUMNAS_PREVIEW_ACCIONES = [
    COL_BMC_ID,
    COL_OUT_CLAVE,
    COL_ESTADO_BMC,
    COL_ESTADO_JIRA,
    COL_TECNICO_ASIGNADO,
    COL_PERSONA_ASIGNADA,
    COL_GRUPO_ASIGNADO,
    COL_CELULA,
    COL_ACCION_SUGERIDA,
]

EQUIVALENCIAS = {
    # PBI
    "Assigned": ["Backlog", "Por hacer", "Tareas por hacer", "En progreso"],
    "Cancelled": ["Cancelado"],
    "Closed": ["Finalizada", "Listo", "Cancelado"],
    "Completed": ["Finalizada", "Listo"],
    "Draft": ["Backlog", "Listo", "Por hacer", "Tareas por hacer"],
    "Pending": ["Stand By"],
    "Under Investigation": ["En progreso", "Dev Doing", "Tareas por hacer"],
    # WO
    "Abandonado": ["Cancelado"],
    "Analisis Tecnico": ["Backlog", "Por hacer", "Tareas por hacer", "En progreso", "Stand By"],
    "Cambio Creado": ["En progreso", "Stand By", "Tareas por hacer"],
    "En ejecucion": ["En progreso", "Stand By", "Tareas por hacer"],
    "En curso": ["En progreso", "Stand By", "Tareas por hacer"],
    "Finalizada": ["Finalizada", "Listo", "Cancelado"],
    "Pendiente Aprobacion del negocio": ["Stand By", "Tareas por hacer", "En progreso"],
    "registrado": ["Backlog"],
    "Asignado": ["Backlog"],
}

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
URL_WO_BMC = "https://portaltiarcor-or1.onbmc.com/dashboards/d/aecvnwwjfjfggd/wo-panel-general-x-estados?orgId=622379620"
URL_PBI_BMC = "https://portaltiarcor-or1.onbmc.com/dashboards/d/decuhbh2tnri8c/pbi-panel-general-backlog?orgId=622379620"
URL_JIRA_FILTER = "https://arcor-saic.atlassian.net/issues/?filter=11150"
URL_EPICAS_JIRA = "https://arcor-saic.atlassian.net/issues/?filter=23612&atlOrigin=eyJpIjoiYTE5YjA4ZTFjMWViNDA4MjlhNTQxZTdjMjZlZDBiMWUiLCJwIjoiaiJ9"
URL_TAREAS_JIRA = "https://arcor-saic.atlassian.net/issues/?filter=14116"

# --- Version ---
VERSION = "v1.1"
