"""Contratos de validacion JSON Schema generados desde el modelo destino.

Los contratos son la contraparte ejecutable del modelo documentado en la fase 5:
la carga valida una muestra de cada tabla contra su schema antes de publicarla.
"""

import json

import pandas as pd
from jsonschema import ValidationError, validate

from src.comun.rutas import CONFIG
from src.comun.yaml_util import cargar_yaml

CONTRATOS = CONFIG / "contratos"

TIPOS = {
    "entero": {"type": "integer"},
    "texto": {"type": "string"},
    "fecha": {"type": "string", "format": "date"},
    "hora": {"type": "string", "pattern": r"^\d{2}:\d{2}$"},
    "importe": {"type": "number"},
    "porcentaje": {"type": "number"},
    "booleano": {"type": "boolean"},
}


def generar_contratos() -> dict[str, dict]:
    """Escribe un contrato JSON Schema por tabla del modelo destino."""
    modelo = cargar_yaml(CONFIG / "mapeos" / "modelo_destino.yaml")
    CONTRATOS.mkdir(parents=True, exist_ok=True)
    contratos: dict[str, dict] = {}
    for tabla in modelo["tablas"]:
        propiedades = {}
        obligatorias = []
        for columna in tabla["columnas"]:
            esquema = dict(TIPOS[columna["tipo"]])
            if columna.get("nulo", False):
                esquema["type"] = [esquema["type"], "null"]
            if columna.get("dominio"):
                esquema["enum"] = columna["dominio"]
            propiedades[columna["nombre"]] = esquema
            if not columna.get("nulo", False):
                obligatorias.append(columna["nombre"])
        contrato = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": tabla["nombre"],
            "type": "object",
            "required": obligatorias,
            "properties": propiedades,
        }
        ruta = CONTRATOS / f"{tabla['nombre']}.json"
        ruta.write_text(
            json.dumps(contrato, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        contratos[tabla["nombre"]] = contrato
    return contratos


def validar_muestra(tabla: str, df: pd.DataFrame, contrato: dict, cantidad: int = 200) -> list[str]:
    """Valida una muestra de filas contra el contrato y devuelve los errores."""
    errores = []
    muestra = json.loads(df.head(cantidad).to_json(orient="records", date_format="iso"))
    for fila in muestra:
        try:
            validate(instance=fila, schema=contrato)
        except ValidationError as error:
            errores.append(f"{tabla}: {error.message} en {fila}")
    return errores
