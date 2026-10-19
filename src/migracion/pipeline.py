"""Pipeline de migracion por ensayos: extraccion, transformacion y carga.

Uso:
    .venv/bin/python -m src.migracion.pipeline --ensayo todos
    .venv/bin/python -m src.migracion.pipeline --ensayo v3 --sin-delta

Cada ensayo queda en datos/destino/ensayo_v{n} como Parquet, con sus rechazos,
su bitacora y un resumen JSON con las cifras de la corrida.
"""

import argparse
import json
import time
from datetime import date

import pandas as pd

from src.comun.rutas import BITACORA, LEGADO, LEGADO_DELTA, RESULTADOS, asegurar_directorios
from src.comun.yaml_util import cargar_yaml
from src.migracion import carga, contratos, extraccion, reglas
from src.migracion.transformacion import Contexto, Transformador, catalogos_destino


def _fechas_config() -> tuple[date, date]:
    config = cargar_yaml(reglas.CONFIG / "parametrico" / "escala.yaml")
    return (
        date.fromisoformat(str(config["fecha_extraccion"])),
        date.fromisoformat(str(config["fecha_delta"])),
    )


def _leer_legado(entidades: list[str]) -> tuple[dict[str, pd.DataFrame], list[dict]]:
    crudo: dict[str, pd.DataFrame] = {}
    rechazos: list[dict] = []
    for entidad in entidades:
        crudo[entidad], registros = extraccion.leer_entidad(entidad, LEGADO)
        rechazos.extend(registros)
    return crudo, rechazos


def _escribir_rechazos(rechazos: list[dict], ruta) -> None:
    pd.DataFrame(rechazos).to_csv(ruta, index=False)


def _escribir_bitacora(bitacora: list[dict], ruta) -> None:
    pd.DataFrame(bitacora).to_csv(ruta, index=False)


def _metricas(
    crudo_principal: dict[str, pd.DataFrame],
    rechazos: list[dict],
    bitacora: list[dict],
    tablas: dict[str, int],
) -> dict:
    entidades = {}
    for entidad in crudo_principal:
        entidades[entidad] = {"filas_origen": len(crudo_principal[entidad])}
    for registro in rechazos:
        entidad = registro["entidad"]
        seccion = entidades.setdefault(entidad, {"filas_origen": 0})
        clave = "revisados" if registro["destino"] == "revision" else "rechazados"
        seccion[clave] = seccion.get(clave, 0) + 1
        motivos = seccion.setdefault("motivos", {})
        motivos[registro["motivo"]] = motivos.get(registro["motivo"], 0) + 1
    for registro in bitacora:
        entidad = registro["entidad"]
        seccion = entidades.setdefault(entidad, {"filas_origen": 0})
        acciones = seccion.setdefault("acciones", {})
        acciones[registro["accion"]] = acciones.get(registro["accion"], 0) + 1
    return {"por_entidad": entidades, "tablas_cargadas": tablas}


