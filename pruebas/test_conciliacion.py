"""Pruebas de integracion de la conciliacion contra la verdad de terreno."""

import json

import numpy as np
import pandas as pd
import pytest

from src.comun.rutas import CONCILIACION, CONFIG, LEGADO_DELTA, VERDAD
from src.comun.yaml_util import cargar_yaml
from src.migracion import extraccion

pytestmark = pytest.mark.integracion


def _leer_descuadres(version: str = "v3") -> pd.DataFrame:
    return pd.read_csv(CONCILIACION / f"conciliacion_ensayo_{version}_descuadres.csv")


def _leer_desfases(version: str = "v3") -> pd.DataFrame:
    return pd.read_csv(CONCILIACION / f"conciliacion_ensayo_{version}_desfases.csv")


def _ids_delta() -> set[int]:
    crudo, rechazos = extraccion.leer_entidad(
        "saldos", LEGADO_DELTA, extraccion.ARCHIVOS_DELTA["saldos"]
    )
    assert rechazos == []
    return set(crudo["id_cuenta"].astype(int))


def _casos_de_verdad(verdad: pd.DataFrame, tipos: tuple[str, ...]) -> pd.DataFrame:
    casos = verdad[verdad["tipo_defecto"].isin(tipos)].copy()
    casos["id_cuenta"] = casos["clave"].astype(int)
    casos["delta_verdad"] = casos["detalle"].str.extract(r"delta=(-?[\d.]+)")[0].astype(float)
    return casos


@pytest.mark.escenario("PR-008")
def test_saldos_reconciliados(conciliacion_v3, tablas):
    """El saldo destino coincide con la reconstruccion desde el legado."""
    saldos = conciliacion_v3["saldos"]
    assert saldos["sin_esperado"] == 0
    assert saldos["diferencias"] == 0
    assert saldos["diferencia_monto"] == pytest.approx(0.0, abs=0.01)
    assert saldos["filas"] == len(tablas("saldo_cuenta"))


@pytest.mark.escenario("PR-009")
def test_descuadres_coinciden_con_la_verdad(conciliacion_v3, tablas):
    """Cada descuadre cargado coincide con el inyectado y su clasificacion."""
    verdad = _casos_de_verdad(
        pd.read_csv(VERDAD / "defectos_inyectados.csv", dtype=str),
        ("descuadre_leve", "descuadre_grave"),
    )
    ids_delta = _ids_delta()
    cargadas = set(tablas("saldo_cuenta")["id_cuenta"].astype(int))
    esperadas = (
        verdad[verdad["id_cuenta"].isin(cargadas - ids_delta)]
        .groupby("id_cuenta", as_index=False)["delta_verdad"]
        .sum()
    )
    obtenidas = _leer_descuadres("v3")

    assert len(obtenidas) == len(esperadas) == conciliacion_v3["descuadres"]["cuentas_descuadradas"]
    assert set(obtenidas["id_cuenta"]) == set(esperadas["id_cuenta"])

    comparado = obtenidas.merge(esperadas, on="id_cuenta", how="inner")
    assert (comparado["descuadre"] - comparado["delta_verdad"]).abs().max() < 0.01

    clasificacion_esperada = np.where(
        comparado["descuadre"].abs() <= 100, "ajuste_automatico", "revision_manual"
    )
    assert (comparado["clasificacion"] == clasificacion_esperada).all()

    ajustes = comparado[comparado["clasificacion"] == "ajuste_automatico"]
    revision = comparado[comparado["clasificacion"] == "revision_manual"]
    assert (ajustes["descuadre"].abs() <= 100).all()
    assert (revision["descuadre"].abs() > 100).all()
    parametros = cargar_yaml(CONFIG / "reglas" / "conciliacion.yaml")
    assert parametros["tolerancias"]["ajuste_automatico"] == pytest.approx(100.0)
    assert ajustes["descuadre"].sum() == pytest.approx(
        conciliacion_v3["descuadres"]["monto_ajustado"], abs=0.01
    )


@pytest.mark.escenario("PR-010")
def test_descuadres_graves_van_a_revision(conciliacion_v3):
    """Los descuadres fuera de tolerancia no reciben ajuste de apertura."""
    obtenidas = _leer_descuadres("v3")
    revision = obtenidas[obtenidas["clasificacion"] == "revision_manual"]
    assert len(revision) == conciliacion_v3["descuadres"]["revision_manual"]
    assert (revision["ajuste_apertura"] == 0).all()
    assert (revision["descuadre"].abs() > 100).all()


@pytest.mark.escenario("PR-011")
def test_desfases_contables_coinciden_con_la_verdad(conciliacion_v3):
    """El recalculo detecta los ocho desfases y los imputa a resultados."""
    verdad = pd.read_csv(VERDAD / "defectos_inyectados.csv", dtype=str)
    desfases = verdad[verdad["tipo_defecto"] == "desfase_contable"].copy()
    desfases["delta_verdad"] = desfases["detalle"].str.extract(r"delta=(-?[\d.]+)")[0].astype(float)
    obtenidos = _leer_desfases("v3")
    assert len(obtenidos) == len(desfases) == 8
    comparado = obtenidos.merge(
        desfases[["clave", "delta_verdad"]], left_on="codigo_contable", right_on="clave"
    )
    assert len(comparado) == 8
    esperado = np.where(
        comparado["tipo_cuenta"] == "P",
        -comparado["delta_verdad"],
        comparado["delta_verdad"],
    )
    assert (comparado["diferencia"] - esperado).abs().max() < 0.01
    assert (comparado["contrapartida"] == "3.3.01").all()
    assert (comparado["estado"] == "aplicado").all()
    contable = conciliacion_v3["contable"]
    assert contable["desbalances_internos"] == 0
    assert contable["desfases"] == 8
    assert contable["monto_ajuste"] == pytest.approx(-contable["monto_desfase"], abs=0.01)


@pytest.mark.escenario("PR-012")
def test_decision_go_no_go(conciliacion_v3):
    """La decision por ensayo respeta los criterios conciliados."""
    decisiones = {}
    for version in ("v1", "v2", "v3"):
        ruta = CONCILIACION / f"conciliacion_ensayo_{version}.json"
        if not ruta.exists():
            pytest.skip("faltan resultados de ensayos")
        decisiones[version] = json.loads(ruta.read_text(encoding="utf-8"))["go_no_go"]
    assert decisiones["v1"]["decision"] == "NO-GO"
    assert decisiones["v2"]["decision"] == "NO-GO"
    assert decisiones["v3"]["decision"] == "GO con observaciones"
    assert all(criterio["cumple"] for criterio in decisiones["v3"]["criterios"])
    assert decisiones["v3"]["observaciones"]
