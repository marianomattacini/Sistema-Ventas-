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
    def obtener_turno_abierto():
        """
        Retorna el turno abierto actual (si existe).
        Retorna una tupla (id, usuario_id) o None.
        """
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, usuario_id FROM turnos WHERE estado = 'Abierto' LIMIT 1")
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
                SELECT p.metodo_pago, SUM(p.monto_abonado - COALESCE(p.monto_vuelto, 0))
                FROM ventas_pagos p
                JOIN ventas_cabecera c ON c.nro_ticket = p.nro_ticket
                WHERE c.turno_id = ? AND c.estado = 'Completado'
                GROUP BY p.metodo_pago
            ''', (turno_id,))
            rows = cursor.fetchall()
            conn.close()

            for metodo, total in rows:
                if metodo in totales:
                    totales[metodo] = total or 0.0
        except sqlite3.Error as e:
            print(f"❌ Error al calcular totales de ventas del turno: {e}")

        return totales

    @staticmethod
    def cerrar_turno(turno_id, forzado=False):
        """
        Cierra un turno (normal o forzado).
        Antes de cerrarlo, recalcula los totales de ventas por método de pago
        (total_ventas_efectivo/debito/credito/transferencia) a partir de las
        ventas realmente registradas durante el turno.
        Retorna True si fue exitoso, False en caso de error.
        """
        try:
            totales = Turno.calcular_totales_ventas(turno_id)

            conn = get_sqlite_connection()
            cursor = conn.cursor()
            fecha_cierre = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            estado = "Forzado" if forzado else "Cerrado"
            cursor.execute('''
                UPDATE turnos
                SET estado = ?, fecha_hora_cierre = ?,
                    total_ventas_efectivo = ?, total_ventas_debito = ?,
                    total_ventas_credito = ?, total_ventas_transferencia = ?
                WHERE id = ?
            ''', (estado, fecha_cierre,
                  totales["Efectivo"], totales["Débito"],
                  totales["Crédito"], totales["Transferencia"],
                  turno_id))
            conn.commit()
            conn.close()
            return True
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
                return turno
            return None
        except sqlite3.Error as e:
            print(f"❌ Error al obtener turno por ID: {e}")
            return None