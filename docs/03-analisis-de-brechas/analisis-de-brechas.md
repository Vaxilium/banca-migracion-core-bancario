# Análisis de brechas funcionales

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

Comparar, capacidad por capacidad, lo que ofrece el core legado con lo que ofrece el
core nuevo, clasificar cada brecha, priorizarla y asignar responsable; y derivar los
requisitos funcionales y no funcionales que gobiernan la construcción y las pruebas.

## Alcance

Las 15 capacidades del [mapa de capacidades](../02-analisis-as-is/mapa-de-capacidades.md)
más brechas transversales (datos, pipeline, satélites y seguridad).

## Método

**Tipos de brecha**

| Tipo | Significado | Tratamiento |
|---|---|---|
| `cubierta` | El core nuevo cubre la capacidad sin trabajo adicional | Verificar en pruebas de aceptación. |
| `configuracion` | Se cubre con parametrización | Cargar parámetros y validar en UAT. |
| `desarrollo` | Requiere desarrollo o regla nueva | Planificar, mapear y probar. |
| `proceso_manual` | Requiere proceso operativo (revisión, decisión, conciliación) | Documentar en runbook y capacitar. |
| `descontinuar` | La capacidad o producto no continúa | Excluir y comunicar (ver ADR-005). |

**Prioridad (MoSCoW):** Must (imprescindible para el corte), Should (importante),
Could (deseable), Won't (no se hará en esta migración).

**Esfuerzo:** S (hasta 1 semana), M (2 a 4 semanas), L (1 a 3 meses), XL (más de 3
meses) — estimaciones relativas del equipo, no compromisos de cronograma.

**Riesgo funcional:** alto (afecta saldos, contabilidad o cumplimiento), medio,
bajo.

## Resumen de la matriz

<!-- INICIO AUTO: resumen-brechas -->
Total de brechas analizadas: **44**.

**Distribucion por tipo**

| Tipo | Brechas |
|---|---|
| desarrollo | 23 |
| configuracion | 10 |
| proceso_manual | 5 |
| descontinuar | 3 |
| cubierta | 3 |

**Distribucion por prioridad**

| Prioridad | Brechas |
|---|---|
| Must | 32 |
| Should | 9 |
| Could | 2 |
| Won't | 1 |

**Distribucion por esfuerzo**

| Esfuerzo | Brechas |
|---|---|
| S | 19 |
| M | 18 |
| L | 7 |

**Distribucion por riesgo**

| Riesgo | Brechas |
|---|---|
| alto | 17 |
| medio | 15 |
| bajo | 12 |

Brechas que requieren trabajo del proyecto (todas menos `cubierta`): **41** de 44.
Porcentaje de brechas Must: **72.7 %**.
<!-- FIN AUTO: resumen-brechas -->

## Matriz completa

La versión completa con descripciones, responsables y dolores asociados está en
[matriz-brechas.csv](matriz-brechas.csv) y [matriz-brechas.xlsx](matriz-brechas.xlsx).

