import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from models.proveedor import Proveedor
from models.producto import Producto
from models.compra import Compra
from models.usuario import Usuario
from models.notificacion import Notificacion
from views.base_frame import BaseFrame

class FrameCompras(BaseFrame):
    """
    Pantalla de gestión de compras (abastecimiento).
    Solo accesible para Administradores y Gerentes Generales.
    """

    def __init__(self, parent, controller, usuario_actual, **kwargs):
        super().__init__(parent, controller, usuario_actual)
        
        # Verificar permisos
        if not self.usuario_actual.tiene_permiso('gestionar_compras'):
            messagebox.showerror("Acceso Denegado", 
                                "No tiene permisos para gestionar compras.\nSe notificará al Gerente General.")
            Notificacion.crear_notificacion_seguridad(
                1,
                f"Intento de acceso no autorizado a Gestión de Compras por '{self.usuario_actual.nombre_usuario}'"
            )
            self.controller.volver()
            return
        
        # Configuración de la pantalla
        self.configure(fg_color="#F4F6F9")
        
        # Estado de la compra actual
        self.detalles = []
        self.proveedor_seleccionado = None
        self.compra_actual = None
        
        # Crear widgets
        self._crear_widgets()
        self._actualizar_lista_detalles()
    
    def _crear_widgets(self):
        # Frame principal
        frame_principal = ctk.CTkFrame(self, fg_color="#F9FAFB", corner_radius=15, border_width=1, border_color="#B8C1CE")
        frame_principal.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Barra superior
        barra = ctk.CTkFrame(frame_principal, fg_color="transparent")
        barra.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(barra, text="📦 GESTIÓN DE COMPRAS (ABASTECIMIENTO)", 
                    font=("Roboto", 24, "bold"), text_color="#1D4ED8"
        ).pack(side="left")
        
        btn_volver = ctk.CTkButton(barra, text="← Volver", font=("Roboto", 14), height=35,
                                  fg_color="#64748B", hover_color="#D6DBE3",
                                  corner_radius=10, command=self.destroy, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_volver.pack(side="right", padx=10)
        
        # Panel de datos de la compra
        panel_compra = ctk.CTkFrame(frame_principal, fg_color="#F4F6F9", corner_radius=10, border_width=1, border_color="#B8C1CE")
        panel_compra.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(panel_compra, text="📋 DATOS DE LA COMPRA", 
                    font=("Roboto", 16, "bold"), text_color="#1D4ED8"
        ).pack(anchor="w", padx=20, pady=(20, 10))
        
        # Fila: Nro Factura y Proveedor
        frame_fila1 = ctk.CTkFrame(panel_compra, fg_color="transparent")
        frame_fila1.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(frame_fila1, text="Nro. Factura:", font=("Roboto", 14, "bold")
        ).pack(side="left", padx=(0, 10))
        
        self.entry_factura = ctk.CTkEntry(frame_fila1, placeholder_text="Ingrese número de factura",
                                         width=200, height=35, font=("Roboto", 13))
        self.entry_factura.pack(side="left", padx=(0, 20))
        
        ctk.CTkLabel(frame_fila1, text="Proveedor:", font=("Roboto", 14, "bold")
        ).pack(side="left", padx=(0, 10))
        
        self.entry_proveedor = ctk.CTkEntry(frame_fila1, placeholder_text="CUIT o razón social",
                                           width=200, height=35, font=("Roboto", 13))
        self.entry_proveedor.pack(side="left", padx=(0, 10))
        
        btn_buscar_prov = ctk.CTkButton(frame_fila1, text="Buscar", height=35,
                                      fg_color="#2563EB", hover_color="#2563EB",
                                      corner_radius=10, command=self._buscar_proveedor, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_buscar_prov.pack(side="left", padx=5)
        
        self.label_proveedor = ctk.CTkLabel(frame_fila1, text="", font=("Roboto", 12), text_color="#15803D")
        self.label_proveedor.pack(side="left", padx=10)
        
        # Fila: Supervisor
        frame_fila2 = ctk.CTkFrame(panel_compra, fg_color="transparent")
        frame_fila2.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(frame_fila2, text="Supervisor:", font=("Roboto", 14, "bold")
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkLabel(frame_fila2, text=f"{self.usuario_actual.nombre_usuario} (ID: {self.usuario_actual.id})", 
                    font=("Roboto", 13), text_color="#6B7280"
        ).pack(side="left")
        
        # Panel de productos
        panel_productos = ctk.CTkFrame(frame_principal, fg_color="#F4F6F9", corner_radius=10, border_width=1, border_color="#B8C1CE")
        panel_productos.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(panel_productos, text="🛒 AGREGAR PRODUCTOS", 
                    font=("Roboto", 16, "bold"), text_color="#1D4ED8"
        ).pack(anchor="w", padx=20, pady=(20, 10))
        
        frame_prod = ctk.CTkFrame(panel_productos, fg_color="transparent")
        frame_prod.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(frame_prod, text="Código:", font=("Roboto", 13, "bold")
        ).pack(side="left", padx=(0, 5))
        
        self.entry_codigo = ctk.CTkEntry(frame_prod, placeholder_text="Código de barras",
                                        width=150, height=35, font=("Roboto", 13))
        self.entry_codigo.pack(side="left", padx=(0, 10))
        self.entry_codigo.bind("<Return>", lambda e: self._buscar_producto())
        
        ctk.CTkLabel(frame_prod, text="Cantidad:", font=("Roboto", 13, "bold")
        ).pack(side="left", padx=(0, 5))
        
        self.entry_cantidad = ctk.CTkEntry(frame_prod, placeholder_text="1",
                                          width=80, height=35, font=("Roboto", 13))
        self.entry_cantidad.insert(0, "1")
        self.entry_cantidad.pack(side="left", padx=(0, 10))
        
        ctk.CTkLabel(frame_prod, text="Precio Costo:", font=("Roboto", 13, "bold")
        ).pack(side="left", padx=(0, 5))
        
        self.entry_precio = ctk.CTkEntry(frame_prod, placeholder_text="0.00",
                                        width=120, height=35, font=("Roboto", 13))
        self.entry_precio.pack(side="left", padx=(0, 10))
        
        btn_agregar = ctk.CTkButton(frame_prod, text="➕ Agregar", height=35,
                                   fg_color="#15803D", hover_color="#166534",
                                   corner_radius=10, command=self._agregar_detalle, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_agregar.pack(side="left")
        
        self.label_producto = ctk.CTkLabel(frame_prod, text="", font=("Roboto", 12), text_color="#C2410C")
        self.label_producto.pack(side="left", padx=10)
        
        # Tabla de detalles
        frame_detalles = ctk.CTkFrame(frame_principal, fg_color="#F4F6F9", corner_radius=10, border_width=1, border_color="#B8C1CE")
        frame_detalles.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(frame_detalles, text="📋 DETALLE DE LA COMPRA", 
                    font=("Roboto", 16, "bold"), text_color="#1D4ED8"
        ).pack(anchor="w", padx=20, pady=(20, 10))
        
        self.frame_detalles_tabla = ctk.CTkScrollableFrame(frame_detalles, fg_color="#F4F6F9", corner_radius=10)
        self.frame_detalles_tabla.pack(fill="both", expand=True, padx=20, pady=10)
        
        encabezados = ["Código", "Producto", "Cantidad", "Precio Costo", "Subtotal", "Acción"]
        for i, texto in enumerate(encabezados):
            ctk.CTkLabel(self.frame_detalles_tabla, text=texto, font=("Roboto", 13, "bold"),
                        text_color="#6B7280").grid(row=0, column=i, padx=10, pady=5, sticky="w")
        
        # Panel total y botones finales
        panel_total = ctk.CTkFrame(frame_principal, fg_color="#F4F6F9", corner_radius=10, border_width=1, border_color="#B8C1CE")
        panel_total.pack(fill="x", padx=20, pady=(10, 20))
        
        ctk.CTkLabel(panel_total, text="TOTAL FACTURA:", font=("Roboto", 18, "bold"), text_color="#1D4ED8"
        ).pack(side="left", padx=20, pady=15)
        
        self.label_total = ctk.CTkLabel(panel_total, text="$ 0.00", 
                                       font=("Roboto", 24, "bold"), text_color="#15803D")
        self.label_total.pack(side="left", padx=20, pady=15)
        
        btn_guardar = ctk.CTkButton(panel_total, text="💾 GUARDAR COMPRA", height=50,
                                   font=("Roboto", 16, "bold"),
                                   fg_color="#15803D", hover_color="#166534",
                                   corner_radius=10, command=self._guardar_compra, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_guardar.pack(side="right", padx=20, pady=10)
        
        btn_limpiar = ctk.CTkButton(panel_total, text="🗑️ Limpiar", height=40,
                                   fg_color="#DC2626", hover_color="#B91C1C",
                                   corner_radius=10, command=self._limpiar_formulario, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_limpiar.pack(side="right", padx=10, pady=10)
    
    # =====================================================================
    # MÉTODOS DE PROVEEDOR
    # =====================================================================
    def _buscar_proveedor(self):
        termino = self.entry_proveedor.get().strip()
        if not termino:
            messagebox.showwarning("Aviso", "Ingrese CUIT o razón social del proveedor.")
            return
        
        proveedor = Proveedor.buscar_por_cuit(termino)
        if not proveedor:
            proveedores = Proveedor.buscar_por_razon_social(termino)
            if proveedores:
                proveedor = proveedores[0]
        
        if proveedor and proveedor.estado == 'Activo':
            self.proveedor_seleccionado = proveedor
            self.label_proveedor.configure(
                text=f"✅ {proveedor.razon_social} (CUIT: {proveedor.cuit})",
                text_color="#15803D"
            )
            self.entry_proveedor.delete(0, 'end')
            self.entry_proveedor.insert(0, proveedor.cuit)
        else:
            messagebox.showerror("Error", "Proveedor no encontrado o inactivo.")
            self.proveedor_seleccionado = None
            self.label_proveedor.configure(text="")
    
    # =====================================================================
    # MÉTODOS DE PRODUCTOS Y DETALLES
    # =====================================================================
    def _buscar_producto(self):
        codigo = self.entry_codigo.get().strip()
        if not codigo:
            return
        
        producto = Producto.buscar_por_codigo(codigo)
        if producto and producto.estado == 'Activo':
            self.label_producto.configure(
                text=f"✅ {producto.nombre} - Stock actual: {producto.stock_actual}",
                text_color="#15803D"
            )
            if not self.entry_precio.get().strip():
                self.entry_precio.delete(0, 'end')
                self.entry_precio.insert(0, "0.00")
            self.entry_cantidad.focus_set()
        else:
            self.label_producto.configure(text="❌ Producto no encontrado o inactivo", text_color="#DC2626")
    
    def _agregar_detalle(self):
        codigo = self.entry_codigo.get().strip()
        if not codigo:
            messagebox.showwarning("Aviso", "Ingrese el código del producto.")
            return
        
        producto = Producto.buscar_por_codigo(codigo)
        if not producto or producto.estado != 'Activo':
            messagebox.showerror("Error", "Producto no encontrado o inactivo.")
            return
        
        try:
            cantidad = int(self.entry_cantidad.get().strip() or "1")
            if cantidad <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "La cantidad debe ser un número entero positivo.")
            return
        
        try:
            precio_costo = float(self.entry_precio.get().strip() or "0.0")
            if precio_costo < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "El precio de costo debe ser un número positivo.")
            return
        
        for detalle in self.detalles:
            if detalle['codigo'] == codigo:
                detalle['cantidad'] += cantidad
                detalle['precio_costo'] = precio_costo
                detalle['subtotal'] = detalle['cantidad'] * detalle['precio_costo']
                self._actualizar_lista_detalles()
                self._limpiar_campos_producto()
                messagebox.showinfo("Actualizado", f"✅ Producto {producto.nombre} actualizado en el detalle.")
                return
        
        self.detalles.append({
            'codigo': codigo,
            'nombre': producto.nombre,
            'cantidad': cantidad,
            'precio_costo': precio_costo,
            'subtotal': cantidad * precio_costo
        })
        self._actualizar_lista_detalles()
        self._limpiar_campos_producto()
        messagebox.showinfo("Agregado", f"✅ Producto {producto.nombre} agregado al detalle.")
    
    def _limpiar_campos_producto(self):
        self.entry_codigo.delete(0, 'end')
        self.entry_cantidad.delete(0, 'end')
        self.entry_cantidad.insert(0, "1")
        self.entry_precio.delete(0, 'end')
        self.entry_precio.insert(0, "0.00")
        self.label_producto.configure(text="")
        self.entry_codigo.focus_set()
    
    def _actualizar_lista_detalles(self):
        for widget in self.frame_detalles_tabla.winfo_children():
            if widget.grid_info() != {}:
                widget.destroy()
        
        if not self.detalles:
            ctk.CTkLabel(self.frame_detalles_tabla, text="No hay productos cargados.", 
                        font=("Roboto", 14), text_color="#8B93A3"
            ).grid(row=1, column=0, columnspan=6, padx=10, pady=20)
            self.label_total.configure(text="$ 0.00")
            return
        
        total = 0.0
        for i, detalle in enumerate(self.detalles, start=1):
            total += detalle['subtotal']
            ctk.CTkLabel(self.frame_detalles_tabla, text=detalle['codigo'], 
                        font=("Roboto", 13)).grid(row=i, column=0, padx=10, pady=5, sticky="w")
            ctk.CTkLabel(self.frame_detalles_tabla, text=detalle['nombre'], 
                        font=("Roboto", 13)).grid(row=i, column=1, padx=10, pady=5, sticky="w")
            ctk.CTkLabel(self.frame_detalles_tabla, text=str(detalle['cantidad']), 
                        font=("Roboto", 13)).grid(row=i, column=2, padx=10, pady=5, sticky="e")
            ctk.CTkLabel(self.frame_detalles_tabla, text=f"${detalle['precio_costo']:.2f}", 
                        font=("Roboto", 13)).grid(row=i, column=3, padx=10, pady=5, sticky="e")
            ctk.CTkLabel(self.frame_detalles_tabla, text=f"${detalle['subtotal']:.2f}", 
                        font=("Roboto", 13, "bold"), text_color="#15803D"
            ).grid(row=i, column=4, padx=10, pady=5, sticky="e")
            btn_eliminar = ctk.CTkButton(self.frame_detalles_tabla, text="❌", width=30, height=25,
                                       fg_color="#DC2626", hover_color="#B91C1C",
                                       corner_radius=5, command=lambda idx=i-1: self._eliminar_detalle(idx), border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
            btn_eliminar.grid(row=i, column=5, padx=10, pady=5)
        
        self.label_total.configure(text=f"$ {total:.2f}")
    
    def _eliminar_detalle(self, indice):
        if 0 <= indice < len(self.detalles):
            if messagebox.askyesno("Confirmar", f"¿Eliminar '{self.detalles[indice]['nombre']}' del detalle?"):
                del self.detalles[indice]
                self._actualizar_lista_detalles()
    
    # =====================================================================
    # GUARDADO DE COMPRA
    # =====================================================================
    def _guardar_compra(self):
        if not self.proveedor_seleccionado:
            messagebox.showerror("Error", "Debe seleccionar un proveedor válido y activo.")
            return
        
        nro_factura = self.entry_factura.get().strip()
        if not nro_factura:
            messagebox.showerror("Error", "Debe ingresar el número de factura.")
            return
        if len(nro_factura) < 3:
            messagebox.showerror("Error", "El número de factura debe tener al menos 3 caracteres.")
            return
        
        if not self.detalles:
            messagebox.showerror("Error", "Debe agregar al menos un producto al detalle.")
            return
        
        total = sum(d['subtotal'] for d in self.detalles)
        if not messagebox.askyesno("Confirmar", 
                                   f"¿Guardar compra con factura {nro_factura}?\n"
                                   f"Proveedor: {self.proveedor_seleccionado.razon_social}\n"
                                   f"Total: $ {total:.2f}"):
            return
        
        compra = Compra(
            nro_factura=nro_factura,
            proveedor_id=self.proveedor_seleccionado.cuit,
            supervisor_id=self.usuario_actual.id,
            total_factura=total
        )
        
        for detalle in self.detalles:
            compra.agregar_detalle(detalle['codigo'], detalle['cantidad'], detalle['precio_costo'])
        
        try:
            if compra.guardar():
                messagebox.showinfo("Éxito", f"✅ Compra {nro_factura} guardada correctamente.\n"
                                            f"Stock actualizado automáticamente.")
                if self.usuario_actual.rol != "Gerente General":
                    Notificacion.crear_notificacion_sistema(
                        1,
                        f"Nueva compra registrada por {self.usuario_actual.nombre_usuario}: {nro_factura} - ${compra.total_factura:.2f}"
                    )
                self._limpiar_formulario()
            else:
                messagebox.showerror("Error", "❌ No se pudo guardar la compra.\nVerifique que la factura no esté duplicada.")
        except Exception as e:
            messagebox.showerror("Error", f"❌ Error inesperado al guardar: {str(e)}")
    
    def _limpiar_formulario(self):
        self.detalles = []
        self.proveedor_seleccionado = None
        self.entry_factura.delete(0, 'end')
        self.entry_proveedor.delete(0, 'end')
        self.label_proveedor.configure(text="")
        self.entry_codigo.delete(0, 'end')
        self.entry_cantidad.delete(0, 'end')
        self.entry_cantidad.insert(0, "1")
        self.entry_precio.delete(0, 'end')
        self.entry_precio.insert(0, "0.00")
        self.label_producto.configure(text="")
        self._actualizar_lista_detalles()
        self.entry_factura.focus_set()