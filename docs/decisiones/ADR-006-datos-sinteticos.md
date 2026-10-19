# ADR-006: Generación sintética de los datos de origen con verdad de terreno

| Fecha | Estado | Decisores | Autor |
|---|---|---|---|
| 19/10/2026 | Aceptada | Comité operativo | Franco Tilleria, Analista de Negocios |

## Contexto

El proyecto necesita un origen de datos realista para migrar: no se puede usar
información real de clientes (privacidad), y datos "perfectos" no permitirían
demostrar nada sobre calidad ni sobre el tratamiento de errores. Además, cada cifra
publicada en la documentación debe poder reproducirse con una sola ejecución.

## Decisión

1. **Datos 100 % sintéticos generados por código** con semilla fija (20261019),
   escalas parametrizables (completa, piloto, humo) y contrato de archivos en
   `config/disenos_legado/`. El banco, las personas y los documentos son ficticios
   y no coinciden con entidades reales.
2. **Enmascaramiento determinista** como control adicional: cualquier dato personal
   publicado (muestras, ejemplos de documentos) pasa por el módulo de enmascaramiento
   del proyecto antes de volcarse a Markdown o CSV pequeños.
3. **Defectos inyectados con verdad de terreno:** una tasa controlada de errores
   realistas se inyecta de forma reproducible y **cada caso queda registrado** en
   `datos/verdad/defectos_inyectados.csv`. La eficacia del pipeline y del perfilado
   se mide contra ese registro, no contra expectativas.
4. **Los archivos generados no se versionan** (solo las muestras reducidas): el
   repositorio publica el generador y las cifras, no los volúmenes.

## Alternativas consideradas

1. Usar datos reales anonimizados: riesgo de privacidad inaceptable para un portfolio.
2. Datos sintéticos "limpios": no permitirían demostrar el manejo de rechazos,
   descuadres ni duplicados, que es el corazón del trabajo de migración.
3. Datos aleatorios no reproducibles: imposibilita verificar cifras del tablero.

## Consecuencias

- Toda cifra de la documentación se regenera con `make todo`; los documentos usan
  secciones autogeneradas para no desactualizarse.
- La tasa de defectos es una decisión paramétrica (`config/parametrico/defectos.yaml`),
  auditable y ajustable sin tocar código.
- Las métricas de detección (perfilado y conciliación) se reportan contra la verdad
  de terreno: porcentaje detectado, falsos positivos y casos no detectados.
