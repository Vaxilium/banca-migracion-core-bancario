# ADR-009: Deduplicación de clientes en la migración

| Fecha | Estado | Decisores | Autor |
|---|---|---|---|
| 19/10/2026 | Aceptada | Comité operativo | Franco Tilleria, Analista de Negocios |

## Contexto

El maestro de clientes del legado contiene registros que representan a la misma
persona: altas duplicadas por captura manual, variantes de nombre (apellidos
invertidos, tipeos, espacios dobles) y documentos repetidos entre fichas. En la
extracción sintética esto está inyectado y registrado en la verdad de terreno
(`duplicado_nombre_variante`, `documento_repetido_otro_cliente`), pero el fenómeno
existe igual en un legado real.

Migrar sin deduplicar deja clientes repetidos en el destino: duplica la base de
contacto, fragmenta cuentas del mismo titular y hace inútil la conciliación por
conteo de clientes.

## Decisión

1. **Criterio de duplicado:** dos registros son la misma persona si, tras normalizar
   el nombre (sin tildes, sin puntuación, espacios simples), se cumple cualquiera de:
   - nombre normalizado igual y misma fecha de nacimiento; o
   - mismo tipo y número de documento (aunque el nombre varíe).
2. **Sobreviviente:** se conserva el registro con el `id_cliente` menor (el más
   antiguo) y los demás se fusionan.
3. **Reapuntado:** documentos, domicilios, cuentas, préstamos, plazos y mandatos del
   registro fusionado se reapuntan al sobreviviente antes de la carga.
4. **Evidencia:** cada fusión se registra en la bitácora
   (`id_origen`, `id_destino`, criterio y campos que coincidieron) y alimenta la
   tabla de explicación de diferencias de la conciliación.
5. **La deduplicación se activa en el ensayo 2** (`deduplicacion_clientes: true`);
   el ensayo 1 mide el costo de no hacerla.

## Alternativas consideradas

1. No deduplicar y cargar tal cual: contaminación del destino y conciliación de
   clientes sin sentido.
2. Deduplicar solo por documento: pierde los duplicados cuyo documento también fue
   recreado con variante.
3. Deduplicar por nombre solo: fusionaría homónimos con distinta fecha de nacimiento.

## Consecuencias

- El conteo de clientes del destino es menor que el del origen y la diferencia es
  **explicable** con la bitácora de fusiones (exigencia de la conciliación).
- Casos ambiguos (mismo nombre y fecha pero documentos distintos vigentes) no se
  fusionan automáticamente: van a revisión manual con la evidencia adjunta.
- La calidad de los datos de contacto mejora: una sola ficha por persona con sus
  canales consolidados.
