"""Generacion de la carga delta del dia de corte (altas, movimientos y saldos)."""

from datetime import date

import numpy as np
import pandas as pd

from src.comun.fechas import aammdd_desde_fecha

CANALES_DELTA = ("VE", "AT", "IB", "MO")
PESOS_CANAL_DELTA = (0.20, 0.40, 0.25, 0.15)
DESCRIPCIONES_DELTA = {
    "01": "DEPOSITO", "02": "EXTRACCION", "04": "TRF ENV", "03": "TRF REC",
}


def generar_delta(
    cuentas: pd.DataFrame,
    saldos: pd.DataFrame,
    config: dict,
    rng: np.random.Generator,
    fecha_delta: date,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Genera cuentas nuevas, movimientos del dia y saldos actualizados del corte."""
    vigentes = cuentas[
        cuentas["estado_cuenta"].isin(["A", "B", "D"])
        & cuentas["codigo_producto"].isin(["CA", "CC", "CJ", "CI"])
    ].reset_index(drop=True)
    total_movs = config["movimientos_delta"]
    cantidad_cuentas = max(1, int(total_movs * 0.85))
    elegidas = rng.choice(len(vigentes), size=cantidad_cuentas, replace=False)
    llegadas = rng.poisson(1.2, cantidad_cuentas) + 1
    filas_vigentes = np.repeat(elegidas, llegadas)
    total = len(filas_vigentes)
    operaciones = rng.choice(["01", "02", "03", "04"], total, p=[0.45, 0.30, 0.15, 0.10])
    importes = np.round(rng.lognormal(np.log(1200.0), 1.1, total), 2)
    signos = np.where(operaciones == "01", 1.0, np.where(operaciones == "02", -1.0,
                     np.where(operaciones == "03", 1.0, -1.0)))
    importes = importes * signos
    canales = rng.choice(CANALES_DELTA, total, p=PESOS_CANAL_DELTA)
    horas = (rng.integers(0, 24, total) * 100 + rng.integers(0, 60, total)).astype(int)
    orden = np.lexsort((horas, filas_vigentes))
    filas_vigentes = filas_vigentes[orden]
    importes = importes[orden]
    operaciones = operaciones[orden]
    canales = canales[orden]
    horas = horas[orden]

    mapa_saldo = saldos.set_index("id_cuenta")["saldo_final"].to_dict()
    ids_cuenta = vigentes["id_cuenta"].to_numpy()[filas_vigentes]
    saldos_previos = np.array([float(mapa_saldo.get(c, 0.0)) for c in ids_cuenta])
    acumulado = (
        pd.Series(importes).groupby(pd.Series(filas_vigentes)).cumsum().to_numpy()
    )
    saldo_despues = np.round(saldos_previos + acumulado, 2)

    id_movimiento = np.arange(2000000000, 2000000000 + total)
    movimientos_delta = pd.DataFrame(
        {
            "tipo_registro": "M",
            "id_movimiento": id_movimiento,
            "id_cuenta": ids_cuenta,
            "fecha_movimiento": aammdd_desde_fecha(fecha_delta),
            "hora_movimiento": horas,
            "codigo_operacion": operaciones,
            "canal": canales,
            "importe": importes,
            "saldo_despues": saldo_despues,
            "numero_comprobante": id_movimiento + 500000000,
            "descripcion": [DESCRIPCIONES_DELTA[o] for o in operaciones],
            "sucursal": rng.integers(1, 351, total),
        }
    )

    cantidad_nuevas = config["cuentas_delta"]
    secuencias = {}
    for producto in ("CA", "CC"):
        existentes = cuentas[cuentas["codigo_producto"] == producto]["id_cuenta"]
        secuencias[producto] = max(int(c[2:]) for c in existentes) if len(existentes) else 0
    nuevas = []
    ids_clientes = cuentas["id_cliente"].unique()
    for _ in range(cantidad_nuevas):
        producto = "CA" if rng.random() < 0.8 else "CC"
        secuencias[producto] += 1
        cliente = int(rng.choice(ids_clientes))
        sucursal = int(rng.integers(1, 351))
        nuevas.append(
            {
                "tipo_registro": "A",
                "id_cuenta": f"{'01' if producto == 'CA' else '02'}{secuencias[producto]:08d}",
                "id_cliente": cliente,
                "codigo_producto": producto,
                "codigo_sucursal": sucursal,
                "moneda": "ARS",
                "fecha_apertura": aammdd_desde_fecha(fecha_delta),
                "estado_cuenta": "A",
                "indicador_tarjeta": "S" if rng.random() < 0.5 else "N",
                "numero_tarjeta": "4559" + "".join(
                    str(d) for d in rng.integers(0, 10, 12)
                ),
                "fecha_ultimo_movimiento": aammdd_desde_fecha(fecha_delta),
                "observaciones": "ALTA EN VENTANA DE CORTE",
            }
        )
    cuentas_delta = pd.DataFrame(nuevas)

    depositos = np.round(rng.lognormal(np.log(8000.0), 1.0, cantidad_nuevas), 2)
    nuevos_ids = cuentas_delta["id_cuenta"].to_numpy()
    movimientos_nuevas = pd.DataFrame(
        {
            "tipo_registro": "M",
            "id_movimiento": np.arange(2100000000, 2100000000 + cantidad_nuevas),
            "id_cuenta": nuevos_ids,
            "fecha_movimiento": aammdd_desde_fecha(fecha_delta),
            "hora_movimiento": (rng.integers(9, 19, cantidad_nuevas) * 100
                                + rng.integers(0, 60, cantidad_nuevas)).astype(int),
            "codigo_operacion": "01",
            "canal": "VE",
            "importe": depositos,
            "saldo_despues": depositos,
            "numero_comprobante": np.arange(510000000, 510000000 + cantidad_nuevas),
            "descripcion": "DEPOSITO",
            "sucursal": cuentas_delta["codigo_sucursal"].to_numpy(),
        }
    )
    movimientos_delta = pd.concat([movimientos_delta, movimientos_nuevas], ignore_index=True)

    afectadas = pd.DataFrame(
        {
            "tipo_registro": "S",
            "id_cuenta": ids_cuenta,
            "moneda": vigentes["moneda"].to_numpy()[filas_vigentes],
            "saldo_apertura": saldos_previos,
            "saldo_final": saldo_despues,
            "fecha_saldo": aammdd_desde_fecha(fecha_delta),
        }
    )
    ultimas = afectadas.groupby("id_cuenta").last().reset_index()
    nuevas_saldos = pd.DataFrame(
        {
            "tipo_registro": "S",
            "id_cuenta": nuevos_ids,
            "moneda": "ARS",
            "saldo_apertura": 0.0,
            "saldo_final": depositos,
            "fecha_saldo": aammdd_desde_fecha(fecha_delta),
        }
    )
    saldos_delta = pd.concat([ultimas, nuevas_saldos], ignore_index=True)
    return cuentas_delta, movimientos_delta, saldos_delta
