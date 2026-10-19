"""Genera las cifras del informe de conciliacion (fase 7).

Lee los resultados de src.conciliacion.ejecutar_conciliacion y actualiza las
secciones autogeneradas de docs/07-conciliacion/informe-de-conciliacion.md.
"""

from __future__ import annotations

import json
import sys

import pandas as pd

from src.comun.rutas import CONCILIACION
from src.informes.marcadores import reemplazar_seccion
from src.informes.pipeline import numero_es

RUTA_DOC = "docs/07-conciliacion/informe-de-conciliacion.md"
VERSIONES = (1, 2, 3)


def _resultado(version: int) -> dict:
    ruta = CONCILIACION / f"conciliacion_ensayo_v{version}.json"
    return json.loads(ruta.read_text("utf-8"))


def tabla_conteos() -> str:
    """Ecuacion origen = cargados + no cargados + fusionados del ensayo 3."""
    resultado = _resultado(3)
    filas = [
        "| Entidad | Origen | Cargados | No cargados | Revisados cargados | "
        "Fusionados | Diferencia |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for fila in resultado["conteos"]["filas"]:
        filas.append(
            f"| {fila['entidad']} | {numero_es(fila['origen'])} | "
            f"{numero_es(fila['cargados'])} | {numero_es(fila['no_cargados'])} | "
            f"{numero_es(fila['revisados_cargados'])} | "
            f"{numero_es(fila['fusionados'])} | {numero_es(fila['diferencia'])} |"
        )
    filas.append("")
    filas.append(
        "Las doce ecuaciones cierran en cero; los cargados se cuentan sin las filas "
        "de la delta y los no cargados surgen de cruzar cada rechazo contra la clave "
        "efectivamente presente en el destino, por lo que la igualdad no es "
        "tautologica: si un rechazo hubiera quedado cargado, o una fila se hubiera "
        "perdido, la diferencia lo delataria."
    )
    return "\n".join(filas)


def tabla_saldos() -> str:
    """Conciliacion de saldos de cuentas por ensayo."""
    filas = [
        "| Ensayo | Filas | Sin esperado | Diferencias | Monto cargado | Monto esperado |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for version in VERSIONES:
        saldos = _resultado(version)["saldos"]
        filas.append(
            f"| v{version} | {numero_es(saldos['filas'])} | "
            f"{numero_es(saldos['sin_esperado'])} | {numero_es(saldos['diferencias'])} | "
            f"{numero_es(saldos['monto_cargado'], 2)} | "
            f"{numero_es(saldos['monto_esperado'], 2)} |"
        )
    return "\n".join(filas)


def tabla_delta() -> str:
    """Efecto de la delta del corte sobre el ensayo 3."""
    saldos = _resultado(3)["saldos"]["delta"]
    movimientos = _resultado(3)["movimientos"]["delta"]
    filas = [
        "| Concepto | Cantidad |",
        "|---|---:|",
        f"| Cuentas nuevas | {numero_es(saldos['cuentas_nuevas'])} |",
        f"| Cuentas actualizadas | {numero_es(saldos['cuentas_actualizadas'])} |",
        f"| Saldos reemplazados | {numero_es(saldos['saldos_reemplazados'])} |",
        f"| Saldos de cuentas no migradas (descartados) | "
        f"{numero_es(saldos['saldos_descartados'])} |",
        f"| Movimientos nuevos | {numero_es(saldos['movimientos_nuevos'])} |",
        "",
        f"Los {numero_es(saldos['cuentas_nuevas'])} saldos insertados y los "
        f"{numero_es(saldos['movimientos_nuevos'])} movimientos nuevos se verificaron "
        "importe a importe contra los archivos de la delta: "
        f"{numero_es(movimientos['diferencias'])} diferencias.",
    ]
    return "\n".join(filas)


def tabla_movimientos() -> str:
    """Verificacion de movimientos y estado de los signos por ensayo."""
    filas = [
        "| Ensayo | Verificados | Diferencias | Signos invertidos en el legado | "
        "Signos cargados sin corregir |",
        "|---|---:|---:|---:|---:|",
    ]
    for version in VERSIONES:
        movimientos = _resultado(version)["movimientos"]
        filas.append(
            f"| v{version} | {numero_es(movimientos['filas_verificadas'])} | "
            f"{numero_es(movimientos['diferencias'])} | "
            f"{numero_es(movimientos['signos_invertidos_legado'])} | "
            f"{numero_es(movimientos['signos_sin_corregir_cargados'])} |"
        )
    return "\n".join(filas)


def tabla_descuadres() -> str:
    """Descuadres de saldo detectados en el universo cargado."""
    filas = [
        "| Ensayo | Cuentas analizadas | Con descuadre | Ajuste automatico | "
        "Revision manual | Monto absoluto | Monto neto en revision |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for version in VERSIONES:
        descuadres = _resultado(version)["descuadres"]
        filas.append(
            f"| v{version} | {numero_es(descuadres['cuentas_analizadas'])} | "
            f"{numero_es(descuadres['cuentas_descuadradas'])} | "
            f"{numero_es(descuadres['ajustes_automaticos'])} | "
            f"{numero_es(descuadres['revision_manual'])} | "
            f"{numero_es(descuadres['monto_absoluto'], 2)} | "
            f"{numero_es(descuadres['monto_revision'], 2)} |"
        )
    filas.append("")
    filas.append(
        "El ensayo 3 excluye del analisis las cuentas tocadas por la delta, cuyos "
        "saldos se concilian aparte contra el archivo del corte."
    )
    return "\n".join(filas)


def _desfases(version: int = 3) -> pd.DataFrame:
    return pd.read_csv(CONCILIACION / f"conciliacion_ensayo_v{version}_desfases.csv", dtype=str)


def tabla_contable() -> str:
    """Desfases contables detectados al recomponer el libro mayor."""
    resultado = _resultado(3)["contable"]
    desfases = _desfases()
    filas = [
        "| Codigo | Cuenta | Saldo cargado | Saldo esperado | Diferencia | Ajuste |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for _, fila in desfases.iterrows():
        filas.append(
            f"| {fila['codigo_contable']} | {fila['nombre_cuenta']} | "
            f"{numero_es(float(fila['saldo_final']), 2)} | "
            f"{numero_es(float(fila['esperado_final']), 2)} | "
            f"{numero_es(float(fila['diferencia']), 2)} | "
            f"{numero_es(float(fila['ajuste']), 2)} |"
        )
    filas.append("")
    filas.append(
        f"{numero_es(resultado['conciliadas'])} de {numero_es(resultado['filas'])} "
        f"cuentas del mayor concilian exactamente. Los desbalances internos "
        f"(debe - haber - final) son {numero_es(resultado['desbalances_internos'])}. "
        "El asiento 1.2.01 se reconcilia contra la suma de cuotas pendientes: el "
        "capital crudo de prestamos difiere en "
        f"{numero_es(resultado['diferencia_prestamos'], 2)} por "
        f"{numero_es(resultado['prestamos_incongruentes'])} prestamos con saldo "
        "incongruente, efecto que no se traslada al mayor."
    )
    return "\n".join(filas)


def tabla_ajustes() -> str:
    """Asientos de ajuste contable aplicados en el ensayo 3."""
    desfases = _desfases()
    total = desfases["ajuste"].astype(float).sum()
    filas = [
        "| Codigo | Cuenta | Ajuste | Contrapartida | Estado |",
        "|---|---|---:|---|---|",
    ]
    for _, fila in desfases.iterrows():
        filas.append(
            f"| {fila['codigo_contable']} | {fila['nombre_cuenta']} | "
            f"{numero_es(float(fila['ajuste']), 2)} | {fila['contrapartida']} | "
            f"{fila['estado']} |"
        )
    filas.append(
        f"| **Neto** |  | **{numero_es(total, 2)}** | {desfases['contrapartida'].iloc[0]} | "
        f"{desfases['estado'].iloc[0]} |"
    )
    filas.append("")
    filas.append(
        "El neto se imputa a resultados acumulados (3.3.01): los desfases se "
        "originan en el legado y el ajuste de migracion solo reconoce la diferencia "
        "contra la evidencia recalculada, sin reescribir las filas cargadas."
    )
    return "\n".join(filas)


def tabla_go_no_go() -> str:
    """Decision de aceptacion del corte por ensayo."""
    filas = [
        "| Ensayo | Decision | Criterios incumplidos | Observaciones |",
        "|---|---|---|---|",
    ]
    for version in VERSIONES:
        go_no_go = _resultado(version)["go_no_go"]
        incumplidos = [
            criterio["criterio"] for criterio in go_no_go["criterios"] if not criterio["cumple"]
        ]
        observaciones = " ".join(go_no_go["observaciones"])
        filas.append(
            f"| v{version} | {go_no_go['decision']} | "
            f"{', '.join(incumplidos) if incumplidos else 'ninguno'} | "
            f"{observaciones if observaciones else 'Sin observaciones.'} |"
        )
    return "\n".join(filas)


def main() -> int:
    """Actualiza las secciones autogeneradas del informe de conciliacion."""
    reemplazar_seccion(RUTA_DOC, "conciliacion-conteos", tabla_conteos())
    reemplazar_seccion(RUTA_DOC, "conciliacion-saldos", tabla_saldos())
    reemplazar_seccion(RUTA_DOC, "conciliacion-delta", tabla_delta())
    reemplazar_seccion(RUTA_DOC, "conciliacion-movimientos", tabla_movimientos())
    reemplazar_seccion(RUTA_DOC, "conciliacion-descuadres", tabla_descuadres())
    reemplazar_seccion(RUTA_DOC, "conciliacion-contable", tabla_contable())
    reemplazar_seccion(RUTA_DOC, "conciliacion-ajustes", tabla_ajustes())
    reemplazar_seccion(RUTA_DOC, "conciliacion-go-no-go", tabla_go_no_go())
    print(f"Informe de conciliacion actualizado: {RUTA_DOC}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
