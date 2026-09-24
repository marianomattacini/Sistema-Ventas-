import sqlite3
from datetime import datetime
from database.config import get_base_datos
from models.usuario import Usuario

class Notificacion:
    """
    Representa una notificación de seguridad o sistema destinada al Gerente General.
    """

    # Tipos de notificación
    TIPO_SEGURIDAD = "Seguridad"
    TIPO_SISTEMA = "Sistema"

    def __init__(self, usuario_destino, tipo, mensaje, fecha_hora=None, leida=False, id=None):
        """
        Inicializa una notificación.
        - usuario_destino: ID del usuario destinatario (debe ser Gerente General).
        - tipo: 'Seguridad' o 'Sistema'.
        - mensaje: texto descriptivo.
        - fecha_hora: fecha y hora de creación (se genera automáticamente).
        - leida: 0 (no leída) o 1 (leída).
        - id: identificador único (para consultas).
        """
        self.id = id
        self.usuario_destino = usuario_destino
        self.tipo = tipo
        self.mensaje = mensaje
        self.fecha_hora = fecha_hora or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.leida = leida

        # Validar que el usuario destino existe y es Gerente General
        self._validar()

    def _validar(self):
        """
        Valida que el usuario destino exista y tenga rol 'Gerente General'.
        """
        usuario = Usuario.obtener_por_id(self.usuario_destino)
        if not usuario:
            raise ValueError(f"Usuario destino con ID {self.usuario_destino} no encontrado.")
        if usuario.rol != "Gerente General":
            raise ValueError(f"El usuario {usuario.nombre_usuario} no es Gerente General.")

    # =====================================================================
    # MÉTODOS DE PERSISTENCIA
    # =====================================================================
    def guardar(self):
        """
        Inserta o actualiza la notificación en la base de datos.
        Retorna True si fue exitoso, False en caso de error.
        """
        bd = get_base_datos()
        if self.id is None:
            nuevo_id = bd.insertar('''
                INSERT INTO notificaciones (
                    usuario_destino, tipo, mensaje, fecha_hora, leida
                ) VALUES (?, ?, ?, ?, ?)
            ''', (self.usuario_destino, self.tipo, self.mensaje, self.fecha_hora, self.leida))
            if nuevo_id is not None:
                self.id = nuevo_id
                return True
            return False
        else:
            filas = bd.actualizar('''
                UPDATE notificaciones
                SET leida = ?
                WHERE id = ?
            ''', (self.leida, self.id))
            return filas >= 0

    def marcar_como_leida(self):
        """
        Marca la notificación como leída (leida = 1).
        Retorna True si fue exitoso, False en caso de error.
        """
        if self.leida == 1:
            print("ℹ️ La notificación ya estaba marcada como leída.")
            return True

        self.leida = 1
        return self.guardar()

    # =====================================================================
    # MÉTODOS DE CONSULTA (ESTÁTICOS)
    # =====================================================================
    @staticmethod
    def obtener_notificaciones_por_usuario(usuario_id, solo_no_leidas=False):
        """
        Retorna una lista de notificaciones para un usuario específico.
        - usuario_id: ID del usuario destinatario.
        - solo_no_leidas: si True, solo retorna notificaciones no leídas.
        """
        bd = get_base_datos()
        query = '''
            SELECT id, usuario_destino, tipo, mensaje, fecha_hora, leida
            FROM notificaciones
            WHERE usuario_destino = ?
        '''
        params = [usuario_id]

        if solo_no_leidas:
            query += " AND leida = 0"
        query += " ORDER BY fecha_hora DESC"

        filas = bd.consultar(query, params)
        return [
            Notificacion(
                usuario_destino=fila[1], tipo=fila[2], mensaje=fila[3],
                fecha_hora=fila[4], leida=fila[5], id=fila[0]
            )
            for fila in filas
        ]

    @staticmethod
    def contar_no_leidas(usuario_id):
        """
        Retorna la cantidad de notificaciones no leídas para un usuario.
        """
        bd = get_base_datos()
        filas = bd.consultar('''
            SELECT COUNT(*)
            FROM notificaciones
            WHERE usuario_destino = ? AND leida = 0
        ''', (usuario_id,))
        return filas[0][0] if filas else 0

    # =====================================================================
    # MÉTODOS DE CREACIÓN RÁPIDA (FACADE)
    # =====================================================================
    @staticmethod
    def crear_notificacion_seguridad(usuario_destino, mensaje):
        """
        Crea una notificación de tipo 'Seguridad'.
        - usuario_destino: ID del Gerente General.
        - mensaje: texto descriptivo del incidente.
        """
        notificacion = Notificacion(
            usuario_destino=usuario_destino,
            tipo=Notificacion.TIPO_SEGURIDAD,
            mensaje=mensaje
        )
        if notificacion.guardar():
            print(f"🔔 Notificación de seguridad creada para usuario ID {usuario_destino}")
            return notificacion
        return None

    @staticmethod
    def crear_notificacion_sistema(usuario_destino, mensaje):
        """
        Crea una notificación de tipo 'Sistema'.
        - usuario_destino: ID del Gerente General.
        - mensaje: texto descriptivo del evento.
        """
        notificacion = Notificacion(
            usuario_destino=usuario_destino,
            tipo=Notificacion.TIPO_SISTEMA,
            mensaje=mensaje
        )
        if notificacion.guardar():
            print(f"🔔 Notificación de sistema creada para usuario ID {usuario_destino}")
            return notificacion
        return None

    # =====================================================================
    # REPRESENTACIÓN
    # =====================================================================
    def __str__(self):
        estado = "📩 No leída" if self.leida == 0 else "✅ Leída"
        return f"[{self.tipo}] {self.mensaje[:50]}... ({estado})"

    def __repr__(self):
        return f"Notificacion(id={self.id}, tipo='{self.tipo}', leida={self.leida})"