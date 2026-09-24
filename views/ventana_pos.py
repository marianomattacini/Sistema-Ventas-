import customtkinter as ctk
from tkinter import messagebox
from models.producto import Producto
from models.cliente import Cliente
from models.venta import Venta
from models.usuario import Usuario
from models.turno import Turno
from models.promocion import Promocion
from models.entidad_pago import EntidadPago
from controllers.venta_controller import VentaController
from utils.generadores import generar_ticket_pdf, generar_reporte_turno_pdf
from database.config import get_sqlite_connection
from datetime import datetime
from views.base_frame import BaseFrame
import os
import platform
import subprocess

class FramePOS(BaseFrame):
    """Pantalla principal del Punto de Venta (POS)."""

    def __init__(self, parent, controller, usuario_actual, turno_actual=None, **kwargs):
        super().__init__(parent, controller, usuario_actual)

        self.turno_actual = turno_actual

        self.configure(fg_color="#F4F6F9")
        
        # Estado del carrito
        self.carrito = []
        self.pagos_acumulados = []
        self.monto_restante = 0.0
        self.venta_actual = None
        # Controlador de venta: la Vista delega en él todo el flujo de negocio
        # (agregar producto, registrar pago, confirmar venta), en línea con
        # el patrón MVC. self.venta_actual queda sincronizado como referencia
        # de solo lectura para el resto de la UI.
        self.venta_ctrl = VentaController()
        self.ultimo_vuelto = 0.0
        self.ticket_pausado_id = None
        
        # Configurar grid principal
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=4)
        self.grid_columnconfigure(2, weight=3)
        
        self._crear_widgets()
        self._actualizar_carrito_ui()
        self._focus_escaneo()
        self._verificar_ticket_pausado()

        if self.turno_actual is None:
            self._mostrar_apertura_turno()
    
    # =====================================================================
    # CREACIÓN DE WIDGETS
    # =====================================================================
    def _crear_widgets(self):
        self._crear_barra_superior()
        self._crear_panel_izquierdo()
        self._crear_panel_central()
        self._crear_panel_derecho()
    
    def _crear_barra_superior(self):
        barra = ctk.CTkFrame(self, height=40, fg_color="#F4F6F9", corner_radius=0, border_width=1, border_color="#B8C1CE")
        barra.grid(row=0, column=0, columnspan=3, sticky="ew")
        
        turno_texto = str(self.turno_actual) if self.turno_actual is not None else "Sin abrir"
        texto = f"🏪 Kwik-E-Mart POS | Turno #{turno_texto} | 👤 Cajero: {self.usuario_actual.nombre_usuario}"
        ctk.CTkLabel(barra, text=texto, font=("Roboto", 14, "bold"), 
                    text_color="#6B7280").pack(side="left", padx=20, pady=10)
        
        btn_cerrar = ctk.CTkButton(barra, text="Cerrar Sesión", height=30,
                                  fg_color="#DC2626", hover_color="#B91C1C",
                                  corner_radius=10, command=self._cerrar_sesion, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_cerrar.pack(side="right", padx=20, pady=5)
    
    def _crear_panel_izquierdo(self):
        panel = ctk.CTkFrame(self, fg_color="#F9FAFB", corner_radius=0, border_width=1, border_color="#B8C1CE")
        panel.grid(row=1, column=0, sticky="nsew", padx=(0, 2), pady=2)
        
        ctk.CTkLabel(panel, text="🛒 ESCÁNER DE PRODUCTOS", 
                    font=("Roboto", 16, "bold"), text_color="#1D4ED8"
        ).pack(pady=(20, 10))
        
        self.entry_codigo = ctk.CTkEntry(panel, placeholder_text="Código de Barras...",
                                        height=50, font=("Roboto", 18),
                                        fg_color="#D6DBE3", text_color="#1A2233")
        self.entry_codigo.pack(fill="x", padx=20, pady=10)
        self.entry_codigo.bind("<Return>", lambda e: self._procesar_escaneo())
        
        ctk.CTkLabel(panel, text="(Usa el código '123456' para pruebas)", 
                    font=("Roboto", 12), text_color="#8B93A3"
        ).pack()
        
        ctk.CTkFrame(panel, height=2, fg_color="#D6DBE3").pack(fill="x", padx=20, pady=30)
        
        # Sección Cliente
        ctk.CTkLabel(panel, text="🎁 FIDELIZACIÓN", 
                    font=("Roboto", 16, "bold"), text_color="#1D4ED8"
        ).pack(pady=(0, 10))
        
        self.entry_dni = ctk.CTkEntry(panel, placeholder_text="DNI Cliente",
                                     height=40, font=("Roboto", 14),
                                     fg_color="#D6DBE3", text_color="#1A2233")
        self.entry_dni.pack(fill="x", padx=20, pady=10)
        self.entry_dni.bind("<Return>", lambda e: self._buscar_cliente())
        
        self.label_cliente = ctk.CTkLabel(panel, text="", font=("Roboto", 12), text_color="#15803D")
        self.label_cliente.pack(pady=5)
    
    def _crear_panel_central(self):
        panel = ctk.CTkFrame(self, fg_color="#F9FAFB", corner_radius=0, border_width=1, border_color="#B8C1CE")
        panel.grid(row=1, column=1, sticky="nsew", padx=2, pady=2)
        
        ctk.CTkLabel(panel, text="🧾 DETALLE DEL CARRITO", 
                    font=("Roboto", 16, "bold"), text_color="#1D4ED8"
        ).pack(pady=(20, 10))
        
        self.frame_ticket = ctk.CTkScrollableFrame(panel, fg_color="#F4F6F9", corner_radius=10)
        self.frame_ticket.pack(expand=True, fill="both", padx=20, pady=10)
        
        self.label_pagos_parciales = ctk.CTkLabel(panel, text="", 
                                                 font=("Roboto", 14, "italic"), 
                                                 text_color="#C2410C")
        self.label_pagos_parciales.pack(pady=5)
        
        frame_totales = ctk.CTkFrame(panel, fg_color="#DCFCE7", corner_radius=10)
        frame_totales.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkLabel(frame_totales, text="RESTA PAGAR:", 
                    font=("Roboto", 24, "bold"), text_color="#15803D"
        ).pack(side="left", padx=20, pady=15)
        
        self.label_total = ctk.CTkLabel(frame_totales, text="$ 0.00", 
                                       font=("Roboto", 36, "bold"), text_color="#15803D")
        self.label_total.pack(side="right", padx=20, pady=15)
    
    def _crear_panel_derecho(self):
        panel = ctk.CTkScrollableFrame(self, fg_color="#F9FAFB", corner_radius=0, border_width=1, border_color="#B8C1CE")
        panel.grid(row=1, column=2, sticky="nsew", padx=(2, 0), pady=2)
        
        ctk.CTkLabel(panel, text="💳 MÉTODOS DE PAGO", 
                    font=("Roboto", 16, "bold"), text_color="#1D4ED8"
        ).pack(pady=(20, 10))
        
        btn_efectivo = ctk.CTkButton(panel, text="💵 Efectivo", height=50,
                                    fg_color="#D6DBE3", hover_color="#64748B",
                                    corner_radius=10, command=lambda: self._procesar_pago("Efectivo"), border_width=1, border_color="#CBD2DC", text_color="#1A2233")
        btn_efectivo.pack(fill="x", padx=20, pady=5)
        
        btn_debito = ctk.CTkButton(panel, text="💳 Tarj. Débito (Red)", height=50,
                                  fg_color="#D6DBE3", hover_color="#64748B",
                                  corner_radius=10, command=lambda: self._procesar_pago("Débito"), border_width=1, border_color="#CBD2DC", text_color="#1A2233")
        btn_debito.pack(fill="x", padx=20, pady=5)
        
        btn_credito = ctk.CTkButton(panel, text="💳 Tarj. Crédito (Cuotas)", height=50,
                                   fg_color="#D6DBE3", hover_color="#64748B",
                                   corner_radius=10, command=lambda: self._procesar_pago("Crédito"), border_width=1, border_color="#CBD2DC", text_color="#1A2233")
        btn_credito.pack(fill="x", padx=20, pady=5)
        
        btn_transferencia = ctk.CTkButton(panel, text="💸 Transferencia", height=50,
                                         fg_color="#D6DBE3", hover_color="#64748B",
                                         corner_radius=10, command=lambda: self._procesar_pago("Transferencia"), border_width=1, border_color="#CBD2DC", text_color="#1A2233")
        btn_transferencia.pack(fill="x", padx=20, pady=5)
        
        btn_qr = ctk.CTkButton(panel, text="📱 QR / Billetera Virtual", height=50,
                              fg_color="#D6DBE3", hover_color="#64748B",
                              corner_radius=10, command=lambda: self._procesar_pago("QR"), border_width=1, border_color="#CBD2DC", text_color="#1A2233")
        btn_qr.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkFrame(panel, height=2, fg_color="#D6DBE3").pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(panel, text="⚙️ ACCIONES", 
                    font=("Roboto", 16, "bold"), text_color="#1D4ED8"
        ).pack(pady=(0, 10))
        
        self.btn_pausar = ctk.CTkButton(panel, text="⏸️ Pausar Ticket", height=40,
                                        fg_color="#C2410C", hover_color="#9A3412",
                                        corner_radius=10, command=self._pausar_o_reanudar_ticket, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        self.btn_pausar.pack(fill="x", padx=20, pady=5)
        
        btn_descanso = ctk.CTkButton(panel, text="☕ Descanso", height=40,
                                    fg_color="#64748B", hover_color="#D6DBE3",
                                    corner_radius=10, command=self._descanso, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_descanso.pack(fill="x", padx=20, pady=5)
        
        # Botón de sangría (solo para supervisor o superior)
        if self.usuario_actual.tiene_permiso('autorizar_sangria'):
            btn_sangria = ctk.CTkButton(panel, text="💰 Retiro de Efectivo", height=40,
                                       fg_color="#C2410C", hover_color="#9A3412",
                                       corner_radius=10, command=self._registrar_sangria, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
            btn_sangria.pack(fill="x", padx=20, pady=5)
        
        # Botón Cerrar Caja - SIEMPRE VISIBLE
        btn_cerrar_caja = ctk.CTkButton(panel, text="🔒 Cerrar Caja", height=40,
                                       fg_color="#2563EB", hover_color="#1D4ED8",
                                       corner_radius=10, command=self._cerrar_caja, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_cerrar_caja.pack(fill="x", padx=20, pady=5)
        
        btn_anular = ctk.CTkButton(panel, text="🗑️ ANULAR PEDIDO", height=50,
                                  font=("Roboto", 14, "bold"),
                                  fg_color="#DC2626", hover_color="#B91C1C",
                                  corner_radius=10, command=self._anular_pedido, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_anular.pack(fill="x", padx=20, pady=(20, 10))
        
        btn_retomar = ctk.CTkButton(panel, text="🔄 Retomar Ticket (Manual)", height=35,
                                   fg_color="#7C3AED", hover_color="#6D28D9",
                                   corner_radius=10, command=self._retomar_ticket_manual, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_retomar.pack(fill="x", padx=20, pady=5)
    
    # =====================================================================
    # LÓGICA DE ESCANEO Y CARRITO
    # =====================================================================
    def _procesar_escaneo(self):
        codigo = self.entry_codigo.get().strip()
        self.entry_codigo.delete(0, 'end')
        
        if not codigo:
            messagebox.showwarning("Aviso", "Ingrese un código de barras.")
            self._focus_escaneo()
            return
        
        try:
            producto = Producto.buscar_por_codigo(codigo)
            if not producto:
                messagebox.showerror("Error", "Producto no encontrado.")
                self._focus_escaneo()
                return
            
            if producto.estado != 'Activo':
                messagebox.showerror("Error", "Producto inactivo.")
                self._focus_escaneo()
                return
            
            if producto.stock_actual <= 0:
                messagebox.showwarning("Stock Agotado", f"El producto '{producto.nombre}' no tiene stock disponible.")
                self._focus_escaneo()
                return
            
            cantidad_str = ctk.CTkInputDialog(
                text=f"{producto.nombre}\nPrecio: ${producto.precio_venta:.2f} | Stock disponible: {producto.stock_actual}\n\n¿Cuántas unidades desea agregar?",
                title="Cantidad"
            ).get_input()
            if cantidad_str is None:
                self._focus_escaneo()
                return
            if not cantidad_str.strip():
                cantidad_str = "1"
            if not cantidad_str.strip().isdigit() or int(cantidad_str.strip()) <= 0:
                messagebox.showerror("Error", "Cantidad inválida. Debe ser un número entero positivo.")
                self._focus_escaneo()
                return
            cantidad = int(cantidad_str.strip())
            
            if cantidad > producto.stock_actual:
                messagebox.showerror("Error", f"Stock insuficiente. Disponible: {producto.stock_actual}")
                self._focus_escaneo()
                return
            
            if not self.venta_actual:
                self.venta_ctrl.iniciar_venta(self.turno_actual)
                self.venta_actual = self.venta_ctrl.venta_actual
            
            exito, mensaje, _ = self.venta_ctrl.escanear_producto(codigo, cantidad)
            if not exito:
                messagebox.showerror("Error", mensaje)
            else:
                self._actualizar_carrito_ui()
            
            self._focus_escaneo()
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al escanear: {str(e)}")
            self._focus_escaneo()
    
    def _actualizar_carrito_ui(self):
        for widget in self.frame_ticket.winfo_children():
            widget.destroy()
        
        if not self.venta_actual or not self.venta_actual.carrito:
            ctk.CTkLabel(self.frame_ticket, text="El carrito está vacío", 
                        font=("Roboto", 14), text_color="#8B93A3").pack(pady=20)
            self.label_total.configure(text="$ 0.00")
            self.label_pagos_parciales.configure(text="")
            if hasattr(self, 'label_descuento'):
                self.label_descuento.configure(text="")
            return
        
        for item in self.venta_actual.carrito:
            frame_item = ctk.CTkFrame(self.frame_ticket, fg_color="transparent")
            frame_item.pack(fill="x", pady=5)
            
            ctk.CTkLabel(frame_item, text=f"{item['cantidad']}x {item['nombre']}", 
                        font=("Roboto", 16)).pack(side="left")

            descuento_item = item.get('descuento', 0.0)
            if descuento_item > 0:
                neto = item['subtotal'] - descuento_item
                frame_precio = ctk.CTkFrame(frame_item, fg_color="transparent")
                frame_precio.pack(side="right")
                ctk.CTkLabel(frame_precio, text=f"${item['subtotal']:.2f}",
                            font=("Roboto", 12), text_color="#8B93A3").pack(anchor="e")
                ctk.CTkLabel(frame_precio, text=f"$ {neto:.2f} 🎯",
                            font=("Roboto", 16, "bold"), text_color="#15803D").pack(anchor="e")
            else:
                ctk.CTkLabel(frame_item, text=f"$ {item['subtotal']:.2f}", 
                            font=("Roboto", 16, "bold")).pack(side="right")
        
        self.monto_restante = self.venta_actual.monto_restante
        self.label_total.configure(text=f"$ {max(0, self.monto_restante):.2f}")
        
        if self.venta_actual.pagos:
            pagos_texto = " | ".join([
                f"{pago['metodo']}: ${pago['monto']:.2f}" 
                for pago in self.venta_actual.pagos
            ])
            self.label_pagos_parciales.configure(text=f"Abonado: {pagos_texto}")
        else:
            self.label_pagos_parciales.configure(text="")
        
        # Las promociones ya fueron calculadas y aplicadas por el modelo
        # (Venta._actualizar_totales), que descuenta el importe real del
        # total a pagar. Acá solo se refleja el resultado en la UI.
        descuento_total = self.venta_actual.descuento_total
        if descuento_total > 0:
            if not hasattr(self, 'label_descuento'):
                self.label_descuento = ctk.CTkLabel(self.frame_ticket.master, 
                                                   text="", font=("Roboto", 14, "bold"),
                                                   text_color="#15803D")
                self.label_descuento.pack(side="bottom", pady=5)
            self.label_descuento.configure(text=f"🎯 Descuentos aplicados: -${descuento_total:.2f}")
        else:
            if hasattr(self, 'label_descuento'):
                self.label_descuento.configure(text="")
        
        if self.monto_restante <= 0.01:
            self._finalizar_venta()
    
    def _focus_escaneo(self):
        self.entry_codigo.focus_set()
    
    # =====================================================================
    # CLIENTE
    # =====================================================================
    def _buscar_cliente(self):
        dni = self.entry_dni.get().strip()
        if not dni:
            self.label_cliente.configure(text="")
            return
        
        try:
            cliente = Cliente.buscar_por_dni(dni)
            if cliente and cliente.estado == 'Activo':
                self.label_cliente.configure(
                    text=f"✅ {cliente.nombre} - Puntos: {cliente.puntos_acumulados}",
                    text_color="#15803D"
                )
                if self.venta_actual:
                    self.venta_actual.dni_cliente = dni
            else:
                self.label_cliente.configure(
                    text="❌ Cliente no encontrado o inactivo. Puede registrarlo en Administración.",
                    text_color="#DC2626"
                )
        except Exception as e:
            messagebox.showerror("Error", f"Error al buscar cliente: {str(e)}")
    
    # =====================================================================
    # PAGOS
    # =====================================================================
    def _elegir_entidad(self, tipos_permitidos, titulo):
        """
        Abre un diálogo modal para elegir una entidad de pago activa (banco,
        entidad financiera o billetera virtual) entre las configuradas en
        Gerencia > Entidad de Pago. Retorna la EntidadPago elegida o None si
        se canceló.
        """
        entidades = [e for e in EntidadPago.obtener_todos()
                     if e.activa and e.tipo in tipos_permitidos]
        if not entidades:
            messagebox.showerror(
                "Sin entidades configuradas",
                f"No hay ninguna entidad activa de tipo {'/'.join(tipos_permitidos)}.\n"
                f"Cárguela primero en Gerencia > Entidad de Pago."
            )
            return None

        dialog = ctk.CTkToplevel(self)
        dialog.title(titulo)
        dialog.geometry("380x180")
        dialog.configure(fg_color="#F9FAFB")
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        dialog.lift()
        dialog.focus_force()
        dialog.grab_set()

        x = (dialog.winfo_screenwidth() // 2) - 190
        y = (dialog.winfo_screenheight() // 2) - 90
        dialog.geometry(f"380x180+{x}+{y}")

        frame = ctk.CTkFrame(dialog, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text=titulo, font=("Roboto", 14, "bold")
        ).pack(anchor="w", pady=(0, 10))

        nombres = [e.nombre for e in entidades]
        combo = ctk.CTkOptionMenu(frame, values=nombres, width=220, height=35,
                                 font=("Roboto", 13), fg_color="#D6DBE3",
                                 text_color="#1A2233", button_color="#2563EB",
                                 corner_radius=10)
        combo.pack(anchor="w", pady=(0, 20))
        combo.set(nombres[0])

        resultado = {"entidad": None}

        def confirmar():
            nombre_elegido = combo.get()
            resultado["entidad"] = next((e for e in entidades if e.nombre == nombre_elegido), None)
            dialog.destroy()

        def cancelar():
            dialog.destroy()

        frame_btns = ctk.CTkFrame(frame, fg_color="transparent")
        frame_btns.pack(fill="x")
        ctk.CTkButton(frame_btns, text="Confirmar", height=35, fg_color="#15803D",
                    hover_color="#166534", corner_radius=10,
                    command=confirmar, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF").pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(frame_btns, text="Cancelar", height=35, fg_color="#64748B",
                    hover_color="#D6DBE3", corner_radius=10,
                    command=cancelar, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF").pack(side="left", fill="x", expand=True, padx=(5, 0))

        self.wait_window(dialog)
        return resultado["entidad"]

    def _aplicar_descuento_entidad(self, monto_ingresado, entidad):
        """
        Aplica el descuento promocional configurado para la entidad (si tiene)
        sobre el monto que efectivamente entrega el cliente, calculando cuánto
        de la deuda queda saldado (el descuento hace que rinda más de lo que
        cuesta). Nunca cubre más que el saldo restante real.
        Retorna (monto_acreditado, texto_promocion_o_None).
        """
        descuento = getattr(entidad, 'descuento_porcentaje', 0) or 0
        if descuento <= 0:
            return monto_ingresado, (entidad.promocion_descripcion or None)

        monto_acreditado = monto_ingresado / (1 - descuento / 100.0)
        monto_acreditado = min(round(monto_acreditado, 2), self.monto_restante)
        texto = f"Descuento {entidad.nombre}: {descuento:.0f}%"
        if entidad.promocion_descripcion:
            texto += f" ({entidad.promocion_descripcion})"
        return monto_acreditado, texto

    def _procesar_pago(self, metodo):
        if not self.venta_actual or not self.venta_actual.carrito:
            messagebox.showwarning("Aviso", "El carrito está vacío.")
            return
        
        if self.monto_restante <= 0:
            messagebox.showinfo("Info", "El saldo ya está cubierto.")
            return
        
        monto_str = ctk.CTkInputDialog(
            text=f"Restante a cobrar: ${self.monto_restante:.2f}\n\n¿Monto a pasar por {metodo}?",
            title=f"Cobro {metodo}"
        ).get_input()
        if monto_str is None:
            return
        if not monto_str.strip():
            messagebox.showerror("Error", "Debe ingresar un monto.")
            return
        
        try:
            monto_ingresado = float(monto_str.strip())
            if monto_ingresado <= 0:
                raise ValueError("El monto debe ser positivo.")
        except ValueError:
            messagebox.showerror("Error", "Monto inválido. Ingrese un número positivo.")
            return
        
        vuelto = 0.0
        cuotas = None
        interes = 0.0
        promocion = None
        monto_acreditado = monto_ingresado
        
        if metodo == "Efectivo":
            pass  # el modelo calcula vuelto y monto aplicado
        elif metodo == "Débito":
            if monto_ingresado > self.monto_restante + 0.01:
                messagebox.showerror("Error", "No se puede cobrar de más con tarjeta de débito.")
                return
            
            entidad = self._elegir_entidad(["Banco", "Entidad Financiera"], "Elegir banco/entidad (Débito)")
            if entidad is None:
                return
            
            tarjeta = ctk.CTkInputDialog(
                text=f"{entidad.nombre}\nIngrese Número de Tarjeta (16 dígitos):",
                title="Red Bancaria"
            ).get_input()
            if tarjeta is None:
                return
            if not tarjeta.strip() or len(tarjeta.strip()) != 16 or not tarjeta.strip().isdigit():
                messagebox.showerror("Error", "Número de tarjeta inválido (debe tener 16 dígitos).")
                return
            
            pin_tarjeta = ctk.CTkInputDialog(
                text="Ingrese PIN del Cliente (4 dígitos):",
                title="Red Bancaria",
                show="*"
            ).get_input()
            if pin_tarjeta is None:
                return
            if not pin_tarjeta.strip() or len(pin_tarjeta.strip()) != 4 or not pin_tarjeta.strip().isdigit():
                messagebox.showerror("Error", "PIN inválido (debe tener 4 dígitos).")
                return
            
            monto_acreditado, promocion = self._aplicar_descuento_entidad(monto_ingresado, entidad)
            mensaje = f"✅ Transacción aprobada con {entidad.nombre}."
            if promocion:
                mensaje += f"\n{promocion}"
            messagebox.showinfo("Banca Aprobada", mensaje)
        elif metodo == "Crédito":
            if monto_ingresado > self.monto_restante + 0.01:
                messagebox.showerror("Error", "No se puede cobrar de más con tarjeta de crédito.")
                return
            
            entidad = self._elegir_entidad(["Banco", "Entidad Financiera"], "Elegir banco/entidad (Crédito)")
            if entidad is None:
                return
            
            cuotas_max = entidad.cuotas_maximas if entidad.cuotas_maximas > 0 else 12
            cuotas_str = ctk.CTkInputDialog(
                text=f"{entidad.nombre}\nCuotas sin interés: {entidad.cuotas_sin_interes} | Máximo: {cuotas_max}\n\nIngrese cantidad de CUOTAS (1 a {cuotas_max}):",
                title="Selector de Cuotas"
            ).get_input()
            if cuotas_str is None:
                return
            if not cuotas_str.strip() or not cuotas_str.strip().isdigit() or not (1 <= int(cuotas_str.strip()) <= cuotas_max):
                messagebox.showerror("Error", f"Selección de cuotas inválida (debe ser entre 1 y {cuotas_max}).")
                return
            
            cuotas = int(cuotas_str.strip())
            if cuotas <= entidad.cuotas_sin_interes:
                interes = 0.0
                promocion = f"{entidad.nombre} - Sin interés"
            elif cuotas <= 6:
                interes = 5.0
                promocion = entidad.nombre
            else:
                interes = 10.0
                promocion = entidad.nombre
            
            monto_acreditado, descuento_txt = self._aplicar_descuento_entidad(monto_ingresado, entidad)
            if descuento_txt:
                promocion = f"{promocion} | {descuento_txt}"
            
            mensaje = f"Cobro de ${monto_ingresado:.2f} en {cuotas} cuotas aprobado con {entidad.nombre}."
            if interes == 0.0:
                mensaje += "\nPromoción: Sin interés"
            else:
                mensaje += f"\nInterés aplicado: {interes}%"
            if descuento_txt:
                mensaje += f"\n{descuento_txt}"
            messagebox.showinfo("Crédito Aprobado", mensaje)
        elif metodo == "Transferencia":
            if monto_ingresado > self.monto_restante + 0.01:
                messagebox.showerror("Error", "No se puede cobrar de más con transferencia.")
                return
            
            entidad = self._elegir_entidad(["Banco", "Entidad Financiera"], "Elegir banco (Transferencia)")
            if entidad is None:
                return
            
            comprobante = ctk.CTkInputDialog(
                text=f"{entidad.nombre}\nIngrese el comprobante de transferencia (opcional):",
                title="Transferencia"
            ).get_input()
            
            monto_acreditado, promocion = self._aplicar_descuento_entidad(monto_ingresado, entidad)
            mensaje = f"✅ Transferencia registrada vía {entidad.nombre}.\nComprobante: {comprobante or 'Sin comprobante'}"
            if promocion:
                mensaje += f"\n{promocion}"
            messagebox.showinfo("Transferencia", mensaje)
        elif metodo == "QR":
            if monto_ingresado > self.monto_restante + 0.01:
                messagebox.showerror("Error", "No se puede cobrar de más con QR/billetera virtual.")
                return
            
            entidad = self._elegir_entidad(["Billetera Virtual"], "Elegir billetera virtual (QR)")
            if entidad is None:
                return
            
            monto_acreditado, descuento_txt = self._aplicar_descuento_entidad(monto_ingresado, entidad)
            promocion = f"QR - {entidad.nombre}"
            if descuento_txt:
                promocion = f"{promocion} | {descuento_txt}"
            
            mensaje = f"✅ Pago aprobado vía {entidad.nombre}.\nMonto: ${monto_ingresado:.2f}"
            if descuento_txt:
                mensaje += f"\n{descuento_txt}"
            messagebox.showinfo("QR Aprobado", mensaje)
        
        try:
            exito, mensaje = self.venta_ctrl.registrar_pago(
                metodo=metodo,
                monto=monto_acreditado,
                cuotas=cuotas,
                interes=interes,
                promocion=promocion
            )
            if not exito:
                messagebox.showerror("Error", mensaje)
                return
            self.ultimo_vuelto = self.venta_actual.pagos[-1].get('vuelto', 0.0)
        except Exception as e:
            messagebox.showerror("Error", f"Error al registrar pago: {str(e)}")
            return
        
        self._actualizar_carrito_ui()
    
    # =====================================================================
    # FINALIZAR VENTA (con orden corregido: mensaje primero, PDF después)
    # =====================================================================
    def _finalizar_venta(self):
        if not self.venta_actual:
            return
        
        try:
            ticket = self.venta_actual.nro_ticket
            if not ticket:
                ticket = self.venta_ctrl.confirmar_venta(self.usuario_actual)
                if not ticket:
                    messagebox.showerror("Error", "No se pudo finalizar la venta.")
                    return
            
            productos = []
            for item in self.venta_actual.carrito:
                productos.append({
                    'nombre': item['nombre'],
                    'cantidad': item['cantidad'],
                    'precio': item['precio'],
                    'subtotal': item['subtotal'],
                    'descuento': item.get('descuento', 0.0),
                    'codigo': item.get('codigo', '')
                })
            
            pagos = []
            total_abonado = 0.0
            modos_pago = []
            for pago in self.venta_actual.pagos:
                pagos.append({
                    'metodo': pago['metodo'],
                    'monto': pago['monto'],
                    'recibido': pago.get('recibido', pago['monto']),
                    'vuelto': pago.get('vuelto', 0),
                    'cuotas': pago.get('cuotas'),
                    'promocion': pago.get('promocion')
                })
                total_abonado += pago['monto']
                modos_pago.append(pago['metodo'])
            
            datos_ticket = {
                'nro_ticket': self.venta_actual.nro_ticket,
                'fecha_hora': self.venta_actual.fecha_hora,
                'productos': productos,
                'total': self.venta_actual.total_facturado,
                'pagos': pagos,
                'puntos_ganados': self.venta_actual.puntos_sumados,
                'cliente': self.venta_actual.dni_cliente or "Consumidor Final",
                'cajero': self.usuario_actual.nombre_usuario,
                'descuento_total': getattr(self.venta_actual, 'descuento_total', 0.0)
            }
            
            # 1. Generar el PDF sin abrirlo
            ruta_pdf = generar_ticket_pdf(datos_ticket, abrir=False)
            
            # 2. Mostrar mensaje detallado
            mensaje = f"🧾 **Ticket {self.venta_actual.nro_ticket}**\n\n"
            mensaje += f"💰 **Total cobrado:** ${total_abonado:.2f}\n"
            mensaje += f"💳 **Modo de Pago:** {', '.join(modos_pago)}\n"
            if self.ultimo_vuelto > 0:
                mensaje += f"🔄 **Vuelto:** ${self.ultimo_vuelto:.2f}\n"
            if datos_ticket['descuento_total'] > 0:
                mensaje += f"🎯 **Descuento aplicado:** ${datos_ticket['descuento_total']:.2f}\n"
            mensaje += "\n✅ El ticket en PDF se ha generado correctamente.\n\n"
            mensaje += "🔔 Presione 'Aceptar' para abrirlo."
            
            messagebox.showinfo("✅ Venta Finalizada", mensaje)
            self.ultimo_vuelto = 0.0
            
            # 3. Abrir el PDF después del mensaje (best-effort: si falla, no debe
            # impedir que se limpie el carrito, ya que la venta ya se guardó bien)
            if ruta_pdf and os.path.exists(ruta_pdf):
                try:
                    if platform.system() == "Windows":
                        os.startfile(ruta_pdf)
                    elif platform.system() == "Darwin":
                        subprocess.Popen(["open", ruta_pdf])
                    else:
                        subprocess.Popen(["xdg-open", ruta_pdf],
                                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except Exception:
                    pass  # no se pudo abrir automáticamente, no es crítico
            
            self.venta_actual = None
            self.venta_ctrl.cancelar_venta()
            self.carrito = []
            self.pagos_acumulados = []
            self.entry_dni.delete(0, 'end')
            self.label_cliente.configure(text="")
            self._actualizar_carrito_ui()
        except Exception as e:
            messagebox.showerror("Error", f"Error al finalizar la venta: {str(e)}")
    
    # =====================================================================
    # PAUSA Y REANUDACIÓN
    # =====================================================================
    def _pausar_o_reanudar_ticket(self):
        if self.ticket_pausado_id:
            self._reanudar_ticket()
        else:
            self._pausar_ticket()
    
    def _pausar_ticket(self):
        if not self.venta_actual or not self.venta_actual.carrito:
            messagebox.showwarning("Aviso", "El carrito está vacío.")
            return
        
        try:
            ticket_pausado = self.venta_actual.pausar_ticket()
            if ticket_pausado:
                self.ticket_pausado_id = ticket_pausado
                self.btn_pausar.configure(text="▶️ Reanudar Ticket", 
                                         fg_color="#7C3AED", hover_color="#6D28D9")
                messagebox.showinfo("Ticket Pausado", f"✅ Carrito guardado.\nID: {ticket_pausado}\nPresione 'Reanudar Ticket' para continuar.")
                self.venta_actual = None
                self.venta_ctrl.cancelar_venta()
                self.label_cliente.configure(text="")
                self._actualizar_carrito_ui()
            else:
                messagebox.showerror("Error", "No se pudo pausar el ticket.")
        except Exception as e:
            messagebox.showerror("Error", f"Error al pausar ticket: {str(e)}")
    
    def _reanudar_ticket(self):
        if not self.ticket_pausado_id:
            messagebox.showwarning("Aviso", "No hay un ticket pausado para reanudar.")
            return
        
        try:
            venta = Venta.retomar_ticket(self.ticket_pausado_id)
            if venta:
                self.venta_actual = venta
                self.ticket_pausado_id = None
                self.btn_pausar.configure(text="⏸️ Pausar Ticket",
                                         fg_color="#C2410C", hover_color="#9A3412")
                self._actualizar_carrito_ui()
                messagebox.showinfo("Ticket Retomado", f"✅ Ticket {venta.nro_ticket} retomado.")
            else:
                messagebox.showerror("Error", "No se pudo reanudar el ticket. Puede que ya haya sido completado.")
                self.ticket_pausado_id = None
                self.btn_pausar.configure(text="⏸️ Pausar Ticket",
                                         fg_color="#C2410C", hover_color="#9A3412")
        except Exception as e:
            messagebox.showerror("Error", f"Error al reanudar ticket: {str(e)}")
            self.ticket_pausado_id = None
            self.btn_pausar.configure(text="⏸️ Pausar Ticket",
                                     fg_color="#C2410C", hover_color="#9A3412")
    
    def _verificar_ticket_pausado(self):
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT nro_ticket FROM ventas_cabecera
                WHERE turno_id = ? AND estado = 'Pausado'
                ORDER BY fecha_hora DESC LIMIT 1
            ''', (self.turno_actual,))
            row = cursor.fetchone()
            conn.close()
            if row:
                self.ticket_pausado_id = row[0]
                self.btn_pausar.configure(text="▶️ Reanudar Ticket",
                                         fg_color="#7C3AED", hover_color="#6D28D9")
                self.label_pagos_parciales.configure(text=f"🔄 Hay un ticket pausado: {row[0]}")
        except Exception as e:
            print(f"Error al verificar ticket pausado: {e}")
    
    def _retomar_ticket_manual(self):
        ticket_id = ctk.CTkInputDialog(
            text="Ingrese el ID del ticket pausado:",
            title="Retomar Ticket"
        ).get_input()
        if ticket_id is None:
            return
        ticket_id = ticket_id.strip()
        if not ticket_id:
            messagebox.showwarning("Aviso", "Debe ingresar un ID de ticket.")
            return
        
        try:
            venta = Venta.retomar_ticket(ticket_id)
            if venta:
                if self.ticket_pausado_id:
                    self.ticket_pausado_id = None
                    self.btn_pausar.configure(text="⏸️ Pausar Ticket",
                                             fg_color="#C2410C", hover_color="#9A3412")
                self.venta_actual = venta
                self._actualizar_carrito_ui()
                messagebox.showinfo("Ticket Retomado", f"✅ Ticket {ticket_id} retomado.")
            else:
                messagebox.showerror("Error", "Ticket no encontrado o ya completado.")
        except Exception as e:
            messagebox.showerror("Error", f"Error al retomar ticket: {str(e)}")
    
    # =====================================================================
    # ANULACIÓN Y DESCANSO
    # =====================================================================
    def _anular_pedido(self):
        if not self.venta_actual or not self.venta_actual.carrito:
            messagebox.showwarning("Aviso", "El carrito está vacío.")
            return
        
        if not self.usuario_actual.tiene_permiso('anular_pedido'):
            messagebox.showerror("Acceso Denegado", "Se requiere PIN de SUPERVISOR para anular el pedido.")
            self._solicitar_supervisor("anular_pedido")
            return
        
        if messagebox.askyesno("Confirmar Anulación", "¿Está seguro de que desea anular todo el pedido?"):
            try:
                self.venta_actual.vaciar_carrito()
                self.venta_actual = None
                self.venta_ctrl.cancelar_venta()
                self._actualizar_carrito_ui()
                messagebox.showinfo("Anulado", "El pedido ha sido descartado.")
            except Exception as e:
                messagebox.showerror("Error", f"Error al anular pedido: {str(e)}")
    
    def _solicitar_supervisor(self, accion):
        pin_super = ctk.CTkInputDialog(
            text="Ingrese PIN de SUPERVISOR para autorizar:",
            title="Autorización de Supervisor",
            show="*"
        ).get_input()
        if pin_super is None:
            return
        pin_super = pin_super.strip()
        if not pin_super:
            messagebox.showerror("Error", "Debe ingresar un PIN.")
            return
        
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, nombre_usuario, rol FROM usuarios WHERE pin_hash = ? AND rol = 'Supervisor'", (pin_super,))
            supervisor = cursor.fetchone()
            conn.close()
            
            if supervisor:
                if accion == "anular_pedido" and self.venta_actual:
                    self.venta_actual.vaciar_carrito()
                    self.venta_actual = None
                    self.venta_ctrl.cancelar_venta()
                    self._actualizar_carrito_ui()
                    messagebox.showinfo("Anulado", "El pedido ha sido descartado por Supervisor.")
                else:
                    messagebox.showerror("Error", "Acción no autorizada.")
            else:
                messagebox.showerror("Denegado", "PIN de Supervisor incorrecto.")
        except Exception as e:
            messagebox.showerror("Error", f"Error al validar supervisor: {e}")
    
    def _descanso(self):
        self.frame_descanso = ctk.CTkFrame(self, fg_color="#F4F6F9", border_width=1, border_color="#B8C1CE")
        self.frame_descanso.place(relwidth=1, relheight=1)
        
        ctk.CTkLabel(self.frame_descanso, text="☕ OPERADOR EN DESCANSO", 
                    font=("Roboto", 40, "bold"), text_color="#DC2626"
        ).pack(pady=(200, 20))
        
        ctk.CTkLabel(self.frame_descanso, text="Terminal Bloqueada. Ingrese su PIN para reanudar.", 
                    font=("Roboto", 18), text_color="#6B7280"
        ).pack(pady=20)
        
        entry_pin = ctk.CTkEntry(self.frame_descanso, show="*", width=200, height=50, 
                                 font=("Roboto", 24), justify="center")
        entry_pin.pack()
        entry_pin.focus()
        
        def reanudar(e):
            pin = entry_pin.get().strip()
            if not pin:
                messagebox.showwarning("Aviso", "Ingrese su PIN.")
                return
            
            try:
                if Usuario.verificar_pin(self.usuario_actual.nombre_usuario, pin):
                    self.frame_descanso.destroy()
                    self._focus_escaneo()
                else:
                    messagebox.showerror("Denegado", "PIN incorrecto. Solo el cajero en turno puede desbloquear.")
                    entry_pin.delete(0, 'end')
                    entry_pin.focus()
            except Exception as e:
                messagebox.showerror("Error", f"Error al validar PIN: {str(e)}")
        
        entry_pin.bind("<Return>", reanudar)
    
    # =====================================================================
    # APERTURA DE TURNO
    # =====================================================================
    def _mostrar_apertura_turno(self):
        for widget in self.winfo_children():
            widget.destroy()

        frame = ctk.CTkFrame(self, fg_color="#F9FAFB", corner_radius=15, border_width=1, border_color="#B8C1CE")
        frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.8, relheight=0.7)
        
        ctk.CTkLabel(frame, text="📋 Apertura de Caja", 
                    font=("Roboto", 24, "bold"), text_color="#1D4ED8"
        ).pack(pady=(40, 10))
        
        ctk.CTkLabel(frame, text=f"Cajero: {self.usuario_actual.nombre_usuario}", 
                    font=("Roboto", 16), text_color="#6B7280"
        ).pack(pady=(0, 30))
        
        ctk.CTkLabel(frame, text="Fondo Inicial:", font=("Roboto", 14, "bold")
        ).pack(anchor="w", padx=40, pady=(10, 5))
        
        self.entry_fondo = ctk.CTkEntry(frame, placeholder_text="0.00", font=("Roboto", 16),
                                      fg_color="#D6DBE3", text_color="#1A2233")
        self.entry_fondo.pack(fill="x", padx=40, pady=(0, 20))
        self.entry_fondo.bind("<Return>", lambda e: self._ejecutar_apertura())
        self.entry_fondo.focus_set()
        
        btn_abrir = ctk.CTkButton(frame, text="ABRIR TURNO", height=50,
                                 font=("Roboto", 16, "bold"), fg_color="#15803D",
                                 hover_color="#166534", corner_radius=10,
                                 command=self._ejecutar_apertura, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_abrir.pack(fill="x", padx=40, pady=10)
        
        btn_cancelar = ctk.CTkButton(frame, text="Cancelar", height=40,
                                    fg_color="#64748B", hover_color="#D6DBE3",
                                    corner_radius=10, command=self.controller.cerrar_sesion, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_cancelar.pack(fill="x", padx=40, pady=5)
    
    def _ejecutar_apertura(self):
        fondo_str = self.entry_fondo.get().strip()
        if not fondo_str:
            messagebox.showerror("Error", "Debe ingresar un monto de fondo inicial.")
            return
        
        try:
            fondo = float(fondo_str)
            if fondo < 0:
                raise ValueError("El fondo no puede ser negativo.")
        except ValueError:
            messagebox.showerror("Error", "Ingrese un monto válido (número positivo).")
            return
        
        try:
            from models.turno import Turno
            turno_id = Turno.abrir_turno(self.usuario_actual.id, fondo)
            if turno_id:
                self.controller.turno_actual = turno_id
                self.controller.mostrar_pantalla("pos", turno_actual=turno_id)
            else:
                messagebox.showerror("Error", "No se pudo abrir el turno.")
        except Exception as e:
            messagebox.showerror("Error", f"Error al abrir turno: {str(e)}")
    
    # =====================================================================
    # SANGRÍA Y CIERRE DE CAJA
    # =====================================================================
    def _registrar_sangria(self):
        if not self.turno_actual:
            messagebox.showerror("Error", "No hay turno abierto.")
            return
        
        turno = Turno.obtener_turno_abierto()
        if not turno or turno[0] != self.turno_actual:
            messagebox.showerror("Error", "El turno actual no está abierto.")
            return
        
        dialog = ctk.CTkToplevel(self)
        dialog.title("Registrar Sangría")
        dialog.geometry("400x380")
        dialog.configure(fg_color="#F9FAFB")
        dialog.resizable(False, False)
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 200
        y = (dialog.winfo_screenheight() // 2) - 190
        dialog.geometry(f"400x380+{x}+{y}")
        
        frame = ctk.CTkFrame(dialog, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(frame, text="💰 Registrar Sangría de Caja", 
                    font=("Roboto", 18, "bold"), text_color="#1D4ED8"
        ).pack(pady=(0, 20))
        
        ctk.CTkLabel(frame, text="Monto a retirar:", font=("Roboto", 13, "bold")
        ).pack(anchor="w", pady=(10, 5))
        
        entry_monto = ctk.CTkEntry(frame, placeholder_text="0.00", font=("Roboto", 16),
                                  fg_color="#D6DBE3", text_color="#1A2233")
        entry_monto.pack(fill="x", pady=(0, 10))
        entry_monto.focus_set()
        
        ctk.CTkLabel(frame, text="Motivo:", font=("Roboto", 13, "bold")
        ).pack(anchor="w", pady=(10, 5))
        
        entry_motivo = ctk.CTkEntry(frame, placeholder_text="Ej. Pago a proveedor, cambio...", font=("Roboto", 13),
                                  fg_color="#D6DBE3", text_color="#1A2233")
        entry_motivo.pack(fill="x", pady=(0, 10))
        
        frame_botones = ctk.CTkFrame(frame, fg_color="transparent")
        frame_botones.pack(fill="x", pady=20)
        
        def guardar_sangria():
            monto_str = entry_monto.get().strip()
            if not monto_str:
                messagebox.showerror("Error", "Debe ingresar un monto.")
                return
            
            try:
                monto = float(monto_str)
                if monto <= 0:
                    raise ValueError("El monto debe ser positivo.")
            except ValueError:
                messagebox.showerror("Error", "Ingrese un monto válido (número positivo).")
                return
            
            motivo = entry_motivo.get().strip()
            if not motivo:
                motivo = "Retiro de efectivo por máximo alcanzado"
            
            try:
                conn = get_sqlite_connection()
                cursor = conn.cursor()
                fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                cursor.execute('''
                    INSERT INTO sangrias (turno_id, cajero_id, supervisor_id, fecha_hora, monto_retirado, motivo)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (self.turno_actual, turno[1], self.usuario_actual.id, fecha, monto, motivo))
                
                cursor.execute('''
                    UPDATE turnos 
                    SET total_sangrias = total_sangrias + ?
                    WHERE id = ?
                ''', (monto, self.turno_actual))
                
                conn.commit()
                conn.close()
                
                messagebox.showinfo("Éxito", f"✅ Sangría de ${monto:.2f} registrada correctamente.")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"❌ No se pudo registrar la sangría: {e}")
        
        btn_guardar = ctk.CTkButton(frame_botones, text="💾 Registrar", height=40,
                                   fg_color="#15803D", hover_color="#166534",
                                   corner_radius=10, command=guardar_sangria, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_guardar.pack(side="left", fill="x", expand=True, padx=5)
        
        btn_cancelar = ctk.CTkButton(frame_botones, text="Cancelar", height=40,
                                    fg_color="#64748B", hover_color="#D6DBE3",
                                    corner_radius=10, command=dialog.destroy, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_cancelar.pack(side="left", fill="x", expand=True, padx=5)

    def _cerrar_caja(self):
        if not self.turno_actual:
            messagebox.showerror("Error", "No hay turno abierto.")
            return
        
        turno = Turno.obtener_turno_por_id(self.turno_actual)
        if not turno:
            messagebox.showerror("Error", "No se encontró el turno.")
            return
        
        if turno.estado != "Abierto":
            messagebox.showerror("Error", "El turno ya está cerrado.")
            return
        
        if not messagebox.askyesno("Confirmar", 
                                   f"⚠️ ¿Cerrar el turno #{self.turno_actual}?\n"
                                   "Se generará un reporte en PDF."):
            return
        
        try:
            if not Turno.cerrar_turno(self.turno_actual):
                messagebox.showerror("Error", "❌ No se pudo cerrar el turno.")
                return

            # Releer el turno ya cerrado para tener los totales de ventas recalculados
            turno = Turno.obtener_turno_por_id(self.turno_actual)
            usuario = Usuario.obtener_por_id(turno.usuario_id)
            total_ventas = (turno.total_ventas_efectivo + turno.total_ventas_debito +
                            turno.total_ventas_credito + turno.total_ventas_transferencia)

            datos_reporte = {
                'turno_id': self.turno_actual,
                'cajero': usuario.nombre_usuario if usuario else 'Desconocido',
                'apertura': turno.fecha_hora_apertura,
                'cierre': turno.fecha_hora_cierre or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'estado': 'Cerrado',
                'fondo_inicial': turno.fondo_inicial,
                'total_efectivo': turno.total_ventas_efectivo,
                'total_debito': turno.total_ventas_debito,
                'total_credito': turno.total_ventas_credito,
                'total_transferencia': turno.total_ventas_transferencia,
                'total_sangrias': turno.total_sangrias,
                'total_ventas': total_ventas
            }
            generar_reporte_turno_pdf(datos_reporte)

            messagebox.showinfo("Éxito", f"✅ Turno #{self.turno_actual} cerrado correctamente.\n📄 Reporte generado en PDF.")
            self._volver_al_login()
        except Exception as e:
            messagebox.showerror("Error", f"❌ Error al cerrar turno: {str(e)}")
    
    # =====================================================================
    # CIERRE DE SESIÓN Y VOLVER AL LOGIN
    # =====================================================================
    def _cerrar_sesion(self):
        if self.turno_actual:
            turno = Turno.obtener_turno_abierto()
            if turno and turno[0] == self.turno_actual:
                if messagebox.askyesno("Cerrar Turno", 
                                       "El turno está abierto. ¿Desea cerrarlo antes de salir?\n"
                                       "(Si elige 'No', el turno quedará abierto para reanudar después)"):
                    if Turno.cerrar_turno(self.turno_actual):
                        messagebox.showinfo("Éxito", f"✅ Turno #{self.turno_actual} cerrado correctamente.")
                    else:
                        messagebox.showerror("Error", "❌ No se pudo cerrar el turno.")
                        return
        
        self._volver_al_login()
    
    def _volver_al_login(self):
        self.controller.cerrar_sesion()