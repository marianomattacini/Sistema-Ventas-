import json
from database.config import get_base_datos

class Rol:
    def __init__(self, id=None, nombre=None, permisos=None):
        self.id = id
        self.nombre = nombre
        self.permisos = permisos or {}

    @staticmethod
    def obtener_todos():
        bd = get_base_datos()
        filas = bd.consultar("SELECT id, nombre, permisos FROM roles ORDER BY nombre")
        roles = []
        for fila in filas:
            permisos = json.loads(fila[2]) if fila[2] else {}
            roles.append(Rol(fila[0], fila[1], permisos))
        return roles

    @staticmethod
    def obtener_por_nombre(nombre):
        bd = get_base_datos()
        filas = bd.consultar("SELECT id, nombre, permisos FROM roles WHERE nombre = ?", (nombre,))
        if filas:
            fila = filas[0]
            permisos = json.loads(fila[2]) if fila[2] else {}
            return Rol(fila[0], fila[1], permisos)
        return None

    def guardar(self):
        bd = get_base_datos()
        permisos_json = json.dumps(self.permisos)
        if self.id:
            filas_afectadas = bd.actualizar(
                "UPDATE roles SET nombre=?, permisos=? WHERE id=?",
                (self.nombre, permisos_json, self.id)
            )
            return filas_afectadas > 0
        else:
            nuevo_id = bd.insertar(
                "INSERT INTO roles (nombre, permisos) VALUES (?, ?)",
                (self.nombre, permisos_json)
            )
            if nuevo_id is not None:
                self.id = nuevo_id
                return True
            return False

    @staticmethod
    def crear_rol_predeterminados():
        roles = [
            ("Cajero", {"puede_vender": True, "puede_anular": False, "puede_sangria": False, "puede_cerrar_turno": False}),
            ("Supervisor", {"puede_vender": True, "puede_anular": True, "puede_sangria": True, "puede_cerrar_turno": True}),
            ("Administrador", {"puede_vender": True, "puede_anular": True, "puede_sangria": True, "puede_cerrar_turno": True, "puede_gestionar_productos": True}),
            ("Gerente General", {"puede_vender": True, "puede_anular": True, "puede_sangria": True, "puede_cerrar_turno": True, "puede_gestionar_productos": True, "puede_gestionar_usuarios": True}),
            ("Repositor", {"puede_reponer": True, "puede_ver_stock": True}),
            ("Vendedor", {"puede_vender": True}),
        ]
        for nombre, permisos in roles:
            if not Rol.obtener_por_nombre(nombre):
                r = Rol(nombre=nombre, permisos=permisos)
                r.guardar()
