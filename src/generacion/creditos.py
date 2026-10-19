"""Generacion de prestamos con cronogramas, plazos fijos y mandatos."""

from datetime import date, timedelta

import numpy as np
import pandas as pd

from src.comun.fechas import aammdd_desde_fecha
from src.generacion.pools import SERVICIOS_MANDATO_REFERENCIA


def sumar_meses(fecha: date, meses: int) -> date:
    """Suma meses calendario fijando el dia en 28 para evitar fechas imposibles."""
    anio = fecha.year + (fecha.month - 1 + meses) // 12
    mes = (fecha.month - 1 + meses) % 12 + 1
    return date(anio, mes, min(fecha.day, 28))


def mapa_cuentas_debito(cuentas: pd.DataFrame) -> dict[int, str]:
    """Primera cuenta CA/CC vigente por cliente, para debitos."""
    filtro = cuentas[
        cuentas["codigo_producto"].isin(["CA", "CC"]) & (cuentas["estado_cuenta"] != "C")
    ]
    primera = filtro.sort_values("fecha_apertura").groupby("id_cliente").first()
    return primera["id_cuenta"].to_dict()


def _elegir_cuenta(
    cliente: int, mapa: dict[int, str], alternativas: np.ndarray, rng: np.random.Generator
) -> str:
    cuenta = mapa.get(int(cliente))
    if cuenta is None:
        cuenta = str(alternativas[int(rng.integers(0, len(alternativas)))])
    return cuenta


def _cronograma(
    monto: float, tasa_anual: float, plazo: int, fecha_otorgamiento: date,
    estado: str, rng: np.random.Generator,
) -> tuple[list[dict], float]:
    """Construye el cronograma en sistema frances y devuelve filas y saldo pendiente."""
    factor = tasa_anual / 100.0 / 12.0
    cuota = monto * factor / (1 - (1 + factor) ** (-plazo))
    saldo = monto
    filas = []
    for numero in range(1, plazo + 1):
        interes = round(saldo * factor, 2)
        capital = round(min(cuota - interes, saldo), 2)
        if numero == plazo:
            capital = round(saldo, 2)
        vencimiento = sumar_meses(fecha_otorgamiento, numero)
        vencida = vencimiento <= date(2026, 10, 9)
        estado_cuota = "P"
        fecha_pago = ""
        if estado == "CA":
            estado_cuota = "C"
            fecha_pago = aammdd_desde_fecha(vencimiento + timedelta(days=1))
        elif vencida:
            estado_cuota = "C"
            fecha_pago = aammdd_desde_fecha(vencimiento + timedelta(days=1))
        filas.append(
            {
                "numero_cuota": numero,
                "fecha_vencimiento": aammdd_desde_fecha(vencimiento),
                "capital": capital,
                "interes": interes,
                "total": round(capital + interes, 2),
                "estado_cuota": estado_cuota,
                "fecha_pago": fecha_pago,
            }
        )
        saldo = round(saldo - capital, 2)
    if estado in ("MO", "AT"):
        atrasadas = min(len(filas) - 1, 3 if estado == "MO" else 1)
        for fila in filas[::-1]:
            if fila["estado_cuota"] == "C" and atrasadas > 0:
                fila["estado_cuota"] = "V"
                fila["fecha_pago"] = ""
                atrasadas -= 1
            elif fila["estado_cuota"] == "P":
                break
    saldo_capital = round(sum(f["capital"] for f in filas if f["estado_cuota"] != "C"), 2)
    return filas, saldo_capital


