import sqlite3
import re
from datetime import datetime
from database.config import get_sqlite_connection

# =====================================================================
# CLASE CLIENTE
# =====================================================================
class Cliente:
    """
    Representa un cliente del sistema con gestión de datos, puntos e historial de compras.
    El DNI/CUIL es la clave primaria y debe ser numérico.
    """

    def __init__(self, dni_cuil, nombre, telefono="", email="", puntos_acumulados=0,
                 estado="Activo", fecha_registro=None):
        """
        Inicializa un objeto Cliente.
        - dni_cuil: solo dígitos (ej. 10123456 o 20101234567).
        - nombre: obligatorio.
        - telefono y email: opcionales.
        """
        self.dni_cuil = str(dni_cuil).strip()
        self.nombre = nombre.strip()
        self.telefono = telefono.strip() if telefono else ""
        self.email = email.strip() if email else ""
        self.puntos_acumulados = int(puntos_acumulados)
        self.estado = estado
        self.fecha_registro = fecha_registro or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Validaciones básicas
        self._validar()

    # =====================================================================
    # VALIDACIONES PRIVADAS
    # =====================================================================
    def _validar(self):
        """Valida los campos obligatorios y formatos."""
        if not self.dni_cuil:
            raise ValueError("El DNI/CUIL es obligatorio.")
        if not self.dni_cuil.isdigit():
            raise ValueError("El DNI/CUIL debe contener solo dígitos.")
        if not self.nombre:
            raise ValueError("El nombre es obligatorio.")
        if self.email:
            # Validación simple de email
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', self.email):
                raise ValueError("Formato de email inválido.")
        if self.puntos_acumulados < 0:
            raise ValueError("Los puntos acumulados no pueden ser negativos.")

    # =====================================================================
    # MÉTODOS DE PERSISTENCIA
    # =====================================================================
    def guardar(self):
        """
        Inserta o actualiza el cliente en la base de datos.
        Retorna True si fue exitoso, False en caso de error.
        """
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO clientes (
                    dni_cuil, nombre, telefono, email, puntos_acumulados, estado, fecha_registro
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (self.dni_cuil, self.nombre, self.telefono, self.email,
                  self.puntos_acumulados, self.estado, self.fecha_registro))

            conn.commit()
            conn.close()
            return True

        except sqlite3.IntegrityError as e:
            print(f"❌ Error de integridad: {e}")
            return False
        except sqlite3.Error as e:
            print(f"❌ Error al guardar cliente: {e}")
            return False

    # =====================================================================
    # MÉTODOS ESTÁTICOS DE BÚSQUEDA Y CONSULTA
    # =====================================================================
    @staticmethod
    def buscar_por_dni(dni_cuil):
        """
        Retorna un objeto Cliente si existe, o None si no.
        """
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT dni_cuil, nombre, telefono, email, puntos_acumulados, estado, fecha_registro
                FROM clientes
                WHERE dni_cuil = ?
            ''', (str(dni_cuil),))
            row = cursor.fetchone()
            conn.close()

            if row:
                return Cliente(
                    dni_cuil=row[0],
                    nombre=row[1],
                    telefono=row[2],
                    email=row[3],
                    puntos_acumulados=row[4],
                    estado=row[5],
                    fecha_registro=row[6]
                )
            return None
        except sqlite3.Error as e:
            print(f"❌ Error al buscar cliente por DNI: {e}")
            return None

    @staticmethod
    def buscar_por_nombre(termino):
        """
        Busca clientes cuyo nombre contenga el término (búsqueda parcial, insensible a mayúsculas).
        Retorna una lista de objetos Cliente.
        """
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT dni_cuil, nombre, telefono, email, puntos_acumulados, estado, fecha_registro
                FROM clientes
                WHERE nombre LIKE ? AND estado = 'Activo'
                ORDER BY nombre ASC
            ''', (f'%{termino}%',))
            rows = cursor.fetchall()
            conn.close()

            clientes = []
            for row in rows:
                clientes.append(Cliente(
                    dni_cuil=row[0],
                    nombre=row[1],
                    telefono=row[2],
                    email=row[3],
                    puntos_acumulados=row[4],
                    estado=row[5],
                    fecha_registro=row[6]
                ))
            return clientes
        except sqlite3.Error as e:
            print(f"❌ Error al buscar clientes por nombre: {e}")
            return []

    @staticmethod
    def obtener_todos(estado=None):
        """
        Retorna todos los clientes (activos por defecto, o todos si estado=None).
        """
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()
            query = '''
                SELECT dni_cuil, nombre, telefono, email, puntos_acumulados, estado, fecha_registro
                FROM clientes
            '''
            params = []
            if estado:
                query += " WHERE estado = ?"
                params.append(estado)
            query += " ORDER BY nombre ASC"

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            clientes = []
            for row in rows:
                clientes.append(Cliente(
                    dni_cuil=row[0],
                    nombre=row[1],
                    telefono=row[2],
                    email=row[3],
                    puntos_acumulados=row[4],
                    estado=row[5],
                    fecha_registro=row[6]
                ))
            return clientes
        except sqlite3.Error as e:
            print(f"❌ Error al obtener todos los clientes: {e}")
            return []

    # =====================================================================
    # MÉTODOS DE GESTIÓN DE PUNTOS
    # =====================================================================
    def agregar_puntos(self, puntos):
        """
        Aumenta los puntos acumulados del cliente.
        - puntos: entero positivo.
        Retorna el nuevo total de puntos.
        """
        if puntos <= 0:
            raise ValueError("Los puntos a agregar deben ser positivos.")
        self.puntos_acumulados += puntos
        self.guardar()
        return self.puntos_acumulados

    def canjear_puntos(self, puntos):
        """
        Disminuye los puntos acumulados del cliente.
        - puntos: entero positivo.
        Retorna el nuevo total de puntos.
        """
        if puntos <= 0:
            raise ValueError("Los puntos a canjear deben ser positivos.")
        if puntos > self.puntos_acumulados:
            raise ValueError(f"Puntos insuficientes. Disponibles: {self.puntos_acumulados}")
        self.puntos_acumulados -= puntos
        self.guardar()
        return self.puntos_acumulados

    # =====================================================================
    # MÉTODOS DE HISTORIAL
    # =====================================================================
    def obtener_historial_compras(self):
        """
        Retorna una lista de tickets de compras realizadas por este cliente.
        Incluye: nro_ticket, fecha_hora, total_facturado, puntos_sumados.
        Ordenados por fecha descendente.
        """
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT nro_ticket, fecha_hora, total_facturado, puntos_sumados
                FROM ventas_cabecera
                WHERE dni_cliente = ? AND estado = 'Completado'
                ORDER BY fecha_hora DESC
            ''', (self.dni_cuil,))
            rows = cursor.fetchall()
            conn.close()

            historial = []
            for row in rows:
                historial.append({
                    'nro_ticket': row[0],
                    'fecha_hora': row[1],
                    'total_facturado': row[2],
                    'puntos_sumados': row[3]
                })
            return historial
        except sqlite3.Error as e:
            print(f"❌ Error al obtener historial de compras: {e}")
            return []

    # =====================================================================
    # MÉTODOS DE GESTIÓN DE ESTADO
    # =====================================================================
    def cambiar_estado(self, nuevo_estado, usuario_autorizante):
        """
        Cambia el estado del cliente (solo Administrador o Gerente General puede).
        Registra la acción en logs_auditoria.
        """
        if not usuario_autorizante.tiene_permiso('gestionar_clientes'):
            print("❌ Permisos insuficientes para cambiar el estado de un cliente.")
            return False

        if nuevo_estado not in ['Activo', 'Inactivo']:
            print("❌ Estado inválido. Use 'Activo' o 'Inactivo'.")
            return False

        self.estado = nuevo_estado
        exito = self.guardar()
        if exito:
            self._registrar_auditoria(
                usuario_autorizante.id,
                f"Cambio de estado de cliente {self.dni_cuil} a {nuevo_estado}"
            )
        return exito

    def _registrar_auditoria(self, usuario_id, accion, detalle=None):
        """Registra una acción en la tabla logs_auditoria."""
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO logs_auditoria (usuario_id, accion, detalle)
                VALUES (?, ?, ?)
            ''', (usuario_id, accion, detalle))
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"❌ Error al registrar auditoría: {e}")

    # =====================================================================
    # MÉTODOS ESTÁTICOS PARA CRUD DESDE LA INTERFAZ
    # =====================================================================
    @staticmethod
    def crear_cliente(data):
        """
        Crea un nuevo cliente a partir de un diccionario con los datos.
        data debe contener: dni_cuil, nombre, telefono (opcional), email (opcional).
        Retorna el objeto Cliente creado, o None si hay error.
        """
        try:
            dni = data.get('dni_cuil')
            nombre = data.get('nombre')
            telefono = data.get('telefono', '')
            email = data.get('email', '')

            if not dni or not nombre:
                raise ValueError("DNI y nombre son obligatorios.")

            # Verificar que no exista
            existente = Cliente.buscar_por_dni(dni)
            if existente:
                raise ValueError(f"Ya existe un cliente con DNI {dni}")

            cliente = Cliente(dni_cuil=dni, nombre=nombre, telefono=telefono, email=email)
            if cliente.guardar():
                return cliente
            return None
        except Exception as e:
            print(f"❌ Error al crear cliente: {e}")
            return None

    @staticmethod
    def actualizar_cliente(dni_cuil, nuevos_datos):
        """
        Actualiza los campos de un cliente existente.
        nuevos_datos: diccionario con los campos a modificar.
        Retorna el objeto Cliente actualizado, o None si hay error.
        """
        try:
            cliente = Cliente.buscar_por_dni(dni_cuil)
            if not cliente:
                raise ValueError(f"Cliente con DNI {dni_cuil} no encontrado.")

            if 'nombre' in nuevos_datos:
                cliente.nombre = nuevos_datos['nombre']
            if 'telefono' in nuevos_datos:
                cliente.telefono = nuevos_datos['telefono']
            if 'email' in nuevos_datos:
                cliente.email = nuevos_datos['email']
            if 'estado' in nuevos_datos:
                cliente.estado = nuevos_datos['estado']

            # Validar después de actualizar
            cliente._validar()
            if cliente.guardar():
                return cliente
            return None
        except Exception as e:
            print(f"❌ Error al actualizar cliente: {e}")
            return None

    @staticmethod
    def eliminar_cliente(dni_cuil, usuario_autorizante):
        """
        Cambia el estado del cliente a 'Inactivo' (no lo elimina físicamente).
        Solo Administrador o Gerente General.
        """
        try:
            if not usuario_autorizante.tiene_permiso('gestionar_clientes'):
                print("❌ Permisos insuficientes.")
                return False

            cliente = Cliente.buscar_por_dni(dni_cuil)
            if not cliente:
                print(f"❌ Cliente con DNI {dni_cuil} no encontrado.")
                return False

            return cliente.cambiar_estado('Inactivo', usuario_autorizante)
        except Exception as e:
            print(f"❌ Error al eliminar cliente: {e}")
            return False

    # =====================================================================
    # REPRESENTACIÓN
    # =====================================================================
    def __str__(self):
        return f"{self.nombre} (DNI: {self.dni_cuil}) - Puntos: {self.puntos_acumulados} - {self.estado}"

    def __repr__(self):
        return f"Cliente(dni='{self.dni_cuil}', nombre='{self.nombre}')"