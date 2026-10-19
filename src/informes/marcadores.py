"""Herramientas para inyectar secciones autogeneradas en documentos Markdown."""

from pathlib import Path


def _marcadores(clave: str) -> tuple[str, str]:
    return f"<!-- INICIO AUTO: {clave} -->", f"<!-- FIN AUTO: {clave} -->"


def reemplazar_seccion(ruta: str | Path, clave: str, contenido: str) -> None:
    """Reemplaza el contenido entre los marcadores de una clave dada.

    Levanta ValueError si los marcadores no existen, para no publicar documentos
    desactualizados silenciosamente.
    """
    ruta = Path(ruta)
    texto = ruta.read_text(encoding="utf-8")
    inicio, fin = _marcadores(clave)
    pos_inicio = texto.find(inicio)
    pos_fin = texto.find(fin)
    if pos_inicio == -1 or pos_fin == -1 or pos_fin < pos_inicio:
        raise ValueError(f"marcadores AUTO no encontrados en {ruta}: {clave}")
    nuevo = texto[: pos_inicio + len(inicio)] + "\n" + contenido.strip() + "\n" + texto[pos_fin:]
    ruta.write_text(nuevo, encoding="utf-8")
