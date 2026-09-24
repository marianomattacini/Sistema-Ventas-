import sqlite3
from datetime import datetime
from database.config import get_sqlite_connection
from models.producto import Producto
from models.proveedor import Proveedor
from models.usuario import Usuario

class Compra:
    """
    Representa una compra a un proveedor: cabecera, detalles y actualización de stock.
    """

    def __init__(self, nro_factura, proveedor_id, supervisor_id, total_factura=0.0):
        """
        Inicializa una nueva compra con estado 'Ingresado'.
        """
        self.id = None
        self.nro_factura = nro_factura.strip()
        self.proveedor_id = proveedor_id
        self.supervisor_id = supervisor_id
        self.fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.total_factura = total_factura
        self.estado = "Ingresado"  # Ingresado, Anulado

        # Atributos internos para detalles
        self.detalles = []  # Lista de dicts: {'codigo_producto': str, 'cantidad': int, 'precio_costo': float, 'subtotal': float}

    # =====================================================================
    # MÉTODOS DE GESTIÓN DE DETALLES
    # =====================================================================
    def agregar_detalle(self, codigo_producto, cantidad, precio_costo):
        """
        Agrega un producto al detalle de la compra.
        - Verifica que el producto exista en la BD.
        - Calcula el subtotal = cantidad * precio_costo.
        - Si el producto ya está en el detalle, actualiza la cantidad y el precio.
        Retorna True si se agregó correctamente, False en caso de error.
        """
        # Validar que el producto exista
        producto = Producto.buscar_por_codigo(codigo_producto)
        if not producto:
            print(f"❌ Producto con código {codigo_producto} no encontrado.")
            return False

        if cantidad <= 0:
            print("❌ La cantidad debe ser positiva.")
            return False

        if precio_costo <= 0:
            print("❌ El precio costo debe ser positivo.")
            return False

        # Verificar si el producto ya está en el detalle
        for detalle in self.detalles:
            if detalle['codigo_producto'] == codigo_producto:
                # Actualizar cantidad y precio (reemplazo)
                detalle['cantidad'] = cantidad
                detalle['precio_costo'] = precio_costo
                detalle['subtotal'] = cantidad * precio_costo
                self._calcular_total()
                return True

        # Agregar nuevo detalle
        subtotal = cantidad * precio_costo
        self.detalles.append({
            'codigo_producto': codigo_producto,
            'cantidad': cantidad,
            'precio_costo': precio_costo,
            'subtotal': subtotal
        })
        self._calcular_total()
        return True

    def _calcular_total(self):
        """Recalcula el total de la factura sumando los subtotales de los detalles."""
        self.total_factura = sum(detalle['subtotal'] for detalle in self.detalles)

    # =====================================================================
    # MÉTODOS DE PERSISTENCIA
    # =====================================================================
    def guardar(self):
        """
        Guarda la compra en la base de datos (cabecera y detalles).
        - Actualiza el stock de cada producto sumando la cantidad ingresada.
        Retorna True si fue exitoso, False en caso de error.
        """
        if not self.detalles:
            print("❌ No se puede guardar una compra sin detalles.")
            return False

        # Validar que el proveedor existe
        proveedor = Proveedor.buscar_por_cuit(self.proveedor_id)
        if not proveedor:
            print(f"❌ Proveedor con CUIT {self.proveedor_id} no encontrado.")
            return False

        # Validar que el supervisor existe
        supervisor = Usuario.obtener_por_id(self.supervisor_id)
        if not supervisor:
            print(f"❌ Supervisor con ID {self.supervisor_id} no encontrado.")
            return False

        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()

            # Insertar cabecera
            cursor.execute('''
                INSERT INTO compras_cabecera (
                    nro_factura, proveedor_id, supervisor_id, fecha_hora, total_factura, estado
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (self.nro_factura, self.proveedor_id, self.supervisor_id,
                  self.fecha_hora, self.total_factura, self.estado))
            self.id = cursor.lastrowid

            # Insertar detalles y actualizar stock
            for detalle in self.detalles:
                cursor.execute('''
                    INSERT INTO compras_detalle (
                        compra_id, codigo_producto, cantidad_ingresada, precio_costo, subtotal
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (self.id, detalle['codigo_producto'], detalle['cantidad'],
                      detalle['precio_costo'], detalle['subtotal']))

                # Actualizar stock del producto (sumar), usando la MISMA conexión/
                # transacción para evitar el "database is locked" que dejaba el
                # stock sin actualizar al abrir una segunda conexión de escritura
                cursor.execute('''
                    UPDATE productos SET stock_actual = stock_actual + ?
                    WHERE codigo_barras = ?
                ''', (detalle['cantidad'], detalle['codigo_producto']))

            conn.commit()
            conn.close()
            return True

        except sqlite3.IntegrityError as e:
            print(f"❌ Error de integridad (ej. nro_factura duplicado): {e}")
            return False
        except sqlite3.Error as e:
            try:
                conn.rollback()
                conn.close()
            except Exception:
                pass
            print(f"❌ Error al guardar compra: {e}")
            return False

    # =====================================================================
    # MÉTODOS DE ANULACIÓN
    # =====================================================================
    def anular_compra(self, usuario_autorizante):
        """
        Anula la compra (cambia estado a 'Anulado') y revierte el stock.
        Solo Administrador o Gerente General.
        Retorna True si fue exitoso, False en caso de error.
        """
        if not usuario_autorizante.tiene_permiso('gestionar_compras'):
            print("❌ Permisos insuficientes para anular compra.")
            return False

        if self.estado != "Ingresado":
            print("❌ Solo se pueden anular compras en estado 'Ingresado'.")
            return False

        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()

            # Cambiar estado a 'Anulado'
            cursor.execute('''
                UPDATE compras_cabecera
                SET estado = 'Anulado'
                WHERE id = ?
            ''', (self.id,))
            self.estado = "Anulado"

            # Revertir el stock (restar las cantidades), usando la MISMA conexión/
            # transacción para evitar el "database is locked" que dejaba el stock
            # sin revertir al abrir una segunda conexión de escritura
            for detalle in self.detalles:
                cursor.execute('''
                    UPDATE productos SET stock_actual = stock_actual - ?
                    WHERE codigo_barras = ?
                ''', (detalle['cantidad'], detalle['codigo_producto']))

            conn.commit()
            conn.close()

            # Registrar en auditoría
            self._registrar_auditoria(
                usuario_autorizante.id,
                f"Compra {self.nro_factura} anulada",
                f"Total: ${self.total_factura:.2f} - Proveedor: {self.proveedor_id}"
            )

            return True

        except sqlite3.Error as e:
            try:
                conn.rollback()
                conn.close()
            except Exception:
                pass
            print(f"❌ Error al anular compra: {e}")
            return False

    # =====================================================================
    # MÉTODOS DE CONSULTA (ESTÁTICOS)
    # =====================================================================
    @staticmethod
    def buscar_por_factura(nro_factura):
        """
        Retorna un objeto Compra si existe, o None si no.
        """
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, nro_factura, proveedor_id, supervisor_id, fecha_hora,
                       total_factura, estado
                FROM compras_cabecera
                WHERE nro_factura = ?
            ''', (nro_factura,))
            row = cursor.fetchone()

            if not row:
                conn.close()
                return None

            compra = Compra(
                nro_factura=row[1],
                proveedor_id=row[2],
                supervisor_id=row[3],
                total_factura=row[5]
            )
            compra.id = row[0]
            compra.fecha_hora = row[4]
            compra.estado = row[6]

            # Cargar detalles
            cursor.execute('''
                SELECT codigo_producto, cantidad_ingresada, precio_costo, subtotal
                FROM compras_detalle
                WHERE compra_id = ?
            ''', (compra.id,))
            detalles = cursor.fetchall()
            for detalle in detalles:
                compra.detalles.append({
                    'codigo_producto': detalle[0],
                    'cantidad': detalle[1],
                    'precio_costo': detalle[2],
                    'subtotal': detalle[3]
                })

            conn.close()
            return compra

        except sqlite3.Error as e:
            try:
                conn.rollback()
                conn.close()
            except Exception:
                pass
            print(f"❌ Error al buscar compra por factura: {e}")
            return None

    @staticmethod
    def obtener_compras_por_proveedor(proveedor_id):
        """
        Retorna una lista de objetos Compra realizadas a un proveedor específico.
        """
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, nro_factura, proveedor_id, supervisor_id, fecha_hora,
                       total_factura, estado
                FROM compras_cabecera
                WHERE proveedor_id = ?
                ORDER BY fecha_hora DESC
            ''', (proveedor_id,))
            rows = cursor.fetchall()
            conn.close()

            compras = []
            for row in rows:
                compra = Compra(
                    nro_factura=row[1],
                    proveedor_id=row[2],
                    supervisor_id=row[3],
                    total_factura=row[5]
                )
                compra.id = row[0]
                compra.fecha_hora = row[4]
                compra.estado = row[6]

                # Cargar detalles (se puede optimizar con una segunda consulta, pero por simplicidad lo dejamos así)
                # En producción, se podría cargar bajo demanda con un método separado.
                compras.append(compra)

            return compras

        except sqlite3.Error as e:
            try:
                conn.rollback()
                conn.close()
            except Exception:
                pass
            print(f"❌ Error al obtener compras por proveedor: {e}")
            return []

    # =====================================================================
    # MÉTODOS DE AUDITORÍA
    # =====================================================================
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
            try:
                conn.rollback()
                conn.close()
            except Exception:
                pass
            print(f"❌ Error al registrar auditoría: {e}")

    # =====================================================================
    # REPRESENTACIÓN
    # =====================================================================
    def __str__(self):
        return f"Compra {self.nro_factura} - Proveedor: {self.proveedor_id} - Total: ${self.total_factura:.2f}"

    def __repr__(self):
        return f"Compra(id={self.id}, factura='{self.nro_factura}', proveedor='{self.proveedor_id}')"