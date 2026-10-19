"""Genera las cifras del pipeline de migracion (fase 6).

Lee los resumenes y archivos de rechazos y bitacora de cada ensayo, la verdad de
terreno de los defectos y los resultados de la delta del corte, y actualiza las
secciones autogeneradas de docs/06-pipeline/pipeline-de-migracion.md.
"""

import json
import re
import sys

import pandas as pd

from src.comun.rutas import BITACORA, RESULTADOS, VERDAD
from src.informes.marcadores import reemplazar_seccion

RUTA_DOC = "docs/06-pipeline/pipeline-de-migracion.md"

ETIQUETAS_PARAMETROS = {
    "umbral_siglo": "Umbral de siglo",
    "deduplicacion_clientes": "Deduplicacion de clientes",
    "validar_fechas_contextual": "Validacion contextual de fechas",
    "correccion_signos": "Correccion de signos",
    "extraccion_texto_libre": "Extraccion de texto libre",
    "ajustes_contables": "Ajustes contables",
}


def numero_es(valor: float, decimales: int = 0) -> str:
    """Formatea un numero con separador de miles y decimales al estilo es-AR."""
    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def _resumen(version: int) -> dict:
    return json.loads((RESULTADOS / f"resumen_ensayo_v{version}.json").read_text("utf-8"))


def _booleano(valor: object) -> str:
    return "si" if str(valor).lower() in ("true", "1", "si") else "no"


def tabla_ensayos() -> str:
    """Compara parametros, volumenes y rechazos de los tres ensayos."""
    resumenes = [_resumen(version) for version in (1, 2, 3)]
    filas = [
        "| Parametro | Ensayo 1 | Ensayo 2 | Ensayo 3 |",
        "|---|---|---|---|",
    ]
    for clave, etiqueta in ETIQUETAS_PARAMETROS.items():
        celdas = []
        for resumen in resumenes:
            valor = resumen["parametros"][clave]
            celdas.append(numero_es(valor) if clave == "umbral_siglo" else _booleano(valor))
        filas.append(f"| {etiqueta} | " + " | ".join(celdas) + " |")
    filas.append("|  |  |  |  |")
    for clave, etiqueta in (
        ("total", "Filas cargadas en el destino"),
        ("duracion_segundos", "Duracion (segundos)"),
    ):
        celdas = []
        for resumen in resumenes:
            if clave == "total":
                valor = sum(resumen["tablas_cargadas"].values())
                celdas.append(numero_es(valor))
            else:
                celdas.append(numero_es(resumen.get(clave, 0), 1))
        filas.append(f"| {etiqueta} | " + " | ".join(celdas) + " |")
    for clave, etiqueta in (
        ("cliente", "Clientes"),
        ("movimiento", "Movimientos"),
        ("cuenta", "Cuentas"),
    ):
        celdas = [
            numero_es(resumen["tablas_cargadas"].get(clave, 0)) for resumen in resumenes
        ]
        filas.append(f"| {etiqueta} | " + " | ".join(celdas) + " |")
    filas.append("")
    filas.append(
        "Los ensayos son acumulativos: el 1 deja los defectos documentados, el 2 "
        "activa deduplicacion y validacion contextual, y el 3 corrige signos, "
        "extrae texto libre y aplica ajustes contables respaldados."
    )
    return "\n".join(filas)


def tabla_tablas() -> str:
    """Tablas destino cargadas por el ensayo 3 (con la delta ya incorporada)."""
    resumen = _resumen(3)
    filas = [
        "| Tabla destino | Filas cargadas |",
        "|---|---:|",
    ]
    for tabla, cantidad in sorted(resumen["tablas_cargadas"].items()):
        filas.append(f"| `{tabla}` | {numero_es(cantidad)} |")
    filas.append(
        f"| **Total** | **{numero_es(sum(resumen['tablas_cargadas'].values()))}** |"
    )
    return "\n".join(filas)


def tabla_delta() -> str:
    """Resultado de la carga delta del corte sobre el ensayo 3."""
    resumen = _resumen(3)
    delta = resumen.get("delta")
    if not isinstance(delta, dict):
        return "La corrida vigente no incorporo la delta del corte."
    filas = [
        "| Tabla | Actualizadas | Insertadas |",
        "|---|---:|---:|",
    ]
    for tabla, movimientos in delta.items():
        filas.append(
            f"| `{tabla}` | {numero_es(movimientos['reemplazadas'])} | "
            f"{numero_es(movimientos['insertadas'])} |"
        )
    rechazos = pd.read_csv(RESULTADOS / "rechazos_delta_v3.csv", dtype=str)
    detalle = ", ".join(
        f"`{motivo}` {numero_es(cantidad)}"
        for motivo, cantidad in rechazos["motivo"].value_counts().items()
    )
    filas.append("")
    filas.append(
        f"La ventana del corte ({resumen['fecha_extraccion']} a "
        f"{resumen['fecha_delta']}) aporto {numero_es(len(rechazos))} registros "
        f"rechazados: {detalle}. Son movimientos y saldos de cuentas que no "
        "migraron, por lo que la delta hereda el rechazo explicado."
    )
    return "\n".join(filas)


def _norm(clave: str) -> str:
    """Normaliza claves numericas (saca ceros a la izquierda) para poder cruzarlas."""
    texto = str(clave)
    return str(int(texto)) if texto.isdigit() else texto


