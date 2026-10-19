"""Conciliacion integral por ensayo de migracion (fase 7).

Recorre los ensayos registrados en datos/resultados, contrasta los volumenes
cargados contra el legado y los rechazos, reconcilia saldos y movimientos,
detecta descuadres de saldo, recompone el libro mayor y aplica los ajustes
contables del ensayo aprobado. Deja evidencia en JSON y CSV bajo
datos/resultados/conciliacion.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from src.comun.rutas import (
    BITACORA,
    CONCILIACION,
    CONFIG,
    DESTINO,
    LEGADO,
    LEGADO_DELTA,
    RESULTADOS,
)
from src.comun.yaml_util import cargar_yaml
from src.migracion import extraccion, reglas
from src.migracion.extraccion import ARCHIVOS_DELTA

VERSIONES = (1, 2, 3)
ID_DELTA = 2_000_000_000
CODIGOS_DEBITO = frozenset({"02", "04", "06", "08", "09"})
PREFIJOS_PRODUCTO = {
    "01": "CA",
    "02": "CC",
    "03": "CJ",
    "04": "CI",
    "09": "TR",
    "00": "XX",
}
PARAMETROS = cargar_yaml(CONFIG / "reglas" / "conciliacion.yaml")
TOLERANCIA_MONTO = float(PARAMETROS["tolerancias"]["monetaria"])
TOLERANCIA_AJUSTE = float(PARAMETROS["tolerancias"]["ajuste_automatico"])
CONTRAPARTIDA = str(PARAMETROS["contrapartida_ajustes"])

ENTIDADES = (
    ("clientes", "cliente", "id_cliente", "unicos"),
    ("documentos", "documento_cliente", "id_documento", "filas"),
    ("direcciones", "domicilio_cliente", "id_domicilio", "filas"),
    ("cuentas", "cuenta", "id_cuenta", "unicos"),
    ("saldos", "saldo_cuenta", "id_cuenta", "unicos"),
    ("movimientos", "movimiento", "id_movimiento", "unicos"),
    ("prestamos", "prestamo", "id_prestamo", "unicos"),
    ("cuotas", "cuota_prestamo", None, "filas"),
    ("plazos_fijos", "plazo_fijo", "id_plazo", "unicos"),
    ("mandatos", "mandato_debito", "id_mandato", "unicos"),
    ("plan_cuentas", "cuenta_contable", "codigo_contable", "unicos"),
    ("saldos_contables", "saldo_contable", "codigo_contable", "unicos"),
)


def _limpiar_texto(df: pd.DataFrame) -> pd.DataFrame:
    """Recorta espacios de todas las columnas de texto del registro crudo."""
    for columna in df.columns:
        if df[columna].dtype == object:
            df[columna] = df[columna].astype("string").str.strip()
    return df


def _importes(df: pd.DataFrame, columna: str, destino: str = "valor") -> None:
    """Convierte un campo de importe del legado y lo agrega al DataFrame."""
    df[destino], _ = reglas.convertir_importes(df[columna])


def cargar_legado() -> dict[str, pd.DataFrame]:
    """Lee el legado completo y normaliza las columnas que se concilian."""
    datos = {}
    for entidad in (
        "saldos",
        "cuentas",
        "movimientos",
        "prestamos",
        "cuotas",
        "plazos_fijos",
    ):
        crudo, _ = extraccion.leer_entidad(entidad, LEGADO)
        datos[entidad] = _limpiar_texto(crudo)
    _importes(datos["saldos"], "saldo_apertura", "apertura")
    _importes(datos["saldos"], "saldo_final", "final")
    _importes(datos["movimientos"], "importe", "importe")
    _importes(datos["prestamos"], "saldo_capital", "saldo_capital")
    _importes(datos["cuotas"], "capital", "capital")
    _importes(datos["plazos_fijos"], "monto_capital", "monto_capital")
    datos["saldos"]["id_cuenta"] = datos["saldos"]["id_cuenta"].astype("int64")
    datos["cuentas"]["id_cuenta"] = datos["cuentas"]["id_cuenta"].astype("int64")
    datos["movimientos"]["id_cuenta"] = datos["movimientos"]["id_cuenta"].astype("int64")
    datos["movimientos"]["id_movimiento"] = datos["movimientos"]["id_movimiento"].astype("int64")
    datos["prestamos"]["id_prestamo"] = datos["prestamos"]["id_prestamo"].astype("int64")
    datos["cuotas"]["id_prestamo"] = datos["cuotas"]["id_prestamo"].astype("int64")
    datos["plazos_fijos"]["id_plazo"] = datos["plazos_fijos"]["id_plazo"].astype("int64")
    return datos


def cargar_delta() -> dict[str, pd.DataFrame]:
    """Lee los archivos de la delta del corte y normaliza identificadores."""
    cuentas, _ = extraccion.leer_entidad("cuentas", LEGADO_DELTA, ARCHIVOS_DELTA["cuentas"])
    saldos, _ = extraccion.leer_entidad("saldos", LEGADO_DELTA, ARCHIVOS_DELTA["saldos"])
    movimientos, _ = extraccion.leer_entidad(
        "movimientos", LEGADO_DELTA, ARCHIVOS_DELTA["movimientos"]
    )
    for df in (cuentas, saldos, movimientos):
        _limpiar_texto(df)
    _importes(saldos, "saldo_final", "final")
    _importes(movimientos, "importe", "importe")
    cuentas["id_cuenta"] = cuentas["id_cuenta"].astype("int64")
    saldos["id_cuenta"] = saldos["id_cuenta"].astype("int64")
    movimientos["id_cuenta"] = movimientos["id_cuenta"].astype("int64")
    movimientos["id_movimiento"] = movimientos["id_movimiento"].astype("int64")
    return {"cuentas": cuentas, "saldos": saldos, "movimientos": movimientos}


def _resumen(version: int) -> dict:
    ruta = RESULTADOS / f"resumen_ensayo_v{version}.json"
    return json.loads(ruta.read_text("utf-8"))


def _rechazos(version: int) -> pd.DataFrame:
    ruta = RESULTADOS / f"rechazos_ensayo_v{version}.csv"
    return pd.read_csv(ruta, dtype=str).fillna("")


def _bitacora(version: int) -> pd.DataFrame:
    ruta = BITACORA / f"bitacora_ensayo_v{version}.csv"
    return pd.read_csv(ruta, dtype=str).fillna("")


def _parquet(version: int, tabla: str) -> str:
    return str(DESTINO / f"ensayo_v{version}" / f"{tabla}.parquet")


def _consulta(con: duckdb.DuckDBPyConnection, sql: str):
    return con.execute(sql).fetchone()[0]


def _ids_destino(con: duckdb.DuckDBPyConnection, version: int, tabla: str, columna: str):
    serie = con.execute(
        f"SELECT DISTINCT CAST({columna} AS VARCHAR) AS clave "
        f"FROM read_parquet('{_parquet(version, tabla)}')"
    ).df()["clave"]
    return set(serie.astype(str))


def _filas_destino(con: duckdb.DuckDBPyConnection, version: int, tabla: str) -> int:
    return _consulta(con, f"SELECT count(*) FROM read_parquet('{_parquet(version, tabla)}')")


def conciliar_conteos(
    version: int,
    con: duckdb.DuckDBPyConnection,
    resumen: dict,
    rechazos: pd.DataFrame,
    bitacora: pd.DataFrame,
    ids_legado: set[str],
) -> dict:
    """Cierra la ecuacion origen = cargados + no cargados + fusionados por entidad."""
    fusionados = int(
        ((bitacora["entidad"] == "clientes") & (bitacora["accion"] == "fusion_cliente")).sum()
    )
    filas = []
    for entidad, tabla, columna, modo in ENTIDADES:
        origen = int(resumen["por_entidad"][entidad]["filas_origen"])
        if entidad in ("cuentas", "saldos"):
            cargados = len(_ids_destino(con, version, tabla, columna) & ids_legado)
        elif entidad == "movimientos":
            cargados = _consulta(
                con,
                f"SELECT count(*) FROM read_parquet('{_parquet(version, tabla)}') "
                f"WHERE {columna} < {ID_DELTA}",
            )
        else:
            cargados = _filas_destino(con, version, tabla)

        rechazo = rechazos[rechazos["entidad"] == entidad].copy()
        if entidad == "clientes":
            revisados = int((rechazo["destino"] == "revision").sum())
            rechazo = rechazo[rechazo["destino"] == "rechazo"]
            no_cargados = len(rechazo)
        elif modo == "filas" or columna is None:
            no_cargados = len(rechazo)
            revisados = 0
        else:
            destino = _ids_destino(con, version, tabla, columna)
            claves = set(rechazo["clave"].astype(str))
            no_cargados = len(claves - destino)
            revisados = len(claves & destino)

        diferencia = origen - cargados - no_cargados - (fusionados if entidad == "clientes" else 0)
        motivos: dict[str, int] = {}
        for motivo, grupo in rechazo.groupby("motivo"):
            motivos[str(motivo)] = len(grupo)
        filas.append(
            {
                "entidad": entidad,
                "origen": origen,
                "cargados": cargados,
                "no_cargados": no_cargados,
                "fusionados": fusionados if entidad == "clientes" else 0,
                "revisados_cargados": revisados,
                "diferencia": diferencia,
                "motivos": motivos,
            }
        )
    return {"filas": filas, "cuadra": all(fila["diferencia"] == 0 for fila in filas)}


def conciliar_saldos(
    version: int,
    con: duckdb.DuckDBPyConnection,
    legado: dict[str, pd.DataFrame],
    delta: dict[str, pd.DataFrame],
    activa_delta: bool,
) -> dict:
    """Compara cada saldo cargado contra el legado o el archivo de la delta."""
    saldos = legado["saldos"][["id_cuenta", "apertura", "final"]].rename(
        columns={"final": "esperado"}
    )
    esperado = dict(zip(saldos["id_cuenta"], saldos["esperado"], strict=False))
    if activa_delta:
        delta_saldos = delta["saldos"][["id_cuenta", "final"]]
        esperado.update(dict(zip(delta_saldos["id_cuenta"], delta_saldos["final"], strict=False)))
    cargados = con.execute(
        f"SELECT id_cuenta, saldo_apertura, saldo_final "
        f"FROM read_parquet('{_parquet(version, 'saldo_cuenta')}')"
    ).df()
    cargados["esperado"] = cargados["id_cuenta"].map(esperado)
    sin_esperado = int(cargados["esperado"].isna().sum())
    cargados["diferencia"] = cargados["saldo_final"] - cargados["esperado"]
    diferencias = sin_esperado + int((cargados["diferencia"].abs() > TOLERANCIA_MONTO).sum())
    resumen_delta = {"activa": bool(activa_delta)}
    if activa_delta:
        ids_legado = set(legado["cuentas"]["id_cuenta"].tolist())
        ids_cargados = set(cargados["id_cuenta"].tolist())
        ids_delta = set(delta["saldos"]["id_cuenta"].tolist())
        existentes = ids_delta & ids_legado
        resumen_delta.update(
            {
                "cuentas_nuevas": len(ids_cargados - ids_legado),
                "cuentas_actualizadas": len(ids_cargados & existentes),
                "saldos_reemplazados": len(ids_cargados & existentes),
                "saldos_descartados": len(existentes - ids_cargados),
                "movimientos_nuevos": int(
                    _consulta(
                        con,
                        f"SELECT count(*) FROM read_parquet("
                        f"'{_parquet(version, 'movimiento')}') "
                        f"WHERE id_movimiento >= {ID_DELTA}",
                    )
                ),
            }
        )
    return {
        "filas": len(cargados),
        "sin_esperado": sin_esperado,
        "diferencias": diferencias,
        "monto_cargado": float(cargados["saldo_final"].sum()),
        "monto_esperado": float(cargados["esperado"].sum()),
        "diferencia_monto": float(cargados["diferencia"].sum()),
        "delta": resumen_delta,
    }


def reconstruir_movimientos(legado: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Depura duplicados de reproceso y normaliza el signo de los debitos."""
    movimientos = legado["movimientos"].copy()
    clave = (
        movimientos["id_cuenta"].astype(str)
        + "|"
        + movimientos["fecha_movimiento"]
        + "|"
        + movimientos["hora_movimiento"]
        + "|"
        + movimientos["codigo_operacion"]
        + "|"
        + movimientos["importe"].astype(str)
        + "|"
        + movimientos["numero_comprobante"]
    )
    movimientos["duplicado"] = clave.duplicated(keep="first")
    movimientos["signo_invertido"] = (
        ~movimientos["duplicado"]
        & movimientos["codigo_operacion"].isin(CODIGOS_DEBITO)
        & (movimientos["importe"] > 0)
    )
    movimientos["importe_original"] = movimientos["importe"]
    movimientos.loc[movimientos["signo_invertido"], "importe_original"] = -movimientos["importe"]
    movimientos.loc[movimientos["duplicado"], "importe_original"] = 0.0
    return movimientos


