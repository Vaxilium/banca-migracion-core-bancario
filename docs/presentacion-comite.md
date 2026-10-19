# Presentación al comité directivo

**Migración del core bancario — Banco Meridiano Austral**
Franco Tilleria · Analista de Negocios · 19/10/2026

Entidad y datos 100 % ficticios. Cifras generadas por el pipeline del repositorio.

---

## 1. Qué decidimos hoy

- Aprobar el **ensayo 3** como versión de corte.
- Autorizar la ventana del **24/10/2026**.
- Aceptar las observaciones y los pendientes con dueño.
- Habilitar la **reversa** si se activa un disparador antes de las 04:00 del domingo.

---

## 2. El problema

- Legado con datos inconsistentes y conciliación manual.
- Procesos batch rígidos y reprocesos sin trazabilidad homogénea.
- Riesgo operativo y contable al cambiar de core.
- Necesidad de demostrar que cada saldo del destino se explica contra el origen.

---

## 3. Enfoque de la migración

1. Análisis AS-IS y brechas funcionales.
2. Modelo destino y reglas versionadas.
3. Tres ensayos con la misma semilla y verdad de terreno.
4. Conciliación de conteos, saldos, movimientos y libro mayor.
5. Corte big-bang con delta y reversa probada.

---

## 4. Arquitectura del pipeline

```text
Legado ancho fijo -> extracción -> transformación por reglas -> contratos
      -> Parquet destino -> delta del corte -> conciliación -> tablero
```

- DuckDB embebido, sin infraestructura externa.
- Bitácora y rechazos por fila.
- Reproducible con `make todo` y semilla 20261019.

---

## 5. Tres ensayos, una decisión

| Ensayo | Enfoque | Resultado |
|---|---|---|
| v1 | Línea base con defectos deliberados | NO-GO |
| v2 | Corrige fechas y deduplica clientes | NO-GO |
| v3 | Corrige signos, datos finos y ajustes | GO con observaciones |

El ensayo 3 carga **1.476.247 filas** e incorpora la delta del corte.

---

## 6. Conciliación

- **12 de 12** entidades con conteo cerrado.
- **0** diferencias de saldo y de movimientos.
- **1.747** descuadres: 1.405 automáticos y 342 en revisión.
- **8** desfases contables identificados, con ajuste neto de **−3.907.829,68**.
- **20 de 28** cuentas del mayor conciliadas; **0** desbalances internos.

---

## 7. Por qué el ensayo 3 es confiable

- Reconstruye los movimientos originales: elimina 18.172 duplicados de reproceso y
  corrige 3.068 signos invertidos.
- Detecta los descuadres contra la verdad de terreno: 2.251 casos, sin falsos
  positivos ni negativos en el universo cargado.
- Recalcula el mayor desde cuentas, cuotas pendientes y plazos, no desde el saldo que
  se quiere validar.
- Deja los ajustes con evidencia y contrapartida en resultados acumulados.

---

## 8. Delta y corte

| Concepto | Cantidad |
|---|---:|
| Cuentas nuevas | 117 |
| Cuentas actualizadas | 4.902 |
| Saldos reemplazados | 4.902 |
| Movimientos nuevos | 10.832 |
| Saldos descartados (cuentas no migradas) | 198 |

Ventana: sábado 24/10 20:00 a domingo 25/10 06:00. Apertura de sucursales: lunes
26/10 a las 08:00.

---

## 9. Pendientes que el comité debe conocer

| Pendiente | Cantidad | Dueño |
|---|---:|---|
| Descuadres graves en revisión | 342 | Contabilidad |
| Cuentas en estado desconocido | 3.748 | Operaciones |
| Documentos observados | 2.065 | Cumplimiento |
| Préstamos con saldo incongruente | 540 | Contabilidad |
| Clientes no migrados por fecha imposible | 927 | Negocio |

No afectan las ecuaciones de control, pero requieren decisión y seguimiento.

---

## 10. Reversa y continuidad

- Reversa por conmutación al legado y restauración del respaldo, no por migración
  inversa.
- RTO 4 horas y RPO 15 minutos.
- Respaldo a las 19:45, con canales en consulta desde las 19:30.
- Límite de reversa: 04:00 del domingo.
- Hipercare de 30 días con war room y conciliación diaria.

---

## 11. Lo que pedimos

1. Aprobar el ensayo 3 y la ventana de corte.
2. Confirmar dueños y fechas para los pendientes.
3. Autorizar el plan de comunicación y capacitación.
4. Firmar el go/no-go el domingo 25/10 a la 01:00.

---

## 12. Contacto

- LinkedIn: <https://www.linkedin.com/in/franco-tilleria-centurion>
- GitHub: <https://github.com/Vaxilium>

Documentación completa: [índice](index.md) · [tablero](tablero.html) ·
[conciliación](07-conciliacion/informe-de-conciliacion.md) ·
[runbook](09-corte-y-reversa/runbook-de-corte.md)
