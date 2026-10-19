# Runbook de corte y reversa

| Proyecto | Fecha | Autor | Estado |
|---|---|---|---|
| Migración del core bancario — Banco Meridiano Austral | 19/10/2026 | Franco Tilleria, Analista de Negocios | Aprobado |

## Control de versiones

| Versión | Fecha | Autor | Cambio |
|---|---|---|---|
| 1.0 | 19/10/2026 | Franco Tilleria | Runbook del corte del 24/10/2026 y plan de reversa. |

## Propósito

Ejecutar el pasaje del legado al core nuevo en una ventana controlada, con controles
de entrada y salida verificables, una decisión go/no-go firmada y un procedimiento de
reversa probado. El runbook es operativo: cada paso tiene responsable, evidencia y
criterio de aceptación.

> Entidad y datos 100 % ficticios. El corte se simula sobre el legado sintético y los
> artefactos del repositorio; no existe operatoria real.

## Datos del corte

| Dato | Valor |
|---|---|
| Fecha de corte | Sábado 24/10/2026 |
| Extracción base | 09/10/2026 |
| Fecha de apertura | Lunes 26/10/2026, sucursales 08:00 |
| Ventana técnica | 24/10/2026 20:00 a 25/10/2026 06:00 |
| Reglas | Ensayo 3 (`reglas_v3.yaml`) |
| Estrategia | Big-bang con delta técnico ([ADR-013](../decisiones/ADR-013-estrategia-de-corte-y-reversa.md)) |
| RTO / RPO | 4 horas / 15 minutos (RNF-010) |

## Objetivos del corte

1. Cargar el universo completo y la delta del corte sin pérdida de registros.
2. Conciliar conteos, saldos, movimientos y libro mayor contra el legado.
3. Dejar los ajustes y observaciones con evidencia y dueño.
4. Abrir con canales y procesos críticos verificados.
5. Poder volver al legado dentro de la ventana si un disparador de reversa se activa.

## Roles y responsabilidades

| Rol | Responsabilidad en el corte | Titular |
|---|---|---|
| Director del programa | Aprueba el go/no-go y autoriza la reversa. | Comité directivo |
| Líder de migración | Coordina la ventana, ejecuta el pipeline y custodia la evidencia. | Franco Tilleria |
| Responsable de datos | Extrae la delta, valida archivos y respaldos. | Equipo de datos |
| Contabilidad | Concilia saldos, aprueba ajustes y valida el mayor. | Contador general |
| Operaciones y TI | Congela batch, conmuta canales, monitorea y ejecuta la reversa técnica. | Jefe de operaciones |
| Seguridad y cumplimiento | Controla accesos, datos sensibles y documentación observada. | Oficial de cumplimiento |
| Negocio | Ejecuta los smoke tests y valida la experiencia de sucursal. | Gerente de red |
| Mesa de ayuda | Comunica y registra incidentes del corte. | Jefe de soporte |

## Pendientes de decisión antes del congelamiento

| Pendiente | Cantidad | Dueño | Tratamiento | ¿Bloquea? |
|---|---:|---|---|---|
| Descuadres graves | 342 | Contabilidad | Revisión caso a caso; ajuste manual aprobado o aceptación formal. | Sí, con aprobación del comité |
| Cuentas con estado desconocido (X) cargadas informativas | 3.748 | Operaciones | Decisión registrada antes del corte (RF-010). | Sí |
| Clientes con documento observado | 2.065 | Cumplimiento | Validación documental o bloqueo de productos. | No, con control compensatorio |
| Préstamos con saldo incongruente | 540 | Contabilidad | Conciliación contra cuotas pendientes; diferencia 4.889,14 no trasladada al mayor. | No |
| Plazos con vencimiento incongruente | 134 | Operaciones | Regularización posterior con seguimiento diario. | No |
| Clientes no migrados por fecha imposible | 927 | Negocio | Comunicación y alta manual posterior al corte. | No |
| Saldos de la delta descartados | 198 | Datos | Corresponden a cuentas que no migran; se documentan. | No |

## Prerrequisitos

### T-7 días

- [ ] Runbook y ADR-013 aprobados y difundidos.
- [ ] Pendientes de decisión con dueño y fecha; comité informado del riesgo residual.
- [ ] Respaldos del legado probados y restaurados en ambiente de contingencia.
- [ ] Simulacro de reversa ejecutado con tiempos medidos.
- [ ] Accesos y credenciales vigentes para todos los roles.
- [ ] Plan de comunicaciones y plantillas listas.

### T-2 días

- [ ] Capacidad de disco, CPU y conexiones verificada para la carga completa.
- [ ] Jobs batch y schedulers del legado deshabilitados para la ventana.
- [ ] Monitoreo y alertas del corte configurados.
- [ ] Extracción de corte validada contra los diseños de ancho fijo.
- [ ] Suites de pruebas y conciliación ejecutadas sobre el ensayo 3.
- [ ] Mesa de ayuda con guion de consultas y escalamiento.