def conciliar_movimientos(
    version: int,
    con: duckdb.DuckDBPyConnection,
    legado: dict[str, pd.DataFrame],
    delta: dict[str, pd.DataFrame],
    movimientos: pd.DataFrame,
    activa_delta: bool,
    resumen: dict,
) -> dict:
    """Verifica importe a importe los movimientos cargados y el efecto de la delta."""
    correccion = bool(resumen["parametros"]["correccion_signos"])
    originales = movimientos[["id_movimiento", "importe", "importe_original"]].copy()
    originales["esperado"] = originales["importe"]
    if correccion:
        invertidos = movimientos["signo_invertido"]
        originales.loc[invertidos, "esperado"] = -originales.loc[invertidos, "importe"]
    esperado = dict(zip(originales["id_movimiento"], originales["esperado"], strict=False))
    cargados = con.execute(
        f"SELECT id_movimiento, importe FROM read_parquet("
        f"'{_parquet(version, 'movimiento')}') WHERE id_movimiento < {ID_DELTA}"
    ).df()
    cargados["esperado"] = cargados["id_movimiento"].map(esperado)
    diferencias = int(((cargados["importe"] - cargados["esperado"]).abs() > TOLERANCIA_MONTO).sum())
    signos_cargados = int(
        (
            movimientos["signo_invertido"]
            & movimientos["id_movimiento"].isin(set(cargados["id_movimiento"]))
        ).sum()
    )
    resultado = {
        "filas_verificadas": len(cargados),
        "diferencias": diferencias,
        "signos_invertidos_legado": int(
            (movimientos["signo_invertido"] & ~movimientos["duplicado"]).sum()
        ),
        "signos_sin_corregir_cargados": 0 if correccion else signos_cargados,
        "duplicados_legado": int(movimientos["duplicado"].sum()),
        "correccion_signos": correccion,
    }
    if activa_delta:
        delta_movs = delta["movimientos"][["id_movimiento", "importe"]]
        delta_esperado = dict(zip(delta_movs["id_movimiento"], delta_movs["importe"], strict=False))
        nuevos = con.execute(
            f"SELECT id_movimiento, importe FROM read_parquet("
            f"'{_parquet(version, 'movimiento')}') WHERE id_movimiento >= {ID_DELTA}"
        ).df()
        nuevos["esperado"] = nuevos["id_movimiento"].map(delta_esperado)
        resultado["delta"] = {
            "filas_verificadas": len(nuevos),
            "diferencias": int(
                ((nuevos["importe"] - nuevos["esperado"]).abs() > TOLERANCIA_MONTO).sum()
            ),
        }
    return resultado


