"""Generacion de maestros: clientes, documentos y direcciones (datos sinteticos)."""

from datetime import date, timedelta

import numpy as np
import pandas as pd

from src.comun.fechas import aammdd_desde_fecha
from src.comun.textos import normalizar_texto
from src.comun.validaciones import digito_verificador_dni
from src.generacion.pools import (
    APELLIDOS,
    CALLES,
    DOMINIOS,
    LOCALIDADES,
    NOMBRES_F,
    NOMBRES_M,
    PREFIJOS_TELEFONO,
    PROVINCIAS,
)


def _nombre_aleatorio(rng: np.random.Generator, cantidad: int) -> np.ndarray:
    indice = rng.integers(0, len(APELLIDOS), cantidad)
    apellido1 = np.array(APELLIDOS)[indice]
    indice = rng.integers(0, len(APELLIDOS), cantidad)
    apellido2 = np.array(APELLIDOS)[indice]
    sexo_f = rng.random(cantidad) < 0.51
    indice_m = rng.integers(0, len(NOMBRES_M), cantidad)
    indice_f = rng.integers(0, len(NOMBRES_F), cantidad)
    nombres = np.where(sexo_f, np.array(NOMBRES_F)[indice_f], np.array(NOMBRES_M)[indice_m])
    return apellido1 + " " + apellido2 + " " + nombres


def _fechas_entre(rng: np.random.Generator, inicial: date, final: date, cantidad: int):
    rango = (final - inicial).days
    dias = rng.integers(0, rango, cantidad)
    base = inicial.toordinal()
    return [date.fromordinal(base + int(d)) for d in dias]


def _fechas_alta(rng: np.random.Generator, cantidad: int) -> list[date]:
    anios = np.arange(2000, 2027)
    pesos = np.linspace(0.5, 3.0, len(anios))
    pesos = pesos / pesos.sum()
    elegidos = rng.choice(anios, cantidad, p=pesos)
    fechas = []
    for anio in elegidos:
        dia = int(rng.integers(0, 365))
        fechas.append(date(int(anio), 1, 1) + timedelta(days=dia))
    limite = date(2026, 10, 9)
    return [min(fecha, limite) for fecha in fechas]


def _documento_aleatorio(rng: np.random.Generator, tipo: str, cantidad: int) -> list[str]:
    salida: list[str] = []
    if tipo == "DNI":
        base = rng.integers(1000000, 9999999, cantidad).tolist()
        salida = [f"{b}{digito_verificador_dni(str(b))}" for b in base]
    elif tipo == "CI":
        base = rng.integers(1000000, 99999999, cantidad).tolist()
        salida = [str(b) for b in base]
    return salida


def generar_clientes(cantidad: int, rng: np.random.Generator) -> pd.DataFrame:
    """Genera el maestro de clientes con distribuciones y formatos del legado."""
    ids = np.arange(1, cantidad + 1)
    nombres = _nombre_aleatorio(rng, cantidad)
    nacimiento = _fechas_entre(rng, date(1946, 1, 1), date(2008, 10, 8), cantidad)
    sexo_f = rng.random(cantidad) < 0.51
    sexo = np.where(sexo_f, "F", "M")
    tipos = rng.choice(["DNI", "CI", "PAS"], cantidad, p=[0.85, 0.10, 0.05])
    documentos = np.empty(cantidad, dtype=object)
    for tipo in ("DNI", "CI", "PAS"):
        mascara = tipos == tipo
        cantidad_tipo = int(mascara.sum())
        if tipo == "PAS":
            letras = np.array(list("ABCDEFGHJKLMNPQRSTUVWXYZ"))
            valores = []
            for _ in range(cantidad_tipo):
                letra = "".join(rng.choice(letras, 3))
                numero = int(rng.integers(0, 1000000))
                valores.append(f"{letra}{numero:06d}")
        else:
            valores = _documento_aleatorio(rng, tipo, cantidad_tipo)
        documentos[mascara] = valores
    telefonos = [
        f"{prefijo}-{int(rng.integers(1000, 9999)):04d}-{int(rng.integers(1000, 9999)):04d}"
        for prefijo in rng.choice(PREFIJOS_TELEFONO, cantidad)
    ]
    apellido_correo = [normalizar_texto(a).split()[0].lower() for a in nombres]
    correos = [
        f"{apellido}{int(rng.integers(1, 999)):03d}@{rng.choice(DOMINIOS)}"
        for apellido in apellido_correo
    ]
    estados = rng.choice(["A", "I", "B", "D"], cantidad, p=[0.88, 0.07, 0.03, 0.02])
    provincias = rng.choice(PROVINCIAS, cantidad)
    observaciones = np.where(rng.random(cantidad) < 0.10, "CLIENTE ANTIGUO", "")
    altas = _fechas_alta(rng, cantidad)
    return pd.DataFrame(
        {
            "tipo_registro": "C",
            "id_cliente": ids,
            "tipo_documento": tipos,
            "numero_documento": documentos,
            "nombre_completo": nombres,
            "fecha_nacimiento": [aammdd_desde_fecha(f) for f in nacimiento],
            "sexo": sexo,
            "telefono": telefonos,
            "correo": correos,
            "estado_cliente": estados,
            "fecha_alta": [aammdd_desde_fecha(f) for f in altas],
            "observaciones": observaciones,
            "provincia": provincias,
        }
    )


