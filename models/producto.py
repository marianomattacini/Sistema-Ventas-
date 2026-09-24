import sqlite3
from database.config import get_sqlite_connection

class Producto:
    """
    Representa un producto del inventario con gestión de stock y precios.
    """

    def __init__(self, codigo_barras, nombre, categoria_id, precio_venta, precio_costo,
                stock_actual=0, stock_minimo=0, tipo_garantia='comestible', estado='Activo'):
        self.codigo_barras = codigo_barras
        self.nombre = nombre
        self.categoria_id = categoria_id
        self.precio_venta = precio_venta
        self.precio_costo = precio_costo
        self.stock_actual = stock_actual
        self.stock_minimo = stock_minimo
        self.tipo_garantia = tipo_garantia
        self.estado = estado

    # =====================================================================
    # MÉTODOS DE PERSISTENCIA
    # =====================================================================
    def guardar(self):
        """
        Inserta o actualiza el producto en la base de datos.
        Retorna True si fue exitoso, False en caso de error.
        """
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO productos (
                    codigo_barras, nombre, categoria_id, precio_venta, precio_costo,
                    stock_actual, stock_minimo, tipo_garantia, estado
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (self.codigo_barras, self.nombre, self.categoria_id, self.precio_venta,
                  self.precio_costo, self.stock_actual, self.stock_minimo,
                  self.tipo_garantia, self.estado))

            conn.commit()
            conn.close()
            return True

        except sqlite3.IntegrityError as e:
            print(f"❌ Error de integridad (ej. código duplicado): {e}")
            return False
        except sqlite3.Error as e:
            print(f"❌ Error al guardar producto: {e}")
            return False

    # =====================================================================
    # MÉTODOS ESTÁTICOS DE BÚSQUEDA Y CONSULTA
    # =====================================================================
    @staticmethod
    def buscar_por_codigo(codigo_barras):
        """
        Retorna un objeto Producto si existe, o None si no.
        """
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT codigo_barras, nombre, categoria_id, precio_venta, precio_costo,
                       stock_actual, stock_minimo, tipo_garantia, estado
                FROM productos
                WHERE codigo_barras = ?
            ''', (codigo_barras,))
            row = cursor.fetchone()
            conn.close()

            if row:
                return Producto(
                    codigo_barras=row[0],
                    nombre=row[1],
                    categoria_id=row[2],
                    precio_venta=row[3],
                    precio_costo=row[4],
                    stock_actual=row[5],
                    stock_minimo=row[6],
                    tipo_garantia=row[7],
                    estado=row[8]
                )
            return None
        except sqlite3.Error as e:
            print(f"❌ Error al buscar producto por código: {e}")
            return None

    @staticmethod
    def buscar_por_nombre(termino):
        """
        Busca productos cuyo nombre contenga el término (búsqueda parcial, insensible a mayúsculas).
        Retorna una lista de objetos Producto.
        """
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT codigo_barras, nombre, categoria_id, precio_venta, precio_costo,
                       stock_actual, stock_minimo, tipo_garantia, estado
                FROM productos
                WHERE nombre LIKE ? AND estado = 'Activo'
                ORDER BY nombre ASC
            ''', (f'%{termino}%',))
            rows = cursor.fetchall()
            conn.close()

            productos = []
            for row in rows:
                productos.append(Producto(
                    codigo_barras=row[0],
                    nombre=row[1],
                    categoria_id=row[2],
                    precio_venta=row[3],
                    precio_costo=row[4],
                    stock_actual=row[5],
                    stock_minimo=row[6],
                    tipo_garantia=row[7],
                    estado=row[8]
                ))
            return productos
        except sqlite3.Error as e:
            print(f"❌ Error al buscar productos por nombre: {e}")
            return []

    @staticmethod
    def obtener_todos(estado=None):
        """
        Retorna todos los productos (activos por defecto, o todos si estado=None).
        """
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()
            query = '''
                SELECT codigo_barras, nombre, categoria_id, precio_venta, precio_costo,
                       stock_actual, stock_minimo, tipo_garantia, estado
                FROM productos
            '''
            params = []
            if estado:
                query += " WHERE estado = ?"
                params.append(estado)
            query += " ORDER BY nombre ASC"

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            productos = []
            for row in rows:
                productos.append(Producto(
                    codigo_barras=row[0],
                    nombre=row[1],
                    categoria_id=row[2],
                    precio_venta=row[3],
                    precio_costo=row[4],
                    stock_actual=row[5],
                    stock_minimo=row[6],
                    tipo_garantia=row[7],
                    estado=row[8]
                ))
            return productos
        except sqlite3.Error as e:
            print(f"❌ Error al obtener todos los productos: {e}")
            return []

    # =====================================================================
    # MÉTODOS DE GESTIÓN DE STOCK
    # =====================================================================
    def actualizar_stock(self, cantidad, operacion='sumar'):
        """
        Actualiza el stock actual sumando o restando una cantidad.
        - operacion='sumar': incrementa el stock (ej. compras).
        - operacion='restar': decrementa el stock (ej. ventas).
        Retorna True si fue exitoso, False si no (ej. stock insuficiente).
        """
        if operacion == 'restar' and self.stock_actual < cantidad:
            print(f"❌ Stock insuficiente para {self.nombre}. Disponible: {self.stock_actual}, solicitado: {cantidad}")
            return False

        if operacion == 'sumar':
            self.stock_actual += cantidad
        elif operacion == 'restar':
            self.stock_actual -= cantidad
        else:
            print("❌ Operación inválida. Use 'sumar' o 'restar'.")
            return False

        return self.guardar()

    def verificar_stock_bajo(self):
        """
        Retorna True si el stock_actual <= stock_minimo.
        """
        return self.stock_actual <= self.stock_minimo

    @staticmethod
    def obtener_productos_con_stock_bajo():
        """
        Retorna una lista de productos con stock_actual <= stock_minimo y estado='Activo'.
        """
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT codigo_barras, nombre, categoria_id, precio_venta, precio_costo,
                       stock_actual, stock_minimo, tipo_garantia, estado
                FROM productos
                WHERE estado = 'Activo' AND stock_actual <= stock_minimo
                ORDER BY stock_actual ASC
            ''')
            rows = cursor.fetchall()
            conn.close()

            productos = []
            for row in rows:
                productos.append(Producto(
                    codigo_barras=row[0],
                    nombre=row[1],
                    categoria_id=row[2],
                    precio_venta=row[3],
                    precio_costo=row[4],
                    stock_actual=row[5],
                    stock_minimo=row[6],
                    tipo_garantia=row[7],
                    estado=row[8]
                ))
            return productos
        except sqlite3.Error as e:
            print(f"❌ Error al obtener productos con stock bajo: {e}")
            return []

    # =====================================================================
    # MÉTODOS DE GESTIÓN DE ESTADO
    # =====================================================================
    def cambiar_estado(self, nuevo_estado):
        """
        Cambia el estado del producto (Activo/Inactivo).
        """
        if nuevo_estado not in ['Activo', 'Inactivo']:
            print("❌ Estado inválido. Use 'Activo' o 'Inactivo'.")
            return False
        self.estado = nuevo_estado
        return self.guardar()

    # =====================================================================
    # REPRESENTACIÓN
    # =====================================================================
    def __str__(self):
        return f"{self.nombre} (Cód: {self.codigo_barras}) - Stock: {self.stock_actual} - ${self.precio_venta}"

    def __repr__(self):
        return f"Producto(codigo='{self.codigo_barras}', nombre='{self.nombre}')"