import sqlite3
import random
from datetime import datetime
from database.config import get_sqlite_connection
from models.producto import Producto
from models.cliente import Cliente
from models.usuario import Usuario
from models.notificacion import Notificacion

class Venta:
    """
    Representa una venta completa: carrito, pagos, ticket y descuento de stock.
    """

    def __init__(self, turno_id, dni_cliente=None):
        """
        Inicializa una nueva venta con carrito vacío, sin pagos y estado 'En Curso'.
        """
        self.turno_id = turno_id
        self.dni_cliente = dni_cliente
        self.nro_ticket = None
        self.fecha_hora = None
        self.total_facturado = 0.0
        self.descuento_total = 0.0
        self.puntos_sumados = 0
        self.estado = "En Curso"  # En Curso, Pausado, Completado, Anulado

        # Atributos internos
        self.carrito = []  # Lista de dicts: {'codigo': str, 'nombre': str, 'cantidad': int, 'precio': float, 'subtotal': float}
        self.pagos = []    # Lista de dicts: {'metodo': str, 'monto': float, 'vuelto': float, 'cuotas': int, 'interes': float, 'promocion': str}
        self.monto_restante = 0.0

    # =====================================================================
    # MÉTODOS DE GESTIÓN DEL CARRITO
    # =====================================================================
    def agregar_producto(self, codigo_barras, cantidad=1):
        """
        Agrega un producto al carrito si hay stock suficiente.
        Retorna (True, mensaje) si se agregó, o (False, mensaje de error).
        """
        producto = Producto.buscar_por_codigo(codigo_barras)
        if not producto:
            return False, "Producto no encontrado."

        if producto.estado != 'Activo':
            return False, "Producto inactivo."

        # Considerar la cantidad que ya está en el carrito para no exceder el
        # stock real disponible (antes solo se validaba la cantidad nueva,
        # permitiendo sobrevender si el producto ya estaba en el carrito).
        cantidad_en_carrito = sum(item['cantidad'] for item in self.carrito if item['codigo'] == codigo_barras)
        if producto.stock_actual < cantidad_en_carrito + cantidad:
            disponible = producto.stock_actual - cantidad_en_carrito
            return False, f"Stock insuficiente. Disponible: {max(disponible, 0)}"

        # Verificar si ya está en el carrito
        for item in self.carrito:
            if item['codigo'] == codigo_barras:
                item['cantidad'] += cantidad
                item['subtotal'] = item['cantidad'] * item['precio']
                self._actualizar_totales()
                return True, f"Producto actualizado: {producto.nombre} x{cantidad}"

        # Agregar nuevo producto al carrito
        self.carrito.append({
            'codigo': codigo_barras,
            'nombre': producto.nombre,
            'precio': producto.precio_venta,
            'cantidad': cantidad,
            'subtotal': cantidad * producto.precio_venta
        })
        self._actualizar_totales()
        return True, f"Producto agregado: {producto.nombre} x{cantidad}"

    def quitar_producto(self, codigo_barras, cantidad=1):
        """
        Quita un producto del carrito o reduce su cantidad.
        Retorna True si se pudo quitar, False si no existía.
        """
        for i, item in enumerate(self.carrito):
            if item['codigo'] == codigo_barras:
                if item['cantidad'] <= cantidad:
                    # Eliminar completamente
                    del self.carrito[i]
                else:
                    item['cantidad'] -= cantidad
                    item['subtotal'] = item['cantidad'] * item['precio']
                self._actualizar_totales()
                return True
        return False

    def vaciar_carrito(self):
        """Vacía completamente el carrito (sin eliminar productos de BD)."""
        self.carrito = []
        self.pagos = []
        self._actualizar_totales()

    def _actualizar_totales(self):
        """
        Recalcula el total de productos, aplica las promociones vigentes sobre
        el carrito (descontando el importe real, no solo mostrándolo) y
        recalcula el monto restante.
        """
        from models.promocion import Promocion

        total_bruto = sum(item['subtotal'] for item in self.carrito)

        # Recalcular descuentos por promoción para cada producto del carrito.
        # Se limpia el descuento anterior antes de recalcular para no acumular
        # de más si se agregan/quitan productos varias veces.
        for item in self.carrito:
            item['descuento'] = 0.0
            item['promocion_aplicada'] = None

        descuento_total = 0.0
        for item in self.carrito:
            promos = Promocion.obtener_promociones_por_producto(item['codigo'])
            for promo in promos:
                descuento, mensaje = promo.aplicar_promocion([item])
                if descuento > 0:
                    descuento = min(descuento, item['subtotal'])  # nunca descontar de más
                    item['descuento'] += descuento
                    item['promocion_aplicada'] = mensaje
                    descuento_total += descuento

        # p['monto'] ya es el importe aplicado a la venta (neto de vuelto);
        # NO hay que restar 'vuelto' de nuevo, o el restante queda mal calculado.
        total_pagado = sum(p['monto'] for p in self.pagos)
        self.descuento_total = round(descuento_total, 2)
        self.total_facturado = round(total_bruto - self.descuento_total, 2)
        self.monto_restante = round(self.total_facturado - total_pagado, 2)

    # =====================================================================
    # MÉTODOS DE GESTIÓN DE PAGOS
    # =====================================================================
    def agregar_pago(self, metodo, monto, cuotas=None, interes=0.0, promocion=None):
        """
        Agrega un pago a la venta.
        - metodo: 'Efectivo', 'Débito', 'Crédito', 'Transferencia' o 'QR'
        - monto: monto que efectivamente entrega/pasa el cliente por este método
          (para Efectivo puede ser mayor al restante, ahí se calcula el vuelto;
          para el resto de los métodos no puede superar el restante)
        - cuotas: solo para crédito (1 a 12)
        - interes: solo para crédito (si aplica)
        - promocion: descripción de promoción aplicada (si aplica)
        Retorna (True, mensaje) si el pago fue aceptado, o (False, mensaje de error).
        """
        if monto <= 0:
            return False, "El monto debe ser mayor a cero."

        metodos_validos = ('Efectivo', 'Débito', 'Crédito', 'Transferencia', 'QR')
        if metodo not in metodos_validos:
            return False, f"Método de pago no soportado: {metodo}"

        # Para crédito, validar cuotas
        if metodo == 'Crédito':
            if not cuotas or not (1 <= cuotas <= 12):
                return False, "Seleccione entre 1 y 12 cuotas."
            # Aquí se podría validar límite de la tarjeta (simulado)
            # En producción, se consultaría PostgreSQL

        recibido = monto

        if metodo == 'Efectivo':
            # El cliente puede entregar más que el restante; el vuelto es la diferencia.
            monto_aplicado = min(monto, self.monto_restante)
            vuelto = max(0.0, monto - self.monto_restante)
        else:
            # Débito, Crédito, Transferencia y QR: no se puede cobrar de más.
            if monto > self.monto_restante + 0.01:
                return False, f"El monto no puede superar el saldo restante: ${self.monto_restante:.2f}"
            monto_aplicado = monto
            vuelto = 0.0

        # Registrar el pago
        self.pagos.append({
            'metodo': metodo,
            'monto': monto_aplicado,
            'recibido': recibido,
            'vuelto': vuelto,
            'cuotas': cuotas,
            'interes': interes,
            'promocion': promocion
        })

        self._actualizar_totales()
        if vuelto > 0:
            return True, f"Pago de ${monto_aplicado:.2f} con {metodo} registrado. Vuelto: ${vuelto:.2f}"
        return True, f"Pago de ${monto_aplicado:.2f} con {metodo} registrado."

    # =====================================================================
    # MÉTODOS DE FINALIZACIÓN Y GESTIÓN DE TICKET
    # =====================================================================
    def finalizar_venta(self, usuario_autorizante=None):
        """
        Finaliza la venta: genera ticket, descuenta stock, suma puntos, guarda en BD.
        Retorna el nro_ticket generado, o None si falla.
        """
        if self.monto_restante > 0.01:
            print("❌ No se puede finalizar la venta. Saldo restante:", self.monto_restante)
            return None

        if not self.carrito:
            print("❌ No se puede finalizar una venta sin productos.")
            return None

        # Generar número de ticket único
        self.nro_ticket = self._generar_nro_ticket()
        self.fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.estado = "Completado"

        # Calcular puntos para el cliente (1 punto por cada $100)
        if self.dni_cliente:
            puntos = int(self.total_facturado // 100)
            self.puntos_sumados = puntos
        else:
            self.puntos_sumados = 0

        # Guardar en base de datos
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()

            # Insertar cabecera
            cursor.execute('''
                INSERT INTO ventas_cabecera (
                    nro_ticket, turno_id, dni_cliente, fecha_hora,
                    total_facturado, descuento_total, puntos_sumados, estado
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (self.nro_ticket, self.turno_id, self.dni_cliente,
                  self.fecha_hora, self.total_facturado, self.descuento_total,
                  self.puntos_sumados, self.estado))

            # Insertar detalles y descontar stock
            alertas_stock_bajo = []
            for item in self.carrito:
                cursor.execute('''
                    INSERT INTO ventas_detalle (nro_ticket, codigo_producto, cantidad, subtotal, descuento)
                    VALUES (?, ?, ?, ?, ?)
                ''', (self.nro_ticket, item['codigo'], item['cantidad'], item['subtotal'], item.get('descuento', 0.0)))

                # Descontar stock (usando la MISMA conexión/transacción para evitar
                # el error "database is locked" que ocurría al abrir una segunda
                # conexión de escritura mientras esta transacción seguía sin commitear,
                # lo cual dejaba el stock sin actualizar aunque la venta se guardara)
                cursor.execute('''
                    UPDATE productos SET stock_actual = stock_actual - ?
                    WHERE codigo_barras = ?
                ''', (item['cantidad'], item['codigo']))

                # Verificar si el producto quedó con stock bajo (por debajo de su
                # mínimo configurado) para avisar al Gerente General más abajo,
                # una vez cerrada esta transacción.
                cursor.execute('''
                    SELECT nombre, stock_actual, stock_minimo FROM productos
                    WHERE codigo_barras = ?
                ''', (item['codigo'],))
                fila = cursor.fetchone()
                if fila and fila[1] <= fila[2]:
                    alertas_stock_bajo.append({
                        'codigo': item['codigo'], 'nombre': fila[0],
                        'stock_actual': fila[1], 'stock_minimo': fila[2]
                    })

            # Insertar pagos
            for pago in self.pagos:
                cursor.execute('''
                    INSERT INTO ventas_pagos (
                        nro_ticket, metodo_pago, monto_abonado, monto_recibido,
                        monto_vuelto, cuotas, interes_aplicado, promocion_aplicada
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (self.nro_ticket, pago['metodo'], pago['monto'], pago.get('recibido', pago['monto']),
                      pago.get('vuelto', 0), pago.get('cuotas'), pago.get('interes', 0), pago.get('promocion')))

            # Nota: la suma de puntos al cliente y las notificaciones de stock bajo
            # se hacen DESPUÉS de conn.commit()/conn.close() (ver abajo), porque
            # ambas abren su propia conexión a la BD y hacerlo mientras esta
            # transacción sigue abierta provoca "database is locked" (el mismo
            # bug que afectaba el descuento de stock).

            conn.commit()
            conn.close()

            # Sumar puntos al cliente si se registró (con conexión propia, ya
            # cerrada la transacción de la venta)
            if self.dni_cliente and self.puntos_sumados > 0:
                cliente = Cliente.buscar_por_dni(self.dni_cliente)
                if cliente:
                    cliente.agregar_puntos(self.puntos_sumados)

            # Notificar al Gerente General si algún producto quedó con stock
            # por debajo (o igual) de su mínimo configurado
            if alertas_stock_bajo:
                self._notificar_stock_bajo(alertas_stock_bajo)

            # Registrar en auditoría (si hay usuario autorizante)
            if usuario_autorizante:
                self._registrar_auditoria(
                    usuario_autorizante.id,
                    f"Venta completada - Ticket {self.nro_ticket}",
                    f"Total: ${self.total_facturado:.2f} - Cliente: {self.dni_cliente or 'Sin DNI'}"
                )

            return self.nro_ticket

        except sqlite3.Error as e:
            try:
                conn.rollback()
                conn.close()
            except Exception:
                pass
            print(f"❌ Error al guardar la venta: {e}")
            return None

    @staticmethod
    def _notificar_stock_bajo(alertas):
        """
        Crea una notificación para cada Gerente General activo por cada producto
        que quedó con stock por debajo (o igual) de su mínimo, para que se
        gestione el pedido de reposición al proveedor.
        """
        try:
            gerentes = [u for u in Usuario.obtener_todos()
                        if u.rol == "Gerente General" and u.estado == "Activo"]
            for alerta in alertas:
                mensaje = (
                    f"⚠️ Stock bajo: '{alerta['nombre']}' ({alerta['codigo']}) "
                    f"quedó con {alerta['stock_actual']} unidades "
                    f"(mínimo configurado: {alerta['stock_minimo']}). "
                    f"Se recomienda generar un pedido al proveedor."
                )
                for gerente in gerentes:
                    Notificacion(
                        usuario_destino=gerente.id,
                        tipo=Notificacion.TIPO_SISTEMA,
                        mensaje=mensaje
                    ).guardar()
        except Exception as e:
            print(f"⚠️ No se pudo generar la notificación de stock bajo: {e}")

    def _generar_nro_ticket(self):
        """Genera un número de ticket único con formato TKT-YYYYMMDDHHMMSS-XXX."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_num = random.randint(100, 999)
        return f"TKT-{timestamp}-{random_num}"

    # =====================================================================
    # MÉTODOS DE PAUSA Y REANUDACIÓN
    # =====================================================================
    def pausar_ticket(self):
        """
        Cambia el estado de la venta a 'Pausado' y guarda en la BD con un ticket temporal.
        Retorna el nro_ticket temporal si fue exitoso, None si falla.
        """
        if not self.carrito:
            print("❌ No se puede pausar un carrito vacío.")
            return None

        # Generar ticket temporal con prefijo PAU
        self.nro_ticket = f"PAU-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.estado = "Pausado"

        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()

            # Guardar cabecera con estado Pausado
            cursor.execute('''
                INSERT INTO ventas_cabecera (
                    nro_ticket, turno_id, dni_cliente, fecha_hora,
                    total_facturado, puntos_sumados, estado
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (self.nro_ticket, self.turno_id, self.dni_cliente,
                  self.fecha_hora, self.total_facturado, 0, self.estado))

            # Guardar detalles
            for item in self.carrito:
                cursor.execute('''
                    INSERT INTO ventas_detalle (nro_ticket, codigo_producto, cantidad, subtotal)
                    VALUES (?, ?, ?, ?)
                ''', (self.nro_ticket, item['codigo'], item['cantidad'], item['subtotal']))

            conn.commit()
            conn.close()

            # Limpiar carrito local (los datos quedan en BD)
            self.carrito = []
            self.pagos = []
            self._actualizar_totales()

            return self.nro_ticket

        except sqlite3.Error as e:
            try:
                conn.rollback()
                conn.close()
            except Exception:
                pass
            print(f"❌ Error al pausar ticket: {e}")
            return None

    @staticmethod
    def retomar_ticket(nro_ticket_pausado):
        """
        Carga un ticket pausado desde la BD y retorna un objeto Venta listo para continuar.
        """
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()

            # Obtener cabecera
            cursor.execute('''
                SELECT turno_id, dni_cliente, total_facturado
                FROM ventas_cabecera
                WHERE nro_ticket = ? AND estado = 'Pausado'
            ''', (nro_ticket_pausado,))
            row = cursor.fetchone()

            if not row:
                conn.close()
                return None

            # Crear objeto Venta
            venta = Venta(turno_id=row[0], dni_cliente=row[1])
            venta.nro_ticket = nro_ticket_pausado
            venta.total_facturado = row[2]
            venta.estado = "Pausado"

            # Cargar detalles del carrito
            cursor.execute('''
                SELECT codigo_producto, cantidad, subtotal
                FROM ventas_detalle
                WHERE nro_ticket = ?
            ''', (nro_ticket_pausado,))
            detalles = cursor.fetchall()

            for detalle in detalles:
                # Buscar producto para obtener el nombre y precio
                producto = Producto.buscar_por_codigo(detalle[0])
                if producto:
                    venta.carrito.append({
                        'codigo': detalle[0],
                        'nombre': producto.nombre,
                        'precio': producto.precio_venta,
                        'cantidad': detalle[1],
                        'subtotal': detalle[2]
                    })

            # Calcular monto restante (sin pagos, ya que estaba pausado)
            venta._actualizar_totales()

            conn.close()
            return venta

        except sqlite3.Error as e:
            try:
                conn.rollback()
                conn.close()
            except Exception:
                pass
            print(f"❌ Error al retomar ticket: {e}")
            return None

    # =====================================================================
    # MÉTODOS DE ANULACIÓN Y AUDITORÍA
    # =====================================================================
    def anular_venta(self, usuario_autorizante):
        """
        Anula la venta (cambia estado a 'Anulado').
        Solo puede ser ejecutado por un Supervisor o superior.
        """
        if not usuario_autorizante.tiene_permiso('anular_pedido'):
            print("❌ Permisos insuficientes para anular venta.")
            return False

        if self.estado != "Completado":
            print("❌ Solo se pueden anular ventas ya completadas.")
            return False

        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE ventas_cabecera
                SET estado = 'Anulado'
                WHERE nro_ticket = ?
            ''', (self.nro_ticket,))

            conn.commit()
            conn.close()

            self.estado = "Anulado"

            # Registrar en auditoría
            self._registrar_auditoria(
                usuario_autorizante.id,
                f"Venta anulada - Ticket {self.nro_ticket}",
                f"Total anulado: ${self.total_facturado:.2f}"
            )

            return True

        except sqlite3.Error as e:
            try:
                conn.rollback()
                conn.close()
            except Exception:
                pass
            print(f"❌ Error al anular venta: {e}")
            return False

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
    # MÉTODOS ESTÁTICOS DE CONSULTA
    # =====================================================================
    @staticmethod
    def obtener_venta_por_ticket(nro_ticket):
        """
        Carga una venta completada desde la BD y retorna un objeto Venta.
        """
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT turno_id, dni_cliente, fecha_hora, total_facturado, puntos_sumados, estado
                FROM ventas_cabecera
                WHERE nro_ticket = ?
            ''', (nro_ticket,))
            row = cursor.fetchone()

            if not row:
                conn.close()
                return None

            venta = Venta(turno_id=row[0], dni_cliente=row[1])
            venta.nro_ticket = nro_ticket
            venta.fecha_hora = row[2]
            venta.total_facturado = row[3]
            venta.puntos_sumados = row[4]
            venta.estado = row[5]

            # Cargar detalles
            cursor.execute('''
                SELECT codigo_producto, cantidad, subtotal
                FROM ventas_detalle
                WHERE nro_ticket = ?
            ''', (nro_ticket,))
            detalles = cursor.fetchall()

            for detalle in detalles:
                producto = Producto.buscar_por_codigo(detalle[0])
                if producto:
                    venta.carrito.append({
                        'codigo': detalle[0],
                        'nombre': producto.nombre,
                        'precio': producto.precio_venta,
                        'cantidad': detalle[1],
                        'subtotal': detalle[2]
                    })

            # Cargar pagos
            cursor.execute('''
                SELECT metodo_pago, monto_abonado, monto_vuelto, cuotas, interes_aplicado, promocion_aplicada
                FROM ventas_pagos
                WHERE nro_ticket = ?
            ''', (nro_ticket,))
            pagos = cursor.fetchall()

            for pago in pagos:
                venta.pagos.append({
                    'metodo': pago[0],
                    'monto': pago[1],
                    'vuelto': pago[2],
                    'cuotas': pago[3],
                    'interes': pago[4],
                    'promocion': pago[5]
                })

            venta._actualizar_totales()
            conn.close()
            return venta

        except sqlite3.Error as e:
            try:
                conn.rollback()
                conn.close()
            except Exception:
                pass
            print(f"❌ Error al obtener venta por ticket: {e}")
            return None

    @staticmethod
    def obtener_ventas_por_turno(turno_id):
        """
        Retorna una lista de tickets completados en un turno específico.
        """
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT nro_ticket, fecha_hora, total_facturado, estado
                FROM ventas_cabecera
                WHERE turno_id = ? AND estado = 'Completado'
                ORDER BY fecha_hora DESC
            ''', (turno_id,))
            rows = cursor.fetchall()
            conn.close()

            tickets = []
            for row in rows:
                tickets.append({
                    'nro_ticket': row[0],
                    'fecha_hora': row[1],
                    'total_facturado': row[2],
                    'estado': row[3]
                })
            return tickets
        except sqlite3.Error as e:
            try:
                conn.rollback()
                conn.close()
            except Exception:
                pass
            print(f"❌ Error al obtener ventas por turno: {e}")
            return []

    # =====================================================================
    # REPRESENTACIÓN
    # =====================================================================
    def __str__(self):
        return f"Venta {self.nro_ticket} - ${self.total_facturado:.2f} - {self.estado}"

    def __repr__(self):
        return f"Venta(ticket='{self.nro_ticket}', total={self.total_facturado})"