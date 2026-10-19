"""Rutas de trabajo del proyecto, centralizadas para todas las etapas."""

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
CONFIG = RAIZ / "config"
DOCS = RAIZ / "docs"
MUESTRAS = RAIZ / "muestras"
DATOS = RAIZ / "datos"
LEGADO = DATOS / "legado"
LEGADO_DELTA = DATOS / "legado_delta"
ATERRIZAJE = DATOS / "aterrizaje"
TRANSFORMADO = DATOS / "transformado"
DESTINO = DATOS / "destino"
RESULTADOS = DATOS / "resultados"
CONCILIACION = RESULTADOS / "conciliacion"
BITACORA = DATOS / "bitacora"
VERDAD = DATOS / "verdad"
PERFILADO = DATOS / "perfilado"


def asegurar_directorios() -> None:
    """Crea los directorios de trabajo si no existen."""
    for directorio in (
        DATOS,
        LEGADO,
        LEGADO_DELTA,
        ATERRIZAJE,
        TRANSFORMADO,
        DESTINO,
        RESULTADOS,
        CONCILIACION,
        BITACORA,
        VERDAD,
        PERFILADO,
        MUESTRAS,
    ):
        directorio.mkdir(parents=True, exist_ok=True)
