from database.config import get_base_datos

class Configuracion:
    """
    Gestiona los parámetros globales del sistema.
    """
    @staticmethod
    def obtener(clave):
        """Obtiene el valor de una configuración."""
        bd = get_base_datos()
        filas = bd.consultar("SELECT valor FROM configuracion WHERE clave = ?", (clave,))
        return filas[0][0] if filas else None

    @staticmethod
    def guardar(clave, valor):
        """Guarda o actualiza una configuración."""
        bd = get_base_datos()
        resultado = bd.insertar('''
            INSERT OR REPLACE INTO configuracion (clave, valor)
            VALUES (?, ?)
        ''', (clave, valor))
        return resultado is not None

    @staticmethod
    def obtener_todos():
        """Obtiene todas las configuraciones."""
        bd = get_base_datos()
        filas = bd.consultar("SELECT clave, valor FROM configuracion")
        return {fila[0]: fila[1] for fila in filas}
