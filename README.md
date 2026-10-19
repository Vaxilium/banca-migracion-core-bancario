# Migración del core bancario — Banco Meridiano Austral

**Caso de portafolio de migración de un core bancario, de punta a punta y con datos
100 % sintéticos.** Entidad ficticia, cifras reproducibles y cada número de la
documentación generado por el código del repositorio.

Un Analista de Negocios / Analista Funcional conduce el proyecto completo: estrategia,
análisis AS-IS, brechas funcionales, mapeo de datos, reglas de transformación, tres
ensayos de migración, conciliación contable, pruebas con Gherkin, corte y reversa,
gestión del cambio, riesgos y controles, y trazabilidad de requisitos.

## Resultados destacados

- **1.476.247 filas** cargadas en el ensayo final (v3), con contratos de datos validados.
- **12 de 12 entidades** con conciliación de conteos cerrada y **0 diferencias** de
  saldo y de movimientos.
- **1.747 descuadres** detectados contra la verdad de terreno: 1.405 automáticos y
  342 para revisión.
- **Decisión GO con observaciones** documentada en el informe de conciliación.
- **34 pruebas automatizadas** (reglas, integración, Gherkin y documentación) en verde.

## Cómo reproducirlo

Requiere Python 3.13 y `make`. Todo el pipeline corre con una semilla fija (20261019):

```bash
make todo
```

Eso genera el legado sintético, ejecuta los tres ensayos con la carga delta, concilia,
perfila, corre las pruebas, actualiza la documentación y publica el tablero en
`docs/tablero.html`. Para una versión reducida (escala piloto, ideal para CI):

```bash
make reducido
```

Otras puertas de entrada: `make datos`, `make migracion`, `make conciliacion`,
`make perfilado`, `make pruebas`, `make informes`, `make tablero`, `make sitio`
(sitio MkDocs) y `make lint`.

## Estructura

```text
config/       parámetros, reglas de versiones, catálogos y contratos
src/          paquete Python: generación, extracción, transformación, carga,
              conciliación, calidad, informes y tablero
pruebas/      suite pytest con escenarios Gherkin
docs/         documentación del proyecto (12 fases + ADRs + tablero)
muestras/     CSV enmascarados y pequeños, aptos para publicar
datos/        datos generados (no versionado; se recrea con make)
```

## Empezar a leer

| Recurso | Descripción |
|---|---|
| [Resumen ejecutivo](docs/resumen-ejecutivo.md) | Una página con el problema, el enfoque y los resultados. |
| [Tablero interactivo](docs/tablero.html) | Estado, calidad de datos, ensayos y go/no-go. |
| [Presentación al comité](docs/presentacion-comite.md) | Diapositivas para el comité directivo. |
| [Índice de documentación](docs/index.md) | Todas las fases y decisiones del proyecto. |

## Autor

**Franco Tilleria — Analista de Negocios / Analista Funcional (banca)**

- LinkedIn: <https://www.linkedin.com/in/franco-tilleria-centurion>
- GitHub: <https://github.com/Vaxilium>

> Todos los nombres, documentos, cuentas y movimientos son datos sintéticos generados
> por código con semilla fija. Cualquier parecido con personas o entidades reales es
> coincidencia.
