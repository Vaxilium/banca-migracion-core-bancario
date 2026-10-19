"""Genera las tablas del modelo destino, el mapeo campo a campo y las reglas.

Lee config/mapeos/ y config/reglas/ y actualiza las secciones autogeneradas de los
documentos de la fase 5 en docs/05-mapeo-de-datos/.
"""

import csv
import sys

from src.comun.rutas import CONFIG, DOCS
from src.comun.yaml_util import cargar_yaml
from src.informes.marcadores import reemplazar_seccion

MAPEOS = CONFIG / "mapeos"
REGLAS = CONFIG / "reglas"
RUTA_MODELO = DOCS / "05-mapeo-de-datos" / "modelo-de-datos.md"
RUTA_MAPEO = DOCS / "05-mapeo-de-datos" / "mapeo-de-datos.md"
RUTA_REGLAS = DOCS / "05-mapeo-de-datos" / "reglas-de-transformacion.md"

CAMPOS_CSV = [
    "archivo_origen", "campo_origen", "tabla_destino", "campo_destino",
    "tipo_destino", "carga", "obligatorio", "transformacion", "regla", "observacion",
]
PARAMETROS = [
    "umbral_siglo", "deduplicacion_clientes", "validar_fechas_contextual",
    "correccion_signos", "extraccion_texto_libre", "ajustes_contables",
    "tolerancia_conciliacion", "ventana_meses",
]


def _leer_csv_mapeos() -> list[dict]:
    filas: list[dict] = []
    for ruta in sorted(MAPEOS.glob("mapeo_*.csv")):
        if ruta.name == "mapeo_catalogos.csv":
            continue
        with open(ruta, encoding="utf-8", newline="") as archivo:
            for fila in csv.DictReader(archivo):
                filas.append(dict(fila))
    return filas


def tabla_modelo() -> str:
    """Tabla resumen de las tablas del modelo destino."""
    modelo = cargar_yaml(MAPEOS / "modelo_destino.yaml")
    filas = [
        "| Tabla | Descripción | Clave primaria | Origen | Columnas |",
        "|---|---|---|---|---:|",
    ]
    for tabla in modelo["tablas"]:
        clave = ", ".join(tabla["clave_primaria"])
        filas.append(
            f"| `{tabla['nombre']}` | {tabla['descripcion']} | `{clave}` | "
            f"`{tabla['origen']}` | {len(tabla['columnas'])} |"
        )
    total = sum(len(t["columnas"]) for t in modelo["tablas"])
    filas.append(f"| **Total: {len(modelo['tablas'])} tablas** |  |  |  | **{total}** |")
    derivadas = sum(
        1 for t in modelo["tablas"] for c in t["columnas"] if c.get("derivado")
    )
    filas.append("")
    filas.append(
        f"El modelo tiene {len(modelo['tablas'])} tablas y {total} columnas; "
        f"{derivadas} columnas son derivadas (no existen en la extracción y las "
        "calcula una regla del pipeline)."
    )
    return "\n".join(filas)


def tabla_catalogos() -> str:
    """Tabla de catálogos derivados de la extracción."""
    modelo = cargar_yaml(MAPEOS / "modelo_destino.yaml")
    catalogo = _leer_catalogos()
    filas = [
        "| Catálogo | Columnas | Códigos | Códigos especiales |",
        "|---|---|---:|---|",
    ]
    for entrada in modelo["catalogos"]:
        nombre = entrada["nombre"]
        codigos = [c for c in catalogo if c["dominio"] == nombre]
        especiales = [c for c in codigos if c["valor_destino"] in ("RECHAZAR", "REVISION")]
        etiquetas = {"RECHAZAR": "rechazar", "REVISION": "revisión"}
        detalle = ", ".join(
            f"`{c['codigo_legado']}` ({etiquetas[c['valor_destino']]})" for c in especiales
        )
        if nombre == "sucursal":
            detalle = "Derivado de la extracción: códigos 0001 a 0350, todos activos."
        columnas = ", ".join(entrada["columnas"])
        cantidad = str(len(codigos)) if codigos else "—"
        filas.append(
            f"| `{nombre}` | {columnas} | {cantidad} | {detalle or '—'} |"
        )
    return "\n".join(filas)


def _leer_catalogos() -> list[dict]:
    with open(MAPEOS / "mapeo_catalogos.csv", encoding="utf-8", newline="") as archivo:
        return list(csv.DictReader(archivo))


def tabla_cobertura(filas: list[dict]) -> str:
    """Tabla de cobertura del mapeo por archivo de origen."""
    archivos = sorted({f["archivo_origen"] for f in filas})
    encabezado = (
        "| Archivo origen | Campos | Carga directa | Con regla | Derivados | Solo control |"
    )
    filas_tabla = [encabezado, "|---|---:|---:|---:|---:|---:|"]
    for archivo in archivos:
        conjunto = [f for f in filas if f["archivo_origen"] == archivo]
        carga = [f for f in conjunto if f["carga"] == "S"]
        directa = [f for f in carga if f["transformacion"] == "directo"]
        derivados = [f for f in carga if f["transformacion"] == "derivado"]
        con_regla = [f for f in carga if f not in directa and f not in derivados]
        control = [f for f in conjunto if f["carga"] == "N"]
        filas_tabla.append(
            f"| `{archivo}` | {len(conjunto)} | {len(directa)} | {len(con_regla)} | "
            f"{len(derivados)} | {len(control)} |"
        )
    filas_tabla.append("")
    filas_tabla.append(
        f"Se mapearon {len(filas)} campos de origen hacia "
        f"{len({f['tabla_destino'] for f in filas})} tablas del destino."
    )
    return "\n".join(filas_tabla)


