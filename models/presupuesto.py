from database.config import get_base_datos

class Presupuesto:
    def __init__(self, categoria, monto_planificado, mes, anio, id=None, fecha_registro=None):
        self.id = id
        self.categoria = categoria
        self.monto_planificado = monto_planificado
        self.mes = mes
        self.anio = anio
        self.fecha_registro = fecha_registro

    def guardar(self):
        bd = get_base_datos()
        if self.id:
            filas = bd.actualizar('''
                UPDATE presupuestos SET categoria=?, monto_planificado=?, mes=?, anio=?
                WHERE id=?
            ''', (self.categoria, self.monto_planificado, self.mes, self.anio, self.id))
            return filas > 0
        else:
            nuevo_id = bd.insertar('''
                INSERT INTO presupuestos (categoria, monto_planificado, mes, anio)
                VALUES (?, ?, ?, ?)
            ''', (self.categoria, self.monto_planificado, self.mes, self.anio))
            if nuevo_id is not None:
                self.id = nuevo_id
                return True
            return False

    @staticmethod
    def obtener_todos():
        bd = get_base_datos()
        filas = bd.consultar(
            "SELECT id, categoria, monto_planificado, mes, anio, fecha_registro "
            "FROM presupuestos ORDER BY anio DESC, mes DESC"
        )
        return [Presupuesto(f[1], f[2], f[3], f[4], f[0], f[5]) for f in filas]

    @staticmethod
    def obtener_por_id(id):
        bd = get_base_datos()
        filas = bd.consultar(
            "SELECT id, categoria, monto_planificado, mes, anio, fecha_registro "
            "FROM presupuestos WHERE id = ?", (id,)
        )
        if filas:
            f = filas[0]
            return Presupuesto(f[1], f[2], f[3], f[4], f[0], f[5])
        return None

    @staticmethod
    def eliminar(id):
        bd = get_base_datos()
        bd.eliminar("DELETE FROM presupuestos WHERE id = ?", (id,))
        return True
