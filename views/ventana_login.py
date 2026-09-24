import customtkinter as ctk
from tkinter import messagebox
from models.usuario import Usuario
from models.notificacion import Notificacion
from models.turno import Turno
from views.base_frame import BaseFrame
from ui.theme import Color, Font


class FrameLogin(BaseFrame):
    """Pantalla de inicio de sesión del sistema (primera pantalla de la app)."""

    def __init__(self, parent, controller, usuario_actual=None, **kwargs):
        super().__init__(parent, controller, usuario_actual)

        self.intentos_fallidos = 0
        self._crear_widgets()

    def _crear_widgets(self):
        """Crea los widgets de la interfaz."""
        # Frame central
        frame = ctk.CTkFrame(
            self, fg_color=Color.BG_CARD, corner_radius=20,
            border_width=2, border_color=Color.ACCENT_HOVER
        )
        frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.55, relheight=0.75)

        # Título
        ctk.CTkLabel(
            frame, text="🏪 Sistema de Ventas",
            font=("Roboto", 36, "bold"), text_color=Color.ACCENT
        ).pack(pady=(40, 10))

        ctk.CTkLabel(
            frame, text="Control de Stock y Facturación",
            font=Font.BODY, text_color=Color.TEXT_SECONDARY
        ).pack(pady=(0, 30))

        # Campo: Usuario
        ctk.CTkLabel(
            frame, text="Usuario", font=Font.BODY,
            text_color="#1A2233"
        ).pack(anchor="w", padx=40, pady=(10, 5))

        self.entry_usuario = ctk.CTkEntry(
            frame, placeholder_text="Nombre de usuario", height=45,
            font=Font.BODY, fg_color=Color.NEUTRAL_HOVER, text_color=Color.TEXT_WHITE,
            corner_radius=10
        )
        self.entry_usuario.pack(fill="x", padx=40, pady=(0, 20))
        self.entry_usuario.bind("<Return>", lambda e: self._procesar_login())

        # Campo: PIN
        ctk.CTkLabel(
            frame, text="PIN", font=Font.BODY,
            text_color="#1A2233"
        ).pack(anchor="w", padx=40, pady=(10, 5))

        self.entry_pin = ctk.CTkEntry(
            frame, placeholder_text="Ingrese su PIN", show="*",
            height=45, font=Font.BODY, fg_color=Color.NEUTRAL_HOVER,
            text_color=Color.TEXT_WHITE, corner_radius=10
        )
        self.entry_pin.pack(fill="x", padx=40, pady=(0, 20))
        self.entry_pin.bind("<Return>", lambda e: self._procesar_login())

        # Etiqueta de error
        self.label_error = ctk.CTkLabel(
            frame, text="", font=Font.SMALL, text_color=Color.DANGER
        )
        self.label_error.pack(pady=(0, 10))

        # Botón: Iniciar Sesión
        self.btn_login = ctk.CTkButton(
            frame, text="INICIAR SESIÓN", height=50,
            font=("Roboto", 16, "bold"), fg_color=Color.ACCENT_STRONG,
            hover_color=Color.ACCENT_HOVER, text_color=Color.TEXT_WHITE,
            corner_radius=15, border_width=2, border_color=Color.ACCENT_HOVER,
            command=self._procesar_login
        )
        self.btn_login.pack(fill="x", padx=40, pady=(10, 20))

        # Botón: Ver Estado de Operadores
        self.btn_estado = ctk.CTkButton(
            frame, text="Ver Estado de Operadores", height=35,
            font=Font.SMALL, fg_color=Color.NEUTRAL_HOVER, hover_color=Color.NEUTRAL,
            text_color=Color.TEXT_SECONDARY, corner_radius=10,
            command=self._mostrar_estado_operadores
        , border_width=1, border_color="#CBD2DC")
        self.btn_estado.pack(fill="x", padx=40, pady=(0, 20))

        self.entry_usuario.focus_set()

    # =====================================================================
    # LÓGICA DE AUTENTICACIÓN
    # =====================================================================
    def _procesar_login(self):
        usuario = self.entry_usuario.get().strip()
        pin = self.entry_pin.get().strip()

        if not usuario or not pin:
            self.label_error.configure(text="❌ Ingrese usuario y PIN.")
            return

        usuario_obj = Usuario.verificar_pin(usuario, pin)

        if usuario_obj:
            self.label_error.configure(text="")
            self._login_exitoso(usuario_obj)
        else:
            self.intentos_fallidos += 1
            self.label_error.configure(
                text=f"❌ Usuario o PIN incorrecto. Intento {self.intentos_fallidos} de 3."
            )
            if self.intentos_fallidos >= 3:
                self._bloquear_usuario(usuario)

    def _login_exitoso(self, usuario_obj):
        """Redirige según el rol del usuario (el controlador decide la pantalla)."""
        if usuario_obj.rol in ["Cajero", "Supervisor"]:
            turno_abierto = Turno.obtener_turno_abierto()
            if turno_abierto and turno_abierto[1] == usuario_obj.id:
                self.controller.iniciar_sesion(usuario_obj, turno_abierto[0])
            else:
                self.controller.iniciar_sesion(usuario_obj, None)
        elif usuario_obj.rol in ["Administrador", "Gerente General"]:
            self.controller.iniciar_sesion(usuario_obj)
        else:
            messagebox.showerror("Error", "Rol de usuario no reconocido.")

    def _bloquear_usuario(self, usuario):
        try:
            from database.config import get_sqlite_connection
            conn = get_sqlite_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM usuarios WHERE nombre_usuario = ?", (usuario,))
            row = cursor.fetchone()
            conn.close()

            if row:
                usuario_obj = Usuario.obtener_por_id(row[0])
                if usuario_obj:
                    usuario_obj.cambiar_estado("Bloqueado", usuario_obj)
                    Notificacion.crear_notificacion_seguridad(
                        1,
                        f"Bloqueo automático de usuario '{usuario}' por 3 intentos fallidos."
                    )
                    messagebox.showwarning(
                        "Usuario Bloqueado",
                        f"⛔ El usuario '{usuario}' ha sido bloqueado.\nContacte al Gerente General."
                    )
                    self.entry_usuario.delete(0, 'end')
                    self.entry_pin.delete(0, 'end')
                    return
        except Exception as e:
            print(f"Error al bloquear usuario: {e}")

    def _mostrar_estado_operadores(self):
        try:
            from database.config import get_sqlite_connection
            conn = get_sqlite_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT nombre_usuario, rol, estado FROM usuarios ORDER BY nombre_usuario ASC")
            rows = cursor.fetchall()
            conn.close()

            if not rows:
                messagebox.showinfo("Estado de Operadores", "No hay operadores registrados.")
                return

            mensaje = "👥 LISTADO ADMINISTRATIVO DE OPERADORES\n\n"
            for row in rows:
                icono = {"Activo": "🟢", "Inactivo": "🔴", "Bloqueado": "⛔"}.get(row[2], "❓")
                mensaje += f"{icono} {row[0]} ({row[1]}) - {row[2]}\n"

            messagebox.showinfo("Estado de Operadores", mensaje)

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo obtener el estado de los operadores:\n{e}")
