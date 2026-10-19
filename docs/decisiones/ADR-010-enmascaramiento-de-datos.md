# ADR-010: Manejo de datos sensibles y muestras no productivas

| Fecha | Estado | Decisores | Autor |
|---|---|---|---|
| 19/10/2026 | Aceptada | Comité operativo, Seguridad de la información | Franco Tilleria, Analista de Negocios |

## Contexto

El legado contiene números de tarjeta, documentos, nombres, teléfonos, correos y
direcciones. El proyecto publica el repositorio, las muestras de datos y los informes
en un entorno no productivo: ningún dato de carácter personal puede quedar expuesto
en claro, ni siquiera tratándose de datos sintéticos, porque la solución se diseña
como si el origen fuera real.

Además, el modelo destino necesita el número de tarjeta para operatoria (débitos
automáticos) pero no requiere el número completo para ningún proceso funcional: los
últimos cuatro dígitos alcanzan para atención al cliente y conciliación de reclamos.

## Decisión

1. **En la migración (RN-11):** el número de tarjeta se carga únicamente enmascarado,
   conservando los últimos cuatro dígitos y reemplazando el resto por `*`. Un valor
   vacío o compuesto solo por ceros se carga como nulo.
2. **En las muestras publicadas** (`muestras/`) y en cualquier extracto no productivo
   se aplica seudoanonimización determinista con sal fija del proyecto
   (`src/comun/enmascaramiento.py`): la misma entrada produce siempre la misma salida,
   de modo que las pruebas y los enlaces de los documentos siguen siendo estables.
   - documentos: se conserva el tipo y el formato;
   - nombres: se reemplazan por un nombre ficticio estable;
   - teléfonos, correos y direcciones: se conserva la estructura (prefijo, dominio,
     numeración) y se reemplaza el contenido.
3. **Prohibiciones:** el pipeline nunca escribe datos en claro en logs, rechazos,
   bitácora ni resúmenes; los detalles de rechazo usan claves e identificadores, no
   valores completos de tarjeta.

## Alternativas consideradas

1. Cargar el número completo y controlar el acceso después: un solo extracto mal
   compartido expone el dato; descartado.
2. Guardar un hash del número: sirve para igualdad, pero rompe la atención al cliente
   (no se puede dar los últimos cuatro dígitos).
3. Eliminar la columna: pierde la operatoria de débitos y el reclamo por tarjeta.

## Consecuencias

- La tabla `cuenta` del destino solo contiene números enmascarados; la validación de
  contratos permite nulos y no impone longitud.
- Los informes y el tablero pueden publicar muestras sin riesgo y sin perder
  legibilidad: se mantienen los formatos y la estructura de los datos.
- Cualquier necesidad futura del número completo exige un circuito aparte con
  cifrado y aprobación de seguridad, fuera del alcance de esta migración.
