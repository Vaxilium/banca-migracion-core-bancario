PY := .venv/bin/python
PIP := .venv/bin/pip
ESCALA ?= completa

.PHONY: todo entorno datos migracion conciliacion perfilado trazabilidad informes \
	tablero muestras pruebas lint sitio reducido limpiar

todo: entorno datos migracion conciliacion perfilado trazabilidad pruebas informes tablero muestras
	@echo "======================================================"
	@echo "Proyecto generado de punta a punta."
	@echo "Revisa docs/tablero.html y la carpeta datos/resultados."

entorno: .venv/bin/python

.venv/bin/python: requirements.txt
	@echo "== Creando entorno virtual e instalando dependencias =="
	python3 -m venv .venv
	$(PIP) install -q --upgrade pip
	$(PIP) install -q -r requirements.txt

datos: entorno
	@echo "== Generando extraccion sintetica del legado =="
	$(PY) -m src.generacion.generar --escala $(ESCALA)

migracion: datos
	@echo "== Ejecutando ensayos de migracion y carga delta =="
	$(PY) -m src.migracion.pipeline --ensayo todos

conciliacion: migracion
	@echo "== Ejecutando conciliacion por ensayo =="
	$(PY) -m src.conciliacion.ejecutar_conciliacion --todos

perfilado: datos
	@echo "== Perfilando datos de origen =="
	$(PY) -m src.calidad.perfilar

trazabilidad: conciliacion
	@echo "== Generando matriz de trazabilidad =="
	$(PY) -m src.informes.trazabilidad

pruebas: entorno
	@echo "== Ejecutando pruebas automatizadas =="
	$(PY) -m pytest pruebas -q --junitxml=datos/resultados/junit.xml

informes: perfilado trazabilidad pruebas
	@echo "== Actualizando documentos con cifras del pipeline =="
	$(PY) -m src.informes.actualizar_documentos

tablero: informes
	@echo "== Generando tablero interactivo =="
	$(PY) -m src.tablero.generar_tablero

muestras: datos
	@echo "== Publicando muestras CSV pequenas =="
	$(PY) -m src.generacion.muestras

lint: entorno
	.venv/bin/ruff check src pruebas

sitio: entorno
	$(PY) -m mkdocs build --site-dir site

reducido: ESCALA=piloto
reducido: entorno
	$(MAKE) --no-print-directory datos migracion conciliacion perfilado pruebas ESCALA=$(ESCALA)

limpiar:
	rm -rf datos site .pytest_cache .ruff_cache
	find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