def tabla_detalle(filas: list[dict]) -> str:
    """Tabla completa de mapeo campo a campo ordenada por archivo y tabla."""
    ordenadas = sorted(
        filas, key=lambda f: (f["archivo_origen"], f["tabla_destino"], f["campo_destino"])
    )
    lineas = [
        "| Archivo origen | Campo origen | Campo destino | Tipo | Carga | Transformación | Regla |",
        "|---|---|---|---|:-:|---|---|",
    ]
    for fila in ordenadas:
        origen = fila["campo_origen"] or "— (derivado)"
        destino = f"{fila['tabla_destino']}.{fila['campo_destino']}"
        regla = fila["regla"] or "—"
        lineas.append(
            f"| `{fila['archivo_origen']}` | {origen} | `{destino}` | "
            f"{fila['tipo_destino']} | {fila['carga']} | {fila['transformacion']} | {regla} |"
        )
    return "\n".join(lineas)


def tabla_matriz_reglas() -> str:
    """Matriz de parámetros de las reglas v1, v2 y v3."""
    versiones = [cargar_yaml(REGLAS / f"reglas_v{v}.yaml") for v in (1, 2, 3)]
    lineas = ["| Parámetro | Ensayo 1 | Ensayo 2 | Ensayo 3 |", "|---|---|---|---|"]
    for parametro in PARAMETROS:
        celdas = []
        for version in versiones:
            valor = version.get(parametro)
            if isinstance(valor, bool):
                celdas.append("sí" if valor else "no")
            else:
                celdas.append(str(valor).replace(".", ","))
        lineas.append(f"| `{parametro}` | " + " | ".join(celdas) + " |")
    return "\n".join(lineas)


def tabla_productos_version() -> str:
    """Tabla de tratamiento por producto en cada versión de reglas."""
    versiones = [cargar_yaml(REGLAS / f"reglas_v{v}.yaml") for v in (1, 2, 3)]
    codigos = sorted(versiones[0]["mapeo_productos"])
    lineas = ["| Producto | Ensayo 1 | Ensayo 2 | Ensayo 3 |", "|---|---|---|---|"]
    for codigo in codigos:
        celdas = []
        for version in versiones:
            config = version["mapeo_productos"][codigo]
            tratamiento = config["tratamiento"]
            destino = config.get("destino")
            marca = config.get("marca")
            if destino:
                etiqueta = f"`{destino}`"
                if marca:
                    etiqueta += f" ({marca.replace('_', ' ')})"
            else:
                etiqueta = f"**{tratamiento}**"
            celdas.append(etiqueta)
        lineas.append(f"| `{codigo}` | " + " | ".join(celdas) + " |")
    return "\n".join(lineas)


def tabla_calidad() -> str:
    """Tabla de reglas de calidad con severidad y acción."""
    config = cargar_yaml(REGLAS / "calidad.yaml")
    lineas = [
        "| ID | Regla | Entidad | Tipo | Severidad | Acción |",
        "|---|---|---|---|---|---|",
    ]
    for regla in config["reglas"]:
        lineas.append(
            f"| {regla['id']} | {regla['nombre']} | `{regla['entidad']}` | "
            f"{regla['tipo'].replace('_', ' ')} | {regla['severidad']} | "
            f"{regla['accion'].replace('_', ' ')} |"
        )
    severidades: dict[str, int] = {}
    for regla in config["reglas"]:
        severidades[regla["severidad"]] = severidades.get(regla["severidad"], 0) + 1
    lineas.append("")
    lineas.append(
        f"{len(config['reglas'])} reglas de calidad: "
        + ", ".join(
            f"{severidades[s]} {s}{'s' if severidades[s] > 1 else ''}"
            for s in ("bloqueante", "grave", "leve")
            if s in severidades
        )
        + ". Las bloqueantes rechazan la fila; las graves la envían a revisión."
    )
    return "\n".join(lineas)


def main() -> int:
    """Punto de entrada del generador."""
    filas = _leer_csv_mapeos()
    reemplazar_seccion(RUTA_MODELO, "resumen-modelo", tabla_modelo())
    reemplazar_seccion(RUTA_MODELO, "catalogos-modelo", tabla_catalogos())
    reemplazar_seccion(RUTA_MAPEO, "cobertura-mapeo", tabla_cobertura(filas))
    reemplazar_seccion(RUTA_MAPEO, "detalle-mapeo", tabla_detalle(filas))
    reemplazar_seccion(RUTA_REGLAS, "matriz-reglas", tabla_matriz_reglas())
    reemplazar_seccion(RUTA_REGLAS, "mapeo-productos-version", tabla_productos_version())
    reemplazar_seccion(RUTA_REGLAS, "reglas-calidad", tabla_calidad())
    print(f"Documentos de modelo y mapeo actualizados: {len(filas)} campos mapeados.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
