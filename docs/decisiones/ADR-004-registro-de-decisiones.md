# ADR-004: Registro de decisiones y trazabilidad en repositorio

| Fecha | Estado | Decisores | Autor |
|---|---|---|---|
| 19/10/2026 | Aceptada | Comité operativo | Franco Tilleria, Analista de Negocios |

## Contexto

El proyecto acumula decisiones funcionales (reglas, mapeos, exclusiones, ajustes)
que en proyectos anteriores vivían en correos y actas dispersas, dificultando la
auditoría y las migraciones posteriores.

## Decisión

Toda decisión relevante se registra como ADR corto en `docs/decisiones/` con
numeración secuencial, y toda cifra publicada en documentos o README se genera
desde salidas reales del código (bitácoras, conciliación, perfilado), mediante
secciones autogeneradas con marcadores `AUTO` o documentos generados por scripts.

## Alternativas consideradas

1. Registro en actas de comité: no versionado y de baja consulta.
2. Documentación manual de cifras: riesgo de inconsistencias inadmisibles para un
   proyecto de migración que se audita.

## Consecuencias

- Las decisiones son citables por ID (por ejemplo, ADR-001) desde requisitos,
  brechas y pruebas.
- Cualquier cifra publicada puede reproducirse ejecutando `make todo`.
- La matriz de trazabilidad verifica automáticamente los enlaces entre artefactos.