def calcular_descuadres(legado: dict[str, pd.DataFrame], movimientos: pd.DataFrame) -> pd.DataFrame:
    """Reconstruye la suma original de movimientos y el descuadre por cuenta."""
    sumas = movimientos.groupby("id_cuenta")["importe_original"].sum()
    saldos = legado["saldos"][["id_cuenta", "apertura", "final"]].copy()
    saldos["suma_movimientos"] = saldos["id_cuenta"].map(sumas).fillna(0.0)
    saldos["descuadre"] = (saldos["final"] - saldos["apertura"] - saldos["suma_movimientos"]).round(
        2
    )
    saldos["abs_descuadre"] = saldos["descuadre"].abs()
    return saldos


def conciliar_descuadres(
    version: int,
    con: duckdb.DuckDBPyConnection,
    saldos: pd.DataFrame,
    activa_delta: bool,
    delta: dict[str, pd.DataFrame],
) -> tuple[dict, pd.DataFrame]:
    """Clasifica los descuadres de las cuentas efectivamente cargadas."""
    ids_cargados = set(
        con.execute(
            f"SELECT CAST(id_cuenta AS VARCHAR) AS clave FROM read_parquet("
            f"'{_parquet(version, 'cuenta')}')"
        )
        .df()["clave"]
        .astype(str)
        .tolist()
    )
    ids_cargados = {int(valor) for valor in ids_cargados}
    ids_delta: set[int] = set()
    if activa_delta:
        ids_delta = set(delta["saldos"]["id_cuenta"].tolist())
    analizadas = saldos[saldos["id_cuenta"].isin(ids_cargados - ids_delta)].copy()
    con_descuadre = analizadas[analizadas["abs_descuadre"] > TOLERANCIA_MONTO].copy()
    con_descuadre["clasificacion"] = np.where(
        con_descuadre["abs_descuadre"] <= TOLERANCIA_AJUSTE,
        "ajuste_automatico",
        "revision_manual",
    )
    con_descuadre["ajuste_apertura"] = np.where(
        con_descuadre["clasificacion"] == "ajuste_automatico",
        con_descuadre["descuadre"],
        0.0,
    )
    con_descuadre = con_descuadre.sort_values("abs_descuadre", ascending=False)
    resumen = {
        "cuentas_analizadas": len(analizadas),
        "cuentas_excluidas_delta": len(ids_delta & ids_cargados),
        "cuentas_descuadradas": len(con_descuadre),
        "ajustes_automaticos": int((con_descuadre["clasificacion"] == "ajuste_automatico").sum()),
        "revision_manual": int((con_descuadre["clasificacion"] == "revision_manual").sum()),
        "monto_descuadre": float(con_descuadre["descuadre"].sum()),
        "monto_absoluto": float(con_descuadre["abs_descuadre"].sum()),
        "monto_ajustado": float(con_descuadre["ajuste_apertura"].sum()),
        "monto_revision": float(
            con_descuadre.loc[
                con_descuadre["clasificacion"] == "revision_manual", "descuadre"
            ].sum()
        ),
    }
    return resumen, con_descuadre


