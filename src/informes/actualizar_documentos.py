"""Actualiza todos los documentos con secciones autogeneradas."""

from __future__ import annotations

import sys

from src.calidad import perfilar
from src.informes import (
    brechas,
    conciliacion,
    datos_origen,
    estrategia,
    mapeo,
    perfilado,
    pipeline,
    pruebas,
    trazabilidad,
)

GENERADORES = (
    ("Estrategia", estrategia),
    ("Perfilado", perfilado),
    ("Datos de origen", datos_origen),
    ("Mapeo", mapeo),
    ("Brechas", brechas),
    ("Pipeline", pipeline),
    ("Conciliacion", conciliacion),
    ("Pruebas", pruebas),
    ("Trazabilidad", trazabilidad),
)


def main() -> int:
    """Ejecuta el perfilado y todos los generadores de documentos."""
    perfilar.main()
    for nombre, modulo in GENERADORES:
        modulo.main()
        print(f"  [ok] {nombre}")
    print("Documentos actualizados con las cifras del pipeline.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
