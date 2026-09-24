from database.config import get_base_datos

class EntidadPago:
    def __init__(self, nombre, tipo, cuotas_maximas=12, activa=True, id=None,
                 descuento_porcentaje=0.0, cuotas_sin_interes=0, promocion_descripcion=""):
        self.id = id
        self.nombre = nombre
        self.tipo = tipo
        self.activa = activa
        self.cuotas_maximas = cuotas_maximas
        self.descuento_porcentaje = descuento_porcentaje or 0.0
        self.cuotas_sin_interes = cuotas_sin_interes or 0
        self.promocion_descripcion = promocion_descripcion or ""

    def guardar(self):
        bd = get_base_datos()
        if self.id:
            filas = bd.actualizar('''
                UPDATE entidades_pago SET nombre=?, tipo=?, activa=?, cuotas_maximas=?,
                    descuento_porcentaje=?, cuotas_sin_interes=?, promocion_descripcion=?
                WHERE id=?
            ''', (self.nombre, self.tipo, self.activa, self.cuotas_maximas,
                  self.descuento_porcentaje, self.cuotas_sin_interes,
                  self.promocion_descripcion, self.id))
            return filas > 0
        else:
            nuevo_id = bd.insertar('''
                INSERT INTO entidades_pago (nombre, tipo, activa, cuotas_maximas,
                    descuento_porcentaje, cuotas_sin_interes, promocion_descripcion)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (self.nombre, self.tipo, self.activa, self.cuotas_maximas,
                  self.descuento_porcentaje, self.cuotas_sin_interes, self.promocion_descripcion))
            if nuevo_id is not None:
                self.id = nuevo_id
                return True
            return False

    @staticmethod
    def _from_row(row):
        return EntidadPago(
            nombre=row[1], tipo=row[2], cuotas_maximas=row[4], activa=bool(row[3]), id=row[0],
            descuento_porcentaje=row[5] if len(row) > 5 else 0.0,
            cuotas_sin_interes=row[6] if len(row) > 6 else 0,
            promocion_descripcion=row[7] if len(row) > 7 else ""
        )

    @staticmethod
    def obtener_todos():
        bd = get_base_datos()
        filas = bd.consultar('''SELECT id, nombre, tipo, activa, cuotas_maximas,
                                 descuento_porcentaje, cuotas_sin_interes, promocion_descripcion
                                 FROM entidades_pago ORDER BY tipo, nombre''')
        return [EntidadPago._from_row(fila) for fila in filas]

    @staticmethod
    def obtener_por_id(id):
        bd = get_base_datos()
        filas = bd.consultar('''SELECT id, nombre, tipo, activa, cuotas_maximas,
                                 descuento_porcentaje, cuotas_sin_interes, promocion_descripcion
                                 FROM entidades_pago WHERE id = ?''', (id,))
        return EntidadPago._from_row(filas[0]) if filas else None
