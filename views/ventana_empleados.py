import customtkinter as ctk
from tkinter import messagebox
from models.empleado import Empleado
from models.rol import Rol
from models.notificacion import Notificacion
from views.base_frame import BaseFrame
import json

class FrameEmpleados(BaseFrame):
    def __init__(self, parent, controller, usuario_actual, empleado=None, **kwargs):
        super().__init__(parent, controller, usuario_actual)
        self.empleado = empleado

        self.configure(fg_color="#F4F6F9")

        self._crear_widgets()

    def _crear_widgets(self):
        frame_scroll = ctk.CTkScrollableFrame(self, fg_color="#F9FAFB", corner_radius=15)
        frame_scroll.pack(fill="both", expand=True, padx=20, pady=20)

        titulo = "Detalles del Empleado" if self.empleado else "Nuevo Empleado"
        ctk.CTkLabel(frame_scroll, text=titulo, font=("Roboto", 20, "bold"), text_color="#1D4ED8"
        ).pack(pady=(20, 10))

        # --- Campos básicos ---
        campos = [
            ("Nombre Completo", "nombre_completo"),
            ("DNI", "dni"),
            ("Fecha de Ingreso (YYYY-MM-DD)", "fecha_ingreso"),
            ("Salario", "salario"),
            ("Teléfono", "telefono"),
            ("Email", "email"),
        ]
        entradas = {}
        for etiqueta, clave in campos:
            ctk.CTkLabel(frame_scroll, text=f"{etiqueta}:", font=("Roboto", 13, "bold")
            ).pack(anchor="w", padx=40, pady=(10, 5))
            entrada = ctk.CTkEntry(frame_scroll, font=("Roboto", 13), height=35,
                                 fg_color="#D6DBE3", text_color="#1A2233")
            entrada.pack(fill="x", padx=40, pady=(0, 5))
            if self.empleado and hasattr(self.empleado, clave):
                valor = getattr(self.empleado, clave, "")
                entrada.insert(0, str(valor) if valor else "")
            entradas[clave] = entrada

        # --- Rol (OptionMenu con opciones predefinidas + botón crear) ---
        frame_rol = ctk.CTkFrame(frame_scroll, fg_color="transparent")
        frame_rol.pack(fill="x", padx=40, pady=(10, 5))

        ctk.CTkLabel(frame_rol, text="Rol:", font=("Roboto", 13, "bold")
        ).pack(side="left", padx=(0, 10))

        roles = Rol.obtener_todos()
        lista_roles = [r.nombre for r in roles] if roles else ["Cajero", "Supervisor", "Administrador", "Gerente General", "Repositor", "Vendedor"]

        self.combo_rol = ctk.CTkOptionMenu(frame_rol, values=lista_roles,
                                         font=("Roboto", 13), fg_color="#D6DBE3",
                                         text_color="#1A2233", button_color="#2563EB",
                                         corner_radius=10, command=self._actualizar_permisos)
        self.combo_rol.pack(side="left", fill="x", expand=True, padx=(0, 10))

        btn_crear_rol = ctk.CTkButton(frame_rol, text="➕ Crear Rol", height=30,
                                    fg_color="#7C3AED", hover_color="#6D28D9",
                                    corner_radius=10, command=self._crear_nuevo_rol, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_crear_rol.pack(side="left")

        if self.empleado and self.empleado.rol:
            self.combo_rol.set(self.empleado.rol)
        else:
            self.combo_rol.set(lista_roles[0] if lista_roles else "Cajero")

        # --- Permisos (checkboxes) ---
        self.frame_permisos = ctk.CTkFrame(frame_scroll, fg_color="#F4F6F9", corner_radius=10, border_width=1, border_color="#B8C1CE")
        self.frame_permisos.pack(fill="x", padx=40, pady=(10, 20))

        ctk.CTkLabel(self.frame_permisos, text="Permisos asociados al rol:", font=("Roboto", 14, "bold"),
                    text_color="#1D4ED8").pack(anchor="w", pady=(10, 5))

        self.check_permisos = {}
        self._actualizar_permisos(self.combo_rol.get())

        # --- Licencias ---
        if self.empleado:
            ctk.CTkLabel(frame_scroll, text="Licencias", font=("Roboto", 16, "bold"), text_color="#1D4ED8"
            ).pack(pady=(20, 10))
            self.frame_licencias = ctk.CTkScrollableFrame(frame_scroll, fg_color="#F4F6F9", corner_radius=10)
            self.frame_licencias.pack(fill="both", expand=True, padx=40, pady=10)
            self._cargar_licencias()

        # --- Botones Guardar/Cancelar ---
        frame_botones = ctk.CTkFrame(frame_scroll, fg_color="transparent")
        frame_botones.pack(fill="x", pady=20)

        def guardar():
            try:
                datos = {}
                for clave, entrada in entradas.items():
                    valor = entrada.get().strip()
                    if not valor and clave in ['nombre_completo', 'dni', 'fecha_ingreso']:
                        raise ValueError(f"El campo {clave} es obligatorio.")
                    datos[clave] = valor

                datos['rol'] = self.combo_rol.get()

                if self.empleado:
                    for clave, valor in datos.items():
                        setattr(self.empleado, clave, valor)
                    if self.empleado.guardar():
                        messagebox.showinfo("Éxito", "Empleado actualizado correctamente.")
                        self.controller.volver()
                    else:
                        messagebox.showerror("Error", "No se pudo actualizar (DNI duplicado).")
                else:
                    nuevo = Empleado(
                        nombre_completo=datos['nombre_completo'],
                        dni=datos['dni'],
                        fecha_ingreso=datos['fecha_ingreso'],
                        rol=datos['rol'],
                        salario=float(datos.get('salario', 0)),
                        telefono=datos.get('telefono', ''),
                        email=datos.get('email', '')
                    )
                    if nuevo.guardar():
                        messagebox.showinfo("Éxito", "Empleado creado correctamente.")
                        self.controller.volver()
                    else:
                        messagebox.showerror("Error", "No se pudo crear (DNI duplicado).")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        btn_guardar = ctk.CTkButton(frame_botones, text="💾 Guardar", height=40,
                                  fg_color="#15803D", hover_color="#166534",
                                  corner_radius=10, command=guardar, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_guardar.pack(side="left", fill="x", expand=True, padx=5)

        btn_cancelar = ctk.CTkButton(frame_botones, text="Cancelar", height=40,
                                   fg_color="#64748B", hover_color="#D6DBE3",
                                   corner_radius=10, command=self.controller.volver, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_cancelar.pack(side="left", fill="x", expand=True, padx=5)

    def _actualizar_permisos(self, nombre_rol):
        """Carga los checkboxes de permisos según el rol seleccionado."""
        for widget in self.frame_permisos.winfo_children():
            if widget != self.frame_permisos.winfo_children()[0]:  # No eliminar el título
                widget.destroy()

        rol = Rol.obtener_por_nombre(nombre_rol)
        if not rol:
            rol = Rol(nombre=nombre_rol, permisos={})

        permisos = rol.permisos

        # Si no hay permisos definidos, mostrar un mensaje
        if not permisos:
            ctk.CTkLabel(self.frame_permisos, text="Este rol no tiene permisos específicos definidos.",
                        font=("Roboto", 12), text_color="#8B93A3"
            ).pack(anchor="w", pady=5)
        else:
            for permiso, valor in permisos.items():
                var = ctk.IntVar(value=1 if valor else 0)
                chk = ctk.CTkCheckBox(self.frame_permisos, text=permiso.replace("_", " ").title(),
                                    variable=var, font=("Roboto", 12),
                                    fg_color="#15803D", hover_color="#166534", text_color="#1A2233")
                chk.pack(anchor="w", pady=2, padx=20)
                self.check_permisos[permiso] = var

    # Puestos de trabajo predefinidos de un supermercado, cada uno con su
    # set de permisos ya definido. Al crear el rol no hay que tipear ni
    # elegir permisos a mano: se asignan solos según el puesto elegido.
    PUESTOS_PREDEFINIDOS = {
        "Cajero": {
            "puede_vender": True, "puede_anular": False,
            "puede_sangria": False, "puede_cerrar_turno": False,
        },
        "Cajero Senior": {
            "puede_vender": True, "puede_anular": True,
            "puede_sangria": True, "puede_cerrar_turno": True,
        },
        "Repositor": {
            "puede_reponer": True, "puede_ver_stock": True,
        },
        "Encargado de Sector": {
            "puede_reponer": True, "puede_ver_stock": True,
            "puede_gestionar_productos": True,
        },
        "Vendedor": {
            "puede_vender": True, "puede_atender_clientes": True,
        },
        "Supervisor": {
            "puede_vender": True, "puede_anular": True, "puede_sangria": True,
            "puede_cerrar_turno": True, "puede_ver_reportes_basicos": True,
        },
        "Encargado de Compras": {
            "puede_gestionar_compras": True, "puede_gestionar_proveedores": True,
        },
        "Encargado de Depósito": {
            "puede_reponer": True, "puede_ver_stock": True,
            "puede_gestionar_compras": True,
        },
        "Administrador": {
            "puede_vender": True, "puede_anular": True, "puede_sangria": True,
            "puede_cerrar_turno": True, "puede_gestionar_productos": True,
            "puede_gestionar_clientes": True, "puede_gestionar_proveedores": True,
            "puede_gestionar_compras": True,
        },
        "Seguridad": {
            "puede_ver_camaras": True, "puede_reportar_incidentes": True,
        },
        "Limpieza y Mantenimiento": {
            "puede_reportar_incidentes": True,
        },
        "Gerente General": {
            "puede_vender": True, "puede_anular": True, "puede_sangria": True,
            "puede_cerrar_turno": True, "puede_gestionar_productos": True,
            "puede_gestionar_clientes": True, "puede_gestionar_proveedores": True,
            "puede_gestionar_compras": True, "puede_gestionar_usuarios": True,
            "puede_ver_balances": True, "puede_gestionar_promociones": True,
        },
    }

    def _crear_nuevo_rol(self):
        """Abre un diálogo para crear un nuevo rol a partir de un puesto de
        trabajo predefinido: los permisos se asignan solos, no hay que
        elegirlos ni tipearlos a mano."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Crear Nuevo Rol")
        dialog.geometry("420x320")
        dialog.configure(fg_color="#F9FAFB")
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        dialog.lift()
        dialog.focus_force()
        dialog.grab_set()

        x = (dialog.winfo_screenwidth() // 2) - 210
        y = (dialog.winfo_screenheight() // 2) - 160
        dialog.geometry(f"420x320+{x}+{y}")

        frame = ctk.CTkFrame(dialog, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text="Puesto de trabajo:", font=("Roboto", 14, "bold")
        ).pack(anchor="w", pady=(10, 5))

        puestos_disponibles = [p for p in self.PUESTOS_PREDEFINIDOS.keys()
                                if not Rol.obtener_por_nombre(p)]
        if not puestos_disponibles:
            ctk.CTkLabel(frame, text="Ya existen roles creados para todos los\npuestos predefinidos.",
                        font=("Roboto", 12), text_color="#8B93A3").pack(pady=20)
            ctk.CTkButton(frame, text="Cerrar", height=40, fg_color="#64748B",
                        hover_color="#D6DBE3", corner_radius=10,
                        command=dialog.destroy, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF").pack(fill="x", pady=10)
            return

        combo_puesto = ctk.CTkOptionMenu(frame, values=puestos_disponibles,
                                        font=("Roboto", 13), fg_color="#D6DBE3",
                                        text_color="#1A2233", button_color="#2563EB",
                                        corner_radius=10,
                                        command=lambda p: _mostrar_permisos(p))
        combo_puesto.pack(fill="x", pady=(0, 15))
        combo_puesto.set(puestos_disponibles[0])

        ctk.CTkLabel(frame, text="Permisos asignados automáticamente:",
                    font=("Roboto", 13, "bold"), text_color="#1D4ED8"
        ).pack(anchor="w", pady=(5, 5))

        frame_preview = ctk.CTkFrame(frame, fg_color="#F4F6F9", corner_radius=10, border_width=1, border_color="#B8C1CE")
        frame_preview.pack(fill="both", expand=True, pady=(0, 10))

        lbl_preview = ctk.CTkLabel(frame_preview, text="", font=("Roboto", 12),
                                  text_color="#6B7280", justify="left")
        lbl_preview.pack(anchor="w", padx=15, pady=15)

        def _mostrar_permisos(puesto):
            permisos = self.PUESTOS_PREDEFINIDOS.get(puesto, {})
            if permisos:
                texto = "\n".join(f"✔ {p.replace('_', ' ').title()}" for p in permisos)
            else:
                texto = "Sin permisos específicos."
            lbl_preview.configure(text=texto)

        _mostrar_permisos(puestos_disponibles[0])

        def guardar_rol():
            puesto = combo_puesto.get()
            permisos = self.PUESTOS_PREDEFINIDOS.get(puesto, {})

            nuevo = Rol(nombre=puesto, permisos=permisos)
            if nuevo.guardar():
                messagebox.showinfo("Éxito", f"Rol '{puesto}' creado con sus permisos correspondientes.")
                roles = Rol.obtener_todos()
                lista_roles = [r.nombre for r in roles]
                self.combo_rol.configure(values=lista_roles)
                self.combo_rol.set(puesto)
                self._actualizar_permisos(puesto)
                dialog.destroy()
            else:
                messagebox.showerror("Error", "No se pudo crear el rol (puede que ya exista).")

        btn_guardar = ctk.CTkButton(frame, text="💾 Crear Rol con estos permisos", height=40,
                                  fg_color="#15803D", hover_color="#166534",
                                  corner_radius=10, command=guardar_rol, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_guardar.pack(fill="x", pady=(10, 5))

        btn_cancelar = ctk.CTkButton(frame, text="Cancelar", height=40,
                                   fg_color="#64748B", hover_color="#D6DBE3",
                                   corner_radius=10, command=dialog.destroy, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_cancelar.pack(fill="x", pady=5)

    def _cargar_licencias(self):
        for widget in self.frame_licencias.winfo_children():
            widget.destroy()
        licencias = self.empleado.obtener_licencias() if self.empleado else []
        if not licencias:
            ctk.CTkLabel(self.frame_licencias, text="No hay licencias registradas.",
                        font=("Roboto", 12), text_color="#8B93A3"
            ).pack(pady=20)
        else:
            for lic in licencias:
                texto = f"{lic['tipo']} - {lic['fecha_inicio']} a {lic['fecha_fin'] or 'Activa'} ({lic['estado']})"
                ctk.CTkLabel(self.frame_licencias, text=texto, font=("Roboto", 12),
                            text_color="#1A2233").pack(anchor="w", pady=2)