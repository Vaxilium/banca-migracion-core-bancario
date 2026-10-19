"""Validacion de documentos de identidad sinteticos (algoritmo ficticio).

El algoritmo de digito verificador es una invencion pedagogica del proyecto: no
corresponde a ningun documento real. Solo se usa para simular reglas de calidad de
datos en el pipeline de migracion.
"""

import re

PESOS_DNI = (2, 3, 4, 5, 6, 7)


def digito_verificador_dni(base: str) -> str:
    """Calcula el digito verificador ficticio de una base numerica de 7 digitos."""
    if not base.isdigit():
        raise ValueError("la base debe ser numerica")
    suma = sum(int(digito) * peso for digito, peso in zip(base, PESOS_DNI, strict=False))
    verificador = (suma * 7) % 10
    return str(verificador)


def dni_valido(documento: str) -> bool:
    """Valida un DNI ficticio: 8 digitos con verificador correcto."""
    limpio = documento.strip()
    if not re.fullmatch(r"\d{8}", limpio):
        return False
    return digito_verificador_dni(limpio[:7]) == limpio[7]


def ci_valida(documento: str) -> bool:
    """Valida una cedula ficticia: entre 7 y 9 digitos."""
    return bool(re.fullmatch(r"\d{7,9}", documento.strip()))


def pasaporte_valido(documento: str) -> bool:
    """Valida un pasaporte ficticio: 3 letras y 6 digitos."""
    return bool(re.fullmatch(r"[A-Z]{3}\d{6}", documento.strip().upper()))


def documento_valido(tipo: str, documento: str) -> bool:
    """Valida segun el tipo de documento legado."""
    if tipo == "DNI":
        return dni_valido(documento)
    if tipo == "CI":
        return ci_valida(documento)
    if tipo == "PAS":
        return pasaporte_valido(documento)
    return False


def digito_verificador_dni_int(base: int) -> int:
    """Version entera del verificador para la generacion vectorizada."""
    return int(digito_verificador_dni(f"{base:07d}"))