def generar_documentos(
    clientes: pd.DataFrame, proporcion_segundo: float, rng: np.random.Generator
) -> pd.DataFrame:
    """Genera los documentos declarados por cliente (algunos con segundo documento)."""
    base = clientes[["id_cliente", "tipo_documento", "numero_documento"]].copy()
    base["pais"] = np.where(base["tipo_documento"] == "PAS", "EXT", "ARG")
    emision = _fechas_entre(rng, date(2005, 1, 1), date(2025, 6, 30), len(base))
    base["fecha_emision"] = [aammdd_desde_fecha(f) for f in emision]
    anios_vigencia = np.where(
        base["tipo_documento"] == "PAS", 10, np.where(base["tipo_documento"] == "CI", 10, 15)
    )
    base["fecha_vencimiento"] = [
        aammdd_desde_fecha(f + timedelta(days=365 * int(v)))
        for f, v in zip(emision, anios_vigencia, strict=False)
    ]
    base["validado"] = np.where(rng.random(len(base)) < 0.92, "S", "N")
    segundo = base.sample(frac=proporcion_segundo, random_state=11).copy()
    segundo["tipo_documento"] = "PAS"
    letras = np.array(list("ABCDEFGHJKLMNPQRSTUVWXYZ"))
    documentos_pas = [
        f"{''.join(rng.choice(letras, 3))}{int(rng.integers(0, 1000000)):06d}"
        for _ in range(len(segundo))
    ]
    segundo["numero_documento"] = documentos_pas
    segundo["pais"] = "EXT"
    combinado = pd.concat([base, segundo], ignore_index=True)
    combinado = combinado.sort_values(["id_cliente", "tipo_documento"]).reset_index(drop=True)
    combinado.insert(0, "tipo_registro", "D")
    return combinado


def generar_direcciones(clientes: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Genera direcciones particulares (y algunas laborales) por cliente."""
    seleccion = clientes.sample(frac=0.97, random_state=7).copy()
    provincias = seleccion["provincia"].to_numpy()
    localidades = [rng.choice(LOCALIDADES[p]) for p in provincias]
    cantidad = len(seleccion)
    calles = np.array(CALLES)[rng.integers(0, len(CALLES), cantidad)]
    numeros = rng.integers(1, 6500, cantidad)
    pisos = np.where(rng.random(cantidad) < 0.35, rng.integers(1, 21, cantidad).astype(str), "")
    deptos = np.where(pisos != "", rng.choice(list("ABCDEF"), cantidad), "")
    codigos = [f"{int(rng.integers(1000, 9999))}" for _ in range(cantidad)]
    marco = pd.DataFrame(
        {
            "tipo_registro": "R",
            "id_cliente": seleccion["id_cliente"].to_numpy(),
            "tipo_direccion": "P",
            "calle": calles,
            "numero": numeros,
            "piso": pisos,
            "departamento": deptos,
            "localidad": localidades,
            "provincia": provincias,
            "codigo_postal": codigos,
            "pais": "ARG",
        }
    )
    laborales = marco.sample(frac=0.30, random_state=13).copy()
    laborales["tipo_direccion"] = "L"
    return pd.concat([marco, laborales], ignore_index=True)
