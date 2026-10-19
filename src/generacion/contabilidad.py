"""Generacion del plan de cuentas contable y de los saldos del libro mayor."""

from datetime import date

import numpy as np
import pandas as pd

from src.comun.fechas import aammdd_desde_fecha

PLAN_CUENTAS = (
    ("1", "ACTIVO", "A", 1, ""),
    ("1.1", "DISPONIBILIDADES", "A", 2, "1"),
    ("1.1.01", "CAJA", "A", 3, "1.1"),
    ("1.1.02", "BANCO CENTRAL", "A", 3, "1.1"),
    ("1.1.03", "BANCOS CORRESPONSALES", "A", 3, "1.1"),
    ("1.2", "CREDITOS POR INTERMEDIACION FINANCIERA", "A", 2, "1"),
    ("1.2.01", "PRESTAMOS PERSONALES VIGENTES", "A", 3, "1.2"),
    ("1.2.02", "PRESTAMOS PERSONALES VENCIDOS", "A", 3, "1.2"),
    ("1.2.03", "INTERESES DEVENGADOS A COBRAR", "A", 3, "1.2"),
    ("1.3", "OTROS CREDITOS", "A", 2, "1"),
    ("1.3.01", "ANTICIPOS AL PERSONAL", "A", 3, "1.3"),
    ("1.4", "BIENES DE USO", "A", 2, "1"),
    ("1.4.01", "MUEBLES Y UTILES", "A", 3, "1.4"),
    ("1.4.02", "INMUEBLES", "A", 3, "1.4"),
    ("1.5", "PARTIDAS PENDIENTES", "A", 2, "1"),
    ("1.5.01", "PARTIDAS PENDIENTES DE IMPUTACION", "A", 3, "1.5"),
    ("2", "PASIVO", "P", 1, ""),
    ("2.1", "DEPOSITOS", "P", 2, "2"),
    ("2.1.01", "CAJAS DE AHORRO", "P", 3, "2.1"),
    ("2.1.02", "CUENTAS CORRIENTES", "P", 3, "2.1"),
    ("2.1.03", "PLAZOS FIJOS", "P", 3, "2.1"),
    ("2.1.04", "CAJAS JUVENILES", "P", 3, "2.1"),
    ("2.1.05", "CUENTAS INTERNACIONALES", "P", 3, "2.1"),
    ("2.2", "OBLIGACIONES DIVERSAS", "P", 2, "2"),
    ("2.2.01", "IMPUESTOS A PAGAR", "P", 3, "2.2"),
    ("2.2.02", "SERVICIOS A PAGAR", "P", 3, "2.2"),
    ("2.3", "PARTIDAS PENDIENTES DE PAGO", "P", 2, "2"),
    ("2.3.01", "PARTIDAS PENDIENTES DE PAGO", "P", 3, "2.3"),
    ("3", "PATRIMONIO NETO", "P", 1, ""),
    ("3.1", "CAPITAL SOCIAL", "P", 2, "3"),
    ("3.1.01", "CAPITAL SOCIAL", "P", 3, "3.1"),
    ("3.2", "RESERVAS", "P", 2, "3"),
    ("3.2.01", "RESERVA LEGAL", "P", 3, "3.2"),
    ("3.3", "RESULTADOS", "P", 2, "3"),
    ("3.3.01", "RESULTADOS ACUMULADOS", "P", 3, "3.3"),
    ("4", "INGRESOS", "R", 1, ""),
    ("4.1", "INGRESOS FINANCIEROS", "R", 2, "4"),
    ("4.1.01", "INTERESES POR PRESTAMOS", "R", 3, "4.1"),
    ("4.1.02", "INTERESES POR PLAZOS FIJOS COLOCADOS", "R", 3, "4.1"),
    ("4.2", "COMISIONES", "R", 2, "4"),
    ("4.2.01", "COMISIONES DE CUENTAS", "R", 3, "4.2"),
    ("4.2.02", "COMISIONES DE SERVICIOS", "R", 3, "4.2"),
    ("5", "EGRESOS", "R", 1, ""),
    ("5.1", "INTERESES PAGADOS", "R", 2, "5"),
    ("5.1.01", "INTERESES CAJAS DE AHORRO", "R", 3, "5.1"),
    ("5.1.02", "INTERESES PLAZOS FIJOS", "R", 3, "5.1"),
    ("5.2", "GASTOS OPERATIVOS", "R", 2, "5"),
    ("5.2.01", "GASTOS DE ADMINISTRACION", "R", 3, "5.2"),
)


