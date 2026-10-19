# ADR-013: Estrategia de corte y reversa

| Fecha | Estado | Decisores | Autor |
|---|---|---|---|
| 19/10/2026 | Aceptada | Comité directivo | Franco Tilleria, Analista de Negocios |

## Contexto

El ensayo 3 quedó en GO con observaciones: el destino concilia conteos, saldos y
movimientos, y los ocho desfases del libro mayor tienen ajuste evidenciado. Falta
definir cómo se pasa del legado al core nuevo con el menor riesgo operativo y con una
reversa posible si la apertura falla.

El banco opera de lunes a viernes, con procesos batch nocturnos y una ventana de
mantenimiento los fines de semana. La extracción base es del 09/10/2026 y el corte se
planifica para el 24/10/2026, por lo que existe un delta de dos semanas que debe
incorporarse sin reprocesar el histórico.

Los requisitos de continuidad fijan un RTO de 4 horas y un RPO de 15 minutos
(RNF-010). El corte debe respetar la ventana de mantenimiento y no puede convivir con
dos maestros operando en paralelo más allá de la ventana.

## Decisión

1. **Corte big-bang en ventana nocturna de fin de semana**, con congelamiento de
   cambios desde el sábado 24/10/2026 a las 00:00 y apertura el lunes 26/10/2026.
   Todo el universo migra en una sola ventana; no se opera con legado y destino en
   paralelo.
2. **Delta técnico con doble extracción**: se toma una extracción de corte el sábado
   24/10, se carga con el pipeline v3 y se valida contra el ensayo completo. La delta
   incorpora cuentas nuevas, saldos vigentes y movimientos posteriores a la
   extracción base.
3. **Go/no-go único y firmado**: el comité decide a las 02:00 del domingo con la
   conciliación del corte, la lista de pendientes y las pruebas verdes. Sin firma no
   se abre el lunes.
4. **Reversa por conmutación al legado, no por migración inversa**: si la apertura
   falla, se congela el destino, se redirigen los canales al legado y se restauran
   los respaldos del legado al punto anterior al corte. Las transacciones del lapso se
   reprocesan en el legado; nunca se intenta devolver datos desde el core nuevo.
5. **Límite de reversa a las 04:00 del domingo**: después de esa hora se ejecuta el
   plan de contingencia del destino y se abre con las observaciones aprobadas. La
   reversa tardía tiene más riesgo que continuar con el destino conciliado.
6. **Hipercare de 30 días** con war room, tablero diario y criterios de salida
   acordados antes de la apertura.

## Alternativas consideradas

1. **Operación en paralelo**: reduce el riesgo de datos, pero exige doble carga
   operativa y duplica los controles durante semanas; el legado no soporta el volumen
   de ambas operaciones sin degradar los batch.
2. **Migración por producto o por sucursal**: acota el impacto, pero obliga a
   interfaces temporales entre sistemas y extiende el riesgo y el costo varias
   semanas. El alcance funcional ya está cerrado y el ensayo 3 es concluyente.
3. **Corte sin delta**: más simple, pero perdería 15 días de movimientos y dejaría
   saldos desactualizados; inaceptable para el negocio.
4. **Reversa con replicación inversa**: técnicamente posible, pero el legado no
   admite escritura desde el core nuevo sin desarrollos no presupuestados; la
   restauración del legado es más simple y comprobable.

## Consecuencias

- El corte se concentra en una ventana de 8 horas y exige una preparación rigurosa:
  congelamiento, respaldos verificados y roles confirmados.
- La reversa depende de la calidad de los respaldos del legado y de la velocidad de
  conmutación de canales; se prueba en el simulacro previo.
- El éxito se mide por conciliación, no por velocidad: si el corte se adelanta pero
  no concilia, no se abre.
- Los pendientes de decisión (descuadres graves, estados desconocidos, documentos
  observados) deben tener dueño y fecha antes del congelamiento; el comité puede
  aprobar observaciones, pero no puede ignorarlas.
- La estrategia supone una ventana de mantenimiento real; si el negocio exige
  operación 24/7, este ADR debe revisarse antes de reutilizar el enfoque.
