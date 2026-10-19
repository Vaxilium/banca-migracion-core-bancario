"""Generacion de cuentas y saldos sinteticos del legado."""

from datetime import date, timedelta

import numpy as np
import pandas as pd

from src.comun.fechas import aammdd_desde_fecha
from src.generacion.pools import CALLES

PREFIJOS_CUENTA = {"CA": "01", "CC": "02", "CJ": "03", "CI": "04", "TR": "09", "XX": "00"}

SALDO_MEDIO = {"CA": 25000, "CC": 18000, "CJ": 8000, "CI": 15000, "TR": 5000, "XX": 3000}

PISO_SALDO = {"CA": 0, "CC": -30000, "CJ": 0, "CI": 0, "TR": 0, "XX": 0}


def _fechas_apertura(rng: np.random.Generator, cantidad: int, fecha_extraccion: date):
    anios = np.arange(2000, 2027)
    pesos = np.linspace(0.4, 3.0, len(anios))
    pesos = pesos / pesos.sum()
    elegidos = rng.choice(anios, cantidad, p=pesos)
    salida = []
    for anio in elegidos:
        dia = int(rng.integers(0, 365))
        fecha = date(int(anio), 1, 1) + timedelta(days=dia)
        salida.append(aammdd_desde_fecha(min(fecha, fecha_extraccion)))
    return salida


def generar_cuentas(
    clientes: pd.DataFrame,
    config_productos: dict,
    rng: np.random.Generator,
    cuentas_por_cliente: float,
    fecha_extraccion: date,
) -> pd.DataFrame:
    """Genera el maestro de cuentas con mezcla de productos y defectos naturales."""
    ids_cliente = clientes["id_cliente"].to_numpy()
    cantidad_clientes = len(ids_cliente)
    extra = cuentas_por_cliente - 1.0
    distribucion = config_productos["cuentas"]["distribucion_extra"]
    total_prob = sum(distribucion.values())
    factor = extra / total_prob if total_prob else 0.0
    marcos = [
        pd.DataFrame(
            {"id_cliente": ids_cliente, "codigo_producto": np.full(cantidad_clientes, "CA")}
        )
    ]
    for producto, probabilidad in distribucion.items():
        mascara = rng.random(cantidad_clientes) < probabilidad * factor
        marcos.append(
            pd.DataFrame({"id_cliente": ids_cliente[mascara], "codigo_producto": producto})
        )
    cuentas = pd.concat(marcos, ignore_index=True)
    cuentas = cuentas.sort_values(["id_cliente", "codigo_producto"]).reset_index(drop=True)
    secuencia = cuentas.groupby("codigo_producto").cumcount() + 1
    cuentas["id_cuenta"] = [
        PREFIJOS_CUENTA[p] + f"{s:08d}"
        for p, s in zip(cuentas["codigo_producto"], secuencia, strict=False)
    ]
    cantidad = len(cuentas)
    tipos_registro = np.full(cantidad, "A")
    cuentas["tipo_registro"] = tipos_registro
    cuentas["codigo_sucursal"] = rng.integers(1, 351, cantidad)
    monedas = config_productos["cuentas"]["monedas"]
    cuentas["moneda"] = cuentas["codigo_producto"].map(monedas)
    cuentas["fecha_apertura"] = _fechas_apertura(rng, cantidad, fecha_extraccion)
    estados = config_productos["estados_cuenta"]
    cuentas["estado_cuenta"] = rng.choice(
        list(estados.keys()), cantidad, p=list(estados.values())
    )
    con_tarjeta = cuentas["codigo_producto"].isin(["CA", "CC", "CJ"]) & (
        rng.random(cantidad) < 0.65
    )
    cuentas["indicador_tarjeta"] = np.where(con_tarjeta, "S", "N")
    digitos = rng.integers(0, 10, (cantidad, 12))
    numeros = ["4559" + "".join(str(d) for d in fila) for fila in digitos]
    cuentas["numero_tarjeta"] = np.where(con_tarjeta, numeros, "")
    cuentas["fecha_ultimo_movimiento"] = "000000"
    cuentas["observaciones"] = _observaciones(cantidad, rng)
    cuentas = cuentas[
        [
            "tipo_registro", "id_cuenta", "id_cliente", "codigo_producto", "codigo_sucursal",
            "moneda", "fecha_apertura", "estado_cuenta", "indicador_tarjeta", "numero_tarjeta",
            "fecha_ultimo_movimiento", "observaciones",
        ]
    ]
    return cuentas


def _observaciones(cantidad: int, rng: np.random.Generator) -> np.ndarray:
    """Texto libre sobrecargado: telefonos, domicilios y notas mezcladas."""
    observaciones = np.full(cantidad, "", dtype=object)
    azar = rng.random(cantidad)
    telefonos = [
        f"TEL {int(rng.integers(11, 300)):03d}-{int(rng.integers(1000, 9999)):04d}"
        for _ in range(cantidad)
    ]
    calles = np.array(CALLES)[rng.integers(0, len(CALLES), cantidad)]
    numeros = rng.integers(1, 6500, cantidad)
    for indice in range(cantidad):
        valor = azar[indice]
        if valor < 0.12:
            observaciones[indice] = telefonos[indice]
        elif valor < 0.18:
            observaciones[indice] = f"DOMICILIO {calles[indice]} {numeros[indice]}"
        elif valor < 0.22:
            observaciones[indice] = "TRANSF A TERCEROS HABITUAL"
        elif valor < 0.25:
            observaciones[indice] = "DOC PENDIENTE ACTUALIZAR"
    return observaciones
