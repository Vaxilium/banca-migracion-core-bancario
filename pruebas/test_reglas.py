"""Pruebas unitarias de las reglas de conversion y validacion."""

from datetime import date

import pandas as pd
import pytest

from src.comun import validaciones
from src.comun.fechas import aammdd_desde_fecha, fecha_desde_aammdd
from src.comun.textos import huella_determinista
from src.migracion import reglas


@pytest.mark.escenario("PR-001")
def test_importes_con_signo_final():
    """Convierte importes de ancho fijo conservando magnitud y signo."""
    serie = pd.Series(
        ["00000000012345+", "00000000012345-", "00000000000100+", "00000000000000-", "abc"]
    )
    valores, valida = reglas.convertir_importes(serie)
    assert valida.tolist() == [True, True, True, True, False]
    assert valores.tolist()[:4] == pytest.approx([123.45, -123.45, 1.0, 0.0])
    assert pd.isna(valores.iloc[4])


@pytest.mark.escenario("PR-002")
def test_regla_de_siglo():
    """Interpreta el anio segun el umbral y rechaza fechas imposibles."""
    assert fecha_desde_aammdd("250101", 25) == date(2025, 1, 1)
    assert fecha_desde_aammdd("260101", 25) == date(1926, 1, 1)
    assert fecha_desde_aammdd("300101", 30) == date(2030, 1, 1)
    assert fecha_desde_aammdd("310101", 30) == date(1931, 1, 1)
    with pytest.raises(ValueError):
        fecha_desde_aammdd("290230", 30)
    with pytest.raises(ValueError):
        fecha_desde_aammdd("133201", 30)


def test_convertir_fechas_vectorial():
    """La conversion vectorial respeta el umbral y marca los invalidos."""
    serie = pd.Series(["010120", "991231", "250101", "260101", "133201", ""])
    fechas, valida = reglas.convertir_fechas(serie, umbral=25)
    assert valida.tolist() == [True, True, True, True, False, False]
    assert fechas.iloc[:4].tolist() == [
        "2001-01-20",
        "1999-12-31",
        "2025-01-01",
        "1926-01-01",
    ]


def test_formato_aammdd_ida_y_vuelta():
    """El formato del legado conserva la fecha al ida y vuelta."""
    fecha = date(2026, 10, 9)
    assert aammdd_desde_fecha(fecha) == "261009"
    assert fecha_desde_aammdd("261009") == fecha


def test_convertir_horas_valida_rangos():
    """Solo acepta horas HHMM con hora y minuto validos."""
    serie = pd.Series(["2359", "0000", "2400", "1260"])
    horas, valida = reglas.convertir_horas(serie)
    assert valida.tolist() == [True, True, False, False]
    assert horas.iloc[:2].tolist() == ["23:59", "00:00"]


@pytest.mark.escenario("PR-003")
def test_documento_con_digito_verificador():
    """Valida el digito verificador ficticio y el formato por tipo."""
    base = "1234567"
    documento = base + validaciones.digito_verificador_dni(base)
    assert validaciones.dni_valido(documento)
    incorrecto = documento[:-1] + str((int(documento[-1]) + 1) % 10)
    assert not validaciones.dni_valido(incorrecto)
    assert validaciones.ci_valida("1234567")
    assert not validaciones.ci_valida("123456")
    assert validaciones.pasaporte_valido("ABC123456")
    assert not validaciones.pasaporte_valido("AB123456")
    assert validaciones.documento_valido("DNI", documento)
    assert not validaciones.documento_valido("OTRO", documento)


def test_normalizacion_de_texto():
    """Normaliza nombres, telefonos y correos para comparar y deduplicar."""
    assert reglas.normalizar_nombre("  José   Pérez-Núñez ") == "JOSE PEREZ NUNEZ"
    assert reglas.normalizar_telefono("(011) 5555-1234") == "01155551234"
    assert reglas.normalizar_telefono("sin digitos") is None
    assert reglas.normalizar_correo(" Test@Example.COM ") == "test@example.com"
    assert reglas.normalizar_correo("sin-arroba") is None
    assert reglas.normalizar_texto("  cta   cte.  ") == "CTA CTE"


@pytest.mark.escenario("PR-006")
def test_enmascarar_tarjeta():
    """Conserva solo los ultimos cuatro digitos del numero de tarjeta."""
    assert reglas.enmascarar_tarjeta("4111 1111 1111 1234") == "************1234"
    assert reglas.enmascarar_tarjeta("0000000000000000") is None
    assert reglas.enmascarar_tarjeta("") is None


def test_extraer_observacion_de_cuenta():
    """Extrae telefono alternativo y marca de documento pendiente."""
    telefono, pendiente = reglas.extraer_observacion_cuenta("TEL 11-5555-1234 DOC PENDIENTE")
    assert telefono == "11-5555-1234"
    assert pendiente is True
    assert reglas.extraer_observacion_cuenta("sin datos") == (None, False)


def test_fecha_ventana():
    """Calcula el inicio de la ventana de extraccion."""
    assert reglas.fecha_ventana(date(2026, 10, 9), 12) == date(2025, 10, 9)
    assert reglas.fecha_ventana(date(2026, 1, 31), 2) == date(2025, 11, 28)


@pytest.mark.escenario("PR-016")
def test_enmascaramiento_determinista():
    """El seudoanonimizado es estable y no devuelve el valor original."""
    from src.comun.enmascaramiento import enmascarar_documento, enmascarar_nombre

    documento = "12345678"
    primero = enmascarar_documento("DNI", documento)
    segundo = enmascarar_documento("DNI", documento)
    assert primero == segundo
    assert primero != documento
    assert enmascarar_nombre("JUAN PEREZ") == enmascarar_nombre("JUAN PEREZ")
    assert huella_determinista("demo") == huella_determinista("demo")