def conciliar_contable(
    version: int,
    con: duckdb.DuckDBPyConnection,
    legado: dict[str, pd.DataFrame],
    saldos: pd.DataFrame,
    resumen: dict,
    tipo_cuenta: dict[str, str],
    nombres: dict[str, str],
) -> tuple[dict, pd.DataFrame]:
    """Recompone el libro mayor desde cuentas, prestamos y plazos y compara."""
    cuentas = legado["cuentas"].copy()
    cuentas["producto_original"] = (
        cuentas["id_cuenta"].astype(str).str.zfill(10).str[:2].map(PREFIJOS_PRODUCTO)
    )
    vigentes = cuentas[cuentas["estado_cuenta"] != "C"][["id_cuenta", "producto_original"]]
    union = saldos[["id_cuenta", "apertura", "suma_movimientos"]].merge(
        vigentes, on="id_cuenta", how="left"
    )
    union["saldo_original"] = (union["apertura"] + union["suma_movimientos"]).round(2)
    totales = union.groupby("producto_original")["saldo_original"].sum()
    depositos = float(
        totales.get("CA", 0) + totales.get("CC", 0) + totales.get("CJ", 0) + totales.get("CI", 0)
    )
    cuotas = legado["cuotas"]
    pendientes = cuotas[cuotas["estado_cuota"].ne("C")].groupby("id_prestamo")["capital"].sum()
    prestamos = legado["prestamos"]
    capital_por_prestamo = prestamos["id_prestamo"].map(pendientes).fillna(0.0)
    capital_esperado = float(capital_por_prestamo.sum())
    desvio = (prestamos["saldo_capital"] - capital_por_prestamo).abs()
    umbral_desvio = np.maximum(0.01, capital_por_prestamo * 0.002)
    plazos = legado["plazos_fijos"]
    plazos_vigentes = float(
        plazos.loc[plazos["estado_plazo"].isin(["V", "R"]), "monto_capital"].sum()
    )
    valores = {
        "2.1.01": float(totales.get("CA", 0.0)),
        "2.1.02": float(totales.get("CC", 0.0)),
        "2.1.03": plazos_vigentes,
        "2.1.04": float(totales.get("CJ", 0.0)),
        "2.1.05": float(totales.get("CI", 0.0)),
        "1.2.01": capital_esperado,
        "1.1.01": round(depositos * 0.08, 2),
        "1.2.03": round(capital_esperado * 0.004, 2),
        "3.1.01": round(depositos * 0.12, 2),
    }
    cargado = con.execute(
        f"SELECT codigo_contable, saldo_debe, saldo_haber, saldo_final "
        f"FROM read_parquet('{_parquet(version, 'saldo_contable')}')"
    ).df()
    cargado["codigo_contable"] = cargado["codigo_contable"].astype(str).str.strip()
    cargado["esperado"] = cargado["codigo_contable"].map(
        lambda codigo: round(valores.get(codigo, 0.0), 2)
    )
    signo = cargado["codigo_contable"].map(
        lambda codigo: 1 if tipo_cuenta.get(codigo) == "A" else -1
    )
    cargado["esperado_final"] = cargado["esperado"] * signo
    cargado["diferencia"] = (cargado["saldo_final"] - cargado["esperado_final"]).round(2)
    cargado["abs_diferencia"] = cargado["diferencia"].abs()
    cargado["desbalance"] = (
        cargado["saldo_debe"] - cargado["saldo_haber"] - cargado["saldo_final"]
    ).abs()
    diferencias = cargado[cargado["abs_diferencia"] > TOLERANCIA_MONTO].copy()
    diferencias["nombre_cuenta"] = diferencias["codigo_contable"].map(nombres)
    diferencias["tipo_cuenta"] = diferencias["codigo_contable"].map(tipo_cuenta)
    diferencias["contrapartida"] = CONTRAPARTIDA
    diferencias["ajuste"] = (diferencias["esperado_final"] - diferencias["saldo_final"]).round(2)
    aplica = bool(resumen["parametros"]["ajustes_contables"])
    diferencias["estado"] = "aplicado" if aplica else "pendiente"
    resumen_contable = {
        "filas": len(cargado),
        "conciliadas": len(cargado) - len(diferencias),
        "desfases": len(diferencias),
        "monto_desfase": float(diferencias["diferencia"].sum()),
        "monto_absoluto": float(diferencias["abs_diferencia"].sum()),
        "desbalances_internos": int((cargado["desbalance"] > TOLERANCIA_MONTO).sum()),
        "ajustes_aplicados": aplica,
        "monto_ajuste": float(diferencias["ajuste"].sum()),
        "contrapartida": CONTRAPARTIDA,
        "capital_prestamos_crudo": float(prestamos["saldo_capital"].sum()),
        "capital_prestamos_esperado": capital_esperado,
        "diferencia_prestamos": round(
            float(prestamos["saldo_capital"].sum()) - capital_esperado, 2
        ),
        "prestamos_incongruentes": int((desvio > umbral_desvio).sum()),
    }
    return resumen_contable, diferencias


