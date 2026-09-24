import customtkinter as ctk
from tkinter import messagebox
from models.producto import Producto
from models.notificacion import Notificacion
from views.base_frame import BaseFrame

class FrameProductos(BaseFrame):
    """
    Pantalla de gestión de productos (CRUD).
    Solo accesible para Administradores y Gerentes Generales.
    """

    def __init__(self, parent, controller, usuario_actual, **kwargs):
        super().__init__(parent, controller, usuario_actual)
        
        # Verificar permisos
        if not self.usuario_actual.tiene_permiso('gestionar_productos'):
            messagebox.showerror("Acceso Denegado", 
                                "No tiene permisos para gestionar productos.\nSe notificará al Gerente General.")
            Notificacion.crear_notificacion_seguridad(
                1,
                f"Intento de acceso no autorizado a Gestión de Productos por '{self.usuario_actual.nombre_usuario}'"
            )
            self.controller.volver()
            return
        
        # Configuración de la pantalla
        self.configure(fg_color="#F4F6F9")
        
        # Estado de la pantalla
        self.producto_seleccionado = None
        self.mostrar_inactivos = False  # Nuevo filtro
        
        # Crear widgets
        self._crear_widgets()
        self._cargar_productos()
    
    def _crear_widgets(self):
        # Frame principal
        frame_principal = ctk.CTkFrame(self, fg_color="#F9FAFB", corner_radius=15, border_width=1, border_color="#B8C1CE")
        frame_principal.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Barra superior
        barra_superior = ctk.CTkFrame(frame_principal, fg_color="transparent")
        barra_superior.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(barra_superior, text="📦 GESTIÓN DE PRODUCTOS", 
                    font=("Roboto", 24, "bold"), text_color="#1D4ED8"
        ).pack(side="left")
        
        btn_volver = ctk.CTkButton(barra_superior, text="← Volver", 
                                  font=("Roboto", 14), height=35,
                                  fg_color="#64748B", hover_color="#D6DBE3",
                                  corner_radius=10, command=self.destroy, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_volver.pack(side="right", padx=10)
        
        # Panel de filtros
        panel_filtros = ctk.CTkFrame(frame_principal, fg_color="#F4F6F9", corner_radius=10, border_width=1, border_color="#B8C1CE")
        panel_filtros.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(panel_filtros, text="🔍 Buscar:", font=("Roboto", 14, "bold")
        ).pack(side="left", padx=10, pady=10)
        
        self.entry_buscar = ctk.CTkEntry(panel_filtros, placeholder_text="Código o nombre...",
                                        width=250, height=35, font=("Roboto", 13))
        self.entry_buscar.pack(side="left", padx=10, pady=10)
        self.entry_buscar.bind("<Return>", lambda e: self._cargar_productos())
        
        btn_buscar = ctk.CTkButton(panel_filtros, text="Buscar", height=35,
                                  fg_color="#2563EB", hover_color="#2563EB",
                                  corner_radius=10, command=self._cargar_productos, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_buscar.pack(side="left", padx=5, pady=10)
        
        btn_limpiar = ctk.CTkButton(panel_filtros, text="Limpiar", height=35,
                                   fg_color="#64748B", hover_color="#D6DBE3",
                                   corner_radius=10, command=self._limpiar_filtros, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_limpiar.pack(side="left", padx=5, pady=10)
        
        # Filtro de estado
        ctk.CTkLabel(panel_filtros, text="Mostrar:", font=("Roboto", 14, "bold")
        ).pack(side="left", padx=(20, 5), pady=10)
        
        self.combo_estado = ctk.CTkOptionMenu(panel_filtros, values=["Activos", "Todos", "Inactivos"],
                                             width=120, height=35, corner_radius=10,
                                             command=lambda e: self._cargar_productos(), text_color="#FFFFFF")
        self.combo_estado.pack(side="left", padx=5, pady=10)
        self.combo_estado.set("Activos")
        
        btn_alertas = ctk.CTkButton(panel_filtros, text="⚠️ Alertas Stock", height=35,
                                   fg_color="#C2410C", hover_color="#9A3412",
                                   corner_radius=10, command=self._mostrar_alertas_stock, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_alertas.pack(side="right", padx=10, pady=10)
        
        # Tabla de productos
        self.frame_tabla = ctk.CTkScrollableFrame(frame_principal, fg_color="#F4F6F9", corner_radius=10)
        self.frame_tabla.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Encabezados
        encabezados = ["Seleccionar", "Código", "Nombre", "Categoría", "Precio", "Stock", "Stock Mín", "Estado"]
        for i, texto in enumerate(encabezados):
            ctk.CTkLabel(self.frame_tabla, text=texto, font=("Roboto", 14, "bold"),
                        text_color="#6B7280").grid(row=0, column=i, padx=10, pady=5, sticky="w")
        
        # Panel de botones
        panel_botones = ctk.CTkFrame(frame_principal, fg_color="#F4F6F9", corner_radius=10, border_width=1, border_color="#B8C1CE")
        panel_botones.pack(fill="x", padx=20, pady=(10, 20))
        
        btn_agregar = ctk.CTkButton(panel_botones, text="➕ Agregar Producto", height=40,
                                   fg_color="#15803D", hover_color="#166534",
                                   corner_radius=10, command=self._abrir_formulario_alta, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_agregar.pack(side="left", padx=10)
        
        btn_editar = ctk.CTkButton(panel_botones, text="✏️ Editar", height=40,
                                  fg_color="#2563EB", hover_color="#1D4ED8",
                                  corner_radius=10, command=self._abrir_formulario_edicion, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_editar.pack(side="left", padx=10)
        
        btn_eliminar = ctk.CTkButton(panel_botones, text="🗑️ Dar de Baja", height=40,
                                    fg_color="#DC2626", hover_color="#B91C1C",
                                    corner_radius=10, command=self._eliminar_producto, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_eliminar.pack(side="left", padx=10)
        
        btn_reactivar = ctk.CTkButton(panel_botones, text="🔄 Reactivar", height=40,
                                     fg_color="#7C3AED", hover_color="#6D28D9",
                                     corner_radius=10, command=self._reactivar_producto, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_reactivar.pack(side="left", padx=10)
        
        ctk.CTkLabel(panel_botones, text="Seleccione un producto para editar/eliminar", 
                    font=("Roboto", 12), text_color="#8B93A3"
        ).pack(side="right", padx=20)
    
    def _cargar_productos(self):
        """Carga los productos según el filtro."""
        for widget in self.frame_tabla.winfo_children():
            if widget.grid_info() != {}:
                widget.destroy()
        
        termino = self.entry_buscar.get().strip()
        filtro_estado = self.combo_estado.get()
        
        # Obtener productos según filtro de estado
        if filtro_estado == "Activos":
            productos = Producto.obtener_todos(estado='Activo')
        elif filtro_estado == "Inactivos":
            productos = Producto.obtener_todos(estado='Inactivo')
        else:  # Todos
            productos = Producto.obtener_todos(estado=None)
        
        # Filtrar por término de búsqueda
        if termino:
            productos = [p for p in productos if termino.lower() in p.nombre.lower() or termino in p.codigo_barras]
        
        if not productos:
            ctk.CTkLabel(self.frame_tabla, text="No hay productos para mostrar", 
                        font=("Roboto", 14), text_color="#8B93A3"
            ).grid(row=1, column=0, columnspan=8, padx=10, pady=20)
            return
        
        for i, producto in enumerate(productos, start=1):
            btn_selector = ctk.CTkButton(
                self.frame_tabla, text="Seleccionar", width=80, height=25,
                fg_color="#D6DBE3", hover_color="#64748B", corner_radius=5,
                command=lambda p=producto: self._seleccionar_producto(p)
            , border_width=1, border_color="#CBD2DC", text_color="#1A2233")
            btn_selector.grid(row=i, column=0, padx=10, pady=5)
            
            ctk.CTkLabel(self.frame_tabla, text=producto.codigo_barras, 
                        font=("Roboto", 13)).grid(row=i, column=1, padx=10, pady=5, sticky="w")
            ctk.CTkLabel(self.frame_tabla, text=producto.nombre, 
                        font=("Roboto", 13)).grid(row=i, column=2, padx=10, pady=5, sticky="w")
            ctk.CTkLabel(self.frame_tabla, text=str(producto.categoria_id), 
                        font=("Roboto", 13)).grid(row=i, column=3, padx=10, pady=5, sticky="w")
            ctk.CTkLabel(self.frame_tabla, text=f"${producto.precio_venta:.2f}", 
                        font=("Roboto", 13)).grid(row=i, column=4, padx=10, pady=5, sticky="e")
            
            color_stock = "#15803D" if producto.stock_actual > producto.stock_minimo else "#DC2626"
            ctk.CTkLabel(self.frame_tabla, text=str(producto.stock_actual), 
                        font=("Roboto", 13), text_color=color_stock
            ).grid(row=i, column=5, padx=10, pady=5, sticky="e")
            
            ctk.CTkLabel(self.frame_tabla, text=str(producto.stock_minimo), 
                        font=("Roboto", 13)).grid(row=i, column=6, padx=10, pady=5, sticky="e")
            
            estado = "🟢 Activo" if producto.estado == 'Activo' else "🔴 Inactivo"
            ctk.CTkLabel(self.frame_tabla, text=estado, 
                        font=("Roboto", 13)).grid(row=i, column=7, padx=10, pady=5, sticky="w")
    
    def _seleccionar_producto(self, producto):
        self.producto_seleccionado = producto
        messagebox.showinfo("Seleccionado", f"✅ Producto seleccionado:\n{producto.nombre} (Cód: {producto.codigo_barras})")
    
    def _limpiar_filtros(self):
        self.entry_buscar.delete(0, 'end')
        self.combo_estado.set("Activos")
        self._cargar_productos()
    
    def _mostrar_alertas_stock(self):
        productos_bajos = Producto.obtener_productos_con_stock_bajo()
        if not productos_bajos:
            messagebox.showinfo("Alertas de Stock", "✅ No hay productos con stock bajo.")
            return
        
        mensaje = "⚠️ PRODUCTOS CON STOCK BAJO\n\n"
        for p in productos_bajos:
            mensaje += f"📦 {p.nombre} (Cód: {p.codigo_barras})\n"
            mensaje += f"   Stock actual: {p.stock_actual} | Mínimo: {p.stock_minimo}\n\n"
        
        messagebox.showwarning("Alertas de Stock", mensaje)
    
    # =====================================================================
    # MÉTODOS DE CRUD CON VALIDACIONES
    # =====================================================================
    def _abrir_formulario_alta(self):
        self._formulario_producto()
    
    def _abrir_formulario_edicion(self):
        if not self.producto_seleccionado:
            messagebox.showwarning("Aviso", "Primero seleccione un producto de la tabla.")
            return
        self._formulario_producto(editar=True)
    
    def _formulario_producto(self, editar=False):
        """Diálogo con scroll para agregar/editar producto."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Editar Producto" if editar else "Nuevo Producto")
        dialog.geometry("550x700")
        dialog.configure(fg_color="#F9FAFB")
        dialog.resizable(False, False)
        
        # Centrar y hacer modal
        dialog.transient(self.winfo_toplevel())
        dialog.lift()
        dialog.focus_force()
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 275
        y = (dialog.winfo_screenheight() // 2) - 350
        dialog.geometry(f"550x700+{x}+{y}")
        
        # Frame contenedor con scroll
        frame_scroll = ctk.CTkScrollableFrame(dialog, fg_color="#F9FAFB", corner_radius=15)
        frame_scroll.pack(fill="both", expand=True, padx=20, pady=20)
        
        titulo = "✏️ Editar Producto" if editar else "➕ Nuevo Producto"
        ctk.CTkLabel(frame_scroll, text=titulo, font=("Roboto", 20, "bold"), text_color="#1D4ED8"
        ).pack(pady=(0, 20))
        
        # Campos
        campos = [
            ("Código de Barras", "codigo_barras", "TEXT", True),
            ("Nombre", "nombre", "TEXT", True),
            ("Categoría ID", "categoria_id", "INT", True),
            ("Precio Venta", "precio_venta", "REAL", True),
            ("Precio Costo", "precio_costo", "REAL", True),
            ("Stock Actual", "stock_actual", "INT", False),
            ("Stock Mínimo", "stock_minimo", "INT", False),
            ("Tipo Garantía", "tipo_garantia", "TEXT", False),
        ]
        
        entradas = {}
        valores_por_defecto = {
            'stock_actual': 0,
            'stock_minimo': 0,
            'tipo_garantia': 'comestible'
        }
        
        for etiqueta, clave, tipo, obligatorio in campos:
            ctk.CTkLabel(frame_scroll, text=f"{etiqueta}:", font=("Roboto", 13, "bold")
            ).pack(anchor="w", pady=(10, 5))
            
            entrada = ctk.CTkEntry(frame_scroll, font=("Roboto", 13), height=35,
                                  fg_color="#D6DBE3", text_color="#1A2233")
            entrada.pack(fill="x", padx=0, pady=(0, 5))
            
            if editar and hasattr(self.producto_seleccionado, clave):
                valor = getattr(self.producto_seleccionado, clave, "")
                entrada.insert(0, str(valor))
                if clave == "codigo_barras":
                    entrada.configure(state="disabled")
            elif clave in valores_por_defecto:
                entrada.insert(0, str(valores_por_defecto[clave]))
            
            entradas[clave] = entrada
        
        # Botones (siempre visibles al final)
        frame_botones = ctk.CTkFrame(frame_scroll, fg_color="transparent")
        frame_botones.pack(fill="x", pady=30)
        
        def guardar():
            try:
                datos = {}
                errores = []
                
                for clave, entrada in entradas.items():
                    valor = entrada.get().strip() if entrada.cget("state") != "disabled" else entrada.get().strip()
                    if clave in ['codigo_barras', 'nombre', 'categoria_id', 'precio_venta', 'precio_costo']:
                        if not valor:
                            errores.append(f"El campo '{clave}' es obligatorio.")
                            continue
                    
                    if clave in ['categoria_id']:
                        if not valor.isdigit() or int(valor) <= 0:
                            errores.append("La categoría debe ser un número entero positivo.")
                            continue
                        datos[clave] = int(valor)
                    elif clave in ['stock_actual', 'stock_minimo']:
                        if valor and (not valor.isdigit() or int(valor) < 0):
                            errores.append(f"'{clave}' debe ser un número entero >= 0.")
                            continue
                        datos[clave] = int(valor) if valor else 0
                    elif clave in ['precio_venta', 'precio_costo']:
                        try:
                            num = float(valor)
                            if num <= 0:
                                errores.append(f"'{clave}' debe ser un número positivo.")
                                continue
                            datos[clave] = num
                        except ValueError:
                            errores.append(f"'{clave}' debe ser un número válido (ej. 10.50).")
                            continue
                    elif clave == 'nombre':
                        if len(valor) < 2:
                            errores.append("El nombre debe tener al menos 2 caracteres.")
                            continue
                        datos[clave] = valor
                    else:
                        datos[clave] = valor
                
                if 'precio_venta' in datos and 'precio_costo' in datos:
                    if datos['precio_venta'] < datos['precio_costo']:
                        if not messagebox.askyesno("Advertencia", 
                            f"El precio de venta (${datos['precio_venta']:.2f}) es menor que el costo (${datos['precio_costo']:.2f}).\n"
                            "¿Desea continuar de todas formas?"):
                            return
                
                if errores:
                    messagebox.showerror("Errores de Validación", "\n".join(errores))
                    return
                
                if editar:
                    for clave, valor in datos.items():
                        setattr(self.producto_seleccionado, clave, valor)
                    if self.producto_seleccionado.guardar():
                        messagebox.showinfo("Éxito", "✅ Producto actualizado correctamente.")
                        dialog.destroy()
                        self._cargar_productos()
                    else:
                        messagebox.showerror("Error", "❌ No se pudo actualizar el producto.\nVerifique que el código no esté duplicado.")
                else:
                    nuevo = Producto(
                        codigo_barras=datos['codigo_barras'],
                        nombre=datos['nombre'],
                        categoria_id=datos['categoria_id'],
                        precio_venta=datos['precio_venta'],
                        precio_costo=datos['precio_costo'],
                        stock_actual=datos.get('stock_actual', 0),
                        stock_minimo=datos.get('stock_minimo', 0),
                        tipo_garantia=datos.get('tipo_garantia', 'comestible')
                    )
                    if nuevo.guardar():
                        messagebox.showinfo("Éxito", "✅ Producto creado correctamente.")
                        dialog.destroy()
                        self._cargar_productos()
                    else:
                        messagebox.showerror("Error", "❌ No se pudo crear el producto.\nVerifique que el código no esté duplicado.")
                
            except ValueError as e:
                messagebox.showerror("Error", f"❌ {str(e)}")
            except Exception as e:
                messagebox.showerror("Error", f"❌ Error inesperado: {str(e)}")
        
        btn_guardar = ctk.CTkButton(frame_botones, text="💾 Guardar", height=40,
                                   fg_color="#15803D", hover_color="#166534",
                                   corner_radius=10, command=guardar, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_guardar.pack(side="left", fill="x", expand=True, padx=5)
        
        btn_cancelar = ctk.CTkButton(frame_botones, text="Cancelar", height=40,
                                    fg_color="#64748B", hover_color="#D6DBE3",
                                    corner_radius=10, command=dialog.destroy, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_cancelar.pack(side="left", fill="x", expand=True, padx=5)
    
    def _eliminar_producto(self):
        if not self.producto_seleccionado:
            messagebox.showwarning("Aviso", "Primero seleccione un producto de la tabla.")
            return
        
        if self.producto_seleccionado.estado == 'Inactivo':
            messagebox.showinfo("Aviso", "ℹ️ El producto ya está inactivo.")
            return
        
        if messagebox.askyesno("Confirmar", f"¿Está seguro de desactivar '{self.producto_seleccionado.nombre}'?"):
            if self.producto_seleccionado.cambiar_estado('Inactivo'):
                messagebox.showinfo("Éxito", "✅ Producto dado de baja correctamente.")
                self.producto_seleccionado = None
                self._cargar_productos()
            else:
                messagebox.showerror("Error", "❌ No se pudo desactivar el producto.")
    
    def _reactivar_producto(self):
        if not self.producto_seleccionado:
            messagebox.showwarning("Aviso", "Primero seleccione un producto de la tabla.")
            return
        
        if self.producto_seleccionado.estado == 'Activo':
            messagebox.showinfo("Aviso", "ℹ️ El producto ya está activo.")
            return
        
        if messagebox.askyesno("Confirmar", f"¿Está seguro de reactivar '{self.producto_seleccionado.nombre}'?"):
            if self.producto_seleccionado.cambiar_estado('Activo'):
                messagebox.showinfo("Éxito", "✅ Producto reactivado correctamente.")
                self.producto_seleccionado = None
                self._cargar_productos()
            else:
                messagebox.showerror("Error", "❌ No se pudo reactivar el producto.")