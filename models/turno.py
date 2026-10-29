import sqlite3
from datetime import datetime
from database.config import get_sqlite_connection

class Turno:
    """
    Representa un turno de caja: apertura, cierre, sangrías y estadísticas.
    """

    def __init__(self, usuario_id, fondo_inicial, fecha_hora_apertura=None, id=None):
        self.id = id
        self.usuario_id = usuario_id
        self.fondo_inicial = fondo_inicial
        self.fecha_hora_apertura = fecha_hora_apertura or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.fecha_hora_cierre = None
        self.estado = "Abierto"  # Abierto, Cerrado, Forzado
        self.total_ventas_efectivo = 0.0
        self.total_ventas_debito = 0.0
        self.total_ventas_credito = 0.0
        self.total_ventas_transferencia = 0.0
        self.total_sangrias = 0.0

    # =====================================================================
    # MÉTODOS DE PERSISTENCIA
    # =====================================================================
    def guardar(self):
        """Inserta o actualiza el turno en la base de datos."""
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()

            if self.id is None:
                cursor.execute('''
                    INSERT INTO turnos (
                        usuario_id, fecha_hora_apertura, fondo_inicial, estado
                    ) VALUES (?, ?, ?, ?)
                ''', (self.usuario_id, self.fecha_hora_apertura, self.fondo_inicial, self.estado))
                self.id = cursor.lastrowid
            else:
                cursor.execute('''
                    UPDATE turnos
                    SET fecha_hora_cierre = ?, estado = ?,
                        total_ventas_efectivo = ?, total_ventas_debito = ?,
                        total_ventas_credito = ?, total_ventas_transferencia = ?,
                        total_sangrias = ?
                    WHERE id = ?
                ''', (self.fecha_hora_cierre, self.estado,
                      self.total_ventas_efectivo, self.total_ventas_debito,
                      self.total_ventas_credito, self.total_ventas_transferencia,
                      self.total_sangrias, self.id))

            conn.commit()
            conn.close()
            return True
        except sqlite3.Error as e:
            print(f"❌ Error al guardar turno: {e}")
            return False

    # =====================================================================
    # MÉTODOS ESTÁTICOS DE CONSULTA
    # =====================================================================
    @staticmethod
    def obtener_turno_abierto(usuario_id=None):
        """
        Retorna el turno abierto actual (si existe).
        Retorna una tupla (id, usuario_id) o None.

        Si se indica usuario_id, busca el turno abierto de ESE usuario: así cada
        cajero recupera su propia caja aunque haya otros turnos abiertos.
        """
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()
            if usuario_id is None:
                cursor.execute("SELECT id, usuario_id FROM turnos WHERE estado = 'Abierto' LIMIT 1")
            else:
                cursor.execute('''
                    SELECT id, usuario_id FROM turnos
                    WHERE estado = 'Abierto' AND usuario_id = ?
                    ORDER BY id DESC LIMIT 1
                ''', (usuario_id,))
            row = cursor.fetchone()
            conn.close()
            return row  # (id, usuario_id) o None
        except sqlite3.Error as e:
            print(f"❌ Error al obtener turno abierto: {e}")
            return None

    @staticmethod
    def abrir_turno(usuario_id, fondo_inicial):
        """
        Crea un nuevo turno con estado 'Abierto'.
        Retorna el ID del turno creado, o None si falla.
        """
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute('''
                INSERT INTO turnos (usuario_id, fecha_hora_apertura, fondo_inicial, estado)
                VALUES (?, ?, ?, 'Abierto')
            ''', (usuario_id, fecha, fondo_inicial))
            conn.commit()
            turno_id = cursor.lastrowid
            conn.close()
            return turno_id
        except sqlite3.Error as e:
            print(f"❌ Error al abrir turno: {e}")
            return None

    @staticmethod
    def calcular_totales_ventas(turno_id):
        """
        Recalcula los totales de ventas por método de pago del turno,
        a partir de las ventas completadas (ventas_cabecera + ventas_pagos).
        Retorna un dict con los 4 totales.

        IMPORTANTE: ventas_pagos.monto_abonado ya es el importe aplicado a la
        venta, es decir NETO de vuelto (el vuelto se guarda aparte en
        monto_vuelto y no forma parte de lo cobrado). Por eso se suma
        monto_abonado tal cual: restarle el vuelto otra vez descontaba el
        cambio dos veces y el efectivo del cierre daba de menos.
        Los pagos con QR se acumulan en "Transferencia" (el turno no tiene una
        columna propia para QR), así ninguna venta queda fuera del cierre.
        """
        totales = {
            "Efectivo": 0.0,
            "Débito": 0.0,
            "Crédito": 0.0,
            "Transferencia": 0.0,
        }
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT p.metodo_pago, SUM(p.monto_abonado)
                FROM ventas_pagos p
                JOIN ventas_cabecera c ON c.nro_ticket = p.nro_ticket
                WHERE c.turno_id = ? AND c.estado = 'Completado'
                GROUP BY p.metodo_pago
            ''', (turno_id,))
            rows = cursor.fetchall()
            conn.close()

            for metodo, total in rows:
                if metodo == "QR":
                    metodo = "Transferencia"
                if metodo in totales:
                    totales[metodo] += total or 0.0
            for metodo in totales:
                totales[metodo] = round(totales[metodo], 2)
        except sqlite3.Error as e:
            print(f"❌ Error al calcular totales de ventas del turno: {e}")

        return totales

    @staticmethod
    def calcular_vuelto_entregado(turno_id):
        """Suma del vuelto entregado en las ventas completadas del turno (informativo)."""
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COALESCE(SUM(p.monto_vuelto), 0)
                FROM ventas_pagos p
                JOIN ventas_cabecera c ON c.nro_ticket = p.nro_ticket
                WHERE c.turno_id = ? AND c.estado = 'Completado'
            ''', (turno_id,))
            total = cursor.fetchone()[0] or 0.0
            conn.close()
            return round(total, 2)
        except sqlite3.Error as e:
            print(f"❌ Error al calcular el vuelto del turno: {e}")
            return 0.0

    @staticmethod
    def calcular_sangrias(turno_id):
        """Suma de las sangrías registradas en el turno (fuente de verdad: tabla sangrias)."""
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COALESCE(SUM(monto_retirado), 0) FROM sangrias WHERE turno_id = ?",
                (turno_id,))
            total = cursor.fetchone()[0] or 0.0
            conn.close()
            return round(total, 2)
        except sqlite3.Error as e:
            print(f"❌ Error al calcular las sangrías del turno: {e}")
            return 0.0

    @staticmethod
    def resumen_caja(turno_id):
        """
        Arma el resumen de caja del turno a partir de las ventas y sangrías
        realmente registradas (no de contadores sueltos), para que el cierre
        cuadre siempre:

            efectivo esperado en caja = fondo inicial + ventas en efectivo
                                        (ya netas de vuelto) - sangrías

        También devuelve el control de integridad: lo facturado en los tickets
        completados tiene que ser igual a lo cobrado por todos los métodos
        (diferencia_control == 0). Retorna None si el turno no existe.
        """
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT fondo_inicial FROM turnos WHERE id = ?", (turno_id,))
            fila = cursor.fetchone()
            if not fila:
                conn.close()
                return None
            fondo = fila[0] or 0.0
            cursor.execute('''
                SELECT COUNT(*), COALESCE(SUM(total_facturado), 0)
                FROM ventas_cabecera WHERE turno_id = ? AND estado = 'Completado'
            ''', (turno_id,))
            cantidad_ventas, total_facturado = cursor.fetchone()
            cursor.execute('''
                SELECT COUNT(*) FROM ventas_cabecera
                WHERE turno_id = ? AND estado = 'Pausado'
            ''', (turno_id,))
            tickets_pausados = cursor.fetchone()[0]
            conn.close()
        except sqlite3.Error as e:
            print(f"❌ Error al armar el resumen de caja: {e}")
            return None

        totales = Turno.calcular_totales_ventas(turno_id)
        vuelto = Turno.calcular_vuelto_entregado(turno_id)
        sangrias = Turno.calcular_sangrias(turno_id)
        total_ventas = round(sum(totales.values()), 2)
        efectivo = totales["Efectivo"]

        return {
            "fondo_inicial": round(fondo, 2),
            "total_efectivo": efectivo,
            "total_debito": totales["Débito"],
            "total_credito": totales["Crédito"],
            "total_transferencia": totales["Transferencia"],
            "total_ventas": total_ventas,
            "total_vuelto": vuelto,
            "efectivo_recibido": round(efectivo + vuelto, 2),
            "total_sangrias": sangrias,
            "efectivo_esperado": round(fondo + efectivo - sangrias, 2),
            "cantidad_ventas": cantidad_ventas,
            "total_facturado": round(total_facturado or 0.0, 2),
            "diferencia_control": round((total_facturado or 0.0) - total_ventas, 2),
            "tickets_pausados": tickets_pausados,
        }

    @staticmethod
    def cerrar_turno(turno_id, forzado=False):
        """
        Cierra un turno (normal o forzado).
        Antes de cerrarlo, recalcula los totales de ventas por método de pago
        (total_ventas_efectivo/debito/credito/transferencia) y las sangrías a
        partir de lo realmente registrado durante el turno.
        Solo cierra turnos que están abiertos (un turno ya cerrado no se pisa).
        Retorna True si fue exitoso, False en caso de error.
        """
        try:
            totales = Turno.calcular_totales_ventas(turno_id)
            sangrias = Turno.calcular_sangrias(turno_id)

            conn = get_sqlite_connection()
            cursor = conn.cursor()
            fecha_cierre = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            estado = "Forzado" if forzado else "Cerrado"
            cursor.execute('''
                UPDATE turnos
                SET estado = ?, fecha_hora_cierre = ?,
                    total_ventas_efectivo = ?, total_ventas_debito = ?,
                    total_ventas_credito = ?, total_ventas_transferencia = ?,
                    total_sangrias = ?
                WHERE id = ? AND estado = 'Abierto'
            ''', (estado, fecha_cierre,
                  totales["Efectivo"], totales["Débito"],
                  totales["Crédito"], totales["Transferencia"],
                  sangrias, turno_id))
            cerrado = cursor.rowcount > 0
            conn.commit()
            conn.close()
            return cerrado
        except sqlite3.Error as e:
            print(f"❌ Error al cerrar turno: {e}")
            return False

    @staticmethod
    def obtener_turno_por_id(turno_id):
        """Retorna un objeto Turno si existe, o None."""
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, usuario_id, fecha_hora_apertura, fecha_hora_cierre,
                       fondo_inicial, total_ventas_efectivo, total_ventas_debito,
                       total_ventas_credito, total_ventas_transferencia,
                       total_sangrias, estado
                FROM turnos
                WHERE id = ?
            ''', (turno_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                turno = Turno(usuario_id=row[1], fondo_inicial=row[4], fecha_hora_apertura=row[2], id=row[0])
                turno.fecha_hora_cierre = row[3]
                turno.total_ventas_efectivo = row[5]
                turno.total_ventas_debito = row[6]
                turno.total_ventas_credito = row[7]
                turno.total_ventas_transferencia = row[8]
                turno.total_sangrias = row[9]
                turno.estado = row[10]
                if turno.estado == "Abierto":
                    # Un turno abierto todavía no tiene totales guardados: se
                    # calculan en vivo para que las pantallas y reportes muestren
                    # lo que realmente se vendió hasta ahora.
                    totales = Turno.calcular_totales_ventas(turno_id)
                    turno.total_ventas_efectivo = totales["Efectivo"]
                    turno.total_ventas_debito = totales["Débito"]
                    turno.total_ventas_credito = totales["Crédito"]
                    turno.total_ventas_transferencia = totales["Transferencia"]
                    turno.total_sangrias = Turno.calcular_sangrias(turno_id)
                return turno
            return None
        except sqlite3.Error as e:
            print(f"❌ Error al obtener turno por ID: {e}")
            return None

    @staticmethod
    def datos_reporte(turno_id):
        """
        Datos completos para el reporte PDF del turno (generar_reporte_turno_pdf).
        Un único lugar arma estos datos, así el reporte del cierre de caja y los
        que se piden desde la pantalla de Turnos muestran siempre los mismos números.
        Retorna None si el turno no existe.
        """
        from models.usuario import Usuario

        turno = Turno.obtener_turno_por_id(turno_id)
        if not turno:
            return None
        resumen = Turno.resumen_caja(turno_id) or {}
        usuario = Usuario.obtener_por_id(turno.usuario_id)

        efectivo = turno.total_ventas_efectivo
        vuelto = resumen.get("total_vuelto", 0.0)
        total_ventas = (turno.total_ventas_efectivo + turno.total_ventas_debito +
                        turno.total_ventas_credito + turno.total_ventas_transferencia)
        return {
            "turno_id": turno_id,
            "cajero": usuario.nombre_usuario if usuario else "Desconocido",
            "apertura": turno.fecha_hora_apertura,
            "cierre": turno.fecha_hora_cierre or "Abierto",
            "estado": turno.estado,
            "fondo_inicial": turno.fondo_inicial,
            "total_efectivo": efectivo,
            "total_debito": turno.total_ventas_debito,
            "total_credito": turno.total_ventas_credito,
            "total_transferencia": turno.total_ventas_transferencia,
            "total_sangrias": turno.total_sangrias,
            "total_ventas": total_ventas,
            "total_vuelto": vuelto,
            "efectivo_recibido": round(efectivo + vuelto, 2),
            "efectivo_esperado": round(turno.fondo_inicial + efectivo - turno.total_sangrias, 2),
            "cantidad_ventas": resumen.get("cantidad_ventas", 0),
            "total_facturado": resumen.get("total_facturado", 0.0),
            "diferencia_control": round(resumen.get("total_facturado", 0.0) - total_ventas, 2),
        }