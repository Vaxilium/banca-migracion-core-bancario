# ADR-007: Ventana histórica de movimientos a migrar

| Fecha | Estado | Decisores | Autor |
|---|---|---|---|
| 19/10/2026 | Aceptada | Comité operativo | Franco Tilleria, Analista de Negocios |

## Contexto

El core legado conserva movimientos de más de una década. Migrar todo el historial
multiplica el volumen de datos, el tiempo de los ensayos y el esfuerzo de
conciliación, pero algunos procesos del negocio (extractos, reclamos y
requerimientos de información) necesitan historia reciente completa.

La extracción disponible se genera con corte al 09/10/2026 y el análisis AS-IS
registró consultas típicas de clientes sobre los últimos 12 meses de movimientos.

## Decisión

Migrar los **últimos 12 meses de movimientos** medidos desde la fecha de extracción
(09/10/2025 al 09/10/2026), con dos reglas asociadas:

1. Cada cuenta migrada debe incluir el saldo de apertura de la ventana como
   "saldo inicial migrado", para que la suma de movimientos explique el saldo final.
2. El historial anterior a la ventana no se migra; queda disponible en el archivo
   frío del legado, con procedimiento manual documentado para pedidos excepcionales.

## Alternativas consideradas

1. Migrar todo el historial: costo de volumen y ensayos desproporcionado frente al
   valor para el negocio.
2. Migrar 6 meses: insuficiente para reclamos y comparaciones año contra año.
3. Migrar 24 meses: costo doble de almacenamiento y conciliación sin requisito que
   lo justifique.

## Consecuencias

- El volumen esperado de movimientos queda alrededor del millón de registros en la
  escala completa, manejable para los ensayos.
- Los informes regulatorios que requieren historia mayor a 12 meses se resuelven
  desde el archivo frío hasta que el core nuevo acumule historia.
- La conciliación verifica la ventana explícitamente: movimientos fuera de rango se
  rechazan con motivo `fuera_de_ventana` y se informan como exclusión controlada.
- La carga delta del día de corte nunca abre una brecha: su fecha es posterior a la
  extracción base y es continua respecto de ella.
