"""Motor de reglas de transformacion parametrizado por la version del ensayo.

Las funciones de conversion trabajan vectorizadas sobre columnas de texto crudo de
la extraccion (ancho fijo) y devuelven el valor convertido y una mascara de validez.
Los rechazos, revisiones y la bitacora se arman en src/migracion/transformacion.py.
"""

import csv
import re
import unicodedata
from datetime import date

import numpy as np
import pandas as pd
import yaml

from src.comun.rutas import CONFIG

CODIGOS_DEBITO = ("02", "04", "06", "08", "09")
VARIANTES_FECHA_IMPOSIBLE = ("133201", "000230", "023201", "124506")


def cargar_reglas(version: int) -> dict:
    """Carga las reglas del ensayo indicado (reglas_v{version}.yaml)."""
    ruta = CONFIG / "reglas" / f"reglas_v{version}.yaml"
    with ruta.open(encoding="utf-8") as archivo:
        return yaml.safe_load(archivo)


def cargar_catalogos() -> dict[str, dict[str, str]]:
    """Catalogo legado -> valor destino por dominio (mapeo_catalogos.csv)."""
    catalogos: dict[str, dict[str, str]] = {}
    ruta = CONFIG / "mapeos" / "mapeo_catalogos.csv"
    with ruta.open(encoding="utf-8") as archivo:
        for fila in csv.DictReader(archivo):
            catalogos.setdefault(fila["dominio"], {})[fila["codigo_legado"]] = fila[
                "valor_destino"
            ]
    return catalogos


def convertir_fechas(serie: pd.Series, umbral: int) -> tuple[pd.Series, np.ndarray]:
    """Convierte AAMMDD a ISO con umbral de siglo; devuelve (fechas, validez)."""
    texto = serie.fillna("").astype(str).str.strip()
    forma = texto.str.fullmatch(r"\d{6}").to_numpy()
    yy = pd.to_numeric(texto.str.slice(0, 2), errors="coerce").fillna(0).astype(int)
    anio = np.where(yy <= umbral, 2000 + yy, 1900 + yy)
    iso = (
        pd.Series(anio, index=serie.index).astype(str)
        + "-"
        + texto.str.slice(2, 4)
        + "-"
        + texto.str.slice(4, 6)
    )
    conversiones = pd.to_datetime(iso, format="%Y-%m-%d", errors="coerce")
    valida = forma & conversiones.notna().to_numpy()
    fechas = conversiones.dt.strftime("%Y-%m-%d")
    return fechas.where(valida), valida


def convertir_importes(serie: pd.Series, decimales: int = 2) -> tuple[pd.Series, np.ndarray]:
    """Convierte importes de ancho fijo con signo final (+/-) a float."""
    texto = serie.fillna("").astype(str).str.strip()
    forma = texto.str.fullmatch(r"\d+[+-]").to_numpy()
    signo = np.where(texto.str.endswith("-"), -1.0, 1.0)
    cuerpo = pd.to_numeric(texto.str.slice(0, -1), errors="coerce")
    valor = np.round(cuerpo.to_numpy() / 10**decimales * signo, decimales)
    valida = forma & ~np.isnan(valor)
    return pd.Series(valor, index=serie.index).where(valida), valida


def convertir_horas(serie: pd.Series) -> tuple[pd.Series, np.ndarray]:
    """Convierte HHMM a HH:MM; devuelve (horas, validez)."""
    texto = serie.fillna("").astype(str).str.strip()
    forma = texto.str.fullmatch(r"\d{4}").to_numpy()
    numeros = pd.to_numeric(texto, errors="coerce").fillna(-1).astype(int)
    horas = numeros // 100
    minutos = numeros % 100
    valida = forma & (horas < 24).to_numpy() & (minutos < 60).to_numpy()
    resultado = (
        horas.astype(str).str.zfill(2) + ":" + minutos.astype(str).str.zfill(2)
    )
    return resultado.where(valida), valida


