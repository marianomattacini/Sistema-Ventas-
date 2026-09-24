import customtkinter as ctk
from tkinter import messagebox
from models.proveedor import Proveedor
from models.notificacion import Notificacion
from views.base_frame import BaseFrame
import re

class FrameProveedores(BaseFrame):
    """
    Pantalla de gestión de proveedores (CRUD).
    Solo accesible para Administradores y Gerentes Generales.
    """

    def __init__(self, parent, controller, usuario_actual, **kwargs):
        super().__init__(parent, controller, usuario_actual)
        
        # Verificar permisos
        if not self.usuario_actual.tiene_permiso('gestionar_proveedores'):
            messagebox.showerror("Acceso Denegado", 
                                "No tiene permisos para gestionar proveedores.\nSe notificará al Gerente General.")
            Notificacion.crear_notificacion_seguridad(
                1,
                f"Intento de acceso no autorizado a Gestión de Proveedores por '{self.usuario_actual.nombre_usuario}'"
            )
            self.controller.volver()
            return
        
        # Configuración de la pantalla
        self.configure(fg_color="#F4F6F9")
        
        # Estado
        self.proveedor_seleccionado = None
        
        # Crear widgets
        self._crear_widgets()
        self._cargar_proveedores()
    
    def _crear_widgets(self):
        # Frame principal
        frame_principal = ctk.CTkFrame(self, fg_color="#F9FAFB", corner_radius=15, border_width=1, border_color="#B8C1CE")
        frame_principal.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Barra superior
        barra = ctk.CTkFrame(frame_principal, fg_color="transparent")
        barra.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(barra, text="🏢 GESTIÓN DE PROVEEDORES", 
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
        
        self.entry_buscar = ctk.CTkEntry(panel_busqueda, placeholder_text="CUIT, razón social o teléfono...",
                                        width=300, height=35, font=("Roboto", 13))
        self.entry_buscar.pack(side="left", padx=10, pady=10)
        self.entry_buscar.bind("<Return>", lambda e: self._cargar_proveedores())
        
        btn_buscar = ctk.CTkButton(panel_busqueda, text="Buscar", height=35,
                                  fg_color="#2563EB", hover_color="#2563EB",
                                  corner_radius=10, command=self._cargar_proveedores, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_buscar.pack(side="left", padx=5, pady=10)
        
        btn_limpiar = ctk.CTkButton(panel_busqueda, text="Limpiar", height=35,
                                   fg_color="#64748B", hover_color="#D6DBE3",
                                   corner_radius=10, command=self._limpiar_filtros, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_limpiar.pack(side="left", padx=5, pady=10)
        
        # Tabla de proveedores
        self.frame_tabla = ctk.CTkScrollableFrame(frame_principal, fg_color="#F4F6F9", corner_radius=10)
        self.frame_tabla.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Encabezados
        encabezados = ["Seleccionar", "CUIT", "Razón Social", "Teléfono", "Email", "Estado"]
        for i, texto in enumerate(encabezados):
            ctk.CTkLabel(self.frame_tabla, text=texto, font=("Roboto", 14, "bold"),
                        text_color="#6B7280").grid(row=0, column=i, padx=10, pady=5, sticky="w")
        
        # Panel de botones
        panel_botones = ctk.CTkFrame(frame_principal, fg_color="#F4F6F9", corner_radius=10, border_width=1, border_color="#B8C1CE")
        panel_botones.pack(fill="x", padx=20, pady=(10, 20))
        
        btn_agregar = ctk.CTkButton(panel_botones, text="➕ Agregar Proveedor", height=40,
                                   fg_color="#15803D", hover_color="#166534",
                                   corner_radius=10, command=self._abrir_formulario_alta, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_agregar.pack(side="left", padx=10)
        
        btn_editar = ctk.CTkButton(panel_botones, text="✏️ Editar", height=40,
                                  fg_color="#2563EB", hover_color="#1D4ED8",
                                  corner_radius=10, command=self._abrir_formulario_edicion, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_editar.pack(side="left", padx=10)
        
        btn_eliminar = ctk.CTkButton(panel_botones, text="🗑️ Dar de Baja", height=40,
                                    fg_color="#DC2626", hover_color="#B91C1C",
                                    corner_radius=10, command=self._eliminar_proveedor, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_eliminar.pack(side="left", padx=10)
        
        btn_reactivar = ctk.CTkButton(panel_botones, text="🔄 Reactivar", height=40,
                                     fg_color="#7C3AED", hover_color="#6D28D9",
                                     corner_radius=10, command=self._reactivar_proveedor, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_reactivar.pack(side="left", padx=10)
        
        ctk.CTkLabel(panel_botones, text="Seleccione un proveedor para editar", 
                    font=("Roboto", 12), text_color="#8B93A3"
        ).pack(side="right", padx=20)
    
    def _cargar_proveedores(self):
        """Carga los proveedores según el filtro."""
        for widget in self.frame_tabla.winfo_children():
            if widget.grid_info() != {}:
                widget.destroy()
        
        termino = self.entry_buscar.get().strip()
        if termino:
            proveedor = Proveedor.buscar_por_cuit(termino)
            if proveedor:
                proveedores = [proveedor]
            else:
                proveedores = Proveedor.buscar_por_razon_social(termino)
        else:
            proveedores = Proveedor.obtener_todos(estado=None)
        
        if not proveedores:
            ctk.CTkLabel(self.frame_tabla, text="No hay proveedores para mostrar", 
                        font=("Roboto", 14), text_color="#8B93A3"
            ).grid(row=1, column=0, columnspan=6, padx=10, pady=20)
            return
        
        for i, proveedor in enumerate(proveedores, start=1):
            btn_selector = ctk.CTkButton(self.frame_tabla, text="Seleccionar", width=80, height=25,
                                        fg_color="#D6DBE3", hover_color="#64748B",
                                        corner_radius=5, command=lambda p=proveedor: self._seleccionar_proveedor(p), border_width=1, border_color="#CBD2DC", text_color="#1A2233")
            btn_selector.grid(row=i, column=0, padx=10, pady=5)
            
            ctk.CTkLabel(self.frame_tabla, text=proveedor.cuit, 
                        font=("Roboto", 13)).grid(row=i, column=1, padx=10, pady=5, sticky="w")
            ctk.CTkLabel(self.frame_tabla, text=proveedor.razon_social, 
                        font=("Roboto", 13)).grid(row=i, column=2, padx=10, pady=5, sticky="w")
            ctk.CTkLabel(self.frame_tabla, text=proveedor.telefono or "-", 
                        font=("Roboto", 13)).grid(row=i, column=3, padx=10, pady=5, sticky="w")
            ctk.CTkLabel(self.frame_tabla, text=proveedor.email or "-", 
                        font=("Roboto", 13)).grid(row=i, column=4, padx=10, pady=5, sticky="w")
            estado = "🟢 Activo" if proveedor.estado == 'Activo' else "🔴 Inactivo"
            ctk.CTkLabel(self.frame_tabla, text=estado, font=("Roboto", 13)
            ).grid(row=i, column=5, padx=10, pady=5, sticky="w")
    
    def _seleccionar_proveedor(self, proveedor):
        self.proveedor_seleccionado = proveedor
        messagebox.showinfo("Seleccionado", f"✅ Proveedor seleccionado:\n{proveedor.razon_social} (CUIT: {proveedor.cuit})")
    
    def _limpiar_filtros(self):
        self.entry_buscar.delete(0, 'end')
        self._cargar_proveedores()
    
    # =====================================================================
    # CRUD DE PROVEEDORES CON VALIDACIONES
    # =====================================================================
    def _abrir_formulario_alta(self):
        self._formulario_proveedor()
    
    def _abrir_formulario_edicion(self):
        if not self.proveedor_seleccionado:
            messagebox.showwarning("Aviso", "Primero seleccione un proveedor de la tabla.")
            return
        self._formulario_proveedor(editar=True)
    
    def _formulario_proveedor(self, editar=False):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Editar Proveedor" if editar else "Nuevo Proveedor")
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
        
        titulo = "✏️ Editar Proveedor" if editar else "➕ Nuevo Proveedor"
        ctk.CTkLabel(frame, text=titulo, font=("Roboto", 20, "bold"), text_color="#1D4ED8"
        ).pack(pady=(0, 20))
        
        campos = [
            ("CUIT", "cuit", True),
            ("Razón Social", "razon_social", True),
            ("Teléfono", "telefono", True),
            ("Email", "email", True),
        ]
        
        entradas = {}
        for etiqueta, clave, obligatorio in campos:
            ctk.CTkLabel(frame, text=f"{etiqueta}:", font=("Roboto", 13, "bold")
            ).pack(anchor="w", pady=(10, 5))
            entrada = ctk.CTkEntry(frame, font=("Roboto", 13), height=35,
                                  fg_color="#D6DBE3", text_color="#1A2233")
            entrada.pack(fill="x", padx=0, pady=(0, 5))
            if editar and hasattr(self.proveedor_seleccionado, clave):
                valor = getattr(self.proveedor_seleccionado, clave, "")
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
                    if not valor:
                        errores.append(f"El campo '{clave}' es obligatorio.")
                        continue
                    
                    if clave == "cuit":
                        if not valor.isdigit():
                            errores.append("El CUIT debe contener solo dígitos.")
                            continue
                        if len(valor) < 11 or len(valor) > 13:
                            errores.append("El CUIT debe tener entre 11 y 13 dígitos.")
                            continue
                        # Verificar duplicado en alta
                        if not editar:
                            existente = Proveedor.buscar_por_cuit(valor)
                            if existente:
                                errores.append(f"Ya existe un proveedor con CUIT {valor}.")
                                continue
                        datos[clave] = valor
                    elif clave == "telefono":
                        if not valor.replace("-", "").replace(" ", "").isdigit():
                            errores.append("El teléfono debe ser numérico.")
                            continue
                        datos[clave] = valor
                    elif clave == "email":
                        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', valor):
                            errores.append("Formato de email inválido.")
                            continue
                        datos[clave] = valor
                    else:
                        datos[clave] = valor
                
                if errores:
                    messagebox.showerror("Errores de Validación", "\n".join(errores))
                    return
                
                if editar:
                    for clave, valor in datos.items():
                        setattr(self.proveedor_seleccionado, clave, valor)
                    if self.proveedor_seleccionado.guardar():
                        messagebox.showinfo("Éxito", "✅ Proveedor actualizado correctamente.")
                        dialog.destroy()
                        self._cargar_proveedores()
                    else:
                        messagebox.showerror("Error", "❌ No se pudo actualizar el proveedor.")
                else:
                    nuevo = Proveedor(
                        cuit=datos['cuit'],
                        razon_social=datos['razon_social'],
                        telefono=datos['telefono'],
                        email=datos['email']
                    )
                    if nuevo.guardar():
                        messagebox.showinfo("Éxito", "✅ Proveedor creado correctamente.")
                        dialog.destroy()
                        self._cargar_proveedores()
                    else:
                        messagebox.showerror("Error", "❌ No se pudo crear el proveedor.\nVerifique que los datos sean correctos.")
                
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
    
    def _eliminar_proveedor(self):
        if not self.proveedor_seleccionado:
            messagebox.showwarning("Aviso", "Primero seleccione un proveedor.")
            return
        if self.proveedor_seleccionado.estado == 'Inactivo':
            messagebox.showinfo("Aviso", "ℹ️ El proveedor ya está inactivo.")
            return
        if messagebox.askyesno("Confirmar", f"¿Desactivar a '{self.proveedor_seleccionado.razon_social}'?"):
            if self.proveedor_seleccionado.cambiar_estado('Inactivo'):
                messagebox.showinfo("Éxito", "✅ Proveedor dado de baja.")
                self.proveedor_seleccionado = None
                self._cargar_proveedores()
            else:
                messagebox.showerror("Error", "❌ No se pudo desactivar el proveedor.")
    
    def _reactivar_proveedor(self):
        if not self.proveedor_seleccionado:
            messagebox.showwarning("Aviso", "Primero seleccione un proveedor.")
            return
        if self.proveedor_seleccionado.estado == 'Activo':
            messagebox.showinfo("Aviso", "ℹ️ El proveedor ya está activo.")
            return
        if messagebox.askyesno("Confirmar", f"¿Reactivar a '{self.proveedor_seleccionado.razon_social}'?"):
            if self.proveedor_seleccionado.cambiar_estado('Activo'):
                messagebox.showinfo("Éxito", "✅ Proveedor reactivado.")
                self.proveedor_seleccionado = None
                self._cargar_proveedores()
            else:
                messagebox.showerror("Error", "❌ No se pudo reactivar el proveedor.")