"""Normalizacion de textos para comparaciones, deduplicacion y enmascaramiento."""

import hashlib
import re
import unicodedata

import pandas as pd

SAL_ENMASCARAMIENTO = "banco-meridiano-austral-control-2026"


def normalizar_texto(valor: str) -> str:
    """Pasa a mayusculas sin tildes ni enie y colapsa espacios internos."""
    if valor is None:
        return ""
    sin_tildes = unicodedata.normalize("NFKD", str(valor))
    sin_tildes = "".join(c for c in sin_tildes if not unicodedata.combining(c))
    sin_tildes = sin_tildes.replace("ñ", "n").replace("Ñ", "N")
    return re.sub(r"\s+", " ", sin_tildes).strip().upper()


def normalizar_serie(serie: pd.Series) -> pd.Series:
    """Aplica normalizar_texto a una columna de pandas."""
    return serie.fillna("").astype(str).map(normalizar_texto)


def huella_determinista(valor: str) -> str:
    """Devuelve una huella hexadecimal estable para enmascaramiento controlado."""
    datos = f"{SAL_ENMASCARAMIENTO}:{valor}".encode()
    return hashlib.sha256(datos).hexdigest()


def ordenar_tokens(nombre: str) -> str:
    """Reordena las palabras de un nombre para detectar duplicados por variacion."""
    return " ".join(sorted(normalizar_texto(nombre).split()))
