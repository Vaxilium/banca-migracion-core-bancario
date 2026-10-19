# ADR-001: Estrategia de migración con corte único (big bang controlado)

| Fecha | Estado | Decisores | Autor |
|---|---|---|---|
| 19/10/2026 | Aceptada | Comité directivo | Franco Tilleria, Analista de Negocios |

## Contexto

Debe elegirse entre big bang, migración por olas o paralelo. Los productos
(cuentas, préstamos, plazos fijos y mandatos) se referencian entre sí: separarlos en
olas obliga a conciliaciones cruzadas entre el legado y el core nuevo durante meses.

## Decisión

Migrar todo el alcance en una única ventana de fin de semana, con tres ensayos
previos, paralelo de saldos e intereses, y plan de reversa probado. El análisis
ponderado se publica en el documento de [estrategia](../01-marco-y-estrategia/estrategia-de-migracion.md).

## Alternativas consideradas

1. **Por olas:** menor riesgo por ola, doble operación prolongada y conciliaciones
   cruzadas.
2. **Paralelo:** máxima seguridad, costo de duplicar infraestructura por meses,
   inviable a esta escala.

## Consecuencias

- Positivas: sin conciliaciones cruzadas; costo del legado se elimina de inmediato.
- Negativas: ventana de corte crítica; exige ensayos rigurosos y congelamiento previo.
- Controles compensatorios: criterios go/no-go bloqueantes y reversa ensayada.
