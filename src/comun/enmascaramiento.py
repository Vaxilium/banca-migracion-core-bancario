"""Enmascaramiento determinista de datos personales para entornos no productivos.

Control de seguridad: las muestras publicadas, los entornos de prueba y cualquier
extracto no productivo usan valores seudoanonimizados derivados de una huella
criptografica con sal fija del proyecto. La misma entrada produce siempre la misma
salida (trazabilidad de pruebas sin exponer datos).
"""

import re

import pandas as pd

from src.comun.textos import huella_determinista

NOMBRES_FICTICIOS = (
    "ARGENTINA ROSALES", "AZUL MONTENEGRO", "BENJAMIN QUINTEROS", "CAMILA ROBLEDO",
    "DELFINA SERRANO", "EMILIANO BARRIOS", "FACUNDO PERALTA", "GUADALUPE IRIARTE",
    "HORACIO LEDESMA", "INES VILLALBA", "JOAQUIN AGUIRRE", "LUCIA FERNANDEZ BLANCO",
    "MALENA SOSA", "MATIAS OYARZABAL", "NICOLAS ARRIETA", "OLIVIA CASTAGNO",
    "PEDRO ZABALA", "RENATA MIRANDA", "SANTIAGO BENITEZ", "VALENTINA OCAMPO",
)


def numero_pseudo(valor: str, digitos: int) -> str:
    """Genera una cadena numerica determinista de la longitud pedida."""
    huella = huella_determinista(valor)
    numero = int(huella[:16], 16)
    return f"{numero % (10**digitos):0{digitos}d}"


def enmascarar_documento(tipo: str, documento: str) -> str:
    """Seudoanonimiza un documento conservando su tipo y formato."""
    limpio = str(documento).strip()
    if tipo == "PAS":
        huella = huella_determinista(limpio)
        return f"{huella[:3].upper()}{numero_pseudo(limpio, 6)}"
    return numero_pseudo(limpio, len(limpio) if limpio.isdigit() else 8)


def enmascarar_nombre(nombre: str) -> str:
    """Reemplaza el nombre por uno ficticio estable."""
    indice = int(huella_determinista(str(nombre))[:8], 16) % len(NOMBRES_FICTICIOS)
    return NOMBRES_FICTICIOS[indice]


def enmascarar_telefono(telefono: str) -> str:
    """Seudoanonimiza un telefono conservando el prefijo si lo tiene."""
    texto = str(telefono).strip()
    prefijo = re.match(r"^[+\d()\s-]{3,6}", texto)
    base = prefijo.group(0) if prefijo else "11-"
    return f"{base.rstrip()}-{numero_pseudo(texto, 4)}-{numero_pseudo(texto + 'x', 4)}"


def enmascarar_correo(correo: str) -> str:
    """Seudoanonimiza un correo conservando el dominio."""
    texto = str(correo).strip()
    dominio = texto.split("@")[-1] if "@" in texto else "ejemplo.com"
    return f"cliente{numero_pseudo(texto, 6)}@{dominio}"


def enmascarar_direccion(calle: str, numero: str | int) -> str:
    """Seudoanonimiza la calle dejando el numero como referencia de trabajo."""
    indice = int(huella_determinista(str(calle))[:8], 16) % 900
    return f"CALLE FICTICIA {indice:03d}"


def enmascarar_dataframe(df: pd.DataFrame, columnas: dict[str, str]) -> pd.DataFrame:
    """Aplica enmascaramiento a las columnas indicadas (columna -> tipo de mascara)."""
    resultado = df.copy()
    for columna, mascara in columnas.items():
        if columna not in resultado.columns:
            continue
        if mascara == "nombre":
            resultado[columna] = resultado[columna].map(enmascarar_nombre)
        elif mascara == "telefono":
            resultado[columna] = resultado[columna].map(enmascarar_telefono)
        elif mascara == "correo":
            resultado[columna] = resultado[columna].map(enmascarar_correo)
        elif mascara.startswith("documento"):
            tipo_columna = mascara.split(":")[1] if ":" in mascara else None
            if tipo_columna and tipo_columna in resultado.columns:
                resultado[columna] = [
                    enmascarar_documento(tipo, doc)
                    for tipo, doc in zip(
                        resultado[tipo_columna], resultado[columna], strict=False
                    )
                ]
            else:
                resultado[columna] = resultado[columna].map(
                    lambda v: enmascarar_documento("DNI", v)
                )
    return resultado
