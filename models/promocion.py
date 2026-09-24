import sqlite3
from datetime import datetime
from database.config import get_sqlite_connection
from models.producto import Producto

class Promocion:
    """
    Representa una promoción aplicable a productos o categorías.
    Tipos soportados: 3x2, Descuento por cantidad, Descuento % en categoría, Descuento % en producto.
    """

    # Tipos de promoción
    TIPO_3X2 = "3x2"
    TIPO_DESCUENTO_CANTIDAD = "DescuentoCantidad"
    TIPO_DESCUENTO_CATEGORIA = "DescuentoCategoria"
    TIPO_DESCUENTO_PRODUCTO = "DescuentoProducto"

    def __init__(self, tipo, producto_id=None, categoria_id=None, cantidad_minima=None,
                 descuento_aplicado=0.0, fecha_inicio=None, fecha_fin=None,
                 estado="Activa", id=None):
        """
        Inicializa una promoción.
        - tipo: '3x2', 'DescuentoCantidad', 'DescuentoCategoria', 'DescuentoProducto'.
        - producto_id: código de barras del producto (para promociones específicas).
        - categoria_id: ID de categoría (para promociones por categoría).
        - cantidad_minima: cantidad requerida para activar la promoción (para 3x2 y descuento por cantidad).
        - descuento_aplicado: porcentaje de descuento (ej. 10 para 10%).
        - fecha_inicio: fecha de inicio (YYYY-MM-DD).
        - fecha_fin: fecha de fin (YYYY-MM-DD).
        """
        self.id = id
        self.tipo = tipo
        self.producto_id = producto_id
        self.categoria_id = categoria_id
        self.cantidad_minima = cantidad_minima
        self.descuento_aplicado = descuento_aplicado
        self.fecha_inicio = fecha_inicio or datetime.now().strftime("%Y-%m-%d")
        self.fecha_fin = fecha_fin or datetime.now().strftime("%Y-%m-%d")
        self.estado = estado

        self._validar()

    def _validar(self):
        """Valida que la promoción esté correctamente configurada."""
        if self.tipo not in [self.TIPO_3X2, self.TIPO_DESCUENTO_CANTIDAD,
                             self.TIPO_DESCUENTO_CATEGORIA, self.TIPO_DESCUENTO_PRODUCTO]:
            raise ValueError(f"Tipo de promoción inválido: {self.tipo}")

        if self.tipo in [self.TIPO_3X2, self.TIPO_DESCUENTO_CANTIDAD]:
            if not self.cantidad_minima or self.cantidad_minima < 2:
                raise ValueError("Para 3x2 o descuento por cantidad, se necesita cantidad_minima >= 2.")
            if self.tipo == self.TIPO_3X2 and self.descuento_aplicado != 0:
                print("⚠️ En 3x2, el descuento se calcula automáticamente (se descuenta el producto de menor precio).")
        else:
            if self.descuento_aplicado <= 0 or self.descuento_aplicado > 100:
                raise ValueError("El descuento debe ser un porcentaje entre 1 y 100.")

        # Validar que fecha_inicio <= fecha_fin
        if self.fecha_inicio > self.fecha_fin:
            raise ValueError("La fecha de inicio no puede ser mayor a la fecha de fin.")

        # Validar que si es por producto, el producto exista
        if self.tipo == self.TIPO_DESCUENTO_PRODUCTO:
            if not self.producto_id:
                raise ValueError("Para promoción por producto, se debe especificar producto_id.")
            producto = Producto.buscar_por_codigo(self.producto_id)
            if not producto:
                raise ValueError(f"Producto con código {self.producto_id} no encontrado.")

        # Validar que si es por categoría, la categoría exista (validación simple, se puede mejorar)
        if self.tipo == self.TIPO_DESCUENTO_CATEGORIA:
            if not self.categoria_id:
                raise ValueError("Para promoción por categoría, se debe especificar categoria_id.")
            # Podríamos validar que la categoría existe en la BD, pero no tenemos modelo Categoria aún.
            # Lo dejamos como validación simple y se asume que el ID existe.

    # =====================================================================
    # MÉTODOS DE PERSISTENCIA
    # =====================================================================
    def guardar(self):
        """
        Inserta o actualiza la promoción en la base de datos.
        Retorna True si fue exitoso, False en caso de error.
        """
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()

            if self.id is None:
                cursor.execute('''
                    INSERT INTO promociones (
                        tipo, producto_id, categoria_id, cantidad_minima,
                        descuento_aplicado, fecha_inicio, fecha_fin, estado
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (self.tipo, self.producto_id, self.categoria_id, self.cantidad_minima,
                      self.descuento_aplicado, self.fecha_inicio, self.fecha_fin, self.estado))
                self.id = cursor.lastrowid
            else:
                cursor.execute('''
                    UPDATE promociones
                    SET tipo = ?, producto_id = ?, categoria_id = ?, cantidad_minima = ?,
                        descuento_aplicado = ?, fecha_inicio = ?, fecha_fin = ?, estado = ?
                    WHERE id = ?
                ''', (self.tipo, self.producto_id, self.categoria_id, self.cantidad_minima,
                      self.descuento_aplicado, self.fecha_inicio, self.fecha_fin, self.estado, self.id))

            conn.commit()
            conn.close()
            return True

        except sqlite3.Error as e:
            print(f"❌ Error al guardar promoción: {e}")
            return False

    # =====================================================================
    # MÉTODOS DE CONSULTA (ESTÁTICOS)
    # =====================================================================
    @staticmethod
    def buscar_por_id(promocion_id):
        """Retorna un objeto Promocion si existe, o None si no."""
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, tipo, producto_id, categoria_id, cantidad_minima,
                       descuento_aplicado, fecha_inicio, fecha_fin, estado
                FROM promociones
                WHERE id = ?
            ''', (promocion_id,))
            row = cursor.fetchone()

            if row:
                promocion = Promocion(
                    tipo=row[1],
                    producto_id=row[2],
                    categoria_id=row[3],
                    cantidad_minima=row[4],
                    descuento_aplicado=row[5],
                    fecha_inicio=row[6],
                    fecha_fin=row[7],
                    estado=row[8],
                    id=row[0]
                )
                conn.close()
                return promocion
            conn.close()
            return None

        except sqlite3.Error as e:
            print(f"❌ Error al buscar promoción: {e}")
            return None

    @staticmethod
    def obtener_promociones_activas():
        """Retorna una lista de promociones activas y vigentes (fecha actual dentro del rango)."""
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()
            hoy = datetime.now().strftime("%Y-%m-%d")
            cursor.execute('''
                SELECT id, tipo, producto_id, categoria_id, cantidad_minima,
                       descuento_aplicado, fecha_inicio, fecha_fin, estado
                FROM promociones
                WHERE estado = 'Activa' AND fecha_inicio <= ? AND fecha_fin >= ?
                ORDER BY fecha_inicio ASC
            ''', (hoy, hoy))
            rows = cursor.fetchall()
            conn.close()

            promociones = []
            for row in rows:
                promociones.append(Promocion(
                    tipo=row[1],
                    producto_id=row[2],
                    categoria_id=row[3],
                    cantidad_minima=row[4],
                    descuento_aplicado=row[5],
                    fecha_inicio=row[6],
                    fecha_fin=row[7],
                    estado=row[8],
                    id=row[0]
                ))
            return promociones

        except sqlite3.Error as e:
            print(f"❌ Error al obtener promociones activas: {e}")
            return []

    @staticmethod
    def obtener_promociones_por_producto(codigo_barras):
        """
        Retorna una lista de promociones activas que aplican a un producto específico.
        Busca: por producto_id directo, por categoría del producto, o por cantidad (3x2/DescuentoCantidad).
        """
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()
            hoy = datetime.now().strftime("%Y-%m-%d")

            # Obtener la categoría del producto
            producto = Producto.buscar_por_codigo(codigo_barras)
            if not producto:
                return []

            categoria_id = producto.categoria_id

            # Buscar promociones que coincidan con producto_id, categoria_id, o tipo 3x2/DescuentoCantidad
            cursor.execute('''
                SELECT id, tipo, producto_id, categoria_id, cantidad_minima,
                       descuento_aplicado, fecha_inicio, fecha_fin, estado
                FROM promociones
                WHERE estado = 'Activa'
                  AND fecha_inicio <= ? AND fecha_fin >= ?
                  AND (
                      producto_id = ?
                      OR categoria_id = ?
                      OR tipo IN (?, ?)
                  )
                ORDER BY fecha_inicio ASC
            ''', (hoy, hoy, codigo_barras, categoria_id,
                  Promocion.TIPO_3X2, Promocion.TIPO_DESCUENTO_CANTIDAD))
            rows = cursor.fetchall()
            conn.close()

            promociones = []
            for row in rows:
                promociones.append(Promocion(
                    tipo=row[1],
                    producto_id=row[2],
                    categoria_id=row[3],
                    cantidad_minima=row[4],
                    descuento_aplicado=row[5],
                    fecha_inicio=row[6],
                    fecha_fin=row[7],
                    estado=row[8],
                    id=row[0]
                ))
            return promociones

        except sqlite3.Error as e:
            print(f"❌ Error al obtener promociones por producto: {e}")
            return []

    # =====================================================================
    # MÉTODOS DE APLICACIÓN DE DESCUENTO
    # =====================================================================
    def aplicar_promocion(self, carrito_items):
        """
        Aplica la promoción a un carrito y retorna el descuento total.
        - carrito_items: lista de dicts con 'codigo', 'nombre', 'cantidad', 'precio', 'subtotal'.
        Retorna: (descuento_total, mensaje) donde descuento_total es el monto a restar.
        """
        if self.estado != 'Activa' or not self._esta_vigente():
            return 0.0, "Promoción inactiva o vencida."

        descuento = 0.0
        mensaje = ""

        if self.tipo == self.TIPO_3X2:
            # Buscar el producto específico (si está definido) o aplicar a todos los productos del carrito
            if self.producto_id:
                # Aplicar solo a ese producto
                for item in carrito_items:
                    if item['codigo'] == self.producto_id and item['cantidad'] >= self.cantidad_minima:
                        # Calcular cuántos grupos de 'cantidad_minima' (ej. 3) hay
                        grupos = item['cantidad'] // self.cantidad_minima
                        # El descuento es el precio del producto de menor precio en el grupo
                        # Simplificamos: descuento = precio * grupos (asumiendo que todos los productos tienen el mismo precio)
                        # En realidad, se descuenta el de menor precio, pero simplificamos.
                        descuento += item['precio'] * grupos
                        mensaje = f"Aplicado 3x2 en {item['nombre']} ({grupos} grupos)"
            else:
                # Aplicar a todo el carrito (más complejo, lo simplificamos)
                # Buscamos el item de menor precio entre todos los que tienen cantidad >= cantidad_minima
                items_filtrados = [item for item in carrito_items if item['cantidad'] >= self.cantidad_minima]
                if items_filtrados:
                    # Ordenamos por precio y tomamos el de menor precio
                    items_filtrados.sort(key=lambda x: x['precio'])
                    item_menor_precio = items_filtrados[0]
                    grupos = item_menor_precio['cantidad'] // self.cantidad_minima
                    descuento += item_menor_precio['precio'] * grupos
                    mensaje = f"Aplicado 3x2 en {item_menor_precio['nombre']} ({grupos} grupos)"

        elif self.tipo == self.TIPO_DESCUENTO_CANTIDAD:
            # Descuento por cantidad: se aplica un % de descuento si se supera la cantidad mínima
            if self.producto_id:
                for item in carrito_items:
                    if item['codigo'] == self.producto_id and item['cantidad'] >= self.cantidad_minima:
                        descuento += (item['subtotal'] * self.descuento_aplicado / 100)
                        mensaje = f"Descuento del {self.descuento_aplicado}% por cantidad en {item['nombre']}"
            else:
                # Aplicar a todos los productos del carrito que superen la cantidad mínima
                for item in carrito_items:
                    if item['cantidad'] >= self.cantidad_minima:
                        descuento += (item['subtotal'] * self.descuento_aplicado / 100)
                        mensaje = f"Descuento del {self.descuento_aplicado}% por cantidad en {item['nombre']}"

        elif self.tipo == self.TIPO_DESCUENTO_PRODUCTO:
            # Descuento porcentual sobre un producto específico
            if self.producto_id:
                for item in carrito_items:
                    if item['codigo'] == self.producto_id:
                        descuento += (item['subtotal'] * self.descuento_aplicado / 100)
                        mensaje = f"Descuento del {self.descuento_aplicado}% en {item['nombre']}"

        elif self.tipo == self.TIPO_DESCUENTO_CATEGORIA:
            # Descuento porcentual sobre una categoría completa
            if self.categoria_id:
                # Necesitamos obtener la categoría de cada producto en el carrito
                # Para simplificar, asumimos que tenemos la categoría en el item del carrito
                # o la obtenemos de la BD. Por ahora, dejamos esto como placeholder.
                for item in carrito_items:
                    producto = Producto.buscar_por_codigo(item['codigo'])
                    if producto and producto.categoria_id == self.categoria_id:
                        descuento += (item['subtotal'] * self.descuento_aplicado / 100)
                        mensaje = f"Descuento del {self.descuento_aplicado}% en categoría {self.categoria_id}"

        return round(descuento, 2), mensaje

    def _esta_vigente(self):
        """Verifica si la promoción está vigente según la fecha actual."""
        hoy = datetime.now().date()
        inicio = datetime.strptime(self.fecha_inicio, "%Y-%m-%d").date()
        fin = datetime.strptime(self.fecha_fin, "%Y-%m-%d").date()
        return inicio <= hoy <= fin

    # =====================================================================
    # MÉTODOS DE GESTIÓN DE ESTADO
    # =====================================================================
    def cambiar_estado(self, nuevo_estado):
        """Cambia el estado de la promoción (Activa/Inactiva)."""
        if nuevo_estado not in ['Activa', 'Inactiva']:
            print("❌ Estado inválido. Use 'Activa' o 'Inactiva'.")
            return False
        self.estado = nuevo_estado
        return self.guardar()

    # =====================================================================
    # REPRESENTACIÓN
    # =====================================================================
    def __str__(self):
        return f"Promoción {self.id}: {self.tipo} - {self.estado}"

    def __repr__(self):
        return f"Promocion(id={self.id}, tipo='{self.tipo}', estado='{self.estado}')"