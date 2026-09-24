"""
Controlador de Compras / Abastecimiento (capa "Controlador" del patrón MVC).

Media entre la vista de compras (views/ventana_compras.py) y el modelo
Compra: arma la compra, valida los detalles y delega el alta de stock.
"""

from models.compra import Compra


class CompraController:
    def __init__(self):
        self.compra_actual = None

    def iniciar_compra(self, nro_factura, proveedor_id, supervisor_id):
        if not nro_factura or not str(nro_factura).strip():
            return False, "Debe indicar el número de factura.", None
        if not proveedor_id:
            return False, "Debe seleccionar un proveedor.", None

        self.compra_actual = Compra(
            nro_factura=nro_factura, proveedor_id=proveedor_id, supervisor_id=supervisor_id
        )
        return True, "Compra iniciada.", self.compra_actual

    def agregar_item(self, codigo_producto, cantidad, precio_costo_unitario):
        if not self.compra_actual:
            return False, "No hay una compra iniciada."
        try:
            cantidad = int(cantidad)
            precio_costo_unitario = float(precio_costo_unitario)
        except (TypeError, ValueError):
            return False, "Cantidad y precio de costo deben ser numéricos."
        if cantidad <= 0:
            return False, "La cantidad debe ser mayor a cero."
        if precio_costo_unitario < 0:
            return False, "El precio de costo no puede ser negativo."

        ok = self.compra_actual.agregar_detalle(codigo_producto, cantidad, precio_costo_unitario)
        return ok, ("Ítem agregado a la compra." if ok else "No se pudo agregar el ítem.")

    def confirmar_compra(self):
        """Guarda la compra: suma stock a cada producto (misma conexión/
        transacción para evitar bloqueos) y cierra la operación."""
        if not self.compra_actual:
            return False, "No hay una compra iniciada."
        ok = self.compra_actual.guardar()
        return ok, ("Compra registrada e ingresada al stock." if ok else "No se pudo registrar la compra.")

    def anular_compra(self, usuario_autorizante):
        if not self.compra_actual:
            return False, "No hay una compra cargada."
        ok = self.compra_actual.anular_compra(usuario_autorizante)
        return ok, ("Compra anulada, stock revertido." if ok else "No se pudo anular la compra.")
