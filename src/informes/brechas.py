"""Genera la matriz de brechas (CSV y Excel) y actualiza los documentos de la fase 3.

Fuente unica: config/brechas/matriz_brechas.yaml y config/requisitos/requisitos.yaml.
Salidas: docs/03-analisis-de-brechas/matriz-brechas.csv, matriz-brechas.xlsx,
requisitos.md y las secciones autogeneradas de analisis-de-brechas.md.
"""

import sys

import pandas as pd

from src.comun.rutas import CONFIG, DOCS
from src.comun.yaml_util import cargar_yaml
from src.informes.marcadores import reemplazar_seccion

RUTA_BRECHAS = CONFIG / "brechas" / "matriz_brechas.yaml"
RUTA_REQUISITOS = CONFIG / "requisitos" / "requisitos.yaml"
DIR_DOC = DOCS / "03-analisis-de-brechas"
DOC_BRECHAS = DIR_DOC / "analisis-de-brechas.md"
DOC_REQUISITOS = DIR_DOC / "requisitos.md"

FILTROS_RESUMEN = ("tipo", "prioridad", "esfuerzo", "riesgo")


def tabla_brechas(config: dict) -> pd.DataFrame:
    """Construye el DataFrame completo de la matriz de brechas."""
    filas = []
    for brecha in config["brechas"]:
        filas.append(
            {
                "id": brecha["id"],
                "capacidad": brecha["capacidad"],
                "capacidad_nombre": config["capacidades"][brecha["capacidad"]],
                "titulo": brecha["titulo"],
                "tipo": brecha["tipo"],
                "descripcion": " ".join(str(brecha["descripcion"]).split()),
                "esfuerzo": brecha["esfuerzo"],
                "riesgo": brecha["riesgo"],
                "prioridad": brecha["prioridad"],
                "responsable": brecha["responsable"],
                "requisitos": ", ".join(brecha.get("requisitos") or []),
                "puntos_dolor": ", ".join(brecha.get("puntos_dolor") or []),
            }
        )
    return pd.DataFrame(filas)


def tabla_md(encabezados: list[str], filas: list[list[str]]) -> str:
    """Construye una tabla Markdown simple."""
    lineas = ["| " + " | ".join(encabezados) + " |", "|" + "---|" * len(encabezados)]
    for fila in filas:
        lineas.append("| " + " | ".join(str(c) for c in fila) + " |")
    return "\n".join(lineas)


def seccion_resumen(df: pd.DataFrame) -> str:
    """Genera el resumen cuantitativo de la matriz de brechas."""
    partes = [f"Total de brechas analizadas: **{len(df)}**."]
    for columna in FILTROS_RESUMEN:
        conteo = df[columna].value_counts()
        filas = [[nombre, str(int(valor))] for nombre, valor in conteo.items()]
        partes.append("")
        partes.append(f"**Distribucion por {columna}**")
        partes.append("")
        partes.append(tabla_md([columna.capitalize(), "Brechas"], filas))
    cubiertas = df[df["tipo"] == "cubierta"]
    detalle = (
        f"Brechas que requieren trabajo del proyecto (todas menos `cubierta`): "
        f"**{len(df) - len(cubiertas)}** de {len(df)}."
    )
    porcentaje_must = 100 * (df["prioridad"] == "Must").mean()
    partes.append("")
    partes.append(detalle)
    partes.append(f"Porcentaje de brechas Must: **{porcentaje_must:.1f} %**.")
    return "\n".join(partes)


def seccion_matriz(df: pd.DataFrame) -> str:
    """Genera la tabla Markdown de la matriz completa."""
    encabezados = ["ID", "Capacidad", "Brecha", "Tipo", "Esf.", "Riesgo", "MoSCoW", "Requisitos"]
    filas = []
    for _, fila in df.iterrows():
        filas.append(
            [
                fila["id"],
                f"{fila['capacidad']} {fila['capacidad_nombre']}",
                fila["titulo"],
                fila["tipo"],
                fila["esfuerzo"],
                fila["riesgo"],
                fila["prioridad"],
                fila["requisitos"] or "-",
            ]
        )
    return tabla_md(encabezados, filas)


