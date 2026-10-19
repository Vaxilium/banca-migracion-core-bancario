# ADR-005: Tratamiento de productos sin equivalente en el destino

| Fecha | Estado | Decisores | Autor |
|---|---|---|---|
| 19/10/2026 | Aceptada | Comité operativo | Franco Tilleria, Analista de Negocios |

## Contexto

La extracción del legado contiene productos y códigos que no tienen equivalente
directo en el core nuevo: tarjeta de crédito (TR), préstamo hipotecario (PH), plazo
fijo en moneda extranjera (PX), caja juvenil (CJ), cuenta corriente internacional
(CI) y códigos desconocidos (XX).

## Decisión

Tres tratamientos según el caso:

1. **Rechazo por diseño** (`fuera_de_alcance`): TR, PH y PX permanecen en sistemas
   satélite; se rechazan y notifican.
2. **Mapeo con marca** (equivalencia funcional): CJ se migra como caja de ahorro con
   segmento juvenil; CI como cuenta corriente con bandera internacional.
3. **Revisión manual** (`producto_desconocido`): los códigos XX no se cargan; van a
   cola de revisión con decisión obligatoria antes del corte.

## Alternativas consideradas

1. Desarrollar equivalentes completos de TR/PH/PX: fuera de alcance y presupuesto.
2. Rechazar CJ y CI: perdería clientes vigentes sin justificación funcional.

## Consecuencias

- Los rechazos por diseño son "diferencias aceptadas" con causa raíz documentada.
- El mapeo de CJ y CI se implementa en reglas versionadas (v2: CJ, v3: CI) y se
  verifica en la conciliación.
- Los códigos desconocidos reducen la métrica de conciliación hasta que se resuelven;
  queda evidencia de cada decisión.
