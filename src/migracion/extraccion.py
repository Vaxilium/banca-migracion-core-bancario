"""Lectura de los archivos de ancho fijo del legado guiada por los disenos YAML.

Cada linea se convierte en una fila de texto crudo (sin interpretar tipos): la
interpretacion y las reglas viven en src/migracion/transformacion.py. Las lineas
con longitud distinta al diseno se rechazan con motivo registro_corrupto.
"""

from pathlib import Path

import pandas as pd

from src.comun.rutas import CONFIG
from src.comun.yaml_util import cargar_yaml

DISENOS = CONFIG / "disenos_legado"

ARCHIVOS_DELTA = {
    "cuentas": "cuentas_delta.dat",
    "movimientos": "movimientos_delta.dat",
    "saldos": "saldos_delta.dat",
}


def cargar_disenos() -> dict[str, dict]:
    """Carga todos los disenos de registro del legado, indexados por entidad."""
    disenos: dict[str, dict] = {}
    for ruta in sorted(DISENOS.glob("*.yaml")):
        datos = cargar_yaml(ruta)
        disenos[datos["entidad"]] = datos
    return disenos


def leer_entidad(
    entidad: str, carpeta: Path, archivo: str | None = None
) -> tuple[pd.DataFrame, list[dict]]:
    """Lee una entidad y devuelve (texto crudo por campo, rechazos por longitud)."""
    diseno = cargar_disenos()[entidad]
    nombre_archivo = archivo or diseno["archivo"]
    contenido = (carpeta / nombre_archivo).read_bytes().decode(
        diseno.get("codificacion", "latin-1"), errors="replace"
    )
    registros = pd.Series(contenido.splitlines(), dtype="string")
    correctos = registros.str.len() == diseno["longitud_registro"]
    rechazos = [
        {
            "entidad": entidad,
            "motivo": "registro_corrupto",
            "destino": "rechazo",
            "clave": str(posicion),
            "detalle": f"linea {posicion + 1}: longitud {len(registro)}",
        }
        for posicion, registro in registros[~correctos].items()
    ]
    crudo = {}
    for campo in diseno["campos"]:
        if campo["tipo"] == "relleno":
            continue
        inicio = campo["inicio"] - 1
        crudo[campo["nombre"]] = registros.str.slice(inicio, inicio + campo["longitud"])
    tabla = pd.DataFrame(crudo)
    tabla = tabla[correctos.to_numpy()].copy()
    for columna in tabla.columns:
        tabla[columna] = tabla[columna].str.strip()
    return tabla.reset_index(drop=True), rechazos
