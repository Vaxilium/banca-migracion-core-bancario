# lenguaje: es
Caracteristica: Corte delta entre extraccion y migracion
  Como responsable del corte
  Quiero incorporar los cambios ocurridos entre la extraccion y el corte
  Para que el destino refleje el saldo vigente sin reprocesar el historico

  Escenario: PR-013 Cuentas nuevas del corte se insertan
    Dado el archivo de saldos de la delta
    Cuando la carga incorpora las cuentas que no existian en el legado
    Entonces cada cuenta nueva existe en el destino
    Y su saldo de apertura es cero

  Escenario: PR-014 Saldos de cuentas actualizadas se reemplazan
    Dado una cuenta existente con saldo en la delta
    Cuando la carga aplica el corte
    Entonces el saldo vigente es el de la delta
    Y no queda una fila duplicada por cuenta

  Escenario: PR-015 Movimientos delta se incorporan una sola vez
    Dado los movimientos posteriores a la extraccion
    Cuando la carga los incorpora
    Entonces cada movimiento aparece una sola vez en el destino
    Y su cantidad coincide con la reportada por la conciliacion
