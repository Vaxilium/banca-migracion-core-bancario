"""Genera la evidencia de perfilado del documento de puntos de dolor."""

from __future__ import annotations

import json
import sys

from src.comun.rutas import DOCS, PERFILADO
from src.informes.marcadores import reemplazar_seccion

RUTA_DOC = DOCS / "02-analisis-as-is" / "puntos-de-dolor.md"
RUTA_PERFIL = PERFILADO / "perfil_origen.json"
NOMBRES = {
    "movimientos": "Movimientos",
    "documentos": "Documentos",
    "direcciones": "Direcciones",
    "clientes": "Clientes",
    "cuentas": "Cuentas",
    "prestamos": "Préstamos",
    "cuotas": "Cuotas",
    "plazos_fijos": "Plazos fijos",
    "mandatos": "Mandatos",
    "saldos": "Saldos",
    "plan_cuentas": "Plan de cuentas",
    "saldos_contables": "Saldos contables",
}


def numero(valor: float, decimales: int = 0) -> str:
    """Formatea un numero al estilo es-AR."""
    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def _perfil() -> dict:
    if not RUTA_PERFIL.exists():
        raise FileNotFoundError(
            f"no existe {RUTA_PERFIL}; ejecutar make perfilado antes de regenerar el informe"
        )
    return json.loads(RUTA_PERFIL.read_text(encoding="utf-8"))


def tabla_entidades(perfil: dict) -> str:
    """Resume registros y duplicados de clave por entidad."""
    filas = [
        "| Entidad | Registros | Clave de control | Filas con clave duplicada |",
        "|---|---:|---|---:|",
    ]
    for entidad, datos in perfil["entidades"].items():
        clave = ", ".join(f"`{campo}`" for campo in datos["clave"])
        filas.append(
            f"| {NOMBRES.get(entidad, entidad)} | {numero(datos['registros'])} | {clave} | "
            f"{numero(datos['duplicados'])} |"
        )
    return "\n".join(filas)


def tabla_campos(perfil: dict) -> str:
    """Lista los campos criticos con valores vacios."""
    filas = [
        "| Entidad | Campo | Vacios | Porcentaje |",
        "|---|---|---:|---:|",
    ]
    for entidad, datos in perfil["entidades"].items():
        for campo, vacios in datos["campos"].items():
            if not vacios:
                continue
            porcentaje = f"{vacios / datos['registros'] * 100:.2f}".replace(".", ",")
            filas.append(
                f"| {NOMBRES.get(entidad, entidad)} | `{campo}` | {numero(vacios)} | "
                f"{porcentaje} % |"
            )
    return "\n".join(filas)


def tabla_defectos(perfil: dict) -> str:
    """Resume los defectos inyectados usados como verdad de terreno."""
    filas = [
        "| Entidad | Defecto | Casos |",
        "|---|---|---:|",
    ]
    for registro in perfil["verdad"]:
        filas.append(
            f"| {NOMBRES.get(registro['entidad'], registro['entidad'])} | "
            f"`{registro['tipo_defecto']}` | {numero(registro['casos'])} |"
        )
    return "\n".join(filas)


def main() -> int:
    """Actualiza la seccion autogenerada de evidencia del perfilado."""
    perfil = _perfil()
    contenido = "\n\n".join(
        [
            tabla_entidades(perfil),
            tabla_campos(perfil),
            tabla_defectos(perfil),
        ]
    )
    reemplazar_seccion(RUTA_DOC, "dolores-perfilado", contenido)
    print(f"Evidencia de perfilado actualizada: {RUTA_DOC}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
