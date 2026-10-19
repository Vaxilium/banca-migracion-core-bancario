"""Lectura y escritura de archivos YAML del proyecto."""

from pathlib import Path
from typing import Any

import yaml


def cargar_yaml(ruta: str | Path) -> Any:
    """Carga un YAML en UTF-8 y devuelve su contenido."""
    with open(ruta, encoding="utf-8") as archivo:
        return yaml.safe_load(archivo)


def guardar_yaml(ruta: str | Path, contenido: Any) -> None:
    """Guarda contenido en un YAML UTF-8 con orden estable de claves."""
    with open(ruta, "w", encoding="utf-8") as archivo:
        yaml.safe_dump(contenido, archivo, allow_unicode=True, sort_keys=False)
