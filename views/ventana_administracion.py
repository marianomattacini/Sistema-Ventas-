import customtkinter as ctk
from tkinter import messagebox
from models.usuario import Usuario
from models.notificacion import Notificacion
from models.producto import Producto
from models.venta import Venta
from models.turno import Turno
from views.base_frame import BaseFrame

class FrameAdministracion(BaseFrame):
    """
    Panel de Administración General.
    Acceso central para Administradores y Gerentes Generales.
    """

    def __init__(self, parent, controller, usuario_actual, **kwargs):
        super().__init__(parent, controller, usuario_actual)

        if not self.usuario_actual.tiene_permiso('gestionar_usuarios'):
            messagebox.showerror("Acceso Denegado",
                                "No tiene permisos para acceder al panel de administración.\nSe notificará al Gerente General.")
            Notificacion.crear_notificacion_seguridad(
                1,
                f"Intento de acceso no autorizado a Administración por '{self.usuario_actual.nombre_usuario}'"
            )
            self.controller.cerrar_sesion()
            return

        self.configure(fg_color="#EFEAE2")

        self._crear_widgets()
        self._cargar_resumen()

    def _crear_widgets(self):
        frame_principal = ctk.CTkFrame(self, fg_color="#FBF8F3", corner_radius=15, border_width=2, border_color="#9C927F")
        frame_principal.pack(fill="both", expand=True, padx=20, pady=20)
        
        barra = ctk.CTkFrame(frame_principal, fg_color="transparent")
        barra.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(barra, text="⚙️ PANEL DE ADMINISTRACIÓN", 
                    font=("Roboto", 24, "bold"), text_color="#1D4ED8"
        ).pack(side="left")
        
        ctk.CTkLabel(barra, text=f"👤 {self.usuario_actual.nombre_usuario} ({self.usuario_actual.rol})", 
                    font=("Roboto", 14), text_color="#5A5347"
        ).pack(side="right", padx=10)
        
        # Panel de resumen
        frame_resumen = ctk.CTkFrame(frame_principal, fg_color="#E3DCD0", corner_radius=10, border_width=2, border_color="#9C927F")
        frame_resumen.pack(fill="x", padx=20, pady=(10, 20))
        
        ctk.CTkLabel(frame_resumen, text="📊 RESUMEN DEL SISTEMA", 
                    font=("Roboto", 16, "bold"), text_color="#1D4ED8"
        ).pack(anchor="w", padx=20, pady=(20, 10))
        
        frame_tarjetas = ctk.CTkFrame(frame_resumen, fg_color="transparent")
        frame_tarjetas.pack(fill="x", padx=20, pady=(0, 20))
        
        for i in range(4):
            frame_tarjetas.grid_columnconfigure(i, weight=1)
        
        card_usuarios = ctk.CTkFrame(frame_tarjetas, fg_color="#FBF8F3", corner_radius=10, border_width=2, border_color="#9C927F")
        card_usuarios.grid(row=0, column=0, padx=10, sticky="nsew")
        ctk.CTkLabel(card_usuarios, text="👥 Usuarios", font=("Roboto", 14), text_color="#5A5347"
        ).pack(pady=(15, 5))
        self.lbl_usuarios = ctk.CTkLabel(card_usuarios, text="0", font=("Roboto", 24, "bold"), text_color="#1D4ED8")
        self.lbl_usuarios.pack(pady=(0, 15))
        
        card_productos = ctk.CTkFrame(frame_tarjetas, fg_color="#FBF8F3", corner_radius=10, border_width=2, border_color="#9C927F")
        card_productos.grid(row=0, column=1, padx=10, sticky="nsew")
        ctk.CTkLabel(card_productos, text="📦 Productos", font=("Roboto", 14), text_color="#5A5347"
        ).pack(pady=(15, 5))
        self.lbl_productos = ctk.CTkLabel(card_productos, text="0", font=("Roboto", 24, "bold"), text_color="#15803D")
        self.lbl_productos.pack(pady=(0, 15))
        
        card_ventas = ctk.CTkFrame(frame_tarjetas, fg_color="#FBF8F3", corner_radius=10, border_width=2, border_color="#9C927F")
        card_ventas.grid(row=0, column=2, padx=10, sticky="nsew")
        ctk.CTkLabel(card_ventas, text="💰 Ventas Hoy", font=("Roboto", 14), text_color="#5A5347"
        ).pack(pady=(15, 5))
        self.lbl_ventas = ctk.CTkLabel(card_ventas, text="$ 0.00", font=("Roboto", 24, "bold"), text_color="#C2410C")
        self.lbl_ventas.pack(pady=(0, 15))
        
        card_alertas = ctk.CTkFrame(frame_tarjetas, fg_color="#FBF8F3", corner_radius=10, border_width=2, border_color="#9C927F")
        card_alertas.grid(row=0, column=3, padx=10, sticky="nsew")
        ctk.CTkLabel(card_alertas, text="⚠️ Alertas Stock", font=("Roboto", 14), text_color="#5A5347"
        ).pack(pady=(15, 5))
        self.lbl_alertas = ctk.CTkLabel(card_alertas, text="0", font=("Roboto", 24, "bold"), text_color="#DC2626")
        self.lbl_alertas.pack(pady=(0, 15))
        
        # Panel central: gráfico de ventas + alertas de stock + notificaciones
        frame_medio = ctk.CTkFrame(frame_principal, fg_color="transparent")
        frame_medio.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        frame_medio.grid_columnconfigure(0, weight=3)
        frame_medio.grid_columnconfigure(1, weight=2)
        frame_medio.grid_rowconfigure(0, weight=1)

        # --- Columna izquierda: gráfico de ventas últimos 7 días ---
        frame_grafico = ctk.CTkFrame(frame_medio, fg_color="#E3DCD0", corner_radius=10, border_width=2, border_color="#9C927F")
        frame_grafico.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        ctk.CTkLabel(frame_grafico, text="📈 VENTAS - ÚLTIMOS 7 DÍAS",
                    font=("Roboto", 16, "bold"), text_color="#1D4ED8"
        ).pack(anchor="w", padx=20, pady=(20, 10))

        self.frame_barras = ctk.CTkFrame(frame_grafico, fg_color="transparent")
        self.frame_barras.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # --- Columna derecha: alertas de stock + notificaciones ---
        frame_lateral = ctk.CTkFrame(frame_medio, fg_color="transparent")
        frame_lateral.grid(row=0, column=1, sticky="nsew")
        frame_lateral.grid_rowconfigure(0, weight=1)
        frame_lateral.grid_rowconfigure(1, weight=1)
        frame_lateral.grid_columnconfigure(0, weight=1)

        frame_stock = ctk.CTkFrame(frame_lateral, fg_color="#E3DCD0", corner_radius=10, border_width=2, border_color="#9C927F")
        frame_stock.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        ctk.CTkLabel(frame_stock, text="⚠️ STOCK BAJO", font=("Roboto", 14, "bold"),
                    text_color="#C2410C").pack(anchor="w", padx=15, pady=(15, 5))
        self.frame_stock_lista = ctk.CTkScrollableFrame(frame_stock, fg_color="transparent")
        self.frame_stock_lista.pack(fill="both", expand=True, padx=10, pady=(0, 15))

        frame_notif = ctk.CTkFrame(frame_lateral, fg_color="#E3DCD0", corner_radius=10, border_width=2, border_color="#9C927F")
        frame_notif.grid(row=1, column=0, sticky="nsew")
        header_notif = ctk.CTkFrame(frame_notif, fg_color="transparent")
        header_notif.pack(fill="x", padx=15, pady=(15, 5))
        ctk.CTkLabel(header_notif, text="🔔 NOTIFICACIONES", font=("Roboto", 14, "bold"),
                    text_color="#1D4ED8").pack(side="left")
        ctk.CTkButton(header_notif, text="📋 Auditoría", width=90, height=24,
                     font=("Roboto", 11), fg_color="#D6CDBE", hover_color="#64748B",
                     corner_radius=8, command=self._abrir_auditoria
        , border_width=2, border_color="#9C927F", text_color="#1F1B16").pack(side="right")
        self.frame_notif_lista = ctk.CTkScrollableFrame(frame_notif, fg_color="transparent")
        self.frame_notif_lista.pack(fill="both", expand=True, padx=10, pady=(0, 15))

        # Panel inferior
        frame_inferior = ctk.CTkFrame(frame_principal, fg_color="#E3DCD0", corner_radius=10, border_width=2, border_color="#9C927F")
        frame_inferior.pack(fill="x", padx=20, pady=(0, 10))
        
        btn_salir = ctk.CTkButton(frame_inferior, text="🚪 Cerrar Sesión", height=40,
                                 font=("Roboto", 14, "bold"), fg_color="#DC2626",
                                 hover_color="#B91C1C", corner_radius=10,
                                 command=self._cerrar_sesion, border_width=2, border_color="#9C927F", text_color="#FFFFFF")
        btn_salir.pack(side="right", padx=20, pady=10)
        
        ctk.CTkLabel(frame_inferior, text="Sistema de Gestión de Ventas y Control de Stock v1.0", 
                    font=("Roboto", 12), text_color="#7A7264"
        ).pack(side="left", padx=20, pady=10)
    
    # =====================================================================
    # MÉTODOS DE CARGA DE RESUMEN
    # =====================================================================
    def _cargar_resumen(self):
        try:
            from database.config import get_sqlite_connection
            conn = get_sqlite_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM usuarios WHERE estado = 'Activo'")
            total_usuarios = cursor.fetchone()[0] or 0
            self.lbl_usuarios.configure(text=str(total_usuarios))
            
            cursor.execute("SELECT COUNT(*) FROM productos WHERE estado = 'Activo'")
            total_productos = cursor.fetchone()[0] or 0
            self.lbl_productos.configure(text=str(total_productos))
            
            from datetime import datetime
            hoy = datetime.now().strftime("%Y-%m-%d")
            cursor.execute('''
                SELECT SUM(total_facturado) 
                FROM ventas_cabecera 
                WHERE estado = 'Completado' AND fecha_hora LIKE ?
            ''', (f"{hoy}%",))
            total_ventas = cursor.fetchone()[0] or 0.0
            self.lbl_ventas.configure(text=f"$ {total_ventas:.2f}")
            
            cursor.execute("SELECT COUNT(*) FROM productos WHERE estado = 'Activo' AND stock_actual <= stock_minimo")
            total_alertas = cursor.fetchone()[0] or 0
            self.lbl_alertas.configure(text=str(total_alertas))
            
            conn.close()

            self._cargar_grafico_ventas()
            self._cargar_stock_bajo()
            self._cargar_notificaciones()
        except Exception as e:
            print(f"Error al cargar resumen: {e}")

    def _cargar_grafico_ventas(self):
        """Dibuja un gráfico de barras simple con las ventas de los últimos 7 días."""
        from datetime import datetime, timedelta
        from database.config import get_sqlite_connection

        for widget in self.frame_barras.winfo_children():
            widget.destroy()

        dias = [(datetime.now() - timedelta(days=i)) for i in range(6, -1, -1)]
        totales = []
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()
            for dia in dias:
                clave = dia.strftime("%Y-%m-%d")
                cursor.execute('''
                    SELECT SUM(total_facturado) FROM ventas_cabecera
                    WHERE estado = 'Completado' AND fecha_hora LIKE ?
                ''', (f"{clave}%",))
                totales.append(cursor.fetchone()[0] or 0.0)
            conn.close()
        except Exception as e:
            print(f"Error al cargar gráfico de ventas: {e}")
            totales = [0.0] * 7

        maximo = max(totales) if max(totales) > 0 else 1.0

        self.frame_barras.grid_columnconfigure(tuple(range(7)), weight=1)
        self.frame_barras.grid_rowconfigure(0, weight=1)

        for i, (dia, total) in enumerate(zip(dias, totales)):
            col = ctk.CTkFrame(self.frame_barras, fg_color="transparent")
            col.grid(row=0, column=i, sticky="nsew", padx=6)
            col.grid_rowconfigure(0, weight=1)

            alto_barra = max(int(140 * (total / maximo)), 4)
            relleno = ctk.CTkFrame(col, fg_color="transparent", height=140 - alto_barra)
            relleno.grid(row=0, column=0, sticky="ew")
            barra = ctk.CTkFrame(col, fg_color="#1D4ED8" if total > 0 else "#D6CDBE",
                                 corner_radius=6, height=alto_barra)
            barra.grid(row=1, column=0, sticky="ew")

            ctk.CTkLabel(col, text=f"${total:,.0f}", font=("Roboto", 10),
                        text_color="#5A5347").grid(row=2, column=0, pady=(4, 0))
            ctk.CTkLabel(col, text=dia.strftime("%d/%m"), font=("Roboto", 10, "bold"),
                        text_color="#1F1B16").grid(row=3, column=0, pady=(0, 0))

    def _cargar_stock_bajo(self):
        from models.producto import Producto

        for widget in self.frame_stock_lista.winfo_children():
            widget.destroy()

        productos = Producto.obtener_productos_con_stock_bajo()
        if not productos:
            ctk.CTkLabel(self.frame_stock_lista, text="✅ Sin alertas de stock.",
                        font=("Roboto", 12), text_color="#7A7264").pack(pady=10)
            return

        for p in productos[:8]:
            fila = ctk.CTkFrame(self.frame_stock_lista, fg_color="#FBF8F3", corner_radius=8, border_width=2, border_color="#9C927F")
            fila.pack(fill="x", pady=3)
            ctk.CTkLabel(fila, text=p.nombre, font=("Roboto", 12, "bold"),
                        text_color="#1F1B16", anchor="w").pack(side="left", padx=10, pady=6)
            ctk.CTkLabel(fila, text=f"{p.stock_actual}/{p.stock_minimo}", font=("Roboto", 12, "bold"),
                        text_color="#DC2626").pack(side="right", padx=10, pady=6)

    def _cargar_notificaciones(self):
        from models.notificacion import Notificacion

        for widget in self.frame_notif_lista.winfo_children():
            widget.destroy()

        notificaciones = Notificacion.obtener_notificaciones_por_usuario(self.usuario_actual.id)
        if not notificaciones:
            ctk.CTkLabel(self.frame_notif_lista, text="Sin notificaciones.",
                        font=("Roboto", 12), text_color="#7A7264").pack(pady=10)
            return

        for n in notificaciones[:8]:
            fila = ctk.CTkFrame(self.frame_notif_lista, fg_color="#FBF8F3", corner_radius=8, border_width=2, border_color="#9C927F")
            fila.pack(fill="x", pady=3)
            icono = "🔴" if not n.leida else "⚪"
            ctk.CTkLabel(fila, text=f"{icono} {n.mensaje}", font=("Roboto", 11),
                        text_color="#1F1B16", anchor="w", wraplength=260, justify="left"
            ).pack(side="left", padx=10, pady=6, fill="x", expand=True)
    
    # =====================================================================
    # MÉTODOS DE ACCESO A MÓDULOS
    # =====================================================================
    def _abrir_productos(self):
        self.controller.mostrar_pantalla("productos")

    def _abrir_clientes(self):
        self.controller.mostrar_pantalla("clientes")

    def _abrir_proveedores(self):
        self.controller.mostrar_pantalla("proveedores")

    def _abrir_compras(self):
        self.controller.mostrar_pantalla("compras")

    def _abrir_turnos(self):
        self.controller.mostrar_pantalla("turnos")

    def _abrir_gerente(self):
        self.controller.mostrar_pantalla("gerente")

    def _abrir_usuarios(self):
        self.controller.mostrar_pantalla("usuarios")

    def _abrir_configuracion(self):
        self.controller.mostrar_pantalla("configuracion")
    
    def _abrir_auditoria(self):
        try:
            from database.config import get_sqlite_connection
            conn = get_sqlite_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT fecha_hora, u.nombre_usuario, accion, detalle
                FROM logs_auditoria l
                JOIN usuarios u ON l.usuario_id = u.id
                ORDER BY fecha_hora DESC
                LIMIT 50
            ''')
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                messagebox.showinfo("Auditoría", "No hay registros de auditoría.")
                return
            
            mensaje = "📋 ÚLTIMOS 50 EVENTOS DE AUDITORÍA\n\n"
            for row in rows:
                mensaje += f"{row[0]} - {row[1]}: {row[2]}\n"
                if row[3]:
                    mensaje += f"   Detalle: {row[3]}\n"
                mensaje += "\n"
            
            ventana = ctk.CTkToplevel(self)
            ventana.title("Registro de Auditoría")
            ventana.geometry("800x600")
            ventana.configure(fg_color="#EFEAE2")
            
            frame = ctk.CTkFrame(ventana, fg_color="#FBF8F3", corner_radius=15, border_width=2, border_color="#9C927F")
            frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            ctk.CTkLabel(frame, text="📋 Registro de Auditoría", 
                        font=("Roboto", 20, "bold"), text_color="#1D4ED8"
            ).pack(pady=(20, 10))
            
            texto = ctk.CTkTextbox(frame, font=("Roboto", 12), fg_color="#FFFDF9", text_color="#1F1B16", border_color="#9C927F", border_width=2)
            texto.pack(fill="both", expand=True, padx=20, pady=20)
            texto.insert("1.0", mensaje)
            texto.configure(state="disabled")
            
            btn_cerrar = ctk.CTkButton(frame, text="Cerrar", height=40,
                                     fg_color="#64748B", hover_color="#475569",
                                     corner_radius=10, command=ventana.destroy, border_width=2, border_color="#9C927F", text_color="#FFFFFF")
            btn_cerrar.pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la auditoría: {e}")
    
    # =====================================================================
    # CIERRE DE SESIÓN
    # =====================================================================
    def _cerrar_sesion(self):
        if messagebox.askyesno("Cerrar Sesión", "¿Está seguro de que desea cerrar sesión?"):
            self.controller.cerrar_sesion()