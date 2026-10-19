# ADR-003: Alcance funcional de la migración

| Fecha | Estado | Decisores | Autor |
|---|---|---|---|
| 19/10/2026 | Aceptada | Comité directivo | Franco Tilleria, Analista de Negocios |

## Contexto

El banco evalúa migrar todo el portafolio, pero tarjetas de crédito, comercio
exterior e inversiones tienen complejidad regulatoria propia y equipos separados.

## Decisión

**Dentro del alcance:** cajas de ahorro, cuentas corrientes, depósitos a plazo fijo,
préstamos personales y tarjetas de débito (producto asociado a la cuenta).
**Fuera del alcance:** tarjetas de crédito, comercio exterior e inversiones, que
permanecen en sistemas satélite integrados por archivos hasta la fase 2 del programa.

## Alternativas consideradas

1. Incluir tarjetas de crédito: duplica el esfuerzo de mapeo y pruebas; su motor de
   facturación no tiene equivalente directo en el core nuevo.
2. Incluir comercio exterior: alto componente regulatorio específico.

## Consecuencias

- Los productos legados de rubros excluidos que aparezcan en la extracción se
  rechazan con motivo `fuera_de_alcance` y se registran como diferencia de diseño
  aceptada.
- La interfaz futura con los satélites queda como dependencia del programa.
