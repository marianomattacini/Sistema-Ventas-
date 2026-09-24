"""
Controlador de Ventas (capa "Controlador" del patrón MVC).

Este controlador es el único punto de entrada para realizar una venta.
La Vista (views/ventana_pos.py) NO debe manipular directamente instancias
de Venta salvo a través de este controlador: así queda un lugar único y
claro donde mostrar/explicar el flujo completo de una venta exitosa.

Flujo de una venta exitosa (para la defensa del proyecto):
    1. iniciar_venta(turno_id)               -> crea la venta en curso
    2. escanear_producto(codigo, cantidad)   -> agrega ítems, valida stock
       (las promociones vigentes se recalculan solas en cada paso)
    3. registrar_pago(metodo, monto, ...)    -> registra uno o más pagos
       hasta cubrir el total (soporta pago combinado / vuelto)
    4. confirmar_venta(usuario)              -> descuenta stock, suma
       puntos, notifica stock bajo al gerente y genera el ticket
"""

from models.venta import Venta
from models.producto import Producto


class VentaController:
    def __init__(self):
        self.venta_actual = None

    # ------------------------------------------------------------------
    # 1. Iniciar venta
    # ------------------------------------------------------------------
    def iniciar_venta(self, turno_id, dni_cliente=None):
        self.venta_actual = Venta(turno_id=turno_id, dni_cliente=dni_cliente)
        return self.venta_actual

    # ------------------------------------------------------------------
    # 2. Escanear / agregar producto
    # ------------------------------------------------------------------
    def escanear_producto(self, codigo_barras, cantidad=1):
        """
        Valida el código contra el catálogo y delega en el modelo el alta
        del ítem en el carrito (con control de stock disponible).
        Retorna (exito: bool, mensaje: str, producto: Producto | None)
        """
        if not self.venta_actual:
            return False, "No hay una venta en curso.", None

        producto = Producto.buscar_por_codigo(codigo_barras)
        if not producto:
            return False, "Producto no encontrado.", None
        if producto.estado != 'Activo':
            return False, f"El producto '{producto.nombre}' está inactivo.", producto
        if producto.stock_actual <= 0:
            return False, f"'{producto.nombre}' no tiene stock disponible.", producto

        exito, mensaje = self.venta_actual.agregar_producto(codigo_barras, cantidad)
        return exito, mensaje, producto

    def quitar_producto(self, codigo_barras):
        if not self.venta_actual:
            return False, "No hay una venta en curso."
        return self.venta_actual.quitar_producto(codigo_barras)

    # ------------------------------------------------------------------
    # 3. Registrar pago(s)
    # ------------------------------------------------------------------
    def registrar_pago(self, metodo, monto, cuotas=None, interes=0.0, promocion=None):
        if not self.venta_actual:
            return False, "No hay una venta en curso."
        return self.venta_actual.agregar_pago(
            metodo=metodo, monto=monto, cuotas=cuotas,
            interes=interes, promocion=promocion
        )

    def saldo_restante(self):
        if not self.venta_actual:
            return 0.0
        return self.venta_actual.monto_restante

    # ------------------------------------------------------------------
    # 4. Confirmar / finalizar venta
    # ------------------------------------------------------------------
    def confirmar_venta(self, usuario_autorizante=None):
        """
        Cierra la venta: descuenta stock, suma puntos del cliente, dispara
        notificación de stock bajo si corresponde, y devuelve el número de
        ticket generado (o None si la venta no pudo cerrarse, por ejemplo
        si el saldo restante todavía es mayor a cero).
        """
        if not self.venta_actual:
            return None
        ticket = self.venta_actual.finalizar_venta(usuario_autorizante)
        return ticket

    def cancelar_venta(self):
        self.venta_actual = None
