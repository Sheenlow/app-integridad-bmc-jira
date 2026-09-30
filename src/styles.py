"""
Paleta de colores y categorias de acciones centralizadas.
Usada por la UI (pandas Styler) y por excel_export.py (openpyxl), de modo que
los colores se definen una sola vez.
"""
from .constants import (
    ACCION_OK, ACCION_FALTA_JIRA, ACCION_SOBRA_JIRA, ACCION_INCONGRUENCIA,
    ACCION_DEBERIA_EN_PROGRESO, ACCION_DEBERIA_BACKLOG,
    ACCION_DEBERIA_BACKLOG_STAND_BY,
)

# Los colores se guardan como hex RGB (6 digitos, sin '#'). Cada consumidor
# los formatea segun su contexto: CSS agrega '#', openpyxl agrega 'FF' (aRGB).
COLORES_ACCION = {
    "ok": ("ecfdf5", "065f46"),            # verde
    "falta": ("fef3c7", "92400e"),         # ambar (crear)
    "sobra": ("fee2e2", "991b1b"),         # rojo (borrar / desvio grave)
    "incongruencia": ("ffedd5", "c2410c"), # naranja (actualizar estado)
    "revisar": ("ffedd5", "c2410c"),       # naranja (revisar generico)
    "todas": ("eff6ff", "1e40af"),         # celeste (epicas)
    "sin_parent": ("fef3c7", "92400e"),    # ambar (epica/tarea sin par)
}


def clasificar_accion(valor) -> str | None:
    """
    Clasifica un valor de accion en una categoria de color, o None si no
    corresponde colorear. Orden de chequeo: prefijos mas especificos primero.
    """
    if valor is None:
        return None
    v = str(valor)
    if v.startswith(ACCION_OK):
        return "ok"
    if v.startswith(ACCION_FALTA_JIRA):
        return "falta"
    if v.startswith(ACCION_SOBRA_JIRA):
        return "sobra"
    if (
        v.startswith(ACCION_INCONGRUENCIA)
        or v.startswith(ACCION_DEBERIA_EN_PROGRESO)
        or v.startswith(ACCION_DEBERIA_BACKLOG)
        or v.startswith(ACCION_DEBERIA_BACKLOG_STAND_BY)
    ):
        return "incongruencia"
    if v.startswith("Revisar"):
        return "revisar"
    if v.startswith("Todas"):
        return "todas"
    if v.startswith("Epica sin") or v.startswith("Tarea sin"):
        return "sin_parent"
    return None


def obtener_estilo_accion(valor) -> str:
    """Devuelve el estilo CSS para pandas Styler, o cadena vacia si no aplica."""
    categoria = clasificar_accion(valor)
    if categoria is None:
        return ""
    bg, fg = COLORES_ACCION[categoria]
    return f"background-color: #{bg}; color: #{fg};"
