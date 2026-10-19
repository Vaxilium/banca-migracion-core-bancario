"""Generacion de movimientos historicos y saldos coherentes del legado."""

from datetime import date, timedelta

import numpy as np
import pandas as pd

from src.comun.fechas import aammdd_desde_fecha
from src.generacion.cuentas import PISO_SALDO, SALDO_MEDIO

PORCENTAJE_CREDITO = {
    "CA": 0.45, "CC": 0.50, "CJ": 0.50, "CI": 0.50, "TR": 0.50, "XX": 0.50,
}

CODIGOS_CREDITO = ("01", "03", "05", "07")
PESOS_CREDITO = (0.55, 0.25, 0.10, 0.10)
CODIGOS_DEBITO = ("02", "04", "06", "08", "09")
PESOS_DEBITO = (0.45, 0.30, 0.12, 0.08, 0.05)
PESOS_DEBITO_CC = (0.35, 0.30, 0.22, 0.08, 0.05)

DESCRIPCIONES = {
    "01": "DEPOSITO",
    "02": "EXTRACCION",
    "03": "TRF REC",
    "04": "TRF ENV",
    "05": "PAGO CUOTA",
    "06": "COMISION",
    "07": "INTERES",
    "08": "DEB AUTO",
    "09": "PAGO SERV",
}

CANALES = ("VE", "AT", "IB", "MO")
PESOS_CANAL = (0.25, 0.35, 0.25, 0.15)


def _importes_y_signos(
    productos: np.ndarray, rng: np.random.Generator
) -> tuple[np.ndarray, np.ndarray]:
    cantidad = len(productos)
    importes = rng.lognormal(np.log(1500.0), 1.2, cantidad)
    grandes = rng.random(cantidad) < 0.05
    importes = np.where(grandes, importes * 10, importes)
    importes = np.round(importes, 2)
    p_credito = np.array([PORCENTAJE_CREDITO[p] for p in productos])
    signos = np.where(rng.random(cantidad) < p_credito, 1.0, -1.0)
    return importes * signos, signos


def _codigos_operacion(productos: np.ndarray, signos: np.ndarray, rng: np.random.Generator):
    cantidad = len(productos)
    codigos = np.empty(cantidad, dtype=object)
    credito = signos > 0
    for producto in np.unique(productos):
        for es_credito in (True, False):
            mascara = (productos == producto) & (credito == es_credito)
            total = int(mascara.sum())
            if not total:
                continue
            if es_credito:
                opciones, pesos = CODIGOS_CREDITO, PESOS_CREDITO
            elif producto == "CC":
                opciones, pesos = CODIGOS_DEBITO, PESOS_DEBITO_CC
            else:
                opciones, pesos = CODIGOS_DEBITO, PESOS_DEBITO
            codigos[mascara] = rng.choice(opciones, total, p=pesos)
    return codigos


