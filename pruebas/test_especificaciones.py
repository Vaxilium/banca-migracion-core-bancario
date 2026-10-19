"""Control de cobertura entre las especificaciones Gherkin y las pruebas."""

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
CARACTERISTICAS = RAIZ / "pruebas" / "caracteristicas"
PATRON_ESCENARIO = re.compile(r"Escenario:\s*(PR-\d{3})")


def _escenarios() -> dict[str, str]:
    encontrados: dict[str, str] = {}
    for ruta in sorted(CARACTERISTICAS.glob("*.feature")):
        texto = ruta.read_text(encoding="utf-8")
        assert "Caracteristica:" in texto, ruta.name
        for identificador in PATRON_ESCENARIO.findall(texto):
            assert identificador not in encontrados, f"escenario duplicado: {identificador}"
            encontrados[identificador] = ruta.stem
    return encontrados


def test_especificaciones_bien_formadas():
    """Cada escenario declara dado, cuando y entonces."""
    assert CARACTERISTICAS.exists()
    escenarios = _escenarios()
    assert len(escenarios) >= 10
    for ruta in sorted(CARACTERISTICAS.glob("*.feature")):
        bloques = ruta.read_text(encoding="utf-8").split("Escenario:")[1:]
        assert len(bloques) >= 2, ruta.name
        for bloque in bloques:
            for palabra in ("Dado", "Cuando", "Entonces"):
                assert palabra in bloque, f"{ruta.name}: falta {palabra}"


def test_escenarios_implementados():
    """Todo escenario Gherkin aparece referenciado por una prueba."""
    escenarios = _escenarios()
    codigo = "\n".join(
        ruta.read_text(encoding="utf-8") for ruta in (RAIZ / "pruebas").glob("test_*.py")
    )
    sin_prueba = [clave for clave in escenarios if clave not in codigo]
    assert not sin_prueba, f"escenarios sin prueba: {', '.join(sorted(sin_prueba))}"


def test_pruebas_declaradas_por_escenario():
    """Las pruebas que citan escenarios usan el marker correspondiente."""
    escenarios = _escenarios()
    for ruta in (RAIZ / "pruebas").glob("test_*.py"):
        if ruta.name == "test_especificaciones.py":
            continue
        texto = ruta.read_text(encoding="utf-8")
        for identificador in PATRON_ESCENARIO.findall(texto):
            assert identificador in escenarios
            assert f'@pytest.mark.escenario("{identificador}")' in texto
