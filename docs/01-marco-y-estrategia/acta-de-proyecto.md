# Acta de proyecto: Migración del core bancario

| Proyecto | Migración del core bancario — Banco Meridiano Austral (entidad ficticia) |
|---|---|
| **Código** | PRY-CORE-2026 |
| **Versión** | 1.0 |
| **Fecha** | 19/10/2026 |
| **Autor** | Franco Tilleria, Analista de Negocios |
| **Estado** | Aprobado |

## Control de versiones

| Versión | Fecha | Autor | Cambio |
|---|---|---|---|
| 1.0 | 19/10/2026 | Franco Tilleria | Versión inicial aprobada por el comité directivo. |

## Propósito

Formalizar la iniciación del proyecto de migración del core bancario legado hacia un
core moderno, estableciendo objetivos, alcance, entregables, gobierno y criterios de
éxito. Este documento habilita el inicio del análisis y compromete a las áreas.

## Alcance

**Incluido:**

- Productos: cajas de ahorro, cuentas corrientes, depósitos a plazo fijo, préstamos
  personales y tarjetas de débito como producto asociado a la cuenta.
- Entidades de datos: clientes y documentos, direcciones, cuentas, saldos, movimientos
  históricos (ventana de 12 meses), préstamos y cronogramas de cuotas, plazos fijos,
  mandatos de débito automático, plan de cuentas contable y saldos del libro mayor.
- Actividades: análisis AS-IS, brechas funcionales, mapeo de datos, construcción del
  pipeline, tres ensayos de migración, conciliación, pruebas, corte, reversa, gestión
  del cambio, riesgos y trazabilidad.

**Excluido (documentado en [ADR-003](../decisiones/ADR-003-alcance-funcional.md)):**

- Tarjetas de crédito, comercio exterior e inversiones. Permanecen en sistemas
  satélite y no se migran en esta iniciativa.

## Objetivos del proyecto

1. Migrar el 100 % de las entidades incluidas con conciliación contable completa.
2. Reducir el cierre diario de 9 horas (batch nocturno) a menos de 2 horas.
3. Habilitar operación casi en línea y APIs para canales digitales.
4. Ejecutar el corte en una única ventana de fin de semana con plan de reversa probado.
5. Dejar trazabilidad completa requisito → brecha → mapeo → regla → prueba → evidencia.

## Entregables clave

| Entregable | Fase | Responsable |
|---|---|---|
| Marco y estrategia aprobados | 1 | Analista de Negocios |
| Análisis AS-IS y brechas funcionales | 2–3 | Analista de Negocios + áreas |
| Extracción sintética del legado y diseños de registro | 4 | Datos + Analista de Negocios |
| Modelo de datos y mapeo campo a campo | 5 | Analista de Negocios + Arquitectura |
| Pipeline con tres ensayos y carga delta | 6 | Ingeniería de datos |
| Informe de conciliación por ensayo | 7 | Analista de Negocios + Contabilidad |
| Casos de prueba y registro de defectos | 8 | QA + Analista de Negocios |
| Runbook de corte y plan de reversa | 9 | PMO + Operaciones |
| Plan de gestión del cambio y capacitación | 10 | Recursos Humanos + Sucursales |
| Matriz de riesgos y controles | 11 | Riesgo + Cumplimiento |
| Matriz de trazabilidad | 12 | Analista de Negocios |

## Hitos

| Hito | Fecha | Criterio de cumplimiento |
|---|---|---|
| H1: Aprobación del marco | 17/07/2026 | Acta y estrategia firmadas. |
| H2: AS-IS y brechas cerradas | 21/08/2026 | Matriz de brechas priorizada. |
| H3: Datos de origen disponibles | 04/09/2026 | Extracción completa y perfilado. |
| H4: Ensayo 1 ejecutado | 18/09/2026 | Bitácora y conciliación del ensayo. |
| H5: Ensayo 3 y ensayo general | 16/10/2026 | Criterios de aceptación cumplidos. |
| H6: Corte | 24–25/10/2026 | Semáforos go/no-go en verde. |
| H7: Cierre de hypercare | 23/11/2026 | Indicadores de estabilización cumplidos. |

## Supuestos

- El proveedor del core legado mantiene soporte hasta marzo de 2027; después, el
  costo de extensión de soporte se vuelve inviable.
- La ventana de corte acordada es el fin de semana del 24 y 25 de octubre de 2026.
- El equipo funcional y técnico está disponible a tiempo completo durante septiembre
  y octubre.
- Las cifras económicas del [caso de negocio](caso-de-negocio.md) son ilustrativas y
  no corresponden a una entidad real.

## Riesgos y dependencias

| Riesgo/dependencia | Tipo | Mitigación |
|---|---|---|
| Calidad del dato legado peor a la esperada | Riesgo | Perfilado temprano, reglas versionadas y tres ensayos. |
| Indisponibilidad de ventana de corte | Dependencia | Fecha de respaldo acordada (07–08/11/2026). |
| Rotación del personal clave | Riesgo | Documentación en repositorio y matriz de conocimiento. |
| Congelamiento de cambios no respetado | Riesgo | Comité de corte con potestad de detener. |

## Criterios de éxito

1. Conciliación contable al 100 % (directa o con ajuste de migración evidenciado).
2. Tasa de rechazos del último ensayo dentro de la tolerancia definida por entidad.
3. Cero defectos críticos o altos abiertos al momento del corte.
4. Corte ejecutado dentro de la ventana, con reversa no activada.
5. Indicadores de hypercare y adopción cumplidos al día 30.

## Glosario

Ver [glosario único](../glosario.md).