def generar_plan_cuentas() -> pd.DataFrame:
    """Genera el plan de cuentas contable del legado."""
    filas = [
        {
            "tipo_registro": "L",
            "codigo_contable": codigo,
            "nombre_cuenta": nombre,
            "tipo_cuenta": tipo,
            "nivel": nivel,
            "cuenta_padre": padre,
            "moneda": "ARS",
        }
        for codigo, nombre, tipo, nivel, padre in PLAN_CUENTAS
    ]
    return pd.DataFrame(filas)


def generar_saldos_contables(
    saldos: pd.DataFrame,
    cuentas: pd.DataFrame,
    prestamos: pd.DataFrame,
    plazos: pd.DataFrame,
    config_productos: dict,
    filas_con_desfase: int,
    rng: np.random.Generator,
    fecha_extraccion: date,
) -> tuple[pd.DataFrame, list[dict]]:
    """Genera los saldos del mayor coherentes con las cuentas y creditos.

    Devuelve el DataFrame de saldos contables y los desfases inyectados.
    """
    mapa = config_productos["mapeo_contable"]
    vigentes = cuentas[cuentas["estado_cuenta"] != "C"][["id_cuenta", "codigo_producto"]]
    union = saldos.merge(vigentes, on="id_cuenta", how="left")
    totales = union.groupby("codigo_producto")["saldo_final"].sum()
    prestamos_vigentes = prestamos[prestamos["estado_prestamo"] != "CA"]["saldo_capital"].sum()
    plazos_vigentes = plazos[plazos["estado_plazo"].isin(["V", "R"])]["monto_capital"].sum()
    depositos = float(totales.get("CA", 0) + totales.get("CC", 0) + totales.get("CJ", 0)
                      + totales.get("CI", 0))
    valores = {
        mapa["CA"]: float(totales.get("CA", 0.0)),
        mapa["CC"]: float(totales.get("CC", 0.0)),
        mapa["CJ"]: float(totales.get("CJ", 0.0)),
        mapa["CI"]: float(totales.get("CI", 0.0)),
        mapa["PF"]: float(plazos_vigentes),
        mapa["PP"]: float(prestamos_vigentes),
        config_productos["cuenta_caja"]: round(depositos * 0.08, 2),
        config_productos["cuenta_intereses"]: round(prestamos_vigentes * 0.004, 2),
        config_productos["cuenta_patrimonio"]: round(depositos * 0.12, 2),
    }
    filas = []
    for codigo, nombre, tipo, nivel, _padre in PLAN_CUENTAS:
        if nivel < 3:
            continue
        valor = round(valores.get(codigo, 0.0), 2)
        debe = valor if tipo == "A" else 0.0
        haber = valor if tipo == "P" else 0.0
        filas.append(
            {
                "tipo_registro": "B",
                "codigo_contable": codigo,
                "nombre_cuenta": nombre,
                "tipo_cuenta": tipo,
                "periodo": aammdd_desde_fecha(fecha_extraccion),
                "saldo_debe": debe,
                "saldo_haber": haber,
                "saldo_final": round(debe - haber, 2),
            }
        )
    df = pd.DataFrame(filas)
    desfases = []
    candidatos = df[df["saldo_final"] != 0]
    if len(candidatos) and filas_con_desfase > 0:
        elegidos = candidatos.sample(
            n=min(filas_con_desfase, len(candidatos)), random_state=17
        ).index
        for indice in elegidos:
            valor = float(df.at[indice, "saldo_final"])
            delta = round(abs(valor) * float(rng.uniform(0.001, 0.01)) + 0.5, 2)
            if rng.random() < 0.5:
                delta = -delta
            signo = 1 if df.at[indice, "tipo_cuenta"] == "A" else -1
            df.at[indice, "saldo_final"] = round(valor + delta * signo, 2)
            if df.at[indice, "tipo_cuenta"] == "A":
                df.at[indice, "saldo_debe"] = df.at[indice, "saldo_final"]
            else:
                df.at[indice, "saldo_haber"] = -df.at[indice, "saldo_final"]
            desfases.append(
                {
                    "entidad": "saldos_contables",
                    "tipo_defecto": "desfase_contable",
                    "clave": df.at[indice, "codigo_contable"],
                    "detalle": f"delta={delta}",
                }
            )
    return df, desfases
