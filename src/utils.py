"""
Utilidades compartidas: normalizacion de cadenas.
"""
import unicodedata


def normalizar_texto(cadena: str) -> str:
    """
    Normaliza una cadena para comparacion: quita acentos (NFKD), pasa a
    minusculas y hace strip. Util para comparar estados y encabezados sin
    importar tildes ni mayusculas/minusculas.
    """
    if cadena is None:
        return ""
    s = unicodedata.normalize("NFKD", str(cadena))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower().strip()
