# ADR-012: Ajustes de migración y tolerancia de descuadres

| Fecha | Estado | Decisores | Autor |
|---|---|---|---|
| 19/10/2026 | Aceptada | Comité operativo | Franco Tilleria, Analista de Negocios |

## Contexto

El legado contiene defectos que sobreviven a la transformación: descuadres entre el
saldo final de una cuenta y la suma de sus movimientos, y desfases en los saldos del
libro mayor que no rompen el equilibrio debe–haber–final. La migración no debe
inventar datos ni corregir silenciosamente el origen; tampoco puede declarar el
corte conciliado ignorando diferencias materiales.

La conciliación de la fase 7 detecta:

- **descuadres de saldo**: diferencia entre el saldo final, el saldo de apertura y la
  suma de movimientos originales, reconstruida depurando duplicados de reproceso y
  normalizando el signo de las comisiones invertidas;
- **desfases contables**: diferencia entre cada fila del libro mayor y el valor
  recalculado desde cuentas, cuotas pendientes y plazos.

Las magnitudes observadas separan dos poblaciones: descuadres leves (0,50 a 50) y
descuadres graves (500 a 5.000); los desfases contables son relativos (0,1 % a 1 %
del valor, más 0,50) y pueden ser millonarios en cuentas de depósitos.

## Decisión

1. **Tolerancia de descuadres: 100.** Hasta 100 (en valor absoluto y en pesos) el
   descuadre se regulariza con un ajuste de apertura automático y evidenciado. Por
   encima de 100 queda en revisión manual y se informa como observación del corte.
   El umbral no es arbitrario: separa las dos poblaciones del legado sin dejar casos
   dudosos en la frontera.
2. **Los ajustes de descuadre no modifican las filas cargadas.** Se registran en el
   archivo de evidencia de la conciliación con el saldo de apertura ajustado; el
   destino conserva el valor del legado para que la traza sea reversible.
3. **Los ocho desfases contables se ajustan en el ensayo 3** contra resultados
   acumulados (cuenta 3.3.01), con el detalle por cuenta en
   `conciliacion_ensayo_v3_desfases.csv`. El asiento neto se documenta y queda a la
   vista del comité; no se reescribe el libro mayor cargado.
4. **Los ensayos 1 y 2 no aplican ajustes**: sirven para medir el costo de no
   conciliar y son, por definición, no-go. Solo el ensayo 3, que ya corrige signos y
   deduplica clientes, puede aplicar ajustes respaldados.
5. **Cada ajuste exige evidencia recalculable**: la suma de movimientos originales,
   las cuotas pendientes de los préstamos y los plazos vigentes. La conciliación no
   usa la verdad de terreno de los defectos inyectados: la reconstruye desde los
   datos.

## Alternativas consideradas

1. **Corregir los saldos en el destino**: rompe la trazabilidad y oculta el defecto
   del legado; impediría auditar el origen y comparar contra la extracción.
2. **Tolerancia cero**: derivaría a revisión manual más de 1.700 cuentas por
   diferencias de centavos o de pocos pesos, sin valor de control.
3. **Tolerancia proporcional al saldo**: un descuadre de 5.000 sobre una cuenta de
   millones sería aceptado, pero el defecto es operativo y no de escala; la
   tolerancia absoluta refleja el riesgo real de caja.
4. **Ajustar todos los descuadres sin revisión**: un descuadre grave puede ocultar
   un faltante de fondos; requiere intervención humana.

## Consecuencias

- El ensayo 3 queda en **GO con observaciones**: los descuadres leves se ajustan
  automáticamente y los graves quedan en revisión manual con evidencia, sin bloquear
  el corte.
- La conciliación reporta el monto ajustado y el monto en revisión por ensayo, de modo
  que el comité dimensiona el riesgo residual antes de aprobar.
- Los desfases contables quedan documentados como defecto del legado: el ajuste
  reconoce la diferencia contra la evidencia, no corrige la causa.
- Si el negocio regulariza el origen, basta con volver a correr `make todo`: la
  conciliación se recalcula y los ajustes tienden a cero.