<!-- INICIO AUTO: matriz-brechas -->
| ID | Capacidad | Brecha | Tipo | Esf. | Riesgo | MoSCoW | Requisitos |
|---|---|---|---|---|---|---|---|
| BR-001 | CAP-01 Gestion de clientes | Deduplicacion de clientes por similitud de nombre y documento | desarrollo | M | alto | Must | RF-001, RF-002 |
| BR-002 | CAP-01 Gestion de clientes | Validacion de documentos con digito verificador | desarrollo | M | alto | Must | RF-002 |
| BR-003 | CAP-01 Gestion de clientes | Exclusion de titulares fallecidos con proceso de sucesion | proceso_manual | S | medio | Must | RF-003 |
| BR-004 | CAP-01 Gestion de clientes | Contacto ampliado (correo y celular) obligatorio y validado | configuracion | S | bajo | Must | RF-004 |
| BR-005 | CAP-02 Gestion documental | Vigencia y vencimiento de documentos con alertas | desarrollo | M | medio | Should | RF-005 |
| BR-006 | CAP-02 Gestion documental | Documentos repetidos entre clientes distintos | proceso_manual | S | alto | Should | RF-006 |
| BR-007 | CAP-03 Gestion de direcciones | Normalizacion de direcciones incompletas | desarrollo | S | bajo | Must | RF-007 |
| BR-008 | CAP-03 Gestion de direcciones | Extraccion de datos embebidos en texto libre | desarrollo | M | medio | Should | RF-008 |
| BR-009 | CAP-04 Cajas de ahorro | Parametros de producto configurables por el banco | configuracion | S | bajo | Must | RF-009 |
| BR-010 | CAP-04 Cajas de ahorro | Estados legados desconocidos pasan a revision manual | proceso_manual | S | medio | Must | RF-010 |
| BR-011 | CAP-05 Cuentas corrientes | Regimen de descubierto y comision de mantenimiento | configuracion | M | medio | Must | RF-011 |
| BR-012 | CAP-05 Cuentas corrientes | Impuesto sobre debitos y creditos automatizado | desarrollo | M | alto | Must | RF-012 |
| BR-013 | CAP-06 Plazos fijos | Renovacion automatica de plazos fijos configurable | configuracion | S | bajo | Should | RF-013 |
| BR-014 | CAP-06 Plazos fijos | Cancelacion anticipada con prorrateo de intereses | desarrollo | M | medio | Should | RF-014 |
| BR-015 | CAP-07 Prestamos personales | Cronogramas de cuotas con seguros asociados | desarrollo | L | alto | Must | RF-015 |
| BR-016 | CAP-07 Prestamos personales | Mora y refinanciaciones | desarrollo | L | alto | Must | RF-016 |
| BR-017 | CAP-07 Prestamos personales | Prestamos hipotecarios permanecen fuera del alcance | descontinuar | S | bajo | Must | RF-017 |
| BR-018 | CAP-08 Tarjetas de debito | Emision y bloqueo de tarjetas de debito en linea | desarrollo | M | medio | Must | RF-018 |
| BR-019 | CAP-08 Tarjetas de debito | Modelo de tarjeta de debito asociada a cuenta | configuracion | S | bajo | Must | RF-019 |
| BR-020 | CAP-09 Medios de pago | Debito automatico por mandatos migrados | desarrollo | L | alto | Must | RF-020 |
| BR-021 | CAP-09 Medios de pago | Transferencias inmediatas por API | desarrollo | M | alto | Must | RF-021 |
| BR-022 | CAP-10 Contabilidad de productos | Plan de cuentas y mapeo producto cuenta contable | configuracion | M | alto | Must | RF-022 |
| BR-023 | CAP-10 Contabilidad de productos | Asientos automaticos por evento de negocio | desarrollo | L | alto | Must | RF-023 |
| BR-024 | CAP-10 Contabilidad de productos | Conciliacion contable automatizada del pipeline | desarrollo | M | alto | Must | RF-024 |
| BR-025 | CAP-11 Intereses y comisiones | Motor de intereses diario | desarrollo | L | alto | Must | RF-025 |
| BR-026 | CAP-11 Intereses y comisiones | Comisiones configurables y reversibles | configuracion | M | medio | Must | RF-026 |
| BR-027 | CAP-12 Reportes regulatorios | Reportes regulatorios generados desde el modelo destino | desarrollo | L | alto | Must | RF-027 |
| BR-028 | CAP-12 Reportes regulatorios | Retencion y trazabilidad de informacion migrada | desarrollo | M | medio | Must | RF-028 |
| BR-029 | CAP-13 Consultas y extractos | Extractos y consultas en linea | desarrollo | M | medio | Should | RF-029 |
| BR-030 | CAP-13 Consultas y extractos | Historial de movimientos de 12 meses | cubierta | L | medio | Must | RF-030 |
| BR-031 | CAP-14 Cobranzas y mora | Reintentos programables de debito automatico | configuracion | S | medio | Should | RF-031 |
| BR-032 | CAP-14 Cobranzas y mora | Avisos de mora multicanal | desarrollo | M | bajo | Could | RF-032 |
| BR-033 | CAP-15 Seguridad y accesos | Pista de auditoria por operacion | desarrollo | M | alto | Must | RF-033 |
| BR-034 | CAP-15 Seguridad y accesos | Segregacion de funciones y perfiles | configuracion | S | alto | Must | RF-034 |
| BR-035 | TRV Transversal | Conciliacion de saldos de cuentas en el pipeline | desarrollo | M | alto | Must | RF-036 |
| BR-036 | TRV Transversal | Bitacora de ejecucion y rechazos con motivo | desarrollo | S | medio | Must | RF-037 |
| BR-037 | TRV Transversal | Interfaces por archivo con sistemas satelites | proceso_manual | M | medio | Should | RF-038 |
| BR-038 | TRV Transversal | Productos TR, PH y PX sin equivalente en el destino | descontinuar | S | bajo | Must | RF-039 |
| BR-039 | TRV Transversal | Tipos de firma y condiciones de cuenta simplificadas | configuracion | S | bajo | Could | RF-040 |
| BR-040 | TRV Transversal | Descontinuar libretas fisicas y sellos manuales | descontinuar | S | bajo | Won't | - |
| BR-041 | TRV Transversal | Depositos y extracciones en caja | cubierta | S | bajo | Must | RF-041 |
| BR-042 | TRV Transversal | Enmascaramiento de datos en entornos de prueba | desarrollo | S | alto | Must | RNF-003 |
| BR-043 | TRV Transversal | Consulta de saldos y movimientos por API | cubierta | S | bajo | Must | RF-042 |
| BR-044 | TRV Transversal | Conciliacion manual de archivos satelite durante la transicion | proceso_manual | S | medio | Should | RF-038 |
<!-- FIN AUTO: matriz-brechas -->

## Requisitos derivados

Los requisitos funcionales y no funcionales con identificador único, prioridad y
criterio de aceptación se publican en [requisitos.md](requisitos.md), generado desde
la misma fuente que esta matriz.

## Decisiones de diseño

Las decisiones de tratamiento (duplicados, estados desconocidos, productos fuera de
alcance, entre otras) se documentan en [decisiones de diseño](decisiones-de-diseno.md)
y en el [registro de decisiones](../decisiones/ADR-005-productos-sin-equivalente.md).

## Criterios de cierre de brechas

1. Toda brecha `Must` está cerrada o cuenta con decisión de exclusión aprobada.
2. Ninguna brecha `desarrollo` queda sin requisito asociado ni sin caso de prueba.
3. Las brechas `proceso_manual` están reflejadas en el runbook de corte y en la
   capacitación.
4. Las brechas `descontinuar` están comunicadas y sus rechazos controlados en el
   pipeline.

## Supuestos

- La comparación legado–nuevo se basa en el catálogo de productos y el mapa de
  capacidades; se refina con el proveedor durante el diseño detallado.
- Las estimaciones de esfuerzo son ilustrativas para un equipo de 8 personas.

## Riesgos y dependencias

| Riesgo | Mitigación |
|---|---|
| Brechas de desarrollo subestimadas | Reprogramación temprana vía comité si un ensayo lo evidencia. |
| Capacidad del core nuevo distinta a la documentada | Prueba técnica temprana por capacidad. |
| Aprobaciones tardías de Contabilidad | Comité de datos semanal con Contabilidad. |

## Glosario

Ver [glosario único](../glosario.md).