def documento_requisitos(requisitos: dict) -> str:
    """Genera el documento completo de requisitos RF y RNF."""
    partes = [
        "# Requisitos funcionales y no funcionales",
        "",
        "| Proyecto | Migración del core bancario — Banco Meridiano Austral (entidad ficticia) |",
        "|---|---|",
        "| **Versión** | 1.0 |",
        "| **Fecha** | 19/10/2026 |",
        "| **Autor** | Franco Tilleria, Analista de Negocios |",
        "| **Estado** | Aprobado |",
        "",
        "> Documento generado automáticamente por `src/informes/brechas.py` a partir de",
        "> `config/requisitos/requisitos.yaml`. No editar a mano.",
        "",
        "## Propósito",
        "",
        "Derivar los requisitos funcionales y no funcionales del análisis de brechas,",
        "con identificadores únicos que alimentan la matriz de trazabilidad (fase 12).",
        "",
        "## Alcance",
        "",
        f"Requisitos derivados de la matriz de brechas vigente: "
        f"**{len(requisitos['funcionales'])} funcionales** y "
        f"**{len(requisitos['no_funcionales'])} no funcionales**.",
        "",
        "## Renuncia necesaria",
        "",
        "Cada requisito tiene identificador único, prioridad MoSCoW y criterio de",
        "aceptación verificable. Su cumplimiento se demuestra con casos de prueba (fase 8).",
        "",
        "## Requisitos funcionales",
        "",
    ]
    filas = []
    for req in requisitos["funcionales"]:
        filas.append(
            [
                req["id"],
                req["titulo"],
                " ".join(str(req["descripcion"]).split()),
                " ".join(str(req["criterio_aceptacion"]).split()),
                req["capacidad"],
                req["prioridad"],
            ]
        )
    partes.append(tabla_md(["ID", "Título", "Descripción", "Criterio de aceptación",
                            "Capacidad", "Prioridad"], filas))
    partes += ["", "## Requisitos no funcionales", ""]
    filas = []
    for req in requisitos["no_funcionales"]:
        filas.append(
            [
                req["id"],
                req["titulo"],
                " ".join(str(req["descripcion"]).split()),
                " ".join(str(req["criterio_aceptacion"]).split()),
                req["categoria"],
                req["prioridad"],
            ]
        )
    partes.append(tabla_md(["ID", "Título", "Descripción", "Criterio de aceptación",
                            "Categoría", "Prioridad"], filas))
    partes += [
        "",
        "## Supuestos",
        "",
        "- Los criterios de aceptación se expresan en lenguaje verificable; los casos en",
        "  formato Gherkin se desarrollan en la fase 8 de pruebas.",
        "",
        "## Riesgos y dependencias",
        "",
        "| Riesgo | Mitigación |",
        "|---|---|",
        "| Requisitos sin caso de prueba | La matriz de trazabilidad marca la cobertura. |",
        "| Cambios de alcance tardíos | Control de cambios vía comité operativo y ADR. |",
        "",
        "## Glosario",
        "",
        "Ver [glosario único](../glosario.md).",
    ]
    return "\n".join(partes) + "\n"


def main() -> int:
    """Punto de entrada del generador de brechas y requisitos."""
    config = cargar_yaml(RUTA_BRECHAS)
    requisitos = cargar_yaml(RUTA_REQUISITOS)
    df = tabla_brechas(config)
    DIR_DOC.mkdir(parents=True, exist_ok=True)

    df.to_csv(DIR_DOC / "matriz-brechas.csv", index=False, encoding="utf-8-sig")
    with pd.ExcelWriter(DIR_DOC / "matriz-brechas.xlsx", engine="openpyxl") as escritor:
        df.to_excel(escritor, sheet_name="Matriz de brechas", index=False)
        resumen = (
            df.groupby(["tipo", "prioridad"]).size().reset_index(name="brechas")
        )
        resumen.to_excel(escritor, sheet_name="Resumen", index=False)
        hoja = escritor.sheets["Matriz de brechas"]
        for columna, ancho in zip(
            hoja.columns, (10, 12, 22, 40, 12, 10, 10, 10, 10, 22, 20, 16), strict=False
        ):
            hoja.column_dimensions[columna[0].column_letter].width = ancho

    reemplazar_seccion(DOC_BRECHAS, "resumen-brechas", seccion_resumen(df))
    reemplazar_seccion(DOC_BRECHAS, "matriz-brechas", seccion_matriz(df))
    DOC_REQUISITOS.write_text(documento_requisitos(requisitos), encoding="utf-8")

    print(f"Brechas: {len(df)}. CSV, Excel y requisitos.md generados.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
