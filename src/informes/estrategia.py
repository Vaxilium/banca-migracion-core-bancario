"""Genera la tabla de evaluacion ponderada de estrategias de migracion.

Lee config/estrategia/opciones.yaml, calcula el puntaje ponderado de cada opcion
y actualiza la seccion autogenerada en el documento de estrategia.
"""

import sys

from src.comun.rutas import CONFIG, DOCS
from src.comun.yaml_util import cargar_yaml
from src.informes.marcadores import reemplazar_seccion

RUTA_CONFIG = CONFIG / "estrategia" / "opciones.yaml"
RUTA_DOC = DOCS / "01-marco-y-estrategia" / "estrategia-de-migracion.md"


def calcular_puntajes(config: dict) -> list[dict]:
    """Calcula el puntaje ponderado de cada opcion de migracion."""
    criterios = config["criterios"]
    resultados = []
    for opcion in config["opciones"]:
        puntaje = sum(
            criterio["peso"] * opcion["puntajes"][criterio["id"]] for criterio in criterios
        )
        resultados.append(
            {
                "id": opcion["id"],
                "nombre": opcion["nombre"],
                "justificacion": opcion["justificacion"],
                "puntaje": round(puntaje, 3),
            }
        )
    return sorted(resultados, key=lambda r: r["puntaje"], reverse=True)


def construir_tabla(config: dict, resultados: list[dict]) -> str:
    """Construye la tabla Markdown de la matriz ponderada."""
    criterios = config["criterios"]
    encabezado = "| Criterio (peso) | " + " | ".join(r["nombre"] for r in resultados) + " |"
    separador = "|---" * (len(resultados) + 1) + "|"
    filas = []
    for criterio in criterios:
        celdas = []
        for resultado in resultados:
            opcion = next(o for o in config["opciones"] if o["id"] == resultado["id"])
            celdas.append(f"{opcion['puntajes'][criterio['id']]:.1f}")
        etiqueta = f"{criterio['nombre']} ({criterio['peso'] * 100:.0f} %)"
        filas.append(f"| {etiqueta} | " + " | ".join(celdas) + " |")
    fila_final = (
        "| **Puntaje ponderado** | "
        + " | ".join(f"**{r['puntaje']:.3f}**" for r in resultados)
        + " |"
    )
    lineas = [encabezado, separador, *filas, fila_final]
    ganadora = resultados[0]
    segunda = resultados[1]
    lineas.append("")
    lineas.append(
        f"**Resultado calculado:** la opcion recomendada es **{ganadora['nombre']}** "
        f"con {ganadora['puntaje']:.3f} puntos ponderados, seguida de "
        f"{segunda['nombre']} con {segunda['puntaje']:.3f}."
    )
    for resultado in resultados:
        justificacion = " ".join(str(resultado["justificacion"]).split())
        lineas.append("")
        lineas.append(f"- **{resultado['nombre']}** ({resultado['puntaje']:.3f}): {justificacion}")
    return "\n".join(lineas)


def main() -> int:
    """Punto de entrada del generador."""
    config = cargar_yaml(RUTA_CONFIG)
    resultados = calcular_puntajes(config)
    tabla = construir_tabla(config, resultados)
    reemplazar_seccion(RUTA_DOC, "matriz-estrategia", tabla)
    print(f"Tabla de estrategia actualizada. Opcion recomendada: {resultados[0]['nombre']}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
