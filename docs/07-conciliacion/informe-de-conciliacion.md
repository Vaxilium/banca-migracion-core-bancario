# Informe de conciliación

| Proyecto | Migración del core bancario — Banco Meridiano Austral (entidad ficticia) |
|---|---|
| **Versión** | 1.0 |
| **Fecha** | 19/10/2026 |
| **Autor** | Franco Tilleria, Analista de Negocios |
| **Estado** | Aprobado |

## Control de versiones

| Versión | Fecha | Autor | Cambio |
|---|---|---|---|
| 1.0 | 19/10/2026 | Franco Tilleria | Versión inicial. |

## Propósito

Demostrar, con evidencia reproducible, que las tablas cargadas por cada ensayo de
migración se explican íntegramente a partir del legado, los rechazos y la delta del
corte. La conciliación no es un tablero de control: es la condición de aceptación
del corte. Cada cifra de este documento se regenera con `make todo` y queda
respaldada en `datos/resultados/conciliacion/`.

El alcance cubre los tres ensayos sobre el mismo legado y la delta cargada en el
ensayo 3. El detalle de las reglas aplicadas está en
[el pipeline de migración](../06-pipeline/pipeline-de-migracion.md); las decisiones
de ajuste, en el [ADR-012](../decisiones/ADR-012-ajustes-de-migracion.md).

## Marco de conciliación

### Conteos por entidad

Para cada entidad se verifica la ecuación:

```text
filas_origen = filas_cargadas + filas_no_cargadas + fusionados
```

Las filas cargadas se cuentan sin las incorporadas por la delta. Las no cargadas
no se obtienen restando: se cruza cada clave rechazada contra las claves presentes
en el destino; si un rechazo hubiera quedado cargado, o una fila se hubiera
perdido, la ecuación no cerraría. Las filas marcadas como revisión que igual se
cargan de forma informativa (documentos inválidos de clientes, estados de cuenta
desconocidos, saldos incongruentes de préstamos y vencimientos incongruentes de
plazos) se informan en la columna de revisados cargados.

### Saldos y movimientos

Cada saldo cargado se compara contra el legado y, en el ensayo 3, contra el archivo
de la delta cuando la cuenta fue actualizada o creada por el corte. Los
movimientos se verifican importe a importe; para el ensayo 3 se exige además el
signo normalizado de los débitos. La reconstrucción de los movimientos originales
del legado depura los duplicados de reproceso por clave de negocio y normaliza el
signo de las comisiones invertidas, de modo que la suma por cuenta sea la que
generó el saldo antes de los defectos.

### Descuadres de saldo

Un descuadre es la diferencia entre el saldo final y la suma de movimientos más el
saldo de apertura:

```text
descuadre = saldo_final - saldo_apertura - suma(importes originales)
```

El umbral se parametriza en `config/reglas/conciliacion.yaml` y se aprueba en el
ADR-012: hasta ese monto el ajuste de apertura es
automático y evidenciado; por encima, el caso queda en revisión manual. Los
ensayos 1 y 2 detectan los mismos descuadres, pero no aplican ajustes.

### Libro mayor

El libro mayor se recompone desde las cuentas, los préstamos y los plazos:

- los saldos de cuentas se agrupan por producto original, recuperado del prefijo
  del identificador de cuenta, porque los defectos de producto no alteran el id;
- los préstamos aportan la suma de cuotas pendientes por préstamo, que es el
  capital con el que se generó el asiento 1.2.01, no el saldo crudo defectuoso;
- los plazos vigentes aportan el asiento 2.1.03;
- caja, intereses y patrimonio se derivan de los depósitos y de los préstamos
  (8 %, 0,4 % y 12 % respectivamente).

La comparación es contra las 28 filas cargadas del mayor. Un desfase se considera
tal cuando la diferencia supera la tolerancia de centavos; el ajuste se imputa a
resultados acumulados (3.3.01) y no reescribe las filas cargadas.

### Criterios de aceptación

Un ensayo es GO cuando cierran los conteos, los saldos, los movimientos y el libro
mayor, y además cumple las condiciones de calidad del corte: deduplicación de
clientes, corrección de signos y ajustes contables aplicados. Si quedan casos en
revisión manual documentados, la decisión es GO con observaciones.

## Conteos por entidad

