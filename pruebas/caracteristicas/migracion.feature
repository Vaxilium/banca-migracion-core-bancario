# lenguaje: es
Caracteristica: Transformacion y carga del legado
  Como analista funcional
  Quiero que las reglas conviertan y carguen el legado sin perder trazabilidad
  Para confiar en el corte del core bancario

  Escenario: PR-001 Conversion de importes con signo final
    Dado un importe de ancho fijo con el signo al final del campo
    Cuando la regla lo convierte a numero decimal
    Entonces el valor conserva su magnitud y su signo
    Y un importe con formato invalido queda marcado como no valido

  Escenario: PR-002 Regla de siglo segun el umbral del ensayo
    Dado un anio de dos digitos del legado
    Cuando el anio es menor o igual al umbral configurado
    Entonces la fecha se interpreta en el siglo veintiuno
    Y si supera el umbral se interpreta en el siglo veinte

  Escenario: PR-003 Documento de identidad con digito verificador
    Dado un documento ficticio de tipo DNI, CI o PAS
    Cuando se valida su formato
    Entonces solo se aceptan los documentos que cumplen la regla del tipo

  Escenario: PR-004 Claves unicas en el destino
    Dado el destino del ensayo 3 cargado
    Cuando se revisan las claves de saldo y de cuota
    Entonces no existe mas de una fila vigente por clave

  Escenario: PR-005 Saldo contable internamente balanceado
    Dado el libro mayor del ensayo 3
    Cuando se calcula debe menos haber menos saldo final
    Entonces el resultado es cero en todas las cuentas

  Escenario: PR-006 Tarjetas enmascaradas
    Dado el maestro de cuentas del destino
    Cuando una cuenta tiene tarjeta
    Entonces el numero solo conserva los ultimos cuatro digitos

  Escenario: PR-007 Conteos de migracion cierran contra rechazos
    Dado el resumen de conciliacion del ensayo 3
    Cuando se compara el origen con los cargados, fusionados y rechazados
    Entonces la diferencia es cero en todas las entidades
