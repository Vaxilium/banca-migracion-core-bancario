"""Generador del resumen de la matriz de trazabilidad de requisitos."""

from __future__ import annotations

import re
import sys
from collections import defaultdict

from src.comun.rutas import CONFIG, DOCS
from src.comun.yaml_util import cargar_yaml
from src.informes.marcadores import reemplazar_seccion

RUTA_DOC = DOCS / "12-trazabilidad" / "matriz-de-trazabilidad.md"
PATRON_FILA = re.compile(
    r"^\|\s*((?:RF|RNF)-\d{3})\s*\|[^|]*\|[^|]*\|[^|]*\|\s*"
    r"(Implementado|Parcial|Diseñado)\s*\|$",
    re.MULTILINE,
)
ESTADOS = ("Implementado", "Parcial", "Diseñado")


def _requisitos() -> list[dict]:
    datos = cargar_yaml(CONFIG / "requisitos" / "requisitos.yaml")
    return [requisito for filas in datos.values() for requisito in filas]


def tabla_resumen() -> str:
    """Valida la matriz contra los requisitos y resume su cobertura."""
    requisitos = _requisitos()
    esperados = {requisito["id"]: requisito for requisito in requisitos}
    filas = PATRON_FILA.findall(RUTA_DOC.read_text(encoding="utf-8"))
    identificadores = [identificador for identificador, _ in filas]

    faltantes = sorted(set(esperados) - set(identificadores))
    duplicados = sorted(
        identificador
        for identificador in set(identificadores)
        if identificadores.count(identificador) > 1
    )
    ajenos = sorted(set(identificadores) - set(esperados))
    if faltantes or duplicados or ajenos:
        raise ValueError(
            f"matriz inconsistente: faltan={faltantes}, duplicados={duplicados}, ajenos={ajenos}"
        )

    conteo: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "must": 0})
    for identificador, estado in filas:
        conteo[estado]["total"] += 1
        if esperados[identificador]["prioridad"] == "Must":
            conteo[estado]["must"] += 1

    total = len(requisitos)
    filas_tabla = [
        "| Estado | Requisitos | Must | Porcentaje |",
        "|---|---:|---:|---:|",
    ]
    for estado in ESTADOS:
        cantidad = conteo[estado]["total"]
        porcentaje = f"{cantidad / total * 100:.1f}".replace(".", ",")
        filas_tabla.append(f"| {estado} | {cantidad} | {conteo[estado]['must']} | {porcentaje} % |")
    must_total = sum(requisito["prioridad"] == "Must" for requisito in requisitos)
    filas_tabla.append(f"| **Total** | **{total}** | **{must_total}** | **100,0 %** |")
    cubiertos = conteo["Implementado"]["total"] + conteo["Parcial"]["total"]
    porcentaje = f"{cubiertos / total * 100:.1f}".replace(".", ",")
    return "\n".join(filas_tabla) + (
        f"\n\n{cubiertos} de {total} requisitos ({porcentaje} %) tienen evidencia "
        "implementada o parcial; el resto queda diseñado para el core nuevo."
    )


def main() -> int:
    """Actualiza el resumen autogenerado de la matriz de trazabilidad."""
    reemplazar_seccion(RUTA_DOC, "trazabilidad-resumen", tabla_resumen())
    print(f"Matriz de trazabilidad actualizada: {RUTA_DOC}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