<!-- INICIO AUTO: conciliacion-conteos -->
| Entidad | Origen | Cargados | No cargados | Revisados cargados | Fusionados | Diferencia |
|---|---:|---:|---:|---:|---:|---:|
| clientes | 61.800 | 59.179 | 927 | 2.065 | 1.694 | 0 |
| documentos | 69.000 | 67.717 | 1.283 | 0 | 0 | 0 |
| direcciones | 75.660 | 74.541 | 1.119 | 0 | 0 | 0 |
| cuentas | 90.059 | 76.302 | 13.757 | 3.748 | 0 | 0 |
| saldos | 90.059 | 76.302 | 13.757 | 0 | 0 | 0 |
| movimientos | 926.794 | 764.045 | 162.749 | 0 | 0 | 0 |
| prestamos | 18.000 | 15.686 | 2.314 | 458 | 0 | 0 |
| cuotas | 347.316 | 302.616 | 44.700 | 0 | 0 | 0 |
| plazos_fijos | 8.000 | 6.977 | 1.023 | 134 | 0 | 0 |
| mandatos | 25.000 | 21.363 | 3.637 | 0 | 0 | 0 |
| plan_cuentas | 48 | 48 | 0 | 0 | 0 | 0 |
| saldos_contables | 28 | 28 | 0 | 0 | 0 | 0 |

Las doce ecuaciones cierran en cero; los cargados se cuentan sin las filas de la delta y los no cargados surgen de cruzar cada rechazo contra la clave efectivamente presente en el destino, por lo que la igualdad no es tautologica: si un rechazo hubiera quedado cargado, o una fila se hubiera perdido, la diferencia lo delataria.
<!-- FIN AUTO: conciliacion-conteos -->

## Saldos de cuentas

<!-- INICIO AUTO: conciliacion-saldos -->
| Ensayo | Filas | Sin esperado | Diferencias | Monto cargado | Monto esperado |
|---|---:|---:|---:|---:|---:|
| v1 | 78.153 | 0 | 0 | 2.717.016.285,71 | 2.717.016.285,71 |
| v2 | 73.990 | 0 | 0 | 2.572.003.380,44 | 2.572.003.380,44 |
| v3 | 76.419 | 0 | 0 | 2.633.669.689,51 | 2.633.669.689,51 |
<!-- FIN AUTO: conciliacion-saldos -->

## Delta del corte

<!-- INICIO AUTO: conciliacion-delta -->
| Concepto | Cantidad |
|---|---:|
| Cuentas nuevas | 117 |
| Cuentas actualizadas | 4.902 |
| Saldos reemplazados | 4.902 |
| Saldos de cuentas no migradas (descartados) | 198 |
| Movimientos nuevos | 10.832 |

Los 117 saldos insertados y los 10.832 movimientos nuevos se verificaron importe a importe contra los archivos de la delta: 0 diferencias.
<!-- FIN AUTO: conciliacion-delta -->

## Movimientos

<!-- INICIO AUTO: conciliacion-movimientos -->
| Ensayo | Verificados | Diferencias | Signos invertidos en el legado | Signos cargados sin corregir |
|---|---:|---:|---:|---:|
| v1 | 810.366 | 0 | 3.068 | 2.760 |
| v2 | 755.530 | 0 | 3.068 | 2.573 |
| v3 | 764.045 | 0 | 3.068 | 0 |
<!-- FIN AUTO: conciliacion-movimientos -->

## Descuadres de saldo

<!-- INICIO AUTO: conciliacion-descuadres -->
| Ensayo | Cuentas analizadas | Con descuadre | Ajuste automatico | Revision manual | Monto absoluto | Monto neto en revision |
|---|---:|---:|---:|---:|---:|---:|
| v1 | 78.153 | 1.933 | 1.549 | 384 | 1.073.168,84 | -9.596,34 |
| v2 | 73.990 | 1.823 | 1.467 | 356 | 987.755,76 | -10.235,03 |
| v3 | 71.400 | 1.747 | 1.405 | 342 | 957.614,40 | -15.529,82 |

El ensayo 3 excluye del analisis las cuentas tocadas por la delta, cuyos saldos se concilian aparte contra el archivo del corte.
<!-- FIN AUTO: conciliacion-descuadres -->

## Libro mayor

<!-- INICIO AUTO: conciliacion-contable -->
| Codigo | Cuenta | Saldo cargado | Saldo esperado | Diferencia | Ajuste |
|---|---|---:|---:|---:|---:|
| 1.1.01 | CAJA | 238.441.689,22 | 240.379.985,93 | -1.938.296,71 | 1.938.296,71 |
| 1.2.03 | INTERESES DEVENGADOS A COBRAR | 4.828.000,91 | 4.841.948,75 | -13.947,84 | 13.947,84 |
| 2.1.01 | CAJAS DE AHORRO | -2.242.325.934,38 | -2.229.061.892,45 | -13.264.041,93 | 13.264.041,93 |
| 2.1.02 | CUENTAS CORRIENTES | -657.045.132,04 | -661.135.308,88 | 4.090.176,84 | -4.090.176,84 |
| 2.1.03 | PLAZOS FIJOS | -1.509.382.094,23 | -1.521.866.253,09 | 12.484.158,86 | -12.484.158,86 |
| 2.1.04 | CAJAS JUVENILES | -56.258.483,95 | -56.559.078,52 | 300.594,57 | -300.594,57 |
| 2.1.05 | CUENTAS INTERNACIONALES | -57.522.719,45 | -57.993.544,28 | 470.824,83 | -470.824,83 |
| 3.1.01 | CAPITAL SOCIAL | -358.791.617,84 | -360.569.978,90 | 1.778.361,06 | -1.778.361,06 |

