# ADR-002: Modelo de gobierno de dos niveles con comité de datos

| Fecha | Estado | Decisores | Autor |
|---|---|---|---|
| 19/10/2026 | Aceptada | Comité directivo | Franco Tilleria, Analista de Negocios |

## Contexto

El proyecto requiere decisiones rápidas de negocio (brechas, reglas, cortes) y
decisiones técnicas (arquitectura, rendimiento) sin bloquearse entre sí.

## Decisión

Gobierno de dos niveles: comité directivo quincenal (alcance, presupuesto, go/no-go)
y comité operativo semanal (plan, impedimentos). En periodo de ensayos se agrega el
comité de datos y calidad (semanal) con Contabilidad y Datos, donde se aprueban
reglas, rechazos y ajustes de migración.

## Alternativas consideradas

1. Comité único semanal: más lento para temas técnicos y de datos.
2. Sin comité de datos: las reglas y ajustes se decidirían sin dueño contable.

## Consecuencias

- Las reglas de transformación y los ajustes tienen aprobación explícita de
  Contabilidad, requisito para la conciliación al 100 %.
- Escalamiento con plazos máximos definidos en el documento de gobierno.