def _plan_contable() -> tuple[dict[str, str], dict[str, str]]:
    from src.generacion.contabilidad import PLAN_CUENTAS

    tipos = {codigo: tipo for codigo, _nombre, tipo, _nivel, _padre in PLAN_CUENTAS}
    nombres = {codigo: nombre for codigo, nombre, _tipo, _nivel, _padre in PLAN_CUENTAS}
    return tipos, nombres


def evaluar_go_no_go(
    version: int,
    conteos: dict,
    saldos: dict,
    movimientos: dict,
    descuadres: dict,
    contable: dict,
    resumen: dict,
) -> dict:
    """Aplica los criterios de aceptacion del corte para el ensayo."""
    parametros = resumen["parametros"]
    criterios = [
        {
            "criterio": "Conteos por entidad",
            "resultado": "todas las ecuaciones cierran" if conteos["cuadra"] else "hay diferencias",
            "cumple": conteos["cuadra"],
        },
        {
            "criterio": "Saldos de cuentas",
            "resultado": f"{saldos['diferencias']} diferencias",
            "cumple": saldos["diferencias"] == 0,
        },
        {
            "criterio": "Movimientos",
            "resultado": f"{movimientos['diferencias']} diferencias",
            "cumple": movimientos["diferencias"] == 0,
        },
        {
            "criterio": "Deduplicacion de clientes",
            "resultado": "activa" if parametros["deduplicacion_clientes"] else "inactiva",
            "cumple": bool(parametros["deduplicacion_clientes"]),
        },
        {
            "criterio": "Correccion de signos",
            "resultado": (
                f"{movimientos['signos_sin_corregir_cargados']} movimientos sin corregir"
            ),
            "cumple": movimientos["signos_sin_corregir_cargados"] == 0,
        },
        {
            "criterio": "Descuadres de saldo",
            "resultado": (
                f"{descuadres['ajustes_automaticos']} ajustes automaticos, "
                f"{descuadres['revision_manual']} en revision manual"
            ),
            "cumple": descuadres["revision_manual"] == 0 or contable["ajustes_aplicados"],
        },
        {
            "criterio": "Ajustes contables",
            "resultado": (
                f"{contable['desfases']} ajustes aplicados"
                if contable["ajustes_aplicados"]
                else f"{contable['desfases']} desfases pendientes"
            ),
            "cumple": contable["desfases"] == 0 or contable["ajustes_aplicados"],
        },
    ]
    observaciones = []
    if not parametros["deduplicacion_clientes"]:
        observaciones.append("Carga sin deduplicacion de clientes duplicados.")
    if not parametros["correccion_signos"]:
        observaciones.append(
            f"{movimientos['signos_sin_corregir_cargados']} movimientos con signo "
            "invertido cargados en el destino."
        )
    if not parametros["ajustes_contables"]:
        observaciones.append(f"{contable['desfases']} desfases contables sin ajuste documentado.")
    if parametros["ajustes_contables"] and descuadres["revision_manual"]:
        observaciones.append(
            f"{descuadres['revision_manual']} descuadres graves derivados a revision manual "
            f"con evidencia en el archivo de ajustes."
        )
    cumple = all(criterio["cumple"] for criterio in criterios)
    if not cumple:
        decision = "NO-GO"
    elif not parametros["deduplicacion_clientes"] or not parametros["correccion_signos"]:
        decision = "NO-GO"
    elif observaciones:
        decision = "GO con observaciones"
    else:
        decision = "GO"
    return {"decision": decision, "criterios": criterios, "observaciones": observaciones}