20 de 28 cuentas del mayor concilian exactamente. Los desbalances internos (debe - haber - final) son 0. El asiento 1.2.01 se reconcilia contra la suma de cuotas pendientes: el capital crudo de prestamos difiere en 4.889,14 por 540 prestamos con saldo incongruente, efecto que no se traslada al mayor.
<!-- FIN AUTO: conciliacion-contable -->

## Ajustes de migración

<!-- INICIO AUTO: conciliacion-ajustes -->
| Codigo | Cuenta | Ajuste | Contrapartida | Estado |
|---|---|---:|---|---|
| 1.1.01 | CAJA | 1.938.296,71 | 3.3.01 | aplicado |
| 1.2.03 | INTERESES DEVENGADOS A COBRAR | 13.947,84 | 3.3.01 | aplicado |
| 2.1.01 | CAJAS DE AHORRO | 13.264.041,93 | 3.3.01 | aplicado |
| 2.1.02 | CUENTAS CORRIENTES | -4.090.176,84 | 3.3.01 | aplicado |
| 2.1.03 | PLAZOS FIJOS | -12.484.158,86 | 3.3.01 | aplicado |
| 2.1.04 | CAJAS JUVENILES | -300.594,57 | 3.3.01 | aplicado |
| 2.1.05 | CUENTAS INTERNACIONALES | -470.824,83 | 3.3.01 | aplicado |
| 3.1.01 | CAPITAL SOCIAL | -1.778.361,06 | 3.3.01 | aplicado |
| **Neto** |  | **-3.907.829,68** | 3.3.01 | aplicado |

El neto se imputa a resultados acumulados (3.3.01): los desfases se originan en el legado y el ajuste de migracion solo reconoce la diferencia contra la evidencia recalculada, sin reescribir las filas cargadas.
<!-- FIN AUTO: conciliacion-ajustes -->

## Go / no-go

<!-- INICIO AUTO: conciliacion-go-no-go -->
| Ensayo | Decision | Criterios incumplidos | Observaciones |
|---|---|---|---|
| v1 | NO-GO | Deduplicacion de clientes, Correccion de signos, Descuadres de saldo, Ajustes contables | Carga sin deduplicacion de clientes duplicados. 2760 movimientos con signo invertido cargados en el destino. 8 desfases contables sin ajuste documentado. |
| v2 | NO-GO | Correccion de signos, Descuadres de saldo, Ajustes contables | 2573 movimientos con signo invertido cargados en el destino. 8 desfases contables sin ajuste documentado. |
| v3 | GO con observaciones | ninguno | 342 descuadres graves derivados a revision manual con evidencia en el archivo de ajustes. |
<!-- FIN AUTO: conciliacion-go-no-go -->

## Conclusiones

El ensayo 3 es el único aceptable para el corte. Los ensayos 1 y 2 concilian
volúmenes y saldos, pero cargan movimientos con signo invertido y desfases
contables sin ajuste; el ensayo 1 además no deduplica clientes. El ensayo 3
corrige los signos, aplica los ocho ajustes contables respaldados y deja los
descuadres graves en revisión manual con evidencia, condición suficiente para un
GO con observaciones.

La conciliación también delimita la responsabilidad: los desfases contables, los
descuadres de saldo, los documentos inválidos y los movimientos imposibles o
duplicados son defectos del legado, no del proceso de migración. El pipeline los
detecta, los rechaza o los ajusta, y deja la traza para que el negocio regularice
el origen.

## Referencias

- [Pipeline de migración](../06-pipeline/pipeline-de-migracion.md)
- [Decisiones de diseño](../03-analisis-de-brechas/decisiones-de-diseno.md)
- [ADR-012: ajustes de migración](../decisiones/ADR-012-ajustes-de-migracion.md)

## Anexos

| Artefacto | Contenido |
|---|---|
| `datos/resultados/conciliacion/conciliacion_ensayo_v{n}.json` | Resultado completo por ensayo: conteos, saldos, movimientos, descuadres, contable y go/no-go. |
| `datos/resultados/conciliacion/conciliacion_ensayo_v{n}_descuadres.csv` | Descuadres de las cuentas cargadas con clasificación y ajuste propuesto. |
| `datos/resultados/conciliacion/conciliacion_ensayo_v{n}_desfases.csv` | Desfases del libro mayor con el ajuste y su contrapartida. |
