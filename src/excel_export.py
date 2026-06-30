"""
Formateo de archivos Excel para exportaciones.
"""
import pandas as pd


def formatear_excel(writer, df: pd.DataFrame, sheet_name: str, columna_color: str | None = None):
    """
    Aplica formato al Excel exportado:
    - Auto-ajuste de columnas
    - Header con fondo oscuro y texto blanco
    - Freeze en primera fila
    - Bordes finos
    - Color condicional en la columna especificada
    """
    from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
    from openpyxl.utils import get_column_letter

    ws = writer.sheets[sheet_name]

    # Auto-ajuste de columnas
    for i, col in enumerate(df.columns, 1):
        max_len = max(
            df[col].astype(str).str.len().max(),
            len(str(col)),
        )
        ws.column_dimensions[get_column_letter(i)].width = min(max_len + 3, 50)

    # Header
    header_fill = PatternFill("solid", fgColor="1e293b")
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_align = Alignment(horizontal="center", vertical="center")
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_align

    # Freeze
    ws.freeze_panes = "A2"

    # Bordes finos
    thin = Side(style="thin", color="cbd5e1")
    border = Border(top=thin, bottom=thin, left=thin, right=thin)
    for row in ws.iter_rows(min_row=1, max_row=ws.max_row, max_col=ws.max_column):
        for cell in row:
            cell.border = border
            if cell.alignment and not cell.alignment.horizontal:
                cell.alignment = Alignment(vertical="center")

    # Color condicional en columna de estado
    if columna_color and columna_color in df.columns:
        col_idx = list(df.columns).index(columna_color) + 1
        colores = {
            "OK": PatternFill("solid", fgColor="ecfdf5"),
            "Revisar": PatternFill("solid", fgColor="eff6ff"),
            "Falta": PatternFill("solid", fgColor="fef3c7"),
            "Sobra": PatternFill("solid", fgColor="fee2e2"),
            "Actualizar": PatternFill("solid", fgColor="fef2f2"),
            "Epica sin": PatternFill("solid", fgColor="fef3c7"),
            "Tarea sin": PatternFill("solid", fgColor="fef3c7"),
            "Todas": PatternFill("solid", fgColor="eff6ff"),
        }
        for row in range(2, ws.max_row + 1):
            cell = ws.cell(row=row, column=col_idx)
            val = str(cell.value or "")
            for prefix, fill in colores.items():
                if val.startswith(prefix):
                    cell.fill = fill
                    break