def _horas(canales: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    horas = rng.integers(8, 20, len(canales))
    minutos = rng.integers(0, 60, len(canales))
    horario_comercial = canales == "VE"
    horas = np.where(horario_comercial, horas, rng.integers(0, 24, len(canales)))
    return (horas.astype(int) * 100 + minutos.astype(int)).astype(int)


def generar_movimientos_y_saldos(
    cuentas: pd.DataFrame,
    config_productos: dict,
    rng: np.random.Generator,
    fecha_extraccion: date,
    tope_movimientos: int,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, str]]:
    """Genera movimientos y saldos con coherencia saldo = apertura + movimientos.

    Devuelve (movimientos, saldos, fecha_ultimo_movimiento por cuenta).
    Las cuentas cerradas no tienen movimientos y quedan en cero.
    """
    activas = cuentas[cuentas["estado_cuenta"] != "C"].reset_index(drop=True)
    productos = activas["codigo_producto"].to_numpy()
    medias = config_productos["cuentas"]["movimientos_medios"]
    medias_vec = np.array([medias[p] for p in productos], dtype=float)
    n_movs = rng.poisson(medias_vec)
    n_movs = np.minimum(n_movs, 60)
    if n_movs.sum() > tope_movimientos:
        n_movs = (n_movs * (tope_movimientos / n_movs.sum())).astype(int)

    base = np.array(
        [rng.lognormal(np.log(SALDO_MEDIO[p]), 0.9) for p in productos], dtype=float
    )
    cuentas_rep = np.repeat(np.arange(len(activas)), n_movs)
    total = len(cuentas_rep)
    importes, signos = _importes_y_signos(productos[cuentas_rep], rng)
    codigos = _codigos_operacion(productos[cuentas_rep], signos, rng)
    canales = rng.choice(CANALES, total, p=PESOS_CANAL)
    sucursales = rng.integers(1, 351, total)
    horas = _horas(canales, rng)
    offsets = rng.integers(0, 366, total)
    totales = np.bincount(cuentas_rep, weights=importes, minlength=len(activas))
    saldo_final = base + totales
    pisos = np.array([PISO_SALDO[p] for p in productos])
    deficit = np.maximum(0.0, pisos - saldo_final)
    base = np.round(base + deficit, 2)
    saldo_final = np.round(saldo_final + deficit, 2)

    orden = np.lexsort((horas, offsets, cuentas_rep))
    cuentas_rep = cuentas_rep[orden]
    importes = importes[orden]
    codigos = codigos[orden]
    canales = canales[orden]
    horas = horas[orden]
    offsets = offsets[orden]
    sucursales = sucursales[orden]

    acumulado = np.cumsum(importes)
    indices_inicio = np.searchsorted(cuentas_rep, np.arange(len(activas)), side="left")
    tiene_movs = n_movs > 0
    cum_inicial = np.zeros(len(activas))
    cum_inicial[tiene_movs] = (
        acumulado[indices_inicio[tiene_movs]] - importes[indices_inicio[tiene_movs]]
    )
    base_rep = base[cuentas_rep]
    saldo_despues = np.round(base_rep + acumulado - cum_inicial[cuentas_rep], 2)

    fecha_base = np.datetime64(fecha_extraccion)
    fechas = fecha_base - 365 + offsets
    fechas_str = pd.to_datetime(fechas).strftime("%y%m%d").to_numpy()

    id_movimiento = np.arange(1, total + 1)
    movimientos = pd.DataFrame(
        {
            "tipo_registro": "M",
            "id_movimiento": id_movimiento,
            "id_cuenta": activas["id_cuenta"].to_numpy()[cuentas_rep],
            "fecha_movimiento": fechas_str,
            "hora_movimiento": horas,
            "codigo_operacion": codigos,
            "canal": canales,
            "importe": importes,
            "saldo_despues": saldo_despues,
            "numero_comprobante": (id_movimiento + 700000000),
            "descripcion": [DESCRIPCIONES[c] for c in codigos],
            "sucursal": sucursales,
        }
    )

    saldos = pd.DataFrame(
        {
            "tipo_registro": "S",
            "id_cuenta": activas["id_cuenta"].to_numpy(),
            "moneda": activas["moneda"].to_numpy(),
            "saldo_apertura": base,
            "saldo_final": saldo_final,
            "fecha_saldo": aammdd_desde_fecha(fecha_extraccion),
        }
    )
    cerradas = cuentas[cuentas["estado_cuenta"] == "C"]
    if len(cerradas):
        saldos_cerradas = pd.DataFrame(
            {
                "tipo_registro": "S",
                "id_cuenta": cerradas["id_cuenta"].to_numpy(),
                "moneda": cerradas["moneda"].to_numpy(),
                "saldo_apertura": 0.0,
                "saldo_final": 0.0,
                "fecha_saldo": aammdd_desde_fecha(fecha_extraccion),
            }
        )
        saldos = pd.concat([saldos, saldos_cerradas], ignore_index=True)

    ultimo = {}
    for indice in np.where(tiene_movs)[0]:
        inicio = indices_inicio[indice]
        fin = indices_inicio[indice + 1] if indice + 1 < len(activas) else total
        if fin > inicio:
            offset_max = offsets[fin - 1]
            fecha_mov = fecha_extraccion - timedelta(days=365 - int(offset_max))
            ultimo[activas["id_cuenta"].iloc[indice]] = aammdd_desde_fecha(fecha_mov)
    return movimientos, saldos, ultimo
