from database.config import get_base_datos

class Proveedor:
    """
    Representa un proveedor del sistema.
    """

    def __init__(self, cuit, razon_social, telefono, email, estado="Activo"):
        self.cuit = cuit
        self.razon_social = razon_social
        self.telefono = telefono
        self.email = email
        self.estado = estado

    def guardar(self):
        bd = get_base_datos()
        resultado = bd.insertar('''
            INSERT OR REPLACE INTO proveedores (cuit, razon_social, telefono, email, estado)
            VALUES (?, ?, ?, ?, ?)
        ''', (self.cuit, self.razon_social, self.telefono, self.email, self.estado))
        return resultado is not None

    @staticmethod
    def buscar_por_cuit(cuit):
        bd = get_base_datos()
        filas = bd.consultar('''
            SELECT cuit, razon_social, telefono, email, estado
            FROM proveedores
            WHERE cuit = ?
        ''', (cuit,))
        if filas:
            fila = filas[0]
            return Proveedor(fila[0], fila[1], fila[2], fila[3], fila[4])
        return None

    @staticmethod
    def buscar_por_razon_social(termino):
        bd = get_base_datos()
        filas = bd.consultar('''
            SELECT cuit, razon_social, telefono, email, estado
            FROM proveedores
            WHERE razon_social LIKE ? OR telefono LIKE ?
            ORDER BY razon_social ASC
        ''', (f'%{termino}%', f'%{termino}%'))
        return [Proveedor(fila[0], fila[1], fila[2], fila[3], fila[4]) for fila in filas]

    @staticmethod
    def obtener_todos(estado=None):
        bd = get_base_datos()
        query = "SELECT cuit, razon_social, telefono, email, estado FROM proveedores"
        params = []
        if estado:
            query += " WHERE estado = ?"
            params.append(estado)
        query += " ORDER BY razon_social ASC"
        filas = bd.consultar(query, params)
        return [Proveedor(fila[0], fila[1], fila[2], fila[3], fila[4]) for fila in filas]

    def cambiar_estado(self, nuevo_estado):
        if nuevo_estado not in ['Activo', 'Inactivo']:
            return False
        self.estado = nuevo_estado
        return self.guardar()

    def __str__(self):
        return f"{self.razon_social} (CUIT: {self.cuit}) - {self.estado}"