def generar_prestamos(
    clientes: pd.DataFrame,
    cuentas: pd.DataFrame,
    config: dict,
    config_productos: dict,
    rng: np.random.Generator,
    fecha_extraccion: date,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Genera prestamos personales y sus cronogramas de cuotas."""
    cantidad = config["prestamos"]
    ids_clientes = rng.choice(clientes["id_cliente"].to_numpy(), cantidad, replace=False)
    mapa = mapa_cuentas_debito(cuentas)
    alternativas = cuentas["id_cuenta"].to_numpy()
    estados = config_productos["estados_prestamo"]
    plazos = np.array([6, 12, 18, 24, 36, 48])
    pesos_plazo = np.array([0.20, 0.25, 0.20, 0.15, 0.12, 0.08])
    prestamos = []
    cuotas = []
    inicio_posible = date(2021, 1, 1)
    for indice, cliente in enumerate(ids_clientes):
        id_prestamo = str(1000000000 + indice + 1)
        monto = float(np.round(rng.lognormal(np.log(300000.0), 0.8), 2))
        monto = float(np.clip(monto, 20000.0, 5000000.0))
        tasa = float(np.round(rng.uniform(
            config_productos["tasa_prestamo_min"], config_productos["tasa_prestamo_max"]
        ), 2))
        plazo = int(rng.choice(plazos, p=pesos_plazo))
        dias = int(rng.integers(0, (fecha_extraccion - inicio_posible).days - 60))
        otorgamiento = inicio_posible + timedelta(days=dias)
        estado = str(rng.choice(list(estados.keys()), p=list(estados.values())))
        filas, saldo_capital = _cronograma(monto, tasa, plazo, otorgamiento, estado, rng)
        pagadas = [f for f in filas if f["estado_cuota"] == "C"]
        primera_pendiente = next(
            (f["numero_cuota"] for f in filas if f["estado_cuota"] != "C"), plazo
        )
        ultimo_pago = max((f["fecha_pago"] for f in pagadas), default="")
        prestamos.append(
            {
                "tipo_registro": "P",
                "id_prestamo": id_prestamo,
                "id_cliente": int(cliente),
                "id_cuenta_debito": _elegir_cuenta(cliente, mapa, alternativas, rng),
                "codigo_producto": "PP",
                "moneda": "ARS",
                "fecha_otorgamiento": aammdd_desde_fecha(otorgamiento),
                "monto_original": monto,
                "saldo_capital": saldo_capital,
                "tasa_anual": tasa,
                "plazo_meses": plazo,
                "cantidad_cuotas": plazo,
                "cuota_actual": primera_pendiente,
                "estado_prestamo": estado,
                "fecha_ultimo_pago": ultimo_pago,
            }
        )
        for fila in filas:
            cuotas.append({"tipo_registro": "Q", "id_prestamo": id_prestamo, **fila})
    return pd.DataFrame(prestamos), pd.DataFrame(cuotas)


def generar_plazos_fijos(
    clientes: pd.DataFrame,
    cuentas: pd.DataFrame,
    config: dict,
    config_productos: dict,
    rng: np.random.Generator,
    fecha_extraccion: date,
) -> pd.DataFrame:
    """Genera depositos a plazo fijo con estados coherentes."""
    cantidad = config["plazos_fijos"]
    ids_clientes = rng.choice(clientes["id_cliente"].to_numpy(), cantidad, replace=False)
    mapa = mapa_cuentas_debito(cuentas)
    alternativas = cuentas["id_cuenta"].to_numpy()
    plazos_dias = np.array([30, 60, 90, 120, 180, 270, 365])
    filas = []
    for indice, cliente in enumerate(ids_clientes):
        dias_atras = int(rng.integers(10, 330))
        constitucion = fecha_extraccion - timedelta(days=dias_atras)
        plazo_dias = int(rng.choice(plazos_dias))
        vencimiento = constitucion + timedelta(days=plazo_dias)
        if vencimiento > fecha_extraccion:
            estado = "V"
        else:
            estado = str(rng.choice(["C", "R"], p=[0.4, 0.6]))
        filas.append(
            {
                "tipo_registro": "F",
                "id_plazo": str(2000000000 + indice + 1),
                "id_cliente": int(cliente),
                "id_cuenta_acredita": _elegir_cuenta(cliente, mapa, alternativas, rng),
                "codigo_producto": str(rng.choice(["PF", "PE"], p=[0.85, 0.15])),
                "moneda": "ARS",
                "fecha_constitucion": aammdd_desde_fecha(constitucion),
                "fecha_vencimiento": aammdd_desde_fecha(vencimiento),
                "monto_capital": float(np.round(rng.lognormal(np.log(150000.0), 1.0), 2)),
                "tasa_anual": float(np.round(rng.uniform(
                    config_productos["tasa_plazo_min"], config_productos["tasa_plazo_max"]
                ), 2)),
                "plazo_dias": plazo_dias,
                "estado_plazo": estado,
            }
        )
    return pd.DataFrame(filas)


def generar_mandatos(
    clientes: pd.DataFrame,
    cuentas: pd.DataFrame,
    config: dict,
    config_productos: dict,
    rng: np.random.Generator,
    fecha_extraccion: date,
) -> pd.DataFrame:
    """Genera mandatos de debito automatico (activos, suspendidos y de baja)."""
    cantidad = config["mandatos"]
    ids_clientes = rng.choice(clientes["id_cliente"].to_numpy(), cantidad, replace=False)
    mapa = mapa_cuentas_debito(cuentas)
    alternativas = cuentas["id_cuenta"].to_numpy()
    servicios = config_productos["servicios_mandato"]
    frecuencias = config_productos["frecuencias_mandato"]
    estados = config_productos["estados_mandato"]
    filas = []
    for indice, cliente in enumerate(ids_clientes):
        servicio = str(rng.choice(servicios))
        referencia = f"{SERVICIOS_MANDATO_REFERENCIA[servicio]} {int(rng.integers(1, 99999)):05d}"
        filas.append(
            {
                "tipo_registro": "N",
                "id_mandato": str(3000000000 + indice + 1),
                "id_cliente": int(cliente),
                "id_cuenta_debito": _elegir_cuenta(cliente, mapa, alternativas, rng),
                "codigo_servicio": servicio,
                "referencia_servicio": referencia,
                "importe_maximo": float(np.round(rng.lognormal(np.log(8000.0), 0.9), 2)),
                "fecha_alta": aammdd_desde_fecha(
                    fecha_extraccion - timedelta(days=int(rng.integers(30, 1100)))
                ),
                "estado_mandato": str(rng.choice(list(estados.keys()), p=list(estados.values()))),
                "frecuencia": str(rng.choice(frecuencias, p=[0.7, 0.15, 0.15])),
            }
        )
    return pd.DataFrame(filas)