def _numero(valor: float) -> float:
    return round(float(valor), 2)


def _volcar_csv(df: pd.DataFrame, ruta: Path, columnas: list[str]) -> None:
    salida = df[[columna for columna in columnas if columna in df.columns]].copy()
    for columna in salida.columns:
        if salida[columna].dtype.kind == "f":
            salida[columna] = salida[columna].round(2)
    salida.to_csv(ruta, index=False)


def ejecutar_ensayo(
    version: int,
    con: duckdb.DuckDBPyConnection,
    legado: dict[str, pd.DataFrame],
    delta: dict[str, pd.DataFrame],
    movimientos: pd.DataFrame,
    ids_legado: set[str],
) -> dict:
    """Conciliacion completa de un ensayo y escritura de su evidencia."""
    resumen = _resumen(version)
    rechazos = _rechazos(version)
    bitacora = _bitacora(version)
    activa_delta = isinstance(resumen.get("delta"), dict)
    conteos = conciliar_conteos(version, con, resumen, rechazos, bitacora, ids_legado)
    saldos = conciliar_saldos(version, con, legado, delta, activa_delta)
    movimientos_resumen = conciliar_movimientos(
        version, con, legado, delta, movimientos, activa_delta, resumen
    )
    saldos_cuenta = calcular_descuadres(legado, movimientos)
    descuadres, detalle_descuadres = conciliar_descuadres(
        version, con, saldos_cuenta, activa_delta, delta
    )
    tipos, nombres = _plan_contable()
    contable, detalle_contable = conciliar_contable(
        version, con, legado, saldos_cuenta, resumen, tipos, nombres
    )
    go_no_go = evaluar_go_no_go(
        version, conteos, saldos, movimientos_resumen, descuadres, contable, resumen
    )
    filas = {
        "tablas_cargadas": resumen["tablas_cargadas"],
        "total": int(sum(resumen["tablas_cargadas"].values())),
        "duracion_segundos": resumen.get("duracion_segundos", 0),
    }
    resultado = {
        "version": version,
        "nombre": resumen["nombre"],
        "delta": activa_delta,
        "parametros": resumen["parametros"],
        "filas": filas,
        "conteos": conteos,
        "saldos": saldos,
        "movimientos": movimientos_resumen,
        "descuadres": descuadres,
        "contable": contable,
        "go_no_go": go_no_go,
    }
    CONCILIACION.mkdir(parents=True, exist_ok=True)
    prefijo = CONCILIACION / f"conciliacion_ensayo_v{version}"
    prefijo.with_suffix(".json").write_text(
        json.dumps(resultado, indent=2, ensure_ascii=False, default=_numero) + "\n",
        encoding="utf-8",
    )
    _volcar_csv(
        detalle_descuadres,
        Path(f"{prefijo}_descuadres.csv"),
        [
            "id_cuenta",
            "saldo_apertura",
            "saldo_final",
            "suma_movimientos",
            "descuadre",
            "clasificacion",
            "ajuste_apertura",
        ],
    )
    _volcar_csv(
        detalle_contable,
        Path(f"{prefijo}_desfases.csv"),
        [
            "codigo_contable",
            "nombre_cuenta",
            "tipo_cuenta",
            "saldo_debe",
            "saldo_haber",
            "saldo_final",
            "esperado",
            "esperado_final",
            "diferencia",
            "ajuste",
            "contrapartida",
            "estado",
        ],
    )
    return resultado