### T-1 día

- [ ] Comunicación de congelamiento a usuarios y sucursales.
- [ ] Bloqueo de altas, modificaciones y productos nuevos.
- [ ] Respaldo completo del legado y verificación de integridad.
- [ ] Confirmación de asistencia de todos los roles.
- [ ] Checklist de la ventana impreso y canal de guerra abierto.

## Cronograma de la ventana

| Hora | Actividad | Responsable | Evidencia |
|---|---|---|---|
| Sáb 00:00 | Congelamiento de cambios y suspensión de batch | Operaciones | Correo y ticket de freeze |
| Sáb 19:30 | Canales en modo consulta y bloqueo de escritura | Operaciones | Estado de canales |
| Sáb 19:45 | Respaldo completo del legado y verificación | TI | Hash y log de restauración |
| Sáb 20:00 | Inicio de la ventana técnica | Migración | Acta de inicio |
| Sáb 20:30 | Extracción delta 09/10 a 24/10 | Datos | Archivos y suma de control |
| Sáb 21:00 | Carga con pipeline v3 (completa + delta) | Migración | Bitácora y resumen |
| Sáb 22:30 | Validación de contratos y conteos por entidad | Migración | Log de contratos |
| Sáb 23:30 | Conciliación de saldos, movimientos y mayor | Contabilidad | JSON y CSV de conciliación |
| Dom 00:30 | Suite de pruebas y smoke tests técnicos | Migración | Reporte JUnit |
| Dom 01:00 | Comité go/no-go | Director del programa | Acta firmada |
| Dom 01:30 | Apertura técnica y smoke tests de negocio | Operaciones y negocio | Checklist de apertura |
| Dom 02:00 | Canales digitales habilitados | Operaciones | Monitoreo en verde |
| Dom 04:00 | Límite de reversa | Director del programa | Decisión registrada |
| Dom 06:00 | Fin de ventana y cierre del puente | Migración | Informe de corte |

## Procedimiento

1. **Congelar**: suspender batch, altas y modificaciones; registrar hora y responsable.
2. **Respaldar**: con canales en consulta, respaldo completo del legado, verificación
   de restauración y hash.
3. **Extraer la delta**: generar cuentas, saldos y movimientos del corte; validar
   longitud de registros y sumas de control.
4. **Cargar**: ejecutar el pipeline v3 con delta; si una entidad falla el contrato, se
   detiene la carga y se evalúa la reversa.
5. **Conciliar**: ejecutar la conciliación de los tres ensayos; revisar conteos,
   saldos, movimientos, descuadres, libro mayor y go/no-go.
6. **Probar**: correr la suite completa y los smoke tests de canales, consultas,
   débitos y extractos.
7. **Decidir**: el comité revisa evidencia, pendientes y observaciones; firma go/no-go.
8. **Abrir**: habilitar canales y sucursales según el cronograma; monitorear.
9. **Hipercare**: war room diario durante 30 días y salida formal.

## Verificación y evidencia

| Control | Fuente | Criterio de aceptación | Ensayo 3 |
|---|---|---|---|
| Conteos por entidad | `conciliacion_ensayo_v3.json` | Diferencia cero en las doce entidades | Cumple |
| Saldos de cuentas | `conciliacion_ensayo_v3.json` | Cero diferencias y mismo monto | Cumple |
| Movimientos | `conciliacion_ensayo_v3.json` | Cero diferencias importe a importe | Cumple |
| Descuadres | `conciliacion_ensayo_v3_descuadres.csv` | Leves ajustados; graves con revisión y dueño | 1.405 automáticos, 342 en revisión |
| Libro mayor | `conciliacion_ensayo_v3_desfases.csv` | Desfases identificados y ajustados | 8 ajustes, neto −3.907.829,68 |
| Contratos de destino | `config/contratos/*.json` y bitácora | Muestras conformes | Cumple |
| Pruebas | `datos/resultados/junit.xml` | Sin fallas bloqueantes | 30 pasan, 1 omitida por muestras |
| Delta | `resumen_ensayo_v3.json` | Cuentas y movimientos del corte incorporados | 117 cuentas nuevas, 4.902 actualizadas, 10.832 movimientos |
| Go/no-go | `conciliacion_ensayo_v3.json` | Decisión firmada | GO con observaciones |

La carga del ensayo 3 totaliza 1.476.247 filas. La diferencia de 4.889,14 entre el
capital crudo de préstamos y la suma de cuotas pendientes está explicada por 540
préstamos incongruentes y no se traslada al libro mayor (ver informe de conciliación).

## Smoke tests de apertura

