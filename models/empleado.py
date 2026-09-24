import sqlite3
from database.config import get_sqlite_connection

class Empleado:
    def __init__(self, nombre_completo, dni, fecha_ingreso, rol, salario=0, telefono="", email="", estado="Activo", id=None):
        self.id = id
        self.nombre_completo = nombre_completo
        self.dni = dni
        self.fecha_nacimiento = None
        self.fecha_ingreso = fecha_ingreso
        self.rol = rol
        self.salario = salario
        self.telefono = telefono
        self.email = email
        self.estado = estado

    def guardar(self):
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()
            if self.id:
                cursor.execute('''
                    UPDATE empleados SET nombre_completo=?, dni=?, fecha_ingreso=?, rol=?, salario=?, telefono=?, email=?, estado=?
                    WHERE id=?
                ''', (self.nombre_completo, self.dni, self.fecha_ingreso, self.rol, self.salario, self.telefono, self.email, self.estado, self.id))
            else:
                cursor.execute('''
                    INSERT INTO empleados (nombre_completo, dni, fecha_ingreso, rol, salario, telefono, email, estado)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (self.nombre_completo, self.dni, self.fecha_ingreso, self.rol, self.salario, self.telefono, self.email, self.estado))
                self.id = cursor.lastrowid
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False

    @staticmethod
    def obtener_todos(estado=None):
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()
            query = "SELECT id, nombre_completo, dni, fecha_ingreso, rol, salario, telefono, email, estado FROM empleados"
            params = []
            if estado:
                query += " WHERE estado = ?"
                params.append(estado)
            query += " ORDER BY nombre_completo ASC"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            empleados = []
            for row in rows:
                e = Empleado(row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[0])
                empleados.append(e)
            return empleados
        except sqlite3.Error as e:
            print(f"Error: {e}")
            return []

    @staticmethod
    def obtener_por_id(id):
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, nombre_completo, dni, fecha_ingreso, rol, salario, telefono, email, estado
                FROM empleados WHERE id = ?
            ''', (id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                return Empleado(row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[0])
            return None
        except sqlite3.Error as e:
            print(f"Error: {e}")
            return None

    def obtener_licencias(self):
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, fecha_inicio, fecha_fin, tipo, motivo, estado
                FROM empleados_licencias
                WHERE empleado_id = ?
                ORDER BY fecha_inicio DESC
            ''', (self.id,))
            rows = cursor.fetchall()
            conn.close()
            licencias = []
            for row in rows:
                licencias.append({
                    'id': row[0],
                    'fecha_inicio': row[1],
                    'fecha_fin': row[2],
                    'tipo': row[3],
                    'motivo': row[4],
                    'estado': row[5]
                })
            return licencias
        except sqlite3.Error as e:
            print(f"Error: {e}")
            return []