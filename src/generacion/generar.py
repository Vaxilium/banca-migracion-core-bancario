"""Orquestador de la generacion de la extraccion sintetica del legado.

Uso: python -m src.generacion.generar --escala completa|piloto|humo
Genera los archivos .dat de ancho fijo, la carga delta del corte, la verdad de
terreno de los defectos inyectados y un resumen JSON con cifras verificables.
"""

import argparse
import json
import sys
import time
from datetime import date, timedelta

import pandas as pd

from src.comun import rutas
from src.comun.fechas import aammdd_desde_fecha
from src.comun.semilla import generador_numpy
from src.comun.yaml_util import cargar_yaml
from src.generacion import contabilidad, creditos, maestros
from src.generacion import cuentas as mod_cuentas
from src.generacion import defectos as mod_defectos
from src.generacion import delta as mod_delta
from src.generacion import movimientos as mod_movimientos
from src.generacion.escritura import DisenoAnchoFijo

ENTIDADES_LEGADO = (
    "clientes", "documentos", "direcciones", "cuentas", "saldos", "movimientos",
    "prestamos", "cuotas", "plazos_fijos", "mandatos", "plan_cuentas", "saldos_contables",
)


def _diseno(entidad: str) -> DisenoAnchoFijo:
    return DisenoAnchoFijo(rutas.CONFIG / "disenos_legado" / f"{entidad}.yaml")


def generar(escala: str) -> dict:
    """Genera la extraccion completa del legado y devuelve el resumen de cifras."""
    inicio = time.time()
    rutas.asegurar_directorios()
    cfg_escala = cargar_yaml(rutas.CONFIG / "parametrico" / "escala.yaml")
    if escala not in cfg_escala["escalas"]:
        raise SystemExit(f"escala desconocida: {escala}")
    config = cfg_escala["escalas"][escala]
    config_productos = cargar_yaml(rutas.CONFIG / "parametrico" / "productos.yaml")
    tasas_defectos = cargar_yaml(rutas.CONFIG / "parametrico" / "defectos.yaml")
    fecha_extraccion = date.fromisoformat(str(cfg_escala["fecha_extraccion"]))
    fecha_delta = date.fromisoformat(str(cfg_escala["fecha_delta"]))
    rng = generador_numpy()

    clientes = maestros.generar_clientes(config["clientes"], rng)
    direcciones = maestros.generar_direcciones(clientes, rng)
    documentos = maestros.generar_documentos(
        clientes, config["proporcion_segundo_documento"], rng, fecha_extraccion
    )
    cuentas = mod_cuentas.generar_cuentas(
        clientes, config_productos, rng, config["cuentas_por_cliente"], fecha_extraccion
    )
    movimientos, saldos, ultimo_mov = mod_movimientos.generar_movimientos_y_saldos(
        cuentas, config_productos, rng, fecha_extraccion, config["tope_movimientos"]
    )
    defecto_fecha = aammdd_desde_fecha(fecha_extraccion - timedelta(days=500))
    mapa_ultimo = pd.Series(ultimo_mov)
    cuentas["fecha_ultimo_movimiento"] = (
        cuentas["id_cuenta"].map(mapa_ultimo).fillna(defecto_fecha)
    )
    prestamos, cuotas = creditos.generar_prestamos(
        clientes, cuentas, config, config_productos, rng, fecha_extraccion
    )
    plazos = creditos.generar_plazos_fijos(
        clientes, cuentas, config, config_productos, rng, fecha_extraccion
    )
    mandatos = creditos.generar_mandatos(
        clientes, cuentas, config, config_productos, rng, fecha_extraccion
    )
    plan_cuentas = contabilidad.generar_plan_cuentas()
    saldos_contables, desfases = contabilidad.generar_saldos_contables(
        saldos, cuentas, prestamos, plazos, config_productos,
        int(tasas_defectos["contabilidad"]["filas_con_desfase"]), rng, fecha_extraccion,
    )

    inyector = mod_defectos.Inyector(rng, tasas_defectos)
    clientes = inyector.clientes(clientes)
    documentos = inyector.documentos(documentos, fecha_extraccion)
    direcciones = inyector.direcciones(direcciones)
    cuentas = inyector.cuentas(cuentas)
    movimientos = inyector.movimientos(movimientos)
    saldos = inyector.saldos(saldos)
    prestamos = inyector.prestamos(prestamos)
    plazos = inyector.plazos_fijos(plazos)
    mandatos = inyector.mandatos(mandatos)

    datos = {
        "clientes": clientes, "documentos": documentos, "direcciones": direcciones,
        "cuentas": cuentas, "saldos": saldos, "movimientos": movimientos,
        "prestamos": prestamos, "cuotas": cuotas, "plazos_fijos": plazos,
        "mandatos": mandatos, "plan_cuentas": plan_cuentas, "saldos_contables": saldos_contables,
    }
    conteos = {}
    tamanos = {}
    for entidad in ENTIDADES_LEGADO:
        diseno = _diseno(entidad)
        ruta = rutas.LEGADO / diseno.archivo
        conteos[entidad] = diseno.escribir(datos[entidad], ruta)
        tamanos[entidad] = ruta.stat().st_size

    verdad = pd.DataFrame(inyector.verdad + desfases)
    verdad.to_csv(rutas.VERDAD / "defectos_inyectados.csv", index=False)

    cuentas_delta, movs_delta, saldos_delta = mod_delta.generar_delta(
        cuentas, saldos, config, rng, fecha_delta
    )
    conteos["delta_cuentas"] = _escribir_delta("cuentas", cuentas_delta, "cuentas_delta.dat")
    conteos["delta_movimientos"] = _escribir_delta(
        "movimientos", movs_delta, "movimientos_delta.dat"
    )
    conteos["delta_saldos"] = _escribir_delta("saldos", saldos_delta, "saldos_delta.dat")

    resumen = {
        "escala": escala,
        "fecha_extraccion": str(fecha_extraccion),
        "fecha_delta": str(fecha_delta),
        "segundos_generacion": round(time.time() - inicio, 1),
        "registros": conteos,
        "archivos_bytes": tamanos,
        "defectos_inyectados": {
            str(clave): int(valor)
            for clave, valor in verdad["tipo_defecto"].value_counts().items()
        },
        "total_registros_legado": int(sum(conteos[e] for e in ENTIDADES_LEGADO)),
    }
    with open(rutas.RESULTADOS / "resumen_generacion.json", "w", encoding="utf-8") as archivo:
        json.dump(resumen, archivo, ensure_ascii=False, indent=2)
    return resumen


def _escribir_delta(entidad: str, df: pd.DataFrame, nombre: str) -> int:
    diseno = _diseno(entidad)
    return diseno.escribir(df, rutas.LEGADO_DELTA / nombre)


def main() -> int:
    """Punto de entrada por linea de comandos."""
    analizador = argparse.ArgumentParser(description="Genera la extraccion sintetica del legado.")
    analizador.add_argument("--escala", default="completa", choices=["completa", "piloto", "humo"])
    argumentos = analizador.parse_args()
    resumen = generar(argumentos.escala)
    print(f"Generacion '{argumentos.escala}' completada en {resumen['segundos_generacion']} s.")
    for entidad, cantidad in resumen["registros"].items():
        print(f"  {entidad:<20} {cantidad:>10,} registros")
    print(f"  defectos inyectados: {sum(resumen['defectos_inyectados'].values())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
