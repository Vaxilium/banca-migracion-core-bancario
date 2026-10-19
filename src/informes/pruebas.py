"""Generador de las secciones autogeneradas del informe de pruebas."""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from xml.etree import ElementTree

from src.comun.rutas import DOCS, RAIZ, RESULTADOS
from src.informes.marcadores import reemplazar_seccion

RUTA_DOC = DOCS / "08-pruebas" / "estrategia-de-pruebas.md"
JUNIT = RESULTADOS / "junit.xml"
CARACTERISTICAS = RAIZ / "pruebas" / "caracteristicas"
PATRON_ESCENARIO = re.compile(r"Escenario:\s*(PR-\d{3})")
PATRON_CARACTERISTICA = re.compile(r"Caracteristica:\s*(.+)")
MODULOS = {
    "test_conciliacion": "Conciliacion",
    "test_especificaciones": "Especificaciones Gherkin",
    "test_generacion": "Generacion determinista",
    "test_migracion": "Migracion y carga",
    "test_reglas": "Reglas de transformacion",
}


def _casos() -> list[ElementTree.Element]:
    if not JUNIT.exists():
        raise FileNotFoundError(
            f"no existe {JUNIT}; ejecutar make pruebas antes de regenerar el informe"
        )
    arbol = ElementTree.parse(JUNIT)
    return list(arbol.getroot().iter("testcase"))


def _estado(caso: ElementTree.Element) -> str:
    if caso.find("failure") is not None:
        return "fallida"
    if caso.find("error") is not None:
        return "error"
    if caso.find("skipped") is not None:
        return "omitida"
    return "pasada"


def tabla_resumen() -> str:
    """Resume la ultima corrida de pytest por modulo."""
    por_modulo: dict[str, dict[str, float]] = defaultdict(
        lambda: {"total": 0, "pasadas": 0, "fallidas": 0, "omitidas": 0, "tiempo": 0.0}
    )
    totales = {"total": 0, "pasadas": 0, "fallidas": 0, "omitidas": 0, "tiempo": 0.0}
    for caso in _casos():
        modulo = caso.get("classname", "").split(".")[-1] or "general"
        estado = _estado(caso)
        for acumulado in (por_modulo[modulo], totales):
            acumulado["total"] += 1
            acumulado["tiempo"] += float(caso.get("time", 0.0))
            if estado == "pasada":
                acumulado["pasadas"] += 1
            elif estado == "omitida":
                acumulado["omitidas"] += 1
            else:
                acumulado["fallidas"] += 1
    filas = [
        "| Modulo | Pruebas | Pasadas | Fallidas | Omitidas | Duracion (s) |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for modulo in sorted(por_modulo):
        datos = por_modulo[modulo]
        filas.append(
            f"| {MODULOS.get(modulo, modulo)} | {datos['total']:.0f} | "
            f"{datos['pasadas']:.0f} | {datos['fallidas']:.0f} | "
            f"{datos['omitidas']:.0f} | {datos['tiempo']:.2f} |"
        )
    filas.append(
        f"| **Total** | **{totales['total']:.0f}** | **{totales['pasadas']:.0f}** | "
        f"**{totales['fallidas']:.0f}** | **{totales['omitidas']:.0f}** | "
        f"**{totales['tiempo']:.2f}** |"
    )
    return "\n".join(filas)


def tabla_caracteristicas() -> str:
    """Lista las especificaciones Gherkin y sus escenarios."""
    filas = [
        "| Caracteristica | Escenarios | Identificadores |",
        "|---|---:|---|",
    ]
    for ruta in sorted(CARACTERISTICAS.glob("*.feature")):
        texto = ruta.read_text(encoding="utf-8")
        nombre = PATRON_CARACTERISTICA.search(texto)
        identificadores = PATRON_ESCENARIO.findall(texto)
        titulo = nombre.group(1).strip() if nombre else ruta.stem
        filas.append(f"| {titulo} | {len(identificadores)} | {', '.join(identificadores)} |")
    return "\n".join(filas)


def main() -> int:
    """Actualiza las secciones autogeneradas del informe de pruebas."""
    reemplazar_seccion(RUTA_DOC, "pruebas-resumen", tabla_resumen())
    reemplazar_seccion(RUTA_DOC, "pruebas-caracteristicas", tabla_caracteristicas())
    print(f"Informe de pruebas actualizado: {RUTA_DOC}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
