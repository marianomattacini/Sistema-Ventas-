import sqlite3
import bcrypt
from datetime import datetime
from database.config import get_sqlite_connection

# =====================================================================
# CLASE USUARIO
# =====================================================================
class Usuario:
    """
    Representa un usuario del sistema con autenticación, roles y estado.
    """

    def __init__(self, nombre_usuario, pin_plano, rol, estado="Activo", id=None, fecha_creacion=None, ultimo_login=None):
        """
        Inicializa un objeto Usuario.
        - `pin_plano` se recibe en texto plano y se hashea con bcrypt.
        """
        self.id = id
        self.nombre_usuario = nombre_usuario
        self.pin_hash = self._hash_pin(pin_plano) if pin_plano else None
        self.rol = rol
        self.estado = estado
        self.fecha_creacion = fecha_creacion or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.ultimo_login = ultimo_login

    # =====================================================================
    # MÉTODOS PRIVADOS
    # =====================================================================
    @staticmethod
    def _hash_pin(pin_plano):
        """Genera un hash bcrypt a partir de un PIN en texto plano."""
        if not pin_plano:
            return None
        # bcrypt espera bytes, encodeamos el string
        pin_bytes = pin_plano.encode('utf-8')
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(pin_bytes, salt).decode('utf-8')

    @staticmethod
    def _verificar_hash(pin_plano, pin_hash):
        """Verifica si un PIN en texto plano coincide con el hash almacenado."""
        if not pin_hash:
            return False
        pin_bytes = pin_plano.encode('utf-8')
        return bcrypt.checkpw(pin_bytes, pin_hash.encode('utf-8'))

    # =====================================================================
    # MÉTODOS DE PERSISTENCIA
    # =====================================================================
    def guardar(self):
        """
        Inserta o actualiza el usuario en la base de datos.
        Retorna True si fue exitoso, False en caso de error.
        """
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()

            if self.id is None:
                # Insertar nuevo usuario
                cursor.execute('''
                    INSERT INTO usuarios (nombre_usuario, pin_hash, rol, estado, fecha_creacion)
                    VALUES (?, ?, ?, ?, ?)
                ''', (self.nombre_usuario, self.pin_hash, self.rol, self.estado, self.fecha_creacion))
                self.id = cursor.lastrowid
            else:
                # Actualizar usuario existente
                cursor.execute('''
                    UPDATE usuarios
                    SET nombre_usuario = ?, pin_hash = ?, rol = ?, estado = ?, ultimo_login = ?
                    WHERE id = ?
                ''', (self.nombre_usuario, self.pin_hash, self.rol, self.estado, self.ultimo_login, self.id))

            conn.commit()
            conn.close()
            return True

        except sqlite3.IntegrityError as e:
            print(f"❌ Error de integridad (ej. nombre_usuario duplicado): {e}")
            return False
        except sqlite3.Error as e:
            print(f"❌ Error al guardar usuario: {e}")
            return False

    def registrar_login(self):
        """Actualiza el campo ultimo_login con la fecha/hora actual."""
        self.ultimo_login = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return self.guardar()

    # =====================================================================
    # MÉTODOS ESTÁTICOS DE AUTENTICACIÓN Y BÚSQUEDA
    # =====================================================================
    @staticmethod
    def verificar_pin(nombre_usuario, pin_plano):
        """
        Verifica las credenciales de un usuario.
        - Si el PIN es correcto y el estado es 'Activo', retorna el objeto Usuario.
        - Si el PIN es incorrecto, incrementa el contador de intentos.
        - Si falla 3 veces, cambia el estado a 'Bloqueado'.
        - Retorna None si falla.
        """
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()

            # Buscar usuario por nombre
            cursor.execute('''
                SELECT id, nombre_usuario, pin_hash, rol, estado, fecha_creacion, ultimo_login
                FROM usuarios
                WHERE nombre_usuario = ?
            ''', (nombre_usuario,))
            row = cursor.fetchone()
            conn.close()

            if not row:
                print(f"🔒 Intento de login con usuario inexistente: {nombre_usuario}")
                return None

            # Crear objeto Usuario con los datos de la BD
            usuario = Usuario(
                id=row[0],
                nombre_usuario=row[1],
                pin_plano=None,  # No tenemos el PIN plano
                rol=row[3],
                estado=row[4],
                fecha_creacion=row[5],
                ultimo_login=row[6]
            )
            usuario.pin_hash = row[2]  # Asignar el hash manualmente

            # Verificar estado
            if usuario.estado == 'Inactivo':
                print(f"⚠️ Usuario inactivo: {nombre_usuario}")
                return None
            if usuario.estado == 'Bloqueado':
                print(f"⛔ Usuario bloqueado: {nombre_usuario}. Contacte al Gerente General.")
                return None

            # Verificar PIN
            if Usuario._verificar_hash(pin_plano, usuario.pin_hash):
                # Login exitoso -> registrar último login
                usuario.registrar_login()
                # Resetear el contador de intentos (se maneja en la sesión)
                return usuario
            else:
                # PIN incorrecto -> incrementar contador de intentos fallidos en la sesión
                # (el contador lo maneja la vista, no la BD)
                print(f"❌ PIN incorrecto para usuario: {nombre_usuario}")
                return None

        except sqlite3.Error as e:
            print(f"❌ Error al verificar PIN: {e}")
            return None

    @staticmethod
    def obtener_por_id(usuario_id):
        """Retorna un objeto Usuario a partir de su ID, o None si no existe."""
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, nombre_usuario, pin_hash, rol, estado, fecha_creacion, ultimo_login
                FROM usuarios
                WHERE id = ?
            ''', (usuario_id,))
            row = cursor.fetchone()
            conn.close()

            if row:
                return Usuario(
                    id=row[0],
                    nombre_usuario=row[1],
                    pin_plano=None,
                    rol=row[3],
                    estado=row[4],
                    fecha_creacion=row[5],
                    ultimo_login=row[6]
                )
            return None
        except sqlite3.Error as e:
            print(f"❌ Error al obtener usuario por ID: {e}")
            return None

    @staticmethod
    def obtener_todos():
        """Retorna una lista de objetos Usuario con todos los usuarios (ordenados por nombre)."""
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, nombre_usuario, pin_hash, rol, estado, fecha_creacion, ultimo_login
                FROM usuarios
                ORDER BY nombre_usuario ASC
            ''')
            rows = cursor.fetchall()
            conn.close()

            usuarios = []
            for row in rows:
                usuario = Usuario(
                    id=row[0],
                    nombre_usuario=row[1],
                    pin_plano=None,
                    rol=row[3],
                    estado=row[4],
                    fecha_creacion=row[5],
                    ultimo_login=row[6]
                )
                usuario.pin_hash = row[2]
                usuarios.append(usuario)
            return usuarios
        except sqlite3.Error as e:
            print(f"❌ Error al obtener todos los usuarios: {e}")
            return []

    # =====================================================================
    # MÉTODOS DE GESTIÓN DE ESTADO Y PERMISOS
    # =====================================================================
    def cambiar_estado(self, nuevo_estado, usuario_autorizante):
        """
        Cambia el estado del usuario (solo Gerente General puede).
        Registra la acción en logs_auditoria.
        """
        if usuario_autorizante.rol != "Gerente General":
            print("❌ Solo el Gerente General puede cambiar el estado de un usuario.")
            return False

        if nuevo_estado not in ["Activo", "Inactivo", "Bloqueado"]:
            print("❌ Estado inválido. Use 'Activo', 'Inactivo' o 'Bloqueado'.")
            return False

        self.estado = nuevo_estado
        exito = self.guardar()
        if exito:
            # Registrar en auditoría
            self._registrar_auditoria(
                usuario_autorizante.id,
                f"Cambio de estado de {self.nombre_usuario} a {nuevo_estado}"
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

    def tiene_permiso(self, permiso_requerido):
        """
        Verifica si el usuario tiene el rol necesario para realizar una acción.
        Los roles son jerárquicos:
        - Cajero: permisos básicos
        - Supervisor: Cajero + anulaciones, sangrías, cierre forzado
        - Administrador: Supervisor + gestión de productos, clientes, proveedores, compras, usuarios
        - Gerente General: Administrador + bloqueo/desbloqueo, balances, presupuestos, promociones
        """
        jerarquia = {
            "Cajero": 1,
            "Supervisor": 2,
            "Administrador": 3,
            "Gerente General": 4
        }

        permisos = {
            "ver_pos": 1,
            "pausar_ticket": 1,
            "cobrar": 1,
            "ver_turno_propio": 1,
            "anular_pedido": 2,
            "forzar_cierre_turno": 2,
            "autorizar_sangria": 2,
            "ver_reportes_basicos": 2,
            "gestionar_productos": 3,
            "gestionar_clientes": 3,
            "gestionar_proveedores": 3,
            "gestionar_compras": 3,
            "gestionar_usuarios": 3,
            "desbloquear_usuario": 4,
            "ver_balances": 4,
            "gestionar_promociones": 4,
            "gestionar_presupuestos": 4,
            "ver_estadisticas": 4
        }

        nivel_requerido = permisos.get(permiso_requerido, 0)
        nivel_usuario = jerarquia.get(self.rol, 0)
        return nivel_usuario >= nivel_requerido

    # =====================================================================
    # REPRESENTACIÓN EN TEXTO
    # =====================================================================
    def __str__(self):
        return f"{self.nombre_usuario} ({self.rol}) - {self.estado}"

    def __repr__(self):
        return f"Usuario(id={self.id}, nombre={self.nombre_usuario}, rol={self.rol})"