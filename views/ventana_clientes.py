import customtkinter as ctk
from tkinter import messagebox
from models.cliente import Cliente
from models.notificacion import Notificacion
from views.base_frame import BaseFrame
import re

class FrameClientes(BaseFrame):
    """
    Pantalla de gestión de clientes (CRUD).
    Solo accesible para Administradores y Gerentes Generales.
    """

    def __init__(self, parent, controller, usuario_actual, **kwargs):
        super().__init__(parent, controller, usuario_actual)

        # Verificar permisos
        if not self.usuario_actual.tiene_permiso('gestionar_clientes'):
            messagebox.showerror("Acceso Denegado", 
                                "No tiene permisos para gestionar clientes.\nSe notificará al Gerente General.")
            Notificacion.crear_notificacion_seguridad(
                1,
                f"Intento de acceso no autorizado a Gestión de Clientes por '{self.usuario_actual.nombre_usuario}'"
            )
            self.controller.volver()
            return
        
        # Configuración de la pantalla
        self.configure(fg_color="#F4F6F9")
        
        # Estado
        self.cliente_seleccionado = None
        
        # Crear widgets
        self._crear_widgets()
        self._cargar_clientes()
    
    def _crear_widgets(self):
        # Frame principal
        frame_principal = ctk.CTkFrame(self, fg_color="#F9FAFB", corner_radius=15, border_width=1, border_color="#B8C1CE")
        frame_principal.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Barra superior
        barra = ctk.CTkFrame(frame_principal, fg_color="transparent")
        barra.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(barra, text="👥 GESTIÓN DE CLIENTES", 
                    font=("Roboto", 24, "bold"), text_color="#1D4ED8"
        ).pack(side="left")
        
        btn_volver = ctk.CTkButton(barra, text="← Volver", font=("Roboto", 14), height=35,
                                  fg_color="#64748B", hover_color="#D6DBE3",
                                  corner_radius=10, command=self.destroy, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_volver.pack(side="right", padx=10)
        
        # Panel de búsqueda
        panel_busqueda = ctk.CTkFrame(frame_principal, fg_color="#F4F6F9", corner_radius=10, border_width=1, border_color="#B8C1CE")
        panel_busqueda.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(panel_busqueda, text="🔍 Buscar:", font=("Roboto", 14, "bold")
        ).pack(side="left", padx=10, pady=10)
        
        self.entry_buscar = ctk.CTkEntry(panel_busqueda, placeholder_text="DNI o nombre...",
                                        width=250, height=35, font=("Roboto", 13))
        self.entry_buscar.pack(side="left", padx=10, pady=10)
        self.entry_buscar.bind("<Return>", lambda e: self._cargar_clientes())
        
        btn_buscar = ctk.CTkButton(panel_busqueda, text="Buscar", height=35,
                                  fg_color="#2563EB", hover_color="#2563EB",
                                  corner_radius=10, command=self._cargar_clientes, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_buscar.pack(side="left", padx=5, pady=10)
        
        btn_limpiar = ctk.CTkButton(panel_busqueda, text="Limpiar", height=35,
                                   fg_color="#64748B", hover_color="#D6DBE3",
                                   corner_radius=10, command=self._limpiar_filtros, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_limpiar.pack(side="left", padx=5, pady=10)
        
        # Tabla de clientes
        self.frame_tabla = ctk.CTkScrollableFrame(frame_principal, fg_color="#F4F6F9", corner_radius=10)
        self.frame_tabla.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Encabezados
        encabezados = ["Seleccionar", "DNI", "Nombre", "Teléfono", "Email", "Puntos", "Estado"]
        for i, texto in enumerate(encabezados):
            ctk.CTkLabel(self.frame_tabla, text=texto, font=("Roboto", 14, "bold"),
                        text_color="#6B7280").grid(row=0, column=i, padx=10, pady=5, sticky="w")
        
        # Panel de botones
        panel_botones = ctk.CTkFrame(frame_principal, fg_color="#F4F6F9", corner_radius=10, border_width=1, border_color="#B8C1CE")
        panel_botones.pack(fill="x", padx=20, pady=(10, 20))
        
        btn_agregar = ctk.CTkButton(panel_botones, text="➕ Agregar Cliente", height=40,
                                   fg_color="#15803D", hover_color="#166534",
                                   corner_radius=10, command=self._abrir_formulario_alta, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_agregar.pack(side="left", padx=10)
        
        btn_editar = ctk.CTkButton(panel_botones, text="✏️ Editar", height=40,
                                  fg_color="#2563EB", hover_color="#1D4ED8",
                                  corner_radius=10, command=self._abrir_formulario_edicion, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_editar.pack(side="left", padx=10)
        
        btn_eliminar = ctk.CTkButton(panel_botones, text="🗑️ Dar de Baja", height=40,
                                    fg_color="#DC2626", hover_color="#B91C1C",
                                    corner_radius=10, command=self._eliminar_cliente, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_eliminar.pack(side="left", padx=10)
        
        btn_historial = ctk.CTkButton(panel_botones, text="📜 Historial de Compras", height=40,
                                     fg_color="#7C3AED", hover_color="#6D28D9",
                                     corner_radius=10, command=self._ver_historial, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_historial.pack(side="left", padx=10)
        
        ctk.CTkLabel(panel_botones, text="Seleccione un cliente para editar/ver historial", 
                    font=("Roboto", 12), text_color="#8B93A3"
        ).pack(side="right", padx=20)
    
    def _cargar_clientes(self):
        """Carga los clientes según el filtro."""
        for widget in self.frame_tabla.winfo_children():
            if widget.grid_info() != {}:
                widget.destroy()
        
        termino = self.entry_buscar.get().strip()
        if termino:
            # Buscar por DNI exacto o nombre parcial
            cliente = Cliente.buscar_por_dni(termino)
            if cliente:
                clientes = [cliente]
            else:
                clientes = Cliente.buscar_por_nombre(termino)
        else:
            clientes = Cliente.obtener_todos(estado=None)  # Mostrar todos (activos e inactivos)
        
        if not clientes:
            ctk.CTkLabel(self.frame_tabla, text="No hay clientes para mostrar", 
                        font=("Roboto", 14), text_color="#8B93A3"
            ).grid(row=1, column=0, columnspan=7, padx=10, pady=20)
            return
        
        for i, cliente in enumerate(clientes, start=1):
            btn_selector = ctk.CTkButton(self.frame_tabla, text="Seleccionar", width=80, height=25,
                                        fg_color="#D6DBE3", hover_color="#64748B",
                                        corner_radius=5, command=lambda c=cliente: self._seleccionar_cliente(c), border_width=1, border_color="#CBD2DC", text_color="#1A2233")
            btn_selector.grid(row=i, column=0, padx=10, pady=5)
            
            ctk.CTkLabel(self.frame_tabla, text=cliente.dni_cuil, 
                        font=("Roboto", 13)).grid(row=i, column=1, padx=10, pady=5, sticky="w")
            ctk.CTkLabel(self.frame_tabla, text=cliente.nombre, 
                        font=("Roboto", 13)).grid(row=i, column=2, padx=10, pady=5, sticky="w")
            ctk.CTkLabel(self.frame_tabla, text=cliente.telefono or "-", 
                        font=("Roboto", 13)).grid(row=i, column=3, padx=10, pady=5, sticky="w")
            ctk.CTkLabel(self.frame_tabla, text=cliente.email or "-", 
                        font=("Roboto", 13)).grid(row=i, column=4, padx=10, pady=5, sticky="w")
            ctk.CTkLabel(self.frame_tabla, text=str(cliente.puntos_acumulados), 
                        font=("Roboto", 13, "bold"), text_color="#C2410C"
            ).grid(row=i, column=5, padx=10, pady=5, sticky="e")
            estado = "🟢 Activo" if cliente.estado == 'Activo' else "🔴 Inactivo"
            ctk.CTkLabel(self.frame_tabla, text=estado, font=("Roboto", 13)
            ).grid(row=i, column=6, padx=10, pady=5, sticky="w")
    
    def _seleccionar_cliente(self, cliente):
        self.cliente_seleccionado = cliente
        messagebox.showinfo("Seleccionado", f"✅ Cliente seleccionado:\n{cliente.nombre} (DNI: {cliente.dni_cuil})")
    
    def _limpiar_filtros(self):
        self.entry_buscar.delete(0, 'end')
        self._cargar_clientes()
    
    # =====================================================================
    # CRUD DE CLIENTES CON VALIDACIONES
    # =====================================================================
    def _abrir_formulario_alta(self):
        self._formulario_cliente()
    
    def _abrir_formulario_edicion(self):
        if not self.cliente_seleccionado:
            messagebox.showwarning("Aviso", "Primero seleccione un cliente de la tabla.")
            return
        self._formulario_cliente(editar=True)
    
    def _formulario_cliente(self, editar=False):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Editar Cliente" if editar else "Nuevo Cliente")
        dialog.geometry("450x550")
        dialog.configure(fg_color="#F9FAFB")
        dialog.resizable(False, False)
        
        dialog.transient(self.winfo_toplevel())
        dialog.lift()
        dialog.focus_force()
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 225
        y = (dialog.winfo_screenheight() // 2) - 275
        dialog.geometry(f"450x550+{x}+{y}")
        
        frame = ctk.CTkFrame(dialog, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        titulo = "✏️ Editar Cliente" if editar else "➕ Nuevo Cliente"
        ctk.CTkLabel(frame, text=titulo, font=("Roboto", 20, "bold"), text_color="#1D4ED8"
        ).pack(pady=(0, 20))
        
        campos = [
            ("DNI/CUIL", "dni_cuil", True),
            ("Nombre Completo", "nombre", True),
            ("Teléfono", "telefono", False),
            ("Email", "email", False),
        ]
        
        entradas = {}
        for etiqueta, clave, obligatorio in campos:
            ctk.CTkLabel(frame, text=f"{etiqueta}:", font=("Roboto", 13, "bold")
            ).pack(anchor="w", pady=(10, 5))
            entrada = ctk.CTkEntry(frame, font=("Roboto", 13), height=35,
                                  fg_color="#D6DBE3", text_color="#1A2233")
            entrada.pack(fill="x", padx=0, pady=(0, 5))
            if editar and hasattr(self.cliente_seleccionado, clave):
                valor = getattr(self.cliente_seleccionado, clave, "")
                entrada.insert(0, str(valor) if valor else "")
            entradas[clave] = entrada
        
        # Botones
        frame_botones = ctk.CTkFrame(frame, fg_color="transparent")
        frame_botones.pack(fill="x", pady=20)
        
        def guardar():
            try:
                datos = {}
                errores = []
                
                for clave, entrada in entradas.items():
                    valor = entrada.get().strip()
                    
                    if clave == "dni_cuil":
                        if not valor:
                            errores.append("El DNI/CUIL es obligatorio.")
                            continue
                        if not valor.isdigit():
                            errores.append("El DNI/CUIL debe contener solo dígitos.")
                            continue
                        if len(valor) < 7 or len(valor) > 13:
                            errores.append("El DNI/CUIL debe tener entre 7 y 13 dígitos.")
                            continue
                        if not editar:
                            existente = Cliente.buscar_por_dni(valor)
                            if existente:
                                errores.append(f"Ya existe un cliente con DNI {valor}.")
                                continue
                        datos[clave] = valor
                        
                    elif clave == "nombre":
                        if not valor:
                            errores.append("El nombre es obligatorio.")
                            continue
                        if len(valor) < 2:
                            errores.append("El nombre debe tener al menos 2 caracteres.")
                            continue
                        datos[clave] = valor
                        
                    elif clave == "telefono":
                        if valor and not valor.replace("-", "").replace(" ", "").isdigit():
                            errores.append("El teléfono debe ser numérico (permite guiones y espacios).")
                            continue
                        datos[clave] = valor
                        
                    elif clave == "email":
                        if valor and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', valor):
                            errores.append("Formato de email inválido.")
                            continue
                        datos[clave] = valor
                
                if errores:
                    messagebox.showerror("Errores de Validación", "\n".join(errores))
                    return
                
                if editar:
                    for clave, valor in datos.items():
                        setattr(self.cliente_seleccionado, clave, valor)
                    if self.cliente_seleccionado.guardar():
                        messagebox.showinfo("Éxito", "✅ Cliente actualizado correctamente.")
                        dialog.destroy()
                        self._cargar_clientes()
                    else:
                        messagebox.showerror("Error", "❌ No se pudo actualizar el cliente.\nVerifique que los datos sean correctos.")
                else:
                    nuevo = Cliente(
                        dni_cuil=datos['dni_cuil'],
                        nombre=datos['nombre'],
                        telefono=datos.get('telefono', ''),
                        email=datos.get('email', '')
                    )
                    if nuevo.guardar():
                        messagebox.showinfo("Éxito", "✅ Cliente creado correctamente.")
                        dialog.destroy()
                        self._cargar_clientes()
                    else:
                        messagebox.showerror("Error", "❌ No se pudo crear el cliente.\nVerifique que el DNI no esté duplicado.")
                
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
    
    def _eliminar_cliente(self):
        if not self.cliente_seleccionado:
            messagebox.showwarning("Aviso", "Primero seleccione un cliente.")
            return
        if self.cliente_seleccionado.estado == 'Inactivo':
            messagebox.showinfo("Aviso", "ℹ️ El cliente ya está inactivo.")
            return
        if messagebox.askyesno("Confirmar", f"¿Desactivar a '{self.cliente_seleccionado.nombre}'?"):
            if self.cliente_seleccionado.cambiar_estado('Inactivo', self.usuario_actual):
                messagebox.showinfo("Éxito", "✅ Cliente dado de baja.")
                self.cliente_seleccionado = None
                self._cargar_clientes()
            else:
                messagebox.showerror("Error", "❌ No se pudo desactivar el cliente.")
    
    def _ver_historial(self):
        if not self.cliente_seleccionado:
            messagebox.showwarning("Aviso", "Primero seleccione un cliente.")
            return
        
        historial = self.cliente_seleccionado.obtener_historial_compras()
        if not historial:
            messagebox.showinfo("Historial", f"{self.cliente_seleccionado.nombre} no tiene compras registradas.")
            return
        
        ventana = ctk.CTkToplevel(self)
        ventana.title(f"Historial de Compras - {self.cliente_seleccionado.nombre}")
        ventana.geometry("800x500")
        ventana.configure(fg_color="#F4F6F9")
        
        frame = ctk.CTkFrame(ventana, fg_color="#F9FAFB", corner_radius=15, border_width=1, border_color="#B8C1CE")
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(frame, text=f"📜 Historial de {self.cliente_seleccionado.nombre}", 
                    font=("Roboto", 20, "bold"), text_color="#1D4ED8"
        ).pack(pady=(20, 10))
        
        ctk.CTkLabel(frame, text=f"Puntos acumulados: {self.cliente_seleccionado.puntos_acumulados}", 
                    font=("Roboto", 14), text_color="#C2410C"
        ).pack(pady=(0, 20))
        
        frame_tabla = ctk.CTkScrollableFrame(frame, fg_color="#F4F6F9", corner_radius=10)
        frame_tabla.pack(fill="both", expand=True, padx=20, pady=10)
        
        encabezados = ["Ticket", "Fecha", "Total", "Puntos"]
        for i, texto in enumerate(encabezados):
            ctk.CTkLabel(frame_tabla, text=texto, font=("Roboto", 14, "bold"),
                        text_color="#6B7280").grid(row=0, column=i, padx=10, pady=5, sticky="w")
        
        for i, compra in enumerate(historial, start=1):
            ctk.CTkLabel(frame_tabla, text=compra['nro_ticket'], font=("Roboto", 13)
            ).grid(row=i, column=0, padx=10, pady=5, sticky="w")
            ctk.CTkLabel(frame_tabla, text=compra['fecha_hora'], font=("Roboto", 13)
            ).grid(row=i, column=1, padx=10, pady=5, sticky="w")
            ctk.CTkLabel(frame_tabla, text=f"${compra['total_facturado']:.2f}", font=("Roboto", 13)
            ).grid(row=i, column=2, padx=10, pady=5, sticky="e")
            ctk.CTkLabel(frame_tabla, text=str(compra['puntos_sumados']), font=("Roboto", 13)
            ).grid(row=i, column=3, padx=10, pady=5, sticky="e")