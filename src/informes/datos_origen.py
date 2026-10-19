"""Genera las tablas con cifras reales del diseno de la extraccion (fase 4).

Cuenta los registros de los archivos del legado, resume la verdad de terreno de los
defectos inyectados y la carga delta, y actualiza las secciones autogeneradas del
documento en docs/04-datos-de-origen/diseno-de-la-extraccion.md.
"""

import json
import sys
from pathlib import Path

import pandas as pd

from src.comun.rutas import CONFIG, DOCS, LEGADO, RESULTADOS, VERDAD
from src.comun.yaml_util import cargar_yaml
from src.informes.marcadores import reemplazar_seccion

RUTA_DOC = DOCS / "04-datos-de-origen" / "diseno-de-la-extraccion.md"
DISENOS = CONFIG / "disenos_legado"
ORDEN = (
    "clientes", "documentos", "direcciones", "cuentas", "saldos", "movimientos",
    "prestamos", "cuotas", "plazos_fijos", "mandatos", "plan_cuentas", "saldos_contables",
)


def numero_es(valor: float, decimales: int = 0) -> str:
    """Formatea un numero con separador de miles y decimales al estilo es-AR."""
    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def _contar_lineas(ruta: Path) -> int:
    with open(ruta, "rb") as archivo:
        return sum(bloque.count(b"\n") for bloque in iter(lambda: archivo.read(1 << 20), b""))


def tabla_archivos() -> tuple[str, dict]:
    """Construye la tabla de archivos de la extraccion y los conteos por entidad."""
    filas = [
        "| Entidad | Archivo | Longitud (bytes) | Registros | Tamaño | Descripción |",
        "|---|---|---:|---:|---:|---|",
    ]
    conteos = {}
    for entidad in ORDEN:
        diseno = cargar_yaml(DISENOS / f"{entidad}.yaml")
        ruta = LEGADO / diseno["archivo"]
        registros = _contar_lineas(ruta)
        conteos[entidad] = registros
        tamano = ruta.stat().st_size / (1024 * 1024)
        filas.append(
            f"| {entidad.replace('_', ' ').capitalize()} | `{diseno['archivo']}` | "
            f"{diseno['longitud_registro']} | {numero_es(registros)} | "
            f"{numero_es(tamano, 1)} MB | {diseno['descripcion']} |"
        )
    total = sum(conteos.values())
    filas.append(f"| **Total** |  |  | **{numero_es(total)}** |  |  |")
    return "\n".join(filas), conteos


def tabla_verdad(conteos: dict) -> str:
    """Construye la tabla de defectos inyectados con tasas observadas reales."""
    verdad = pd.read_csv(VERDAD / "defectos_inyectados.csv", dtype=str)
    agrupado = verdad.groupby(["entidad", "tipo_defecto"]).size().reset_index(name="cantidad")
    filas = [
        "| Entidad | Defecto inyectado | Casos | Registros de la entidad | Tasa observada |",
        "|---|---|---:|---:|---:|",
    ]
    for _, fila in agrupado.sort_values(["entidad", "tipo_defecto"]).iterrows():
        base = conteos.get(fila["entidad"], 0)
        tasa = fila["cantidad"] / base * 100 if base else 0.0
        filas.append(
            f"| {fila['entidad'].replace('_', ' ')} | `{fila['tipo_defecto']}` | "
            f"{numero_es(fila['cantidad'])} | {numero_es(base)} | "
            f"{numero_es(tasa, 2)} % |"
        )
    total = len(verdad)
    registros = sum(conteos.values())
    filas.append(
        f"| **Total** |  | **{numero_es(total)}** | **{numero_es(registros)}** | "
        f"**{numero_es(total / registros * 100, 2)} %** |"
    )
    return "\n".join(filas)


def _fecha_es(iso: str) -> str:
    """Convierte una fecha ISO (aaaa-mm-dd) a formato dd/mm/aaaa."""
    anio, mes, dia = iso.split("-")
    return f"{dia}/{mes}/{anio}"


def tabla_delta() -> str:
    """Construye la tabla de la carga delta del dia de corte."""
    with open(RESULTADOS / "resumen_generacion.json", encoding="utf-8") as archivo:
        resumen = json.load(archivo)
    registros = resumen["registros"]
    descripciones = {
        "delta_cuentas": "Altas de cuentas del día de corte.",
        "delta_movimientos": "Movimientos del día (incluye el depósito de apertura de las altas).",
        "delta_saldos": "Saldos actualizados de las cuentas afectadas.",
    }
    filas = [
        "| Archivo delta | Registros | Contenido |",
        "|---|---:|---|",
    ]
    for clave, descripcion in descripciones.items():
        nombre = clave.replace("delta_", "") + "_delta.dat"
        filas.append(
            f"| `{nombre}` | {numero_es(registros[clave])} | {descripcion} |"
        )
    filas.append("")
    fecha_base = _fecha_es(resumen["fecha_extraccion"])
    fecha_delta = _fecha_es(resumen["fecha_delta"])
    segundos = numero_es(resumen["segundos_generacion"], 1)
    filas.append(
        f"**Fechas del proceso:** extracción base del **{fecha_base}**, "
        f"carga delta del **{fecha_delta}**. Generación completa en {segundos} segundos."
    )
    return "\n".join(filas)


def main() -> int:
    """Punto de entrada del generador."""
    tabla_1, conteos = tabla_archivos()
    reemplazar_seccion(RUTA_DOC, "archivos-legado", tabla_1)
    reemplazar_seccion(RUTA_DOC, "volumen-verdad", tabla_verdad(conteos))
    reemplazar_seccion(RUTA_DOC, "carga-delta", tabla_delta())
    print("Documento de diseno de la extraccion actualizado con cifras reales.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
