"""Pruebas de integridad de la documentacion publicada."""

from __future__ import annotations

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DOCS = RAIZ / "docs"

PATRON_INICIO = re.compile(r"<!-- INICIO AUTO: ([a-z0-9-]+) -->")
PATRON_FIN = re.compile(r"<!-- FIN AUTO: ([a-z0-9-]+) -->")
PATRON_ENLACE = re.compile(r"\[[^\]]*\]\((?!https?:|#|mailto:)([^)\s]+)")

MARCADORES_ESPERADOS = {
    "01-marco-y-estrategia/estrategia-de-migracion.md": {"matriz-estrategia"},
    "02-analisis-as-is/puntos-de-dolor.md": {"dolores-perfilado"},
    "03-analisis-de-brechas/analisis-de-brechas.md": {"resumen-brechas", "matriz-brechas"},
    "04-datos-de-origen/diseno-de-la-extraccion.md": {
        "archivos-legado",
        "volumen-verdad",
        "carga-delta",
    },
    "05-mapeo-de-datos/modelo-de-datos.md": {"resumen-modelo", "catalogos-modelo"},
    "05-mapeo-de-datos/mapeo-de-datos.md": {"cobertura-mapeo", "detalle-mapeo"},
    "05-mapeo-de-datos/reglas-de-transformacion.md": {
        "matriz-reglas",
        "mapeo-productos-version",
        "reglas-calidad",
    },
    "06-pipeline/pipeline-de-migracion.md": {
        "pipeline-ensayos",
        "pipeline-tablas",
        "pipeline-delta",
        "pipeline-verificacion",
    },
    "07-conciliacion/informe-de-conciliacion.md": {
        "conciliacion-conteos",
        "conciliacion-saldos",
        "conciliacion-delta",
        "conciliacion-movimientos",
        "conciliacion-descuadres",
        "conciliacion-contable",
        "conciliacion-ajustes",
        "conciliacion-go-no-go",
    },
    "08-pruebas/estrategia-de-pruebas.md": {"pruebas-resumen", "pruebas-caracteristicas"},
    "12-trazabilidad/matriz-de-trazabilidad.md": {"trazabilidad-resumen"},
}


def bloques_auto(texto: str) -> list[str]:
    """Devuelve las claves de los bloques autogenerados del texto."""
    return PATRON_INICIO.findall(texto)


def test_marcadores_autogenerados_completos() -> None:
    """Cada seccion autogenerada tiene su apertura, su cierre y su clave esperada."""
    for ruta, esperadas in MARCADORES_ESPERADOS.items():
        texto = (DOCS / ruta).read_text(encoding="utf-8")
        inicios = bloques_auto(texto)
        cierres = PATRON_FIN.findall(texto)
        assert inicios == cierres, f"{ruta}: aperturas y cierres AUTO desalineados"
        assert set(inicios) == esperadas, f"{ruta}: claves AUTO inesperadas"
        for clave in esperadas:
            cuerpo = texto.split(f"<!-- INICIO AUTO: {clave} -->")[1]
            cuerpo = cuerpo.split(f"<!-- FIN AUTO: {clave} -->")[0].strip()
            assert cuerpo, f"{ruta}: la seccion {clave} quedo vacia"


def test_enlaces_relativos_resueltos() -> None:
    """Todos los enlaces relativos de la documentacion apuntan a archivos existentes."""
    rotos = []
    for md in sorted(DOCS.rglob("*.md")):
        for numero, linea in enumerate(md.read_text(encoding="utf-8").splitlines(), 1):
            for enlace in PATRON_ENLACE.findall(linea):
                destino = (md.parent / enlace).resolve()
                if not destino.exists():
                    rotos.append(f"{md.relative_to(RAIZ)}:{numero}: {enlace}")
    assert not rotos, "enlaces rotos:\n" + "\n".join(rotos)


def test_tablero_y_sitio_existen() -> None:
    """El tablero interactivo y el archivo de configuracion de mkdocs estan presentes."""
    assert (DOCS / "tablero.html").stat().st_size > 10_000
    assert (RAIZ / "mkdocs.yml").exists()
