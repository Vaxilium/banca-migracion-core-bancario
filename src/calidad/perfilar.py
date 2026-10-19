"""Perfila el legado sintetico y deja las metricas en datos/perfilado."""

from __future__ import annotations

import json
import sys

import pandas as pd

from src.comun.rutas import LEGADO, PERFILADO, VERDAD
from src.migracion import extraccion

ENTIDADES = (
    "clientes",
    "documentos",
    "direcciones",
    "cuentas",
    "movimientos",
    "prestamos",
    "cuotas",
    "plazos_fijos",
    "mandatos",
    "saldos",
    "plan_cuentas",
    "saldos_contables",
)

CLAVES: dict[str, list[str]] = {
    "clientes": ["id_cliente"],
    "documentos": ["id_cliente", "tipo_documento", "numero_documento"],
    "direcciones": ["id_cliente", "tipo_direccion"],
    "cuentas": ["id_cuenta"],
    "movimientos": ["id_movimiento"],
    "prestamos": ["id_prestamo"],
    "cuotas": ["id_prestamo", "numero_cuota"],
    "plazos_fijos": ["id_plazo"],
    "mandatos": ["id_mandato"],
    "saldos": ["id_cuenta"],
    "plan_cuentas": ["codigo_contable"],
    "saldos_contables": ["codigo_contable", "periodo"],
}

CAMPOS_CRITICOS: dict[str, list[str]] = {
    "clientes": [
        "numero_documento",
        "nombre_completo",
        "fecha_nacimiento",
        "telefono",
        "correo",
        "fecha_alta",
    ],
    "documentos": ["numero_documento", "fecha_emision", "fecha_vencimiento"],
    "direcciones": ["calle", "numero", "localidad", "provincia", "codigo_postal"],
    "cuentas": ["id_cliente", "codigo_producto", "fecha_apertura", "estado_cuenta"],
    "movimientos": [
        "id_cuenta",
        "fecha_movimiento",
        "hora_movimiento",
        "codigo_operacion",
        "importe",
    ],
    "prestamos": [
        "id_cliente",
        "monto_original",
        "saldo_capital",
        "tasa_anual",
        "fecha_otorgamiento",
    ],
    "cuotas": ["fecha_vencimiento", "capital", "interes", "total", "estado_cuota"],
    "plazos_fijos": [
        "id_cliente",
        "monto_capital",
        "fecha_constitucion",
        "fecha_vencimiento",
    ],
    "mandatos": ["id_cuenta_debito", "codigo_servicio", "importe_maximo", "estado_mandato"],
    "saldos": ["saldo_apertura", "saldo_final", "fecha_saldo"],
    "plan_cuentas": ["nombre_cuenta", "tipo_cuenta", "nivel"],
    "saldos_contables": ["saldo_debe", "saldo_haber", "saldo_final"],
}


def perfil_entidad(entidad: str) -> dict:
    """Calcula registros, duplicados de clave y vacios de campos criticos."""
    crudo, rechazos = extraccion.leer_entidad(entidad, LEGADO)
    clave = CLAVES[entidad]
    duplicados = int(crudo.duplicated(clave, keep=False).sum())
    campos = {}
    for campo in CAMPOS_CRITICOS[entidad]:
        if campo not in crudo.columns:
            continue
        vacios = int(crudo[campo].fillna("").astype(str).str.strip().eq("").sum())
        campos[campo] = vacios
    return {
        "registros": len(crudo),
        "clave": clave,
        "duplicados": duplicados,
        "registros_corruptos": len(rechazos),
        "campos": campos,
    }


def perfil_verdad() -> list[dict]:
    """Resume los defectos inyectados por entidad y tipo."""
    verdad = pd.read_csv(VERDAD / "defectos_inyectados.csv", dtype=str)
    agrupado = verdad.groupby(["entidad", "tipo_defecto"]).size().reset_index(name="casos")
    return agrupado.sort_values(["entidad", "tipo_defecto"]).to_dict("records")


def main() -> int:
    """Perfila el legado y guarda el resultado en datos/perfilado."""
    PERFILADO.mkdir(parents=True, exist_ok=True)
    resultado = {
        "entidades": {entidad: perfil_entidad(entidad) for entidad in ENTIDADES},
        "verdad": perfil_verdad(),
    }
    ruta = PERFILADO / "perfil_origen.json"
    ruta.write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding="utf-8")
    total = sum(datos["registros"] for datos in resultado["entidades"].values())
    print(f"Perfilado del origen: {total} registros en {len(ENTIDADES)} entidades -> {ruta}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