| Proceso | Verificación | Responsable |
|---|---|---|
| Consulta de saldo | Cliente de prueba ve el saldo conciliado de la cuenta. | Negocio |
| Débito automático | Mandato activo se ejecuta una sola vez y descuenta el importe correcto. | Operaciones |
| Extracción de fondos | Caja registra movimiento y actualiza saldo en línea. | Negocio |
| Extracto | Últimos 12 meses disponibles y ordenados. | Negocio |
| Préstamo | Cuota vigente, saldo y cronograma coinciden con el legado. | Contabilidad |
| Plazo fijo | Constitución y vencimiento respetan la fecha y tasa migradas. | Negocio |
| Canales digitales | Autenticación, consulta y transferencia responden en verde. | TI |

## Disparadores de reversa

Se declara reversa si ocurre cualquiera de estas condiciones y no se resuelve dentro de
60 minutos:

1. Pérdida o duplicación de registros no explicada por la conciliación.
2. Diferencia de saldo material sin causa identificada.
3. Falla de canales o batch crítico que impide operar.
4. Libro mayor que no concilia o ajuste no aprobado por Contabilidad.
5. Imposibilidad de completar la carga dentro de la ventana.

La decisión la toma el director del programa con Contabilidad y TI. La reversa se
autoriza antes de las 04:00 del domingo.

## Procedimiento de reversa

1. **Declarar**: registrar hora, causa, alcance y responsable; activar el comité.
2. **Detener**: congelar la carga y poner el destino en solo lectura; no borrar
   artefactos.
3. **Conmutar**: redirigir canales al legado y verificar autenticación y consultas.
4. **Restaurar**: restaurar el respaldo del legado previo al corte y validar
   integridad; el respaldo se toma a las 19:45, después de poner los canales en modo
   consulta (19:30), por lo que no hay transacciones nuevas que perder (RPO 0).
5. **Validar**: cuadrar saldos, préstamos y plazos del legado; ejecutar smoke tests.
6. **Comunicar**: avisar a sucursales, mesa de ayuda y comité; publicar estado.
7. **Preservar**: archivar logs, conciliación fallida y artefactos para el postmortem.
8. **Replanificar**: corregir la causa, repetir el ensayo y fijar nueva fecha.

La reversa no migra datos del core nuevo al legado. Cualquier transacción aceptada
por error en el destino se concilia manualmente y se regulariza en el legado.

## Comunicaciones

| Momento | Audiencia | Canal | Mensaje |
|---|---|---|---|
| T-7 | Comité y dueños de proceso | Correo y reunión | Fecha, alcance y pendientes. |
| T-1 | Sucursales y usuarios | Circular interna | Congelamiento y ventana. |
| Inicio | Mesa de ayuda y TI | Canal de guerra | Inicio de ventana y roles. |
| Go/no-go | Comité y negocio | Llamada y correo | Decisión y observaciones. |
| Apertura | Sucursales y clientes | Intranet y sitio | Canales habilitados. |
| Reversa | Todos | Canal de incidentes | Alcance y próximo aviso. |
| Cierre | Comité | Informe | Resultado y evidencias. |

## Hipercare

- War room diario a las 08:00 durante los primeros 10 días; luego tres veces por
  semana hasta el día 30.
- Métricas: disponibilidad, incidentes por severidad, batch fallidos, conciliación
  diaria, reclamos y tiempos de atención.
- Criterio de salida: cinco días consecutivos sin incidentes severos, conciliación
  diaria en cero y backlog de reclamos dentro de la meta.

## Riesgos del corte

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Delta incompleta o fuera de horario | Saldos desactualizados | Doble extracción y suma de control; validar contra resumen. |
| Respaldo del legado no restaurable | Reversa inviable | Simulacro de restauración y hash verificado. |
| Pendientes sin decisión | Apertura con observaciones no aprobadas | Comité previo y bloqueo de go. |
| Falla de conmutación de canales | Indisponibilidad | Prueba de switch y plan manual de contingencia. |
| Diferencia post-apertura | Riesgo contable | Conciliación diaria y ajustes con evidencia. |
| Fatiga del equipo | Error operativo | Roles de relevo y ventana acotada. |

## Anexos

- [Informe de conciliación](../07-conciliacion/informe-de-conciliacion.md)
- [Pipeline de migración](../06-pipeline/pipeline-de-migracion.md)
- [Estrategia de pruebas](../08-pruebas/estrategia-de-pruebas.md)
- [ADR-013: estrategia de corte y reversa](../decisiones/ADR-013-estrategia-de-corte-y-reversa.md)
- Artefactos: `datos/resultados/conciliacion/`, `datos/resultados/junit.xml`,
  `datos/resultados/resumen_ensayo_v3.json`, `datos/bitacora/`.
