"""Genera el tablero HTML con las cifras del pipeline y la conciliacion."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree

import pandas as pd
import plotly.graph_objects as go

from src.comun.rutas import CONCILIACION, DOCS, RESULTADOS

RUTA = DOCS / "tablero.html"
VERDE = "#0f766e"
AMBAR = "#b45309"
ROJO = "#b91c1c"
AZUL = "#1d4ed8"
GRIS = "#64748b"


def numero(valor: float, decimales: int = 0) -> str:
    """Formatea un numero con separadores en espanol."""
    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def _json(nombre: str) -> dict:
    return json.loads((CONCILIACION / nombre).read_text(encoding="utf-8"))


def _resumen(version: str) -> dict:
    return json.loads((RESULTADOS / f"resumen_ensayo_{version}.json").read_text(encoding="utf-8"))


def _figura(fig: go.Figure, incluir_plotly: bool) -> str:
    fig.update_layout(
        template="plotly_white",
        margin={"l": 50, "r": 20, "t": 20, "b": 50},
        height=340,
        font={"family": "Segoe UI, Roboto, Arial, sans-serif", "size": 13},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig.to_html(
        full_html=False,
        include_plotlyjs="cdn" if incluir_plotly else False,
        config={"displayModeBar": False, "responsive": True},
    )


def _kpi(valor: str, etiqueta: str, detalle: str = "") -> str:
    return (
        '<div class="kpi"><div class="kpi-valor">'
        + valor
        + '</div><div class="kpi-etiqueta">'
        + etiqueta
        + "</div>"
        + (f'<div class="kpi-detalle">{detalle}</div>' if detalle else "")
        + "</div>"
    )


def _tabla_go_no_go() -> str:
    filas = []
    for version in ("v1", "v2", "v3"):
        datos = _json(f"conciliacion_ensayo_{version}.json")
        decision = datos["go_no_go"]["decision"]
        clase = "ok" if decision.startswith("GO") else "no"
        incumplidos = (
            ", ".join(
                criterio["criterio"]
                for criterio in datos["go_no_go"]["criterios"]
                if not criterio["cumple"]
            )
            or "ninguno"
        )
        observaciones = " ".join(datos["go_no_go"]["observaciones"]) or "Sin observaciones."
        filas.append(
            f"<tr><td>{version.upper()}</td><td><span class='pill {clase}'>{decision}</span></td>"
            f"<td>{incumplidos}</td><td>{observaciones}</td></tr>"
        )
    return (
        "<table><thead><tr><th>Ensayo</th><th>Decision</th><th>Criterios incumplidos</th>"
        "<th>Observaciones</th></tr></thead><tbody>" + "".join(filas) + "</tbody></table>"
    )


def _tabla_pendientes(datos: dict) -> str:
    conteos = {fila["entidad"]: fila for fila in datos["conteos"]["filas"]}
    pendientes = [
        (
            "Descuadres graves en revision manual",
            datos["descuadres"]["revision_manual"],
            "Contabilidad",
        ),
        (
            "Cuentas en estado desconocido (X)",
            conteos["cuentas"]["revisados_cargados"],
            "Operaciones",
        ),
        (
            "Clientes con documento observado",
            conteos["clientes"]["revisados_cargados"],
            "Cumplimiento",
        ),
        (
            "Prestamos con saldo incongruente",
            datos["contable"]["prestamos_incongruentes"],
            "Contabilidad",
        ),
        ("Clientes no migrados por fecha imposible", conteos["clientes"]["no_cargados"], "Negocio"),
        (
            "Plazos con vencimiento incongruente",
            conteos["plazos_fijos"]["revisados_cargados"],
            "Operaciones",
        ),
    ]
    filas = "".join(
        f"<tr><td>{nombre}</td><td class='num'>{numero(cantidad)}</td><td>{dueno}</td></tr>"
        for nombre, cantidad, dueno in pendientes
    )
    return (
        "<table><thead><tr><th>Pendiente</th><th>Cantidad</th><th>Dueno</th></tr></thead>"
        f"<tbody>{filas}</tbody></table>"
    )


def _figura_filas() -> go.Figure:
    versiones = ["v1", "v2", "v3"]
    totales = [
        _json(f"conciliacion_ensayo_{version}.json")["filas"]["total"] for version in versiones
    ]
    fig = go.Figure(
        go.Bar(
            x=[version.upper() for version in versiones],
            y=totales,
            marker_color=[GRIS, AMBAR, VERDE],
            text=[numero(total) for total in totales],
            textposition="outside",
        )
    )
    fig.update_layout(yaxis_title="Filas cargadas")
    return fig


def _figura_rechazos() -> go.Figure:
    rechazos = pd.read_csv(RESULTADOS / "rechazos_ensayo_v3.csv", dtype=str)
    conteo = Counter(rechazos["motivo"]).most_common()
    fig = go.Figure(
        go.Bar(
            x=[cantidad for _, cantidad in conteo],
            y=[motivo.replace("_", " ") for motivo, _ in conteo],
            orientation="h",
            marker_color=AMBAR,
            text=[numero(cantidad) for _, cantidad in conteo],
            textposition="outside",
        )
    )
    fig.update_layout(xaxis_title="Filas rechazadas", margin={"l": 160, "r": 40})
    return fig


def _figura_descuadres() -> go.Figure:
    versiones = ["v1", "v2", "v3"]
    automaticos = []
    manuales = []
    for version in versiones:
        datos = _json(f"conciliacion_ensayo_{version}.json")["descuadres"]
        automaticos.append(datos["ajustes_automaticos"])
        manuales.append(datos["revision_manual"])
    fig = go.Figure()
    fig.add_bar(
        x=[v.upper() for v in versiones],
        y=automaticos,
        name="Ajuste automatico",
        marker_color=VERDE,
    )
    fig.add_bar(
        x=[v.upper() for v in versiones], y=manuales, name="Revision manual", marker_color=AMBAR
    )
    fig.update_layout(barmode="stack", yaxis_title="Cuentas con descuadre")
    return fig


def _figura_contable() -> go.Figure:
    desfases = pd.read_csv(CONCILIACION / "conciliacion_ensayo_v3_desfases.csv")
    fig = go.Figure(
        go.Bar(
            x=desfases["codigo_contable"],
            y=desfases["diferencia"],
            marker_color=[ROJO if valor < 0 else AZUL for valor in desfases["diferencia"]],
            text=[numero(valor, 2) for valor in desfases["diferencia"]],
            textposition="outside",
        )
    )
    fig.update_layout(yaxis_title="Diferencia (pesos)", xaxis_title="Cuenta contable")
    return fig


def generar() -> Path:
    """Construye el tablero y lo escribe en docs/tablero.html."""
    datos = _json("conciliacion_ensayo_v3.json")
    junit = ElementTree.parse(RESULTADOS / "junit.xml").getroot()
    casos = list(junit.iter("testcase"))
    pruebas = len(casos)
    omitidas = sum(1 for caso in casos if caso.find("skipped") is not None)
    fallidas = sum(
        1 for caso in casos if caso.find("failure") is not None or caso.find("error") is not None
    )
    automaticos = datos["descuadres"]["ajustes_automaticos"]
    manuales = datos["descuadres"]["revision_manual"]

    kpis = "".join(
        [
            _kpi(numero(datos["filas"]["total"]), "Filas en el destino", "Ensayo 3 con delta"),
            _kpi("GO", "Decision del corte", "Con observaciones"),
            _kpi("0", "Diferencias de conciliacion", "Conteos, saldos y movimientos"),
            _kpi(
                f"{numero(automaticos)} / {numero(manuales)}",
                "Descuadres automaticos / manuales",
                "Tolerancia de 100 pesos",
            ),
            _kpi(
                numero(abs(datos["contable"]["monto_ajuste"]), 2),
                "Ajuste contable neto",
                "Contrapartida 3.3.01",
            ),
            _kpi(
                f"{pruebas - omitidas - fallidas} / {pruebas}",
                "Pruebas aprobadas",
                f"{omitidas} omitidas, {fallidas} fallidas",
            ),
        ]
    )

    plantilla = (Path(__file__).with_name("plantilla.html")).read_text(encoding="utf-8")
    html = (
        plantilla.replace("{{KPIS}}", kpis)
        .replace("{{FIG_FILAS}}", _figura(_figura_filas(), True))
        .replace("{{FIG_RECHAZOS}}", _figura(_figura_rechazos(), False))
        .replace("{{FIG_DESCUADRES}}", _figura(_figura_descuadres(), False))
        .replace("{{FIG_CONTABLE}}", _figura(_figura_contable(), False))
        .replace("{{GO_NO_GO}}", _tabla_go_no_go())
        .replace("{{PENDIENTES}}", _tabla_pendientes(datos))
    )
    RUTA.write_text(html, encoding="utf-8")
    return RUTA


def main() -> int:
    """Genera el tablero y devuelve el codigo de salida."""
    ruta = generar()
    print(f"Tablero generado: {ruta}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