def procesar_ensayo(
    version: int,
    fecha_extraccion: date,
    fecha_delta: date,
    incluir_delta: bool = True,
    validar_contratos: bool = True,
) -> dict:
    """Ejecuta un ensayo completo y publica destino, rechazos y bitacora."""
    inicio = time.time()
    cfg = reglas.cargar_reglas(version)
    ctx = Contexto(
        version=version,
        reglas=cfg,
        catalogos=reglas.cargar_catalogos(),
        fecha_extraccion=fecha_extraccion,
        fecha_corte=fecha_extraccion,
        umbral=int(cfg["umbral_siglo"]),
    )
    entidades = sorted(extraccion.cargar_disenos())
    crudo, rechazos = _leer_legado(entidades)
    transformador = Transformador(ctx)
    destino = transformador.transformar_todo(crudo)
    rechazos.extend(transformador.registro.rechazos)
    bitacora = transformador.registro.bitacora

    tablas: dict[str, int] = {}
    for tabla, df in destino.items():
        tablas[tabla] = carga.escribir_tabla(df, tabla, version)
    for tabla, df in catalogos_destino(ctx, destino).items():
        tablas[f"catalogo_{tabla}"] = carga.escribir_tabla(df, f"catalogo_{tabla}", version)

    resumen = {
        "version": version,
        "nombre": cfg["nombre"],
        "parametros": {
            clave: cfg[clave]
            for clave in (
                "umbral_siglo",
                "deduplicacion_clientes",
                "validar_fechas_contextual",
                "correccion_signos",
                "extraccion_texto_libre",
                "ajustes_contables",
            )
        },
        "fecha_extraccion": fecha_extraccion.isoformat(),
        "fecha_delta": fecha_delta.isoformat(),
    }
    delta_info = {}
    if incluir_delta and version == 3:
        crudo_delta = {}
        rechazos_delta = []
        for entidad, archivo in extraccion.ARCHIVOS_DELTA.items():
            crudo_delta[entidad], registros = extraccion.leer_entidad(
                entidad, LEGADO_DELTA, archivo
            )
            rechazos_delta.extend(registros)
        ctx.fecha_corte = fecha_delta
        delta_transformador = Transformador(ctx)
        destino_delta = delta_transformador.transformar_delta(crudo_delta)
        rechazos_delta.extend(delta_transformador.registro.rechazos)
        _escribir_rechazos(rechazos_delta, RESULTADOS / f"rechazos_delta_v{version}.csv")
        _escribir_bitacora(
            delta_transformador.registro.bitacora,
            BITACORA / f"bitacora_delta_v{version}.csv",
        )
        for tabla, df in destino_delta.items():
            insertadas, reemplazadas = carga.incorporar_delta(df, tabla, version)
            delta_info[tabla] = {"insertadas": insertadas, "reemplazadas": reemplazadas}
            tablas[tabla] = carga.contar_tabla(tabla, version)
        resumen["delta"] = delta_info
    elif incluir_delta:
        resumen["delta"] = "solo el ensayo 3 carga la delta del corte"

    if validar_contratos:
        esquemas = contratos.generar_contratos()
        errores = []
        for tabla, contrato in esquemas.items():
            errores.extend(contratos.validar_muestra(tabla, destino[tabla], contrato))
        if errores:
            raise ValueError(
                f"contratos incumplidos en el ensayo {version}: {errores[:3]}"
            )
        resumen["contratos_validados"] = len(esquemas)

    _escribir_rechazos(rechazos, RESULTADOS / f"rechazos_ensayo_v{version}.csv")
    _escribir_bitacora(bitacora, BITACORA / f"bitacora_ensayo_v{version}.csv")
    resumen.update(_metricas(crudo, rechazos, bitacora, tablas))
    resumen["duracion_segundos"] = round(time.time() - inicio, 1)
    (RESULTADOS / f"resumen_ensayo_v{version}.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return resumen


def main() -> None:
    """CLI del pipeline de migracion por ensayos."""
    argumentos = argparse.ArgumentParser(description="Pipeline de migracion por ensayos")
    argumentos.add_argument(
        "--ensayo", choices=["v1", "v2", "v3", "todos"], default="todos"
    )
    argumentos.add_argument("--sin-delta", action="store_true")
    argumentos.add_argument("--sin-contratos", action="store_true")
    opciones = argumentos.parse_args()
    asegurar_directorios()
    fecha_extraccion, fecha_delta = _fechas_config()
    versiones = [1, 2, 3] if opciones.ensayo == "todos" else [int(opciones.ensayo[1])]
    for version in versiones:
        resumen = procesar_ensayo(
            version,
            fecha_extraccion,
            fecha_delta,
            incluir_delta=not opciones.sin_delta,
            validar_contratos=not opciones.sin_contratos,
        )
        cargadas = sum(resumen["tablas_cargadas"].values())
        print(
            f"ensayo v{version}: {cargadas} filas en destino, "
            f"{resumen.get('duracion_segundos')} s"
        )


if __name__ == "__main__":
    main()