def _seleccionar(arg_ensayo: str, todos: bool) -> list[int]:
    if todos or arg_ensayo == "todos":
        return list(VERSIONES)
    limpio = arg_ensayo.lower().replace("v", "")
    return [int(limpio)]


def main(argv: list[str] | None = None) -> int:
    """Ejecuta la conciliacion de uno o de todos los ensayos."""
    parser = argparse.ArgumentParser(description="Conciliacion de ensayos")
    parser.add_argument("--ensayo", default="todos", help="v1, v2, v3 o todos")
    parser.add_argument("--todos", action="store_true", help="concilia los tres ensayos")
    args = parser.parse_args(argv)
    versiones = _seleccionar(args.ensayo, args.todos)
    legado = cargar_legado()
    delta = cargar_delta()
    movimientos = reconstruir_movimientos(legado)
    ids_legado = set(legado["cuentas"]["id_cuenta"].astype(str))
    con = duckdb.connect()
    for version in versiones:
        resultado = ejecutar_ensayo(version, con, legado, delta, movimientos, ids_legado)
        go_no_go = resultado["go_no_go"]["decision"]
        conteos = sum(fila["diferencia"] for fila in resultado["conteos"]["filas"])
        print(
            f"ensayo v{version}: {go_no_go}; conteos={conteos}; "
            f"saldos={resultado['saldos']['diferencias']}; "
            f"movimientos={resultado['movimientos']['diferencias']}; "
            f"descuadres={resultado['descuadres']['cuentas_descuadradas']}; "
            f"desfases={resultado['contable']['desfases']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
