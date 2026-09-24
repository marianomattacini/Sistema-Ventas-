"""
Controlador de Productos (capa "Controlador" del patrón MVC).

Media entre la vista de inventario (views/ventana_productos.py) y el
modelo Producto: validaciones de entrada y reglas de negocio de alto
nivel quedan acá, no mezcladas con el dibujado de la interfaz.
"""

from models.producto import Producto


class ProductoController:

    @staticmethod
    def crear_producto(codigo_barras, nombre, categoria_id, precio_venta,
                        precio_costo, stock_actual, stock_minimo, tipo_garantia="comestible"):
        errores = ProductoController._validar_datos(
            codigo_barras, nombre, precio_venta, precio_costo, stock_actual, stock_minimo
        )
        if errores:
            return False, " / ".join(errores), None

        if Producto.buscar_por_codigo(codigo_barras):
            return False, "Ya existe un producto con ese código de barras.", None

        producto = Producto(
            codigo_barras=codigo_barras, nombre=nombre, categoria_id=categoria_id,
            precio_venta=float(precio_venta), precio_costo=float(precio_costo),
            stock_actual=int(stock_actual), stock_minimo=int(stock_minimo),
            tipo_garantia=tipo_garantia
        )
        ok = producto.guardar()
        return ok, ("Producto creado correctamente." if ok else "No se pudo guardar el producto."), producto

    @staticmethod
    def actualizar_producto(producto, nombre=None, precio_venta=None, precio_costo=None,
                             stock_minimo=None, categoria_id=None):
        if nombre is not None:
            producto.nombre = nombre
        if precio_venta is not None:
            producto.precio_venta = float(precio_venta)
        if precio_costo is not None:
            producto.precio_costo = float(precio_costo)
        if stock_minimo is not None:
            producto.stock_minimo = int(stock_minimo)
        if categoria_id is not None:
            producto.categoria_id = categoria_id

        errores = ProductoController._validar_datos(
            producto.codigo_barras, producto.nombre, producto.precio_venta,
            producto.precio_costo, producto.stock_actual, producto.stock_minimo
        )
        if errores:
            return False, " / ".join(errores)

        ok = producto.guardar()
        return ok, ("Producto actualizado." if ok else "No se pudo actualizar el producto.")

    @staticmethod
    def dar_de_baja(producto):
        producto.estado = "Inactivo"
        ok = producto.guardar()
        return ok, ("Producto dado de baja." if ok else "No se pudo dar de baja el producto.")

    @staticmethod
    def productos_con_stock_bajo():
        return Producto.productos_con_stock_bajo()

    @staticmethod
    def _validar_datos(codigo_barras, nombre, precio_venta, precio_costo, stock_actual, stock_minimo):
        """Control estricto de tipos de datos, pedido explícitamente por la
        consigna: evitar letras en precios, campos vacíos, negativos, etc."""
        errores = []
        if not codigo_barras or not str(codigo_barras).strip():
            errores.append("El código de barras es obligatorio.")
        if not nombre or not str(nombre).strip():
            errores.append("El nombre es obligatorio.")
        try:
            pv = float(precio_venta)
            if pv < 0:
                errores.append("El precio de venta no puede ser negativo.")
        except (TypeError, ValueError):
            errores.append("El precio de venta debe ser un número.")
        try:
            pc = float(precio_costo)
            if pc < 0:
                errores.append("El precio de costo no puede ser negativo.")
        except (TypeError, ValueError):
            errores.append("El precio de costo debe ser un número.")
        try:
            if int(stock_actual) < 0:
                errores.append("El stock actual no puede ser negativo.")
        except (TypeError, ValueError):
            errores.append("El stock actual debe ser un número entero.")
        try:
            if int(stock_minimo) < 0:
                errores.append("El stock mínimo no puede ser negativo.")
        except (TypeError, ValueError):
            errores.append("El stock mínimo debe ser un número entero.")
        return errores