def convertir_enteros(serie: pd.Series) -> tuple[pd.Series, np.ndarray]:
    """Convierte campos numericos enteros de ancho fijo."""
    texto = serie.fillna("").astype(str).str.strip()
    valida = texto.str.fullmatch(r"\d+").to_numpy()
    valores = pd.to_numeric(texto, errors="coerce")
    return valores.where(valida), valida


def normalizar_texto(texto: str) -> str:
    """RN-01: mayusculas, sin puntuacion y con espacios simples."""
    limpio = re.sub(r"[^\w\s]", " ", str(texto or ""), flags=re.UNICODE)
    return re.sub(r"\s+", " ", limpio).strip().upper()


def normalizar_nombre(texto: str) -> str:
    """RN-02: clave de deduplicacion sin tildes ni puntuacion."""
    base = unicodedata.normalize("NFKD", str(texto or ""))
    sin_tildes = "".join(c for c in base if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", re.sub(r"[^A-Za-z0-9 ]", " ", sin_tildes)).strip().upper()


def normalizar_telefono(texto: str) -> str | None:
    """RN-06: solo digitos; nulo si no queda contenido."""
    digitos = re.sub(r"\D", "", str(texto or ""))
    return digitos or None


def normalizar_correo(texto: str) -> str | None:
    """RN-07: minusculas y formato basico; nulo si es invalido."""
    limpio = str(texto or "").strip().lower()
    if re.fullmatch(r"[^@\s]+@[^@\s]+\.[a-z]{2,}", limpio):
        return limpio
    return None


def validar_dni_vector(serie: pd.Series) -> np.ndarray:
    """Valida el digito verificador ficticio de una columna de DNIs."""
    texto = serie.fillna("").astype(str).str.strip()
    forma = texto.str.fullmatch(r"\d{8}").to_numpy()
    digitos_texto = texto.str.slice(0, 8).str.replace(r"\D", "0", regex=True)
    digitos = np.array([list(t.zfill(8)) for t in digitos_texto], dtype=int)
    pesos = np.array([2, 3, 4, 5, 6, 7])
    verificador = (digitos[:, :6] * pesos).sum(axis=1) * 7 % 10
    return forma & (verificador == digitos[:, 7])


def validar_ci_vector(serie: pd.Series) -> np.ndarray:
    """Valida cedulas ficticias: entre 7 y 9 digitos."""
    return serie.fillna("").astype(str).str.strip().str.fullmatch(r"\d{7,9}").to_numpy()


def validar_pasaporte_vector(serie: pd.Series) -> np.ndarray:
    """Valida pasaportes ficticios: 3 letras y 6 digitos."""
    texto = serie.fillna("").astype(str).str.strip().str.upper()
    return texto.str.fullmatch(r"[A-Z]{3}\d{6}").to_numpy()


def enmascarar_tarjeta(numero: str) -> str | None:
    """RN-11: conserva los ultimos cuatro digitos del numero de tarjeta."""
    limpio = re.sub(r"\D", "", str(numero or ""))
    if len(limpio) < 4 or limpio.strip("0") == "":
        return None
    return "*" * (len(limpio) - 4) + limpio[-4:]


def extraer_observacion_cuenta(texto: str) -> tuple[str | None, bool]:
    """RN-12: extrae telefono alternativo y documento pendiente del texto libre."""
    contenido = str(texto or "")
    telefono = None
    coincidencia = re.search(r"TEL\s+([\d-]{6,})", contenido, flags=re.IGNORECASE)
    if coincidencia:
        telefono = coincidencia.group(1)
    documento_pendiente = "DOC PENDIENTE" in contenido.upper()
    return telefono, documento_pendiente


def mapear_catalogo(catalogos: dict[str, dict[str, str]], dominio: str, codigo) -> str | None:
    """Mapea un codigo legado a su valor destino segun el catalogo del dominio."""
    return catalogos.get(dominio, {}).get(str(codigo or "").strip())


def fecha_ventana(fecha_corte: date, meses: int) -> date:
    """Primer dia de la ventana de migracion (meses hacia atras)."""
    anio = fecha_corte.year
    mes = fecha_corte.month - meses
    while mes <= 0:
        mes += 12
        anio -= 1
    return date(anio, mes, min(fecha_corte.day, 28))
