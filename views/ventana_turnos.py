import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from models.turno import Turno
from models.usuario import Usuario
from models.venta import Venta
from models.notificacion import Notificacion
from utils.generadores import generar_reporte_turno_pdf  # <-- NUEVA IMPORTACIÓN
from views.base_frame import BaseFrame

class FrameTurnos(BaseFrame):
    """
    Pantalla de gestión de turnos (apertura, cierre, sangrías, descansos).
    Accesible para Supervisores, Administradores y Gerentes Generales.
    """

    def __init__(self, parent, controller, usuario_actual, **kwargs):
        super().__init__(parent, controller, usuario_actual)
        
        # Verificar permisos (al menos Supervisor)
        if not self.usuario_actual.tiene_permiso('ver_reportes_basicos'):
            messagebox.showerror("Acceso Denegado", 
                                "No tiene permisos para gestionar turnos.\nSe notificará al Gerente General.")
            Notificacion.crear_notificacion_seguridad(
                1,
                f"Intento de acceso no autorizado a Gestión de Turnos por '{self.usuario_actual.nombre_usuario}'"
            )
            self.controller.volver()
            return
        
        # Configuración de la pantalla
        self.configure(fg_color="#F4F6F9")
        
        # Estado
        self.turno_seleccionado = None
        self.turno_seleccionado_data = None  # Guardar datos del turno para mostrar detalles
        
        # Crear widgets
        self._crear_widgets()
        self._cargar_turnos()
    
    def _crear_widgets(self):
        # Frame principal
        frame_principal = ctk.CTkFrame(self, fg_color="#F9FAFB", corner_radius=15, border_width=1, border_color="#B8C1CE")
        frame_principal.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Barra superior
        barra = ctk.CTkFrame(frame_principal, fg_color="transparent")
        barra.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(barra, text="🕒 GESTIÓN DE TURNOS", 
                    font=("Roboto", 24, "bold"), text_color="#1D4ED8"
        ).pack(side="left")
        
        btn_volver = ctk.CTkButton(barra, text="← Volver", font=("Roboto", 14), height=35,
                                  fg_color="#64748B", hover_color="#D6DBE3",
                                  corner_radius=10, command=self.destroy, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_volver.pack(side="right", padx=10)
        
        # Panel de filtros
        panel_filtros = ctk.CTkFrame(frame_principal, fg_color="#F4F6F9", corner_radius=10, border_width=1, border_color="#B8C1CE")
        panel_filtros.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(panel_filtros, text="🔍 Filtros:", font=("Roboto", 14, "bold")
        ).pack(side="left", padx=10, pady=10)
        
        # Filtro por estado
        self.combo_estado = ctk.CTkOptionMenu(panel_filtros, values=["Todos", "Abierto", "Cerrado", "Forzado"],
                                              width=150, height=35, corner_radius=10,
                                              command=lambda e: self._cargar_turnos(), text_color="#FFFFFF")
        self.combo_estado.pack(side="left", padx=10, pady=10)
        self.combo_estado.set("Todos")
        
        # Filtro por operador
        ctk.CTkLabel(panel_filtros, text="Operador:", font=("Roboto", 13, "bold")
        ).pack(side="left", padx=(20, 5), pady=10)
        
        self.combo_operador = ctk.CTkOptionMenu(panel_filtros, values=["Todos"] + self._obtener_operadores(),
                                               width=150, height=35, corner_radius=10,
                                               command=lambda e: self._cargar_turnos(), text_color="#FFFFFF")
        self.combo_operador.pack(side="left", padx=10, pady=10)
        self.combo_operador.set("Todos")
        
        # Botón refrescar
        btn_refrescar = ctk.CTkButton(panel_filtros, text="🔄 Refrescar", height=35,
                                     fg_color="#2563EB", hover_color="#2563EB",
                                     corner_radius=10, command=self._cargar_turnos, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_refrescar.pack(side="right", padx=10, pady=10)
        
        # Tabla de turnos
        self.frame_tabla = ctk.CTkScrollableFrame(frame_principal, fg_color="#F4F6F9", corner_radius=10)
        self.frame_tabla.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Encabezados
        encabezados = ["ID", "Cajero", "Apertura", "Cierre", "Fondo Inicial", "Total Ventas", "Estado", "Acciones"]
        for i, texto in enumerate(encabezados):
            ctk.CTkLabel(self.frame_tabla, text=texto, font=("Roboto", 13, "bold"),
                        text_color="#6B7280").grid(row=0, column=i, padx=10, pady=5, sticky="w")
        
        # Panel de acciones rápidas
        panel_acciones = ctk.CTkFrame(frame_principal, fg_color="#F4F6F9", corner_radius=10, border_width=1, border_color="#B8C1CE")
        panel_acciones.pack(fill="x", padx=20, pady=(10, 20))
        
        btn_sangria = ctk.CTkButton(panel_acciones, text="💰 Registrar Sangría", height=40,
                                   fg_color="#C2410C", hover_color="#9A3412",
                                   corner_radius=10, command=self._registrar_sangria, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_sangria.pack(side="left", padx=10)
        
        btn_cerrar = ctk.CTkButton(panel_acciones, text="🔒 Cerrar Turno Seleccionado", height=40,
                                  fg_color="#2563EB", hover_color="#1D4ED8",
                                  corner_radius=10, command=self._cerrar_turno, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_cerrar.pack(side="left", padx=10)
        
        btn_forzar = ctk.CTkButton(panel_acciones, text="⚠️ Forzar Cierre", height=40,
                                  fg_color="#DC2626", hover_color="#B91C1C",
                                  corner_radius=10, command=self._forzar_cierre, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_forzar.pack(side="left", padx=10)
        
        # NUEVO BOTÓN: Generar Reporte
        btn_reporte = ctk.CTkButton(panel_acciones, text="📄 Generar Reporte", height=40,
                                   fg_color="#7C3AED", hover_color="#6D28D9",
                                   corner_radius=10, command=self._generar_reporte, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_reporte.pack(side="left", padx=10)
        
        ctk.CTkLabel(panel_acciones, text="Seleccione un turno para cerrar o forzar cierre", 
                    font=("Roboto", 12), text_color="#8B93A3"
        ).pack(side="right", padx=20)
    
    def _obtener_operadores(self):
        """Retorna lista de nombres de operadores para el filtro."""
        usuarios = Usuario.obtener_todos()
        return [u.nombre_usuario for u in usuarios]
    
    def _cargar_turnos(self):
        """Carga los turnos según filtros y muestra en la tabla."""
        for widget in self.frame_tabla.winfo_children():
            if widget.grid_info() != {}:
                widget.destroy()
        
        estado_filtro = self.combo_estado.get()
        operador_filtro = self.combo_operador.get()
        
        try:
            from database.config import get_sqlite_connection
            conn = get_sqlite_connection()
            cursor = conn.cursor()
            
            query = '''
                SELECT t.id, u.nombre_usuario, t.fecha_hora_apertura, t.fecha_hora_cierre,
                       t.fondo_inicial, t.total_ventas_efectivo + t.total_ventas_debito + 
                       t.total_ventas_credito + t.total_ventas_transferencia as total_ventas,
                       t.estado
                FROM turnos t
                JOIN usuarios u ON t.usuario_id = u.id
                WHERE 1=1
            '''
            params = []
            
            if estado_filtro != "Todos":
                query += " AND t.estado = ?"
                params.append(estado_filtro)
            
            if operador_filtro != "Todos":
                query += " AND u.nombre_usuario = ?"
                params.append(operador_filtro)
            
            query += " ORDER BY t.fecha_hora_apertura DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                ctk.CTkLabel(self.frame_tabla, text="No hay turnos para mostrar", 
                            font=("Roboto", 14), text_color="#8B93A3"
                ).grid(row=1, column=0, columnspan=8, padx=10, pady=20)
                return
            
            for i, row in enumerate(rows, start=1):
                turno_id = row[0]
                cajero = row[1]
                apertura = row[2] or "-"
                cierre = row[3] or "-"
                fondo = row[4] or 0.0
                total_ventas = row[5] or 0.0
                estado = row[6]
                
                # Color según estado
                color_estado = {
                    "Abierto": "#15803D",
                    "Cerrado": "#2563EB",
                    "Forzado": "#C2410C"
                }.get(estado, "#8B93A3")
                
                ctk.CTkLabel(self.frame_tabla, text=str(turno_id), 
                            font=("Roboto", 13)).grid(row=i, column=0, padx=10, pady=5, sticky="w")
                ctk.CTkLabel(self.frame_tabla, text=cajero, 
                            font=("Roboto", 13)).grid(row=i, column=1, padx=10, pady=5, sticky="w")
                ctk.CTkLabel(self.frame_tabla, text=apertura, 
                            font=("Roboto", 13)).grid(row=i, column=2, padx=10, pady=5, sticky="w")
                ctk.CTkLabel(self.frame_tabla, text=cierre, 
                            font=("Roboto", 13)).grid(row=i, column=3, padx=10, pady=5, sticky="w")
                ctk.CTkLabel(self.frame_tabla, text=f"${fondo:.2f}", 
                            font=("Roboto", 13)).grid(row=i, column=4, padx=10, pady=5, sticky="e")
                ctk.CTkLabel(self.frame_tabla, text=f"${total_ventas:.2f}", 
                            font=("Roboto", 13, "bold"), text_color="#15803D"
                ).grid(row=i, column=5, padx=10, pady=5, sticky="e")
                
                estado_label = ctk.CTkLabel(self.frame_tabla, text=estado, 
                                          font=("Roboto", 13, "bold"), text_color=color_estado)
                estado_label.grid(row=i, column=6, padx=10, pady=5, sticky="w")
                
                # Botón de selección
                btn_selector = ctk.CTkButton(self.frame_tabla, text="Seleccionar", width=80, height=25,
                                            fg_color="#D6DBE3", hover_color="#64748B",
                                            corner_radius=5, command=lambda t=turno_id: self._seleccionar_turno(t), border_width=1, border_color="#CBD2DC", text_color="#1A2233")
                btn_selector.grid(row=i, column=7, padx=10, pady=5)
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los turnos: {e}")
    
    def _seleccionar_turno(self, turno_id):
        """Selecciona un turno y muestra información detallada con opción a reporte PDF."""
        try:
            turno = Turno.obtener_turno_por_id(turno_id)
            if not turno:
                messagebox.showerror("Error", "No se encontró el turno.")
                return
            
            self.turno_seleccionado = turno_id
            self.turno_seleccionado_data = turno
            
            # Obtener nombre del cajero
            usuario = Usuario.obtener_por_id(turno.usuario_id)
            
            # Construir información detallada
            total_ventas = (turno.total_ventas_efectivo + turno.total_ventas_debito + 
                            turno.total_ventas_credito + turno.total_ventas_transferencia)
            
            info = f"🕒 **Turno #{turno_id}**\n\n"
            info += f"👤 **Cajero:** {usuario.nombre_usuario if usuario else 'Desconocido'}\n"
            info += f"📅 **Apertura:** {turno.fecha_hora_apertura}\n"
            if turno.fecha_hora_cierre:
                info += f"📅 **Cierre:** {turno.fecha_hora_cierre}\n"
            info += f"📊 **Estado:** {turno.estado}\n"
            info += f"💰 **Fondo inicial:** ${turno.fondo_inicial:.2f}\n"
            info += f"💰 **Total ventas:** ${total_ventas:.2f}\n"
            info += f"💵 **Efectivo:** ${turno.total_ventas_efectivo:.2f}\n"
            info += f"💳 **Débito:** ${turno.total_ventas_debito:.2f}\n"
            info += f"💳 **Crédito:** ${turno.total_ventas_credito:.2f}\n"
            info += f"🔄 **Transferencia:** ${turno.total_ventas_transferencia:.2f}\n"
            info += f"📤 **Sangrías:** ${turno.total_sangrias:.2f}\n"
            
            # Preguntar si quiere generar reporte PDF
            if messagebox.askyesno("Turno Seleccionado", 
                                   f"{info}\n\n¿Desea generar un reporte en PDF de este turno?"):
                # Generar reporte
                datos_reporte = {
                    'turno_id': turno_id,
                    'cajero': usuario.nombre_usuario if usuario else 'Desconocido',
                    'apertura': turno.fecha_hora_apertura,
                    'cierre': turno.fecha_hora_cierre or 'Abierto',
                    'estado': turno.estado,
                    'fondo_inicial': turno.fondo_inicial,
                    'total_efectivo': turno.total_ventas_efectivo,
                    'total_debito': turno.total_ventas_debito,
                    'total_credito': turno.total_ventas_credito,
                    'total_transferencia': turno.total_ventas_transferencia,
                    'total_sangrias': turno.total_sangrias,
                    'total_ventas': total_ventas
                }
                generar_reporte_turno_pdf(datos_reporte)
            else:
                # Solo mostrar la información
                messagebox.showinfo("Detalles del Turno", info)
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al obtener detalles del turno: {e}")
    
    # =====================================================================
    # ACCIONES SOBRE TURNOS
    # =====================================================================
    def _cerrar_turno(self):
        """Cierra el turno seleccionado si está abierto."""
        if not self.turno_seleccionado:
            messagebox.showwarning("Aviso", "Primero seleccione un turno de la tabla.")
            return
        
        # Verificar que el turno esté abierto
        turno_abierto = Turno.obtener_turno_abierto()
        if not turno_abierto or turno_abierto[0] != self.turno_seleccionado:
            messagebox.showerror("Error", "El turno seleccionado no está abierto.\nSolo se pueden cerrar turnos abiertos.")
            return
        
        # Confirmar
        if not messagebox.askyesno("Confirmar", f"¿Cerrar el turno #{self.turno_seleccionado}?"):
            return
        
        try:
            if Turno.cerrar_turno(self.turno_seleccionado):
                messagebox.showinfo("Éxito", f"✅ Turno #{self.turno_seleccionado} cerrado correctamente.")
                self.turno_seleccionado = None
                self.turno_seleccionado_data = None
                self._cargar_turnos()
            else:
                messagebox.showerror("Error", "❌ No se pudo cerrar el turno.")
        except Exception as e:
            messagebox.showerror("Error", f"❌ Error al cerrar turno: {e}")
    
    def _forzar_cierre(self):
        """Fuerza el cierre del turno seleccionado (solo Supervisor o superior)."""
        if not self.turno_seleccionado:
            messagebox.showwarning("Aviso", "Primero seleccione un turno de la tabla.")
            return
        
        # Verificar permisos
        if not self.usuario_actual.tiene_permiso('forzar_cierre_turno'):
            messagebox.showerror("Acceso Denegado", "Se requiere permiso de Supervisor para forzar cierre.")
            return
        
        # Confirmar
        if not messagebox.askyesno("Confirmar", 
                                   f"⚠️ ¿Forzar cierre del turno #{self.turno_seleccionado}?\n"
                                   "Esta acción requiere autorización de Supervisor."):
            return
        
        # Si el usuario actual es Supervisor o superior, puede forzar directamente
        if self.usuario_actual.rol in ["Supervisor", "Administrador", "Gerente General"]:
            try:
                if Turno.cerrar_turno(self.turno_seleccionado, forzado=True):
                    messagebox.showinfo("Éxito", f"✅ Turno #{self.turno_seleccionado} forzado a cierre.")
                    self.turno_seleccionado = None
                    self.turno_seleccionado_data = None
                    self._cargar_turnos()
                    
                    # Registrar en auditoría
                    self._registrar_auditoria(
                        f"Turno #{self.turno_seleccionado} forzado a cierre por {self.usuario_actual.nombre_usuario}"
                    )
                else:
                    messagebox.showerror("Error", "❌ No se pudo forzar el cierre.")
            except Exception as e:
                messagebox.showerror("Error", f"❌ Error al forzar cierre: {e}")
        else:
            messagebox.showerror("Acceso Denegado", "No tiene permisos para forzar cierre.")
    
    def _generar_reporte(self):
        """Genera un reporte PDF del turno seleccionado."""
        if not self.turno_seleccionado:
            messagebox.showwarning("Aviso", "Primero seleccione un turno de la tabla.")
            return
        
        turno = self.turno_seleccionado_data
        if not turno:
            messagebox.showerror("Error", "No se encontraron datos del turno.")
            return
        
        usuario = Usuario.obtener_por_id(turno.usuario_id)
        total_ventas = (turno.total_ventas_efectivo + turno.total_ventas_debito + 
                        turno.total_ventas_credito + turno.total_ventas_transferencia)
        
        datos_reporte = {
            'turno_id': self.turno_seleccionado,
            'cajero': usuario.nombre_usuario if usuario else 'Desconocido',
            'apertura': turno.fecha_hora_apertura,
            'cierre': turno.fecha_hora_cierre or 'Abierto',
            'estado': turno.estado,
            'fondo_inicial': turno.fondo_inicial,
            'total_efectivo': turno.total_ventas_efectivo,
            'total_debito': turno.total_ventas_debito,
            'total_credito': turno.total_ventas_credito,
            'total_transferencia': turno.total_ventas_transferencia,
            'total_sangrias': turno.total_sangrias,
            'total_ventas': total_ventas
        }
        generar_reporte_turno_pdf(datos_reporte)
    
    # =====================================================================
    # REGISTRO DE SANGRÍA
    # =====================================================================
    def _registrar_sangria(self):
        """Registra una sangría (retiro de efectivo) en el turno seleccionado."""
        if not self.turno_seleccionado:
            messagebox.showwarning("Aviso", "Primero seleccione un turno de la tabla.")
            return
        
        # Verificar que el turno esté abierto
        turno_abierto = Turno.obtener_turno_abierto()
        if not turno_abierto or turno_abierto[0] != self.turno_seleccionado:
            messagebox.showerror("Error", "El turno seleccionado no está abierto.\nSolo se pueden registrar sangrías en turnos abiertos.")
            return
        
        # Verificar permisos (solo Supervisor o superior)
        if not self.usuario_actual.tiene_permiso('autorizar_sangria'):
            messagebox.showerror("Acceso Denegado", "Se requiere permiso de Supervisor para registrar sangrías.")
            return
        
        # Formulario de sangría
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
        
        # Botones
        frame_botones = ctk.CTkFrame(frame, fg_color="transparent")
        frame_botones.pack(fill="x", pady=20)
        
        def guardar_sangria():
            # Validar monto
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
            
            # Registrar sangría
            try:
                from database.config import get_sqlite_connection
                conn = get_sqlite_connection()
                cursor = conn.cursor()
                fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                cursor.execute('''
                    INSERT INTO sangrias (turno_id, cajero_id, supervisor_id, fecha_hora, monto_retirado, motivo)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (self.turno_seleccionado, turno_abierto[1], self.usuario_actual.id, fecha, monto, motivo))
                
                # Actualizar total_sangrias en turnos
                cursor.execute('''
                    UPDATE turnos 
                    SET total_sangrias = total_sangrias + ?
                    WHERE id = ?
                ''', (monto, self.turno_seleccionado))
                
                conn.commit()
                conn.close()
                
                messagebox.showinfo("Éxito", f"✅ Sangría de ${monto:.2f} registrada correctamente.")
                dialog.destroy()
                self._cargar_turnos()
                
                # Registrar en auditoría
                self._registrar_auditoria(
                    f"Sangría registrada en turno #{self.turno_seleccionado} por {self.usuario_actual.nombre_usuario}: ${monto:.2f}"
                )
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
    
    # =====================================================================
    # AUDITORÍA
    # =====================================================================
    def _registrar_auditoria(self, accion, detalle=None):
        """Registra una acción en la tabla logs_auditoria."""
        try:
            from database.config import get_sqlite_connection
            conn = get_sqlite_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO logs_auditoria (usuario_id, accion, detalle)
                VALUES (?, ?, ?)
            ''', (self.usuario_actual.id, accion, detalle))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error al registrar auditoría: {e}")