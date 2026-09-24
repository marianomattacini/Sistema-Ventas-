import customtkinter as ctk
from tkinter import messagebox
from models.usuario import Usuario
from models.notificacion import Notificacion
from database.config import get_sqlite_connection
from views.base_frame import BaseFrame
import bcrypt

class FrameUsuarios(BaseFrame):
    """
    Pantalla de gestión de usuarios (CRUD).
    Solo accesible para Administradores y Gerentes Generales.
    """

    def __init__(self, parent, controller, usuario_actual, **kwargs):
        super().__init__(parent, controller, usuario_actual)
        
        # Verificar permisos
        if not self.usuario_actual.tiene_permiso('gestionar_usuarios'):
            messagebox.showerror("Acceso Denegado", 
                                "No tiene permisos para gestionar usuarios.\nSe notificará al Gerente General.")
            Notificacion.crear_notificacion_seguridad(
                1,
                f"Intento de acceso no autorizado a Gestión de Usuarios por '{self.usuario_actual.nombre_usuario}'"
            )
            self.controller.volver()
            return
        
        # Configuración de la pantalla
        self.configure(fg_color="#F4F6F9")
        
        # Estado
        self.usuario_seleccionado = None
        
        # Crear widgets
        self._crear_widgets()
        self._cargar_usuarios()
    
    def _crear_widgets(self):
        # Frame principal
        frame_principal = ctk.CTkFrame(self, fg_color="#F9FAFB", corner_radius=15, border_width=1, border_color="#B8C1CE")
        frame_principal.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Barra superior
        barra = ctk.CTkFrame(frame_principal, fg_color="transparent")
        barra.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(barra, text="👥 GESTIÓN DE USUARIOS", 
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
        
        self.entry_buscar = ctk.CTkEntry(panel_busqueda, placeholder_text="Nombre de usuario...",
                                        width=250, height=35, font=("Roboto", 13))
        self.entry_buscar.pack(side="left", padx=10, pady=10)
        self.entry_buscar.bind("<Return>", lambda e: self._cargar_usuarios())
        
        btn_buscar = ctk.CTkButton(panel_busqueda, text="Buscar", height=35,
                                  fg_color="#2563EB", hover_color="#2563EB",
                                  corner_radius=10, command=self._cargar_usuarios, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_buscar.pack(side="left", padx=5, pady=10)
        
        btn_limpiar = ctk.CTkButton(panel_busqueda, text="Limpiar", height=35,
                                   fg_color="#64748B", hover_color="#D6DBE3",
                                   corner_radius=10, command=self._limpiar_filtros, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_limpiar.pack(side="left", padx=5, pady=10)
        
        # Tabla de usuarios
        self.frame_tabla = ctk.CTkScrollableFrame(frame_principal, fg_color="#F4F6F9", corner_radius=10)
        self.frame_tabla.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Encabezados
        encabezados = ["ID", "Usuario", "Rol", "Estado", "Último Login", "Acciones"]
        for i, texto in enumerate(encabezados):
            ctk.CTkLabel(self.frame_tabla, text=texto, font=("Roboto", 14, "bold"),
                        text_color="#6B7280").grid(row=0, column=i, padx=10, pady=5, sticky="w")
        
        # Panel de botones
        panel_botones = ctk.CTkFrame(frame_principal, fg_color="#F4F6F9", corner_radius=10, border_width=1, border_color="#B8C1CE")
        panel_botones.pack(fill="x", padx=20, pady=(10, 20))
        
        btn_agregar = ctk.CTkButton(panel_botones, text="➕ Agregar Usuario", height=40,
                                   fg_color="#15803D", hover_color="#166534",
                                   corner_radius=10, command=self._abrir_formulario_alta, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_agregar.pack(side="left", padx=10)
        
        btn_editar = ctk.CTkButton(panel_botones, text="✏️ Editar", height=40,
                                  fg_color="#2563EB", hover_color="#1D4ED8",
                                  corner_radius=10, command=self._abrir_formulario_edicion, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_editar.pack(side="left", padx=10)
        
        btn_reset_pin = ctk.CTkButton(panel_botones, text="🔑 Resetear PIN", height=40,
                                     fg_color="#C2410C", hover_color="#9A3412",
                                     corner_radius=10, command=self._resetear_pin, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_reset_pin.pack(side="left", padx=10)
        
        btn_estado = ctk.CTkButton(panel_botones, text="🔄 Cambiar Estado", height=40,
                                  fg_color="#7C3AED", hover_color="#6D28D9",
                                  corner_radius=10, command=self._cambiar_estado, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_estado.pack(side="left", padx=10)
        
        ctk.CTkLabel(panel_botones, text="Seleccione un usuario para editar", 
                    font=("Roboto", 12), text_color="#8B93A3"
        ).pack(side="right", padx=20)
    
    def _cargar_usuarios(self, filtro=None):
        for widget in self.frame_tabla.winfo_children():
            if widget.grid_info() != {}:
                widget.destroy()
        
        termino = self.entry_buscar.get().strip()
        usuarios = Usuario.obtener_todos()
        
        if termino:
            usuarios = [u for u in usuarios if termino.lower() in u.nombre_usuario.lower()]
        
        if not usuarios:
            ctk.CTkLabel(self.frame_tabla, text="No hay usuarios para mostrar", 
                        font=("Roboto", 14), text_color="#8B93A3"
            ).grid(row=1, column=0, columnspan=6, padx=10, pady=20)
            return
        
        for i, usuario in enumerate(usuarios, start=1):
            ctk.CTkLabel(self.frame_tabla, text=str(usuario.id), 
                        font=("Roboto", 13)).grid(row=i, column=0, padx=10, pady=5, sticky="w")
            ctk.CTkLabel(self.frame_tabla, text=usuario.nombre_usuario, 
                        font=("Roboto", 13)).grid(row=i, column=1, padx=10, pady=5, sticky="w")
            ctk.CTkLabel(self.frame_tabla, text=usuario.rol, 
                        font=("Roboto", 13)).grid(row=i, column=2, padx=10, pady=5, sticky="w")
            
            estado = usuario.estado
            color = {"Activo": "#15803D", "Inactivo": "#DC2626", "Bloqueado": "#C2410C"}.get(estado, "#8B93A3")
            ctk.CTkLabel(self.frame_tabla, text=estado, 
                        font=("Roboto", 13, "bold"), text_color=color
            ).grid(row=i, column=3, padx=10, pady=5, sticky="w")
            
            ultimo = usuario.ultimo_login or "-"
            ctk.CTkLabel(self.frame_tabla, text=ultimo, 
                        font=("Roboto", 13)).grid(row=i, column=4, padx=10, pady=5, sticky="w")
            
            btn_selector = ctk.CTkButton(self.frame_tabla, text="Seleccionar", width=80, height=25,
                                        fg_color="#D6DBE3", hover_color="#64748B",
                                        corner_radius=5, command=lambda u=usuario: self._seleccionar_usuario(u), border_width=1, border_color="#CBD2DC", text_color="#1A2233")
            btn_selector.grid(row=i, column=5, padx=10, pady=5)
    
    def _seleccionar_usuario(self, usuario):
        self.usuario_seleccionado = usuario
        messagebox.showinfo("Seleccionado", f"✅ Usuario seleccionado:\n{usuario.nombre_usuario} ({usuario.rol})")
    
    def _limpiar_filtros(self):
        self.entry_buscar.delete(0, 'end')
        self._cargar_usuarios()
    
    # =====================================================================
    # FORMULARIOS DE ALTA Y EDICIÓN
    # =====================================================================
    def _abrir_formulario_alta(self):
        self._formulario_usuario()
    
    def _abrir_formulario_edicion(self):
        if not self.usuario_seleccionado:
            messagebox.showwarning("Aviso", "Primero seleccione un usuario de la tabla.")
            return
        self._formulario_usuario(editar=True)
    
    def _formulario_usuario(self, editar=False):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Editar Usuario" if editar else "Nuevo Usuario")
        dialog.geometry("450x600")
        dialog.configure(fg_color="#F9FAFB")
        dialog.resizable(False, False)
        
        dialog.transient(self.winfo_toplevel())
        dialog.lift()
        dialog.focus_force()
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 225
        y = (dialog.winfo_screenheight() // 2) - 300
        dialog.geometry(f"450x600+{x}+{y}")
        
        frame = ctk.CTkFrame(dialog, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        titulo = "✏️ Editar Usuario" if editar else "➕ Nuevo Usuario"
        ctk.CTkLabel(frame, text=titulo, font=("Roboto", 20, "bold"), text_color="#1D4ED8"
        ).pack(pady=(0, 20))
        
        campos = [
            ("Nombre de Usuario", "nombre_usuario"),
            ("PIN (mínimo 4 dígitos)", "pin"),
            ("Confirmar PIN", "pin_confirm"),
            ("Rol", "rol"),
        ]
        
        entradas = {}
        for etiqueta, clave in campos:
            ctk.CTkLabel(frame, text=f"{etiqueta}:", font=("Roboto", 13, "bold")
            ).pack(anchor="w", pady=(10, 5))
            
            if clave == "rol":
                entrada = ctk.CTkOptionMenu(frame, values=["Cajero", "Supervisor", "Administrador", "Gerente General"],
                                           font=("Roboto", 13), fg_color="#D6DBE3", text_color="#1A2233",
                                           button_color="#2563EB", corner_radius=10)
                entrada.pack(fill="x", padx=0, pady=(0, 5))
                if editar and hasattr(self.usuario_seleccionado, 'rol'):
                    entrada.set(self.usuario_seleccionado.rol)
                else:
                    entrada.set("Cajero")
            else:
                entrada = ctk.CTkEntry(frame, font=("Roboto", 13), height=35,
                                      fg_color="#D6DBE3", text_color="#1A2233")
                if clave in ["pin", "pin_confirm"]:
                    entrada.configure(show="*")
                entrada.pack(fill="x", padx=0, pady=(0, 5))
                if editar and clave == "nombre_usuario" and self.usuario_seleccionado:
                    entrada.insert(0, self.usuario_seleccionado.nombre_usuario)
            entradas[clave] = entrada
        
        # Botones
        frame_botones = ctk.CTkFrame(frame, fg_color="transparent")
        frame_botones.pack(fill="x", pady=20)
        
        def validar_nombre_usuario(nombre, editar=False, usuario_actual=None):
            if not nombre:
                return False, "El nombre de usuario es obligatorio."
            if len(nombre) < 3:
                return False, "El nombre de usuario debe tener al menos 3 caracteres."
            try:
                conn = get_sqlite_connection()
                cursor = conn.cursor()
                if editar and usuario_actual:
                    cursor.execute("SELECT id FROM usuarios WHERE nombre_usuario = ? AND id != ?", (nombre, usuario_actual.id))
                else:
                    cursor.execute("SELECT id FROM usuarios WHERE nombre_usuario = ?", (nombre,))
                existe = cursor.fetchone()
                conn.close()
                if existe:
                    return False, f"El nombre de usuario '{nombre}' ya está en uso."
            except Exception as e:
                return False, f"Error al verificar nombre de usuario: {e}"
            return True, ""
        
        def guardar():
            try:
                nombre = entradas['nombre_usuario'].get().strip()
                pin = entradas['pin'].get().strip()
                pin_confirm = entradas['pin_confirm'].get().strip()
                rol = entradas['rol'].get()
                
                valido, msg = validar_nombre_usuario(nombre, editar, self.usuario_seleccionado if editar else None)
                if not valido:
                    messagebox.showerror("Error", msg)
                    return
                
                if editar:
                    usuario = self.usuario_seleccionado
                    if pin:
                        if len(pin) < 4:
                            messagebox.showerror("Error", "El PIN debe tener al menos 4 dígitos.")
                            return
                        if not pin.isdigit():
                            messagebox.showerror("Error", "El PIN debe contener solo dígitos.")
                            return
                        if pin != pin_confirm:
                            messagebox.showerror("Error", "Los PINs no coinciden.")
                            return
                        usuario.pin_hash = Usuario._hash_pin(pin)
                    usuario.nombre_usuario = nombre
                    usuario.rol = rol
                    if usuario.guardar():
                        messagebox.showinfo("Éxito", "✅ Usuario actualizado correctamente.")
                        dialog.destroy()
                        self._cargar_usuarios()
                    else:
                        messagebox.showerror("Error", "❌ No se pudo actualizar el usuario.\nVerifique que los datos sean correctos.")
                else:
                    if not pin:
                        messagebox.showerror("Error", "El PIN es obligatorio para nuevos usuarios.")
                        return
                    if len(pin) < 4:
                        messagebox.showerror("Error", "El PIN debe tener al menos 4 dígitos.")
                        return
                    if not pin.isdigit():
                        messagebox.showerror("Error", "El PIN debe contener solo dígitos.")
                        return
                    if pin != pin_confirm:
                        messagebox.showerror("Error", "Los PINs no coinciden.")
                        return
                    
                    nuevo = Usuario(
                        nombre_usuario=nombre,
                        pin_plano=pin,
                        rol=rol,
                        estado="Activo"
                    )
                    if nuevo.guardar():
                        messagebox.showinfo("Éxito", f"✅ Usuario {nombre} creado correctamente con PIN {pin}.")
                        dialog.destroy()
                        self._cargar_usuarios()
                    else:
                        messagebox.showerror("Error", "❌ No se pudo crear el usuario.\nVerifique que el nombre no esté duplicado.")
                
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
    
    # =====================================================================
    # ACCIONES SOBRE USUARIOS
    # =====================================================================
    def _resetear_pin(self):
        if not self.usuario_seleccionado:
            messagebox.showwarning("Aviso", "Primero seleccione un usuario.")
            return
        
        if self.usuario_actual.rol != "Gerente General":
            messagebox.showerror("Acceso Denegado", "Solo el Gerente General puede resetear PINs.")
            return
        
        nuevo_pin = ctk.CTkInputDialog(
            text=f"Ingrese el nuevo PIN para {self.usuario_seleccionado.nombre_usuario} (4 dígitos numéricos):",
            title="Resetear PIN",
            show="*"
        ).get_input()
        
        if not nuevo_pin:
            return
        
        if len(nuevo_pin) < 4:
            messagebox.showerror("Error", "El PIN debe tener al menos 4 dígitos.")
            return
        if not nuevo_pin.isdigit():
            messagebox.showerror("Error", "El PIN debe contener solo dígitos.")
            return
        
        if messagebox.askyesno("Confirmar", f"¿Resetear PIN de '{self.usuario_seleccionado.nombre_usuario}'?"):
            self.usuario_seleccionado.pin_hash = Usuario._hash_pin(nuevo_pin)
            if self.usuario_seleccionado.guardar():
                messagebox.showinfo("Éxito", f"✅ PIN de {self.usuario_seleccionado.nombre_usuario} reseteado a '{nuevo_pin}'.")
                self._cargar_usuarios()
            else:
                messagebox.showerror("Error", "❌ No se pudo resetear el PIN.")
    
    def _cambiar_estado(self):
        if not self.usuario_seleccionado:
            messagebox.showwarning("Aviso", "Primero seleccione un usuario.")
            return
        
        if self.usuario_seleccionado.id == self.usuario_actual.id:
            messagebox.showerror("Error", "No puede cambiar su propio estado.")
            return
        
        estado_actual = self.usuario_seleccionado.estado
        opciones = ["Activo", "Inactivo", "Bloqueado"]
        opciones.remove(estado_actual)
        
        dialog = ctk.CTkToplevel(self)
        dialog.title("Cambiar Estado")
        dialog.geometry("350x280")
        dialog.configure(fg_color="#F9FAFB")
        dialog.resizable(False, False)
        
        dialog.transient(self.winfo_toplevel())
        dialog.lift()
        dialog.focus_force()
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 175
        y = (dialog.winfo_screenheight() // 2) - 140
        dialog.geometry(f"350x280+{x}+{y}")
        
        frame = ctk.CTkFrame(dialog, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(frame, text=f"Usuario: {self.usuario_seleccionado.nombre_usuario}", 
                    font=("Roboto", 16, "bold"), text_color="#1D4ED8"
        ).pack(pady=(0, 10))
        
        ctk.CTkLabel(frame, text=f"Estado actual: {estado_actual}", 
                    font=("Roboto", 14), text_color="#6B7280"
        ).pack(pady=(0, 20))
        
        ctk.CTkLabel(frame, text="Seleccione nuevo estado:", font=("Roboto", 13, "bold")
        ).pack(anchor="w", pady=(10, 5))
        
        combo_estado = ctk.CTkOptionMenu(frame, values=opciones,
                                        font=("Roboto", 13), fg_color="#D6DBE3",
                                        text_color="#1A2233", button_color="#2563EB",
                                        corner_radius=10)
        combo_estado.pack(fill="x", pady=(0, 20))
        combo_estado.set(opciones[0])
        
        def confirmar():
            nuevo_estado = combo_estado.get()
            if self.usuario_seleccionado.cambiar_estado(nuevo_estado, self.usuario_actual):
                messagebox.showinfo("Éxito", f"✅ Estado cambiado a '{nuevo_estado}'.")
                dialog.destroy()
                self._cargar_usuarios()
            else:
                messagebox.showerror("Error", "❌ No se pudo cambiar el estado.")
        
        btn_guardar = ctk.CTkButton(frame, text="Confirmar", height=40,
                                   fg_color="#15803D", hover_color="#166534",
                                   corner_radius=10, command=confirmar, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_guardar.pack(fill="x", pady=(10, 5))
        
        btn_cancelar = ctk.CTkButton(frame, text="Cancelar", height=40,
                                    fg_color="#64748B", hover_color="#D6DBE3",
                                    corner_radius=10, command=dialog.destroy, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_cancelar.pack(fill="x", pady=5)