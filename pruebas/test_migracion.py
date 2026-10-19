"""Pruebas de integracion sobre los artefactos del pipeline."""

import re

import pandas as pd
import pytest

from src.comun.rutas import LEGADO_DELTA, MUESTRAS
from src.migracion import extraccion, reglas

pytestmark = pytest.mark.integracion

ID_DELTA = 2_000_000_000


def _leer_delta(entidad: str) -> pd.DataFrame:
    crudo, rechazos = extraccion.leer_entidad(
        entidad, LEGADO_DELTA, extraccion.ARCHIVOS_DELTA[entidad]
    )
    assert rechazos == []
    return crudo


@pytest.mark.escenario("PR-004")
def test_claves_unicas_en_destino(tablas):
    """Saldos y cuotas no repiten su clave de negocio."""
    saldos = tablas("saldo_cuenta")
    assert not saldos["id_cuenta"].duplicated().any()
    cuotas = tablas("cuota_prestamo")
    assert not cuotas.duplicated(["id_prestamo", "numero_cuota"]).any()
    movimientos = tablas("movimiento")
    assert not movimientos["id_movimiento"].duplicated().any()


@pytest.mark.escenario("PR-005")
def test_libro_mayor_balanceado(tablas):
    """El destino conserva debe menos haber menos final en cero."""
    saldos = tablas("saldo_contable")
    diferencia = (saldos["saldo_debe"] - saldos["saldo_haber"] - saldos["saldo_final"]).abs()
    assert len(saldos) == 28
    assert diferencia.max() < 0.01


@pytest.mark.escenario("PR-006")
def test_tarjetas_enmascaradas_en_destino(tablas):
    """Toda tarjeta cargada conserva solo los ultimos cuatro digitos."""
    cuentas = tablas("cuenta")
    con_tarjeta = cuentas[cuentas["tiene_tarjeta"]]
    assert len(con_tarjeta) > 0
    assert con_tarjeta["numero_tarjeta_enmascarado"].fillna("").str.fullmatch(r"\*+\d{4}").all()


@pytest.mark.escenario("PR-007")
def test_conteos_cierran(conciliacion_v3):
    """La ecuacion origen = cargados + fusionados + no cargados cierra."""
    for fila in conciliacion_v3["conteos"]["filas"]:
        assert fila["diferencia"] == 0, fila["entidad"]
    assert conciliacion_v3["conteos"]["cuadra"] is True


def test_rechazos_de_cuenta_no_se_cargan(tablas, rechazos_v3):
    """Las cuentas rechazadas por producto o cliente no estan en el destino."""
    rechazadas = rechazos_v3[
        (rechazos_v3["entidad"] == "cuentas") & (rechazos_v3["motivo"] != "estado_desconocido")
    ]
    ids_cargados = set(tablas("cuenta")["id_cuenta"].astype(int).astype(str))
    assert not set(rechazadas["clave"]) & ids_cargados


@pytest.mark.escenario("PR-013")
def test_cuentas_nuevas_del_corte(tablas, conciliacion_v3):
    """Las cuentas nuevas de la delta existen con apertura cero."""
    resumen = conciliacion_v3["saldos"]["delta"]
    ids_delta = set(_leer_delta("cuentas")["id_cuenta"].astype(int))
    cuentas = tablas("cuenta")
    nuevas = cuentas[cuentas["id_cuenta"].isin(ids_delta)]
    assert resumen["activa"] is True
    assert len(nuevas) == resumen["cuentas_nuevas"]
    saldos = tablas("saldo_cuenta")
    saldos_nuevos = saldos[saldos["id_cuenta"].isin(ids_delta)]
    assert len(saldos_nuevos) == resumen["cuentas_nuevas"]
    assert (saldos_nuevos["saldo_apertura"] == 0).all()


@pytest.mark.escenario("PR-014")
def test_saldos_de_la_delta_reemplazan_los_vigentes(tablas, conciliacion_v3):
    """Cada cuenta tocada por el corte tiene un unico saldo igual al de la delta."""
    crudo = _leer_delta("saldos")
    ids = crudo["id_cuenta"].astype(int)
    finales, valida = reglas.convertir_importes(crudo["saldo_final"])
    assert valida.all()
    esperado = pd.DataFrame({"id_cuenta": ids, "saldo_delta": finales.astype(float)})
    saldos = tablas("saldo_cuenta")
    unido = saldos.merge(esperado, on="id_cuenta", how="inner")
    assert len(unido) == len(esperado[esperado["id_cuenta"].isin(saldos["id_cuenta"])])
    assert (unido["saldo_final"] - unido["saldo_delta"]).abs().max() < 0.01
    assert not saldos["id_cuenta"].duplicated().any()
    assert conciliacion_v3["saldos"]["delta"]["saldos_reemplazados"] > 0


@pytest.mark.escenario("PR-015")
def test_movimientos_delta_una_sola_vez(tablas, conciliacion_v3):
    """Los movimientos del corte estan una vez y con el importe del archivo."""
    crudo = _leer_delta("movimientos")
    ids = crudo["id_movimiento"].astype(int)
    importes, valida = reglas.convertir_importes(crudo["importe"])
    assert valida.all()
    esperado = pd.DataFrame({"id_movimiento": ids, "importe_delta": importes.astype(float)})
    movimientos = tablas("movimiento")
    nuevos = movimientos[movimientos["id_movimiento"] >= ID_DELTA]
    assert len(nuevos) == conciliacion_v3["movimientos"]["delta"]["filas_verificadas"]
    assert nuevos["id_movimiento"].is_unique
    assert set(nuevos["id_movimiento"]) <= set(esperado["id_movimiento"])
    unido = nuevos.merge(esperado, on="id_movimiento", how="inner")
    assert len(unido) == len(nuevos)
    assert (unido["importe"] - unido["importe_delta"]).abs().max() < 0.01


@pytest.mark.escenario("PR-017")
def test_muestras_sin_tarjetas_completas():
    """Ninguna muestra publicada contiene un numero de tarjeta completo."""
    if not MUESTRAS.exists() or not list(MUESTRAS.glob("*.csv")):
        pytest.skip("muestras no generadas; ejecutar make muestras")
    patron = re.compile(r"(?<!\d)\d{16}(?!\d)")
    for ruta in MUESTRAS.glob("*.csv"):
        texto = ruta.read_text(encoding="utf-8")
        assert not patron.search(texto), ruta.name