def tabla_verificacion() -> str:
    """Cruce de la verdad de terreno contra las detecciones del ensayo 3."""
    verdad = pd.read_csv(VERDAD / "defectos_inyectados.csv", dtype=str)
    rechazos = pd.read_csv(RESULTADOS / "rechazos_ensayo_v3.csv", dtype=str)
    bitacora = pd.read_csv(BITACORA / "bitacora_ensayo_v3.csv", dtype=str)

    def claves_verdad(entidad: str, tipo: str) -> set[str]:
        filas = verdad[(verdad["entidad"] == entidad) & (verdad["tipo_defecto"] == tipo)]
        return {_norm(clave) for clave in filas["clave"]}

    def claves_rechazo(motivo: str, entidad: str) -> set[str]:
        filas = rechazos[(rechazos["entidad"] == entidad) & (rechazos["motivo"] == motivo)]
        return {_norm(clave) for clave in filas["clave"]}

    def claves_bitacora(accion: str) -> set[str]:
        filas = bitacora[bitacora["accion"] == accion]
        return {_norm(clave) for clave in filas["clave"]}

    fusionados = {
        _norm(coincidencia.group(1))
        for detalle in bitacora.loc[bitacora["accion"] == "fusion_cliente", "detalle"]
        if (coincidencia := re.search(r"id_cliente=(\d+)", str(detalle)))
    }

    casos = [
        (
            "Clientes duplicados (fusionados)",
            claves_verdad("clientes", "duplicado_nombre_variante"),
            fusionados,
        ),
        ("Documentos invalidos de clientes", claves_verdad("clientes", "documento_invalido"),
         claves_rechazo("documento_invalido", "clientes")),
        (
            "Documentos repetidos entre clientes",
            claves_verdad("clientes", "documento_repetido_otro_cliente"),
            claves_rechazo("documento_repetido", "clientes"),
        ),
        ("Fechas de nacimiento imposibles", claves_verdad("clientes", "fecha_nacimiento_imposible"),
         claves_rechazo("fecha_imposible", "clientes")),
        ("Documentos vencidos sin marcar", claves_verdad("documentos", "vencido_sin_marcar"),
         claves_bitacora("documento_vencido_sin_marcar")),
        ("Direcciones incompletas", claves_verdad("direcciones", "direccion_incompleta"),
         claves_bitacora("direccion_incompleta")),
        ("Cuentas huerfanas", claves_verdad("cuentas", "cuenta_huerfana"),
         claves_rechazo("cuenta_huerfana", "cuentas")),
        ("Cuentas con estado desconocido", claves_verdad("cuentas", "estado_desconocido"),
         claves_rechazo("estado_desconocido", "cuentas")),
        ("Cuentas de producto fuera de alcance", claves_verdad("cuentas", "producto_fuera_alcance"),
         claves_rechazo("producto_fuera_de_alcance", "cuentas")),
        ("Cuentas de producto desconocido", claves_verdad("cuentas", "producto_desconocido"),
         claves_rechazo("producto_desconocido", "cuentas")),
        ("Movimientos con signo invertido", claves_verdad("movimientos", "signo_invertido"),
         claves_bitacora("correccion_signo")),
        ("Movimientos con fecha imposible", claves_verdad("movimientos", "fecha_imposible"),
         claves_rechazo("fecha_imposible", "movimientos")),
        (
            "Movimientos duplicados por reproceso",
            claves_verdad("movimientos", "duplicado_reproceso"),
            claves_rechazo("duplicado_reproceso", "movimientos"),
        ),
        ("Prestamos con saldo incongruente", claves_verdad("prestamos", "saldo_incongruente"),
         claves_rechazo("saldo_incongruente", "prestamos")),
        (
            "Plazos con vencimiento incongruente",
            claves_verdad("plazos_fijos", "vencimiento_incongruente"),
            claves_rechazo("vencimiento_incongruente", "plazos_fijos"),
        ),
        ("Mandatos con cuenta inexistente", claves_verdad("mandatos", "cuenta_inexistente"),
         claves_rechazo("cuenta_no_migrada", "mandatos")),
    ]
    filas = [
        "| Defecto inyectado | Casos | Detectados | Faltantes |",
        "|---|---:|---:|---:|",
    ]
    for nombre, verdaderos, detectados in casos:
        faltantes = len(verdaderos - detectados)
        filas.append(
            f"| {nombre} | {numero_es(len(verdaderos))} | "
            f"{numero_es(len(verdaderos & detectados))} | {numero_es(faltantes)} |"
        )
    filas.append("")
    filas.append(
        "Los faltantes son filas rechazadas antes de la deteccion especifica por "
        "otro defecto en la misma fila o por una cascada de integridad referencial "
        "(por ejemplo, movimientos de cuentas que no migraron); cada caso queda "
        "registrado en los rechazos con su motivo. Las detecciones pueden superar "
        "los casos inyectados cuando el defecto afecta a mas de una fila (por "
        "ejemplo, un documento compartido queda marcado en ambos clientes)."
    )
    return "\n".join(filas)


def main() -> None:
    """Actualiza las secciones autogeneradas del documento de la fase 6."""
    reemplazar_seccion(RUTA_DOC, "pipeline-ensayos", tabla_ensayos())
    reemplazar_seccion(RUTA_DOC, "pipeline-tablas", tabla_tablas())
    reemplazar_seccion(RUTA_DOC, "pipeline-delta", tabla_delta())
    reemplazar_seccion(RUTA_DOC, "pipeline-verificacion", tabla_verificacion())
    print("Documento del pipeline actualizado: docs/06-pipeline/pipeline-de-migracion.md")


if __name__ == "__main__":
    sys.exit(main())
