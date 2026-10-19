"""Pruebas de generacion determinista y utilidades de creditos."""

from datetime import date

from src.comun import validaciones
from src.comun.semilla import generador_numpy
from src.generacion.creditos import sumar_meses
from src.generacion.maestros import generar_clientes


def test_generacion_determinista_por_semilla():
    """Dos corridas con la misma semilla producen el mismo maestro."""
    primero = generar_clientes(80, generador_numpy())
    segundo = generar_clientes(80, generador_numpy())
    assert primero.equals(segundo)
    assert primero["id_cliente"].is_unique


def test_documentos_generados_validos():
    """El generador crea documentos coherentes con la regla ficticia."""
    clientes = generar_clientes(160, generador_numpy())
    documentos = clientes.loc[clientes["tipo_documento"] == "DNI", "numero_documento"]
    assert len(documentos) > 0
    assert all(validaciones.dni_valido(documento) for documento in documentos)


def test_sumar_meses_evita_fechas_imposibles():
    """La suma de meses fija el dia 28 cuando el mes no lo contiene."""
    assert sumar_meses(date(2026, 1, 31), 1) == date(2026, 2, 28)
    assert sumar_meses(date(2025, 12, 15), 1) == date(2026, 1, 15)
    assert sumar_meses(date(2026, 3, 31), -1) == date(2026, 2, 28)
