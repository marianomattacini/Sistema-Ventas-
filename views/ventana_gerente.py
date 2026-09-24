import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime, timedelta
from models.venta import Venta
from models.compra import Compra
from models.producto import Producto
from models.cliente import Cliente
from models.promocion import Promocion
from models.notificacion import Notificacion
from models.usuario import Usuario
from views.base_frame import BaseFrame
import os

class FrameGerente(BaseFrame):
    """
    Panel de control del Gerente General.
    Incluye balances financieros, presupuestos, estadísticas, promociones y notificaciones.
    """

    def __init__(self, parent, controller, usuario_actual, **kwargs):
        super().__init__(parent, controller, usuario_actual)

        if not self.usuario_actual.tiene_permiso('ver_balances'):
            messagebox.showerror("Acceso Denegado", "No tiene permisos para acceder al panel del Gerente.")
            self.controller.volver()
            return

        self.configure(fg_color="#F4F6F9")

        self.filtro_periodo = "Hoy"

        self._crear_widgets()
        self._cargar_datos()

    def _crear_widgets(self):
        frame_principal = ctk.CTkFrame(self, fg_color="#F9FAFB", corner_radius=15, border_width=1, border_color="#B8C1CE")
        frame_principal.pack(fill="both", expand=True, padx=20, pady=20)
        
        barra = ctk.CTkFrame(frame_principal, fg_color="transparent")
        barra.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(barra, text="📊 PANEL DEL GERENTE GENERAL", 
                    font=("Roboto", 24, "bold"), text_color="#1D4ED8"
        ).pack(side="left")
        
        ctk.CTkLabel(barra, text=f"👤 {self.usuario_actual.nombre_usuario}", 
                    font=("Roboto", 14), text_color="#6B7280"
        ).pack(side="right", padx=10)
        
        btn_volver = ctk.CTkButton(barra, text="← Volver", font=("Roboto", 14), height=35,
                                  fg_color="#64748B", hover_color="#D6DBE3",
                                  corner_radius=10, command=self.destroy, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_volver.pack(side="right", padx=10)
        
        self.tabview = ctk.CTkTabview(frame_principal, fg_color="#F4F6F9", corner_radius=10)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Ajuste de tamaño de fuente para evitar corte de palabras
        self.tabview._segmented_button.configure(font=("Roboto", 12))
        
        self.tabview.add("💰 Balance")
        self.tabview.add("📈 Estadísticas")
        self.tabview.add("🏷️ Promociones")
        self.tabview.add("👥 Empleados")
        self.tabview.add("📋 Presupuestos")
        self.tabview.add("⚙️ Config. Pagos")
        self.tabview.add("🔔 Notificaciones")
        
        self._crear_tab_balance()
        self._crear_tab_estadisticas()
        self._crear_tab_promociones()
        self._crear_tab_empleados()
        self._crear_tab_presupuestos()
        self._crear_tab_config_pagos()
        self._crear_tab_notificaciones()
    
    # =====================================================================
    # BALANCE
    # =====================================================================
    def _crear_tab_balance(self):
        tab = self.tabview.tab("💰 Balance")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_columnconfigure(2, weight=1)
        tab.grid_columnconfigure(3, weight=1)
        
        frame_filtros = ctk.CTkFrame(tab, fg_color="#F9FAFB", corner_radius=10, border_width=1, border_color="#B8C1CE")
        frame_filtros.grid(row=0, column=0, columnspan=4, sticky="ew", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(frame_filtros, text="Período:", font=("Roboto", 14, "bold")
        ).pack(side="left", padx=10, pady=10)
        
        for periodo in ["Hoy", "Semana", "Mes", "Año"]:
            btn = ctk.CTkButton(frame_filtros, text=periodo, height=30, width=80,
                               fg_color="#D6DBE3", hover_color="#64748B",
                               corner_radius=10, command=lambda p=periodo: self._cambiar_periodo(p), border_width=1, border_color="#CBD2DC", text_color="#1A2233")
            btn.pack(side="left", padx=5, pady=10)
        
        self.card_ingresos = ctk.CTkFrame(tab, fg_color="#DCFCE7", corner_radius=15)
        self.card_ingresos.grid(row=1, column=0, sticky="nsew", padx=15, pady=10)
        ctk.CTkLabel(self.card_ingresos, text="💰 Ingresos Totales", 
                    font=("Roboto", 16), text_color="#15803D").pack(pady=(20, 5))
        self.lbl_ingresos = ctk.CTkLabel(self.card_ingresos, text="$ 0.00", 
                                        font=("Roboto", 28, "bold"), text_color="#15803D")
        self.lbl_ingresos.pack(pady=10)
        
        self.card_egresos = ctk.CTkFrame(tab, fg_color="#FEE2E2", corner_radius=15)
        self.card_egresos.grid(row=1, column=1, sticky="nsew", padx=15, pady=10)
        ctk.CTkLabel(self.card_egresos, text="📤 Egresos Totales", 
                    font=("Roboto", 16), text_color="#DC2626").pack(pady=(20, 5))
        self.lbl_egresos = ctk.CTkLabel(self.card_egresos, text="$ 0.00", 
                                       font=("Roboto", 28, "bold"), text_color="#DC2626")
        self.lbl_egresos.pack(pady=10)
        
        self.card_ganancia = ctk.CTkFrame(tab, fg_color="#EDE9FE", corner_radius=15)
        self.card_ganancia.grid(row=1, column=2, sticky="nsew", padx=15, pady=10)
        ctk.CTkLabel(self.card_ganancia, text="🏷️ Ganancia Bruta", 
                    font=("Roboto", 16), text_color="#7C3AED").pack(pady=(20, 5))
        self.lbl_ganancia = ctk.CTkLabel(self.card_ganancia, text="$ 0.00", 
                                        font=("Roboto", 28, "bold"), text_color="#8B5CF6")
        self.lbl_ganancia.pack(pady=10)

        self.card_utilidad = ctk.CTkFrame(tab, fg_color="#DBEAFE", corner_radius=15)
        self.card_utilidad.grid(row=1, column=3, sticky="nsew", padx=15, pady=10)
        ctk.CTkLabel(self.card_utilidad, text="📊 Utilidad Neta", 
                    font=("Roboto", 16), text_color="#2563EB").pack(pady=(20, 5))
        self.lbl_utilidad = ctk.CTkLabel(self.card_utilidad, text="$ 0.00", 
                                        font=("Roboto", 28, "bold"), text_color="#2563EB")
        self.lbl_utilidad.pack(pady=10)
        
        frame_detalle = ctk.CTkFrame(tab, fg_color="#F4F6F9", corner_radius=10, border_width=1, border_color="#B8C1CE")
        frame_detalle.grid(row=2, column=0, columnspan=4, sticky="nsew", padx=20, pady=20)
        
        ctk.CTkLabel(frame_detalle, text="Detalle del Período", 
                    font=("Roboto", 16, "bold"), text_color="#6B7280"
        ).pack(pady=(20, 10))
        
        self.lbl_detalle = ctk.CTkLabel(frame_detalle, text="Cargando...", 
                                       font=("Roboto", 14), text_color="#8B93A3")
        self.lbl_detalle.pack(pady=10)
    
    def _cambiar_periodo(self, periodo):
        self.filtro_periodo = periodo
        self._cargar_balance()
    
    def _cargar_balance(self):
        hoy = datetime.now()
        if self.filtro_periodo == "Hoy":
            fecha_inicio = hoy.replace(hour=0, minute=0, second=0, microsecond=0)
        elif self.filtro_periodo == "Semana":
            fecha_inicio = hoy - timedelta(days=7)
        elif self.filtro_periodo == "Mes":
            fecha_inicio = hoy - timedelta(days=30)
        else:
            fecha_inicio = hoy - timedelta(days=365)
        
        fecha_inicio_str = fecha_inicio.strftime("%Y-%m-%d %H:%M:%S")
        fecha_fin_str = hoy.strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            from database.config import get_sqlite_connection
            conn = get_sqlite_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT SUM(total_facturado), COUNT(*)
                FROM ventas_cabecera 
                WHERE estado = 'Completado' AND fecha_hora BETWEEN ? AND ?
            ''', (fecha_inicio_str, fecha_fin_str))
            fila = cursor.fetchone()
            total_ventas = fila[0] or 0.0
            cantidad_tickets = fila[1] or 0
            
            cursor.execute('''
                SELECT SUM(total_factura), COUNT(*)
                FROM compras_cabecera 
                WHERE estado = 'Ingresado' AND fecha_hora BETWEEN ? AND ?
            ''', (fecha_inicio_str, fecha_fin_str))
            fila = cursor.fetchone()
            total_compras = fila[0] or 0.0
            cantidad_compras = fila[1] or 0
            
            cursor.execute('''
                SELECT SUM(monto_planificado) 
                FROM presupuestos 
                WHERE mes = ? AND anio = ?
            ''', (hoy.month, hoy.year))
            gastos_planificados = cursor.fetchone()[0] or 0.0

            # Ganancia bruta real: (precio de venta - costo) por cada unidad vendida
            # en el período, según lo que efectivamente costó reponer cada producto.
            cursor.execute('''
                SELECT SUM((vd.subtotal - COALESCE(vd.descuento, 0)) - (vd.cantidad * p.precio_costo))
                FROM ventas_detalle vd
                JOIN ventas_cabecera vc ON vd.nro_ticket = vc.nro_ticket
                JOIN productos p ON vd.codigo_producto = p.codigo_barras
                WHERE vc.estado = 'Completado' AND vc.fecha_hora BETWEEN ? AND ?
            ''', (fecha_inicio_str, fecha_fin_str))
            ganancia_bruta = cursor.fetchone()[0] or 0.0
            
            total_egresos = total_compras + gastos_planificados
            utilidad = total_ventas - total_egresos
            
            conn.close()
            
            self.lbl_ingresos.configure(text=f"$ {total_ventas:,.2f}")
            self.lbl_egresos.configure(text=f"$ {total_egresos:,.2f}")
            self.lbl_ganancia.configure(text=f"$ {ganancia_bruta:,.2f}")
            self.lbl_utilidad.configure(text=f"$ {utilidad:,.2f}")
            
            detalle = f"📅 Período: {self.filtro_periodo}\n"
            detalle += f"✅ Ventas totales: {cantidad_tickets} tickets\n"
            detalle += f"📦 Compras registradas: {cantidad_compras} compras\n"
            detalle += f"📊 Gastos planificados: $ {gastos_planificados:,.2f}\n"
            detalle += f"💹 Ganancia bruta (venta - costo de mercadería): $ {ganancia_bruta:,.2f}\n"
            detalle += f"📈 Utilidad neta (caja): $ {utilidad:,.2f}"
            self.lbl_detalle.configure(text=detalle)
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el balance: {e}")
    
    # =====================================================================
    # ESTADÍSTICAS
    # =====================================================================
    def _crear_tab_estadisticas(self):
        tab = self.tabview.tab("📈 Estadísticas")
        
        frame_filtros = ctk.CTkFrame(tab, fg_color="#F9FAFB", corner_radius=10, border_width=1, border_color="#B8C1CE")
        frame_filtros.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(frame_filtros, text="Filtrar por:", font=("Roboto", 14, "bold")
        ).pack(side="left", padx=10, pady=10)
        
        self.combo_estadistica = ctk.CTkOptionMenu(frame_filtros, 
            values=["Todos", "Productos", "Categorías", "Métodos de Pago"],
            width=150, height=35, corner_radius=10,
            command=self._actualizar_estadisticas, text_color="#FFFFFF")
        self.combo_estadistica.pack(side="left", padx=10, pady=10)
        self.combo_estadistica.set("Todos")
        
        btn_exportar = ctk.CTkButton(frame_filtros, text="📤 Exportar a PDF", height=35,
                                   fg_color="#7C3AED", hover_color="#6D28D9",
                                   corner_radius=10, command=self._exportar_estadisticas_pdf, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_exportar.pack(side="right", padx=10, pady=10)
        
        self.frame_estadisticas = ctk.CTkScrollableFrame(tab, fg_color="#F4F6F9", corner_radius=10)
        self.frame_estadisticas.pack(fill="both", expand=True, padx=20, pady=(20, 10))
        
        self._cargar_estadisticas()

        # --- Predicción de ventas (regresión lineal) ---
        frame_prediccion = ctk.CTkFrame(tab, fg_color="#F4F6F9", corner_radius=10, border_width=1, border_color="#B8C1CE")
        frame_prediccion.pack(fill="x", padx=20, pady=(0, 20))

        header_pred = ctk.CTkFrame(frame_prediccion, fg_color="transparent")
        header_pred.pack(fill="x", padx=20, pady=(20, 5))
        ctk.CTkLabel(header_pred, text="🔮 Predicción de Ventas — Próximo Trimestre",
                    font=("Roboto", 16, "bold"), text_color="#1D4ED8"
        ).pack(side="left")
        ctk.CTkButton(header_pred, text="Generar Predicción", height=32, width=160,
                     font=("Roboto", 12, "bold"), fg_color="#2563EB", hover_color="#2563EB",
                     corner_radius=10, command=self._generar_prediccion_ventas
        , border_width=1, border_color="#CBD2DC", text_color="#FFFFFF").pack(side="right")

        ctk.CTkLabel(
            frame_prediccion,
            text=("Regresión lineal (Ridge) sobre el historial de ventas: tendencia, estacionalidad "
                  "semanal/anual y promociones activas como variable externa."),
            font=("Roboto", 11), text_color="#8B93A3", wraplength=900, justify="left"
        ).pack(anchor="w", padx=20, pady=(0, 10))

        self.frame_resultado_prediccion = ctk.CTkFrame(frame_prediccion, fg_color="transparent")
        self.frame_resultado_prediccion.pack(fill="x", padx=20, pady=(0, 20))
    
    def _actualizar_estadisticas(self, choice):
        self._cargar_estadisticas()

    def _generar_prediccion_ventas(self):
        for widget in self.frame_resultado_prediccion.winfo_children():
            widget.destroy()

        ctk.CTkLabel(self.frame_resultado_prediccion, text="Calculando...",
                    font=("Roboto", 12), text_color="#8B93A3").pack(pady=10)
        self.update_idletasks()

        try:
            from models.prediccion_ventas import PrediccionVentas
            resultado = PrediccionVentas().generar_prediccion()
        except Exception as e:
            for widget in self.frame_resultado_prediccion.winfo_children():
                widget.destroy()
            ctk.CTkLabel(self.frame_resultado_prediccion,
                        text=f"❌ No se pudo generar la predicción: {e}",
                        font=("Roboto", 12), text_color="#DC2626").pack(pady=10)
            return

        for widget in self.frame_resultado_prediccion.winfo_children():
            widget.destroy()

        if not resultado["ok"]:
            ctk.CTkLabel(self.frame_resultado_prediccion, text=f"ℹ️ {resultado['motivo']}",
                        font=("Roboto", 12), text_color="#C2410C",
                        wraplength=900, justify="left").pack(pady=10, anchor="w")
            return

        # --- Gráfico de barras: 3 meses proyectados ---
        frame_barras = ctk.CTkFrame(self.frame_resultado_prediccion, fg_color="#F9FAFB", corner_radius=10, border_width=1, border_color="#B8C1CE")
        frame_barras.pack(fill="x", pady=(0, 10))
        cont_barras = ctk.CTkFrame(frame_barras, fg_color="transparent")
        cont_barras.pack(fill="x", padx=20, pady=20)
        cont_barras.grid_columnconfigure(tuple(range(3)), weight=1)

        meses = resultado["prediccion_mensual"]
        maximo = max((m["total"] for m in meses), default=1) or 1
        for i, m in enumerate(meses):
            col = ctk.CTkFrame(cont_barras, fg_color="transparent")
            col.grid(row=0, column=i, sticky="nsew", padx=10)
            alto = max(int(120 * (m["total"] / maximo)), 4)
            relleno = ctk.CTkFrame(col, fg_color="transparent", height=120 - alto)
            relleno.pack(fill="x")
            ctk.CTkFrame(col, fg_color="#1D4ED8", corner_radius=6, height=alto).pack(fill="x")
            ctk.CTkLabel(col, text=f"${m['total']:,.0f}", font=("Roboto", 12, "bold"),
                        text_color="#1A2233").pack(pady=(6, 0))
            ctk.CTkLabel(col, text=m["etiqueta"], font=("Roboto", 11),
                        text_color="#6B7280").pack()

        # --- Totales y calidad del modelo ---
        iconos_tendencia = {"creciendo": "📈", "cayendo": "📉", "estable": "➡️"}
        frame_info = ctk.CTkFrame(self.frame_resultado_prediccion, fg_color="#F9FAFB", corner_radius=10, border_width=1, border_color="#B8C1CE")
        frame_info.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(
            frame_info,
            text=(f"Total estimado del trimestre: ${resultado['total_trimestre']:,.2f}   |   "
                  f"Tendencia detectada: {iconos_tendencia.get(resultado['tendencia'], '')} {resultado['tendencia']}   |   "
                  f"Historial usado: {resultado['dias_historial']} días"),
            font=("Roboto", 13, "bold"), text_color="#15803D", wraplength=900, justify="left"
        ).pack(anchor="w", padx=15, pady=(15, 5))

        calidad = f"R² sobre historial: {resultado['r2_entrenamiento']}"
        if resultado["r2_validacion"] is not None:
            calidad += (f"   |   R² de validación (últimos 14 días no usados para entrenar): "
                        f"{resultado['r2_validacion']}   |   Error promedio: ${resultado['mae_validacion']:,.2f}/día")
        ctk.CTkLabel(frame_info, text=calidad, font=("Roboto", 11), text_color="#6B7280",
                    wraplength=900, justify="left").pack(anchor="w", padx=15, pady=(0, 15))

        # --- Disclaimer correlación ≠ causalidad ---
        ctk.CTkLabel(
            self.frame_resultado_prediccion,
            text=("⚠️ Esto es una proyección estadística basada en patrones del historial (tendencia, "
                  "día de la semana, época del año, promociones), no una garantía. Los patrones detectados "
                  "son correlaciones, no relaciones de causa-efecto comprobadas, y el modelo no puede "
                  "anticipar cambios de mercado que todavía no se reflejaron en las ventas pasadas "
                  "(nueva competencia, crisis económica, cambios de precios, etc.)."),
            font=("Roboto", 10), text_color="#8B93A3", wraplength=900, justify="left"
        ).pack(anchor="w", pady=(0, 10))
    
    def _cargar_estadisticas(self):
        for widget in self.frame_estadisticas.winfo_children():
            widget.destroy()
        
        try:
            from database.config import get_sqlite_connection
            conn = get_sqlite_connection()
            cursor = conn.cursor()
            
            filtro = self.combo_estadistica.get()
            
            if filtro in ["Todos", "Productos"]:
                cursor.execute('''
                    SELECT p.nombre, SUM(vd.cantidad) as total_vendido,
                           SUM((vd.subtotal - COALESCE(vd.descuento,0)) - (vd.cantidad * p.precio_costo)) as ganancia
                    FROM ventas_detalle vd
                    JOIN productos p ON vd.codigo_producto = p.codigo_barras
                    JOIN ventas_cabecera vc ON vd.nro_ticket = vc.nro_ticket
                    WHERE vc.estado = 'Completado'
                    GROUP BY vd.codigo_producto
                    ORDER BY total_vendido DESC
                    LIMIT 20
                ''')
                productos = cursor.fetchall()
                if productos:
                    ctk.CTkLabel(self.frame_estadisticas, text="🏆 Productos Más Vendidos", 
                                font=("Roboto", 16, "bold"), text_color="#1D4ED8"
                    ).pack(anchor="w", pady=(10, 5))
                    for nombre, total, ganancia in productos:
                        frame = ctk.CTkFrame(self.frame_estadisticas, fg_color="#F9FAFB", corner_radius=8, border_width=1, border_color="#B8C1CE")
                        frame.pack(fill="x", pady=3)
                        ctk.CTkLabel(frame, text=nombre, font=("Roboto", 14)).pack(side="left", padx=10)
                        frame_der = ctk.CTkFrame(frame, fg_color="transparent")
                        frame_der.pack(side="right", padx=10)
                        ctk.CTkLabel(frame_der, text=f"{total} unidades", font=("Roboto", 14, "bold"),
                                    text_color="#15803D").pack(side="left", padx=(0, 10))
                        ctk.CTkLabel(frame_der, text=f"💹 ${(ganancia or 0):,.2f}", font=("Roboto", 12),
                                    text_color="#C2410C").pack(side="left")
            
            if filtro in ["Todos", "Métodos de Pago"]:
                cursor.execute('''
                    SELECT metodo_pago, SUM(monto_abonado) as total
                    FROM ventas_pagos
                    GROUP BY metodo_pago
                    ORDER BY total DESC
                ''')
                pagos = cursor.fetchall()
                if pagos:
                    ctk.CTkLabel(self.frame_estadisticas, text="💳 Distribución de Pagos", 
                                font=("Roboto", 16, "bold"), text_color="#1D4ED8"
                    ).pack(anchor="w", pady=(20, 5))
                    total_general = sum(p[1] for p in pagos)
                    for metodo, total in pagos:
                        porcentaje = (total / total_general * 100) if total_general > 0 else 0
                        frame = ctk.CTkFrame(self.frame_estadisticas, fg_color="#F9FAFB", corner_radius=8, border_width=1, border_color="#B8C1CE")
                        frame.pack(fill="x", pady=3)
                        ctk.CTkLabel(frame, text=metodo, font=("Roboto", 14)).pack(side="left", padx=10)
                        ctk.CTkLabel(frame, text=f"${total:,.2f} ({porcentaje:.1f}%)", 
                                    font=("Roboto", 14, "bold"),
                                    text_color="#C2410C").pack(side="right", padx=10)
            
            if not self.frame_estadisticas.winfo_children():
                ctk.CTkLabel(self.frame_estadisticas, text="No hay datos para mostrar.", 
                            font=("Roboto", 14), text_color="#8B93A3"
                ).pack(pady=20)
            
            conn.close()
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar estadísticas: {e}")
    
    def _exportar_estadisticas_pdf(self):
        """Exporta las estadísticas actuales a un PDF."""
        try:
            from fpdf import FPDF
            from database.config import get_sqlite_connection
            from datetime import datetime
            import os

            conn = get_sqlite_connection()
            cursor = conn.cursor()

            pdf = FPDF(orientation='L', unit='mm', format='A4')
            pdf.add_page()
            pdf.set_font("Courier", size=10)
            pdf.set_margins(left=10, top=10, right=10)

            pdf.set_font("Courier", 'B', 16)
            pdf.cell(0, 10, "KWIK-E-MART - ESTADÍSTICAS DE VENTAS", ln=True, align='C')
            pdf.set_font("Courier", size=10)
            pdf.cell(0, 6, f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align='C')
            pdf.ln(5)

            # Top productos
            pdf.set_font("Courier", 'B', 12)
            pdf.cell(0, 6, "TOP 20 PRODUCTOS MÁS VENDIDOS", ln=True)
            pdf.set_font("Courier", size=10)
            cursor.execute('''
                SELECT p.nombre, SUM(vd.cantidad) as total_vendido
                FROM ventas_detalle vd
                JOIN productos p ON vd.codigo_producto = p.codigo_barras
                GROUP BY vd.codigo_producto
                ORDER BY total_vendido DESC
                LIMIT 20
            ''')
            productos = cursor.fetchall()
            for nombre, total in productos:
                pdf.cell(0, 5, f"- {nombre}: {total} unidades", ln=True)

            pdf.ln(5)
            pdf.set_font("Courier", 'B', 12)
            pdf.cell(0, 6, "DISTRIBUCIÓN DE PAGOS", ln=True)
            pdf.set_font("Courier", size=10)
            cursor.execute('''
                SELECT metodo_pago, SUM(monto_abonado) as total
                FROM ventas_pagos
                GROUP BY metodo_pago
                ORDER BY total DESC
            ''')
            pagos = cursor.fetchall()
            total_general = sum(p[1] for p in pagos)
            for metodo, total in pagos:
                porcentaje = (total / total_general * 100) if total_general > 0 else 0
                pdf.cell(0, 5, f"- {metodo}: ${total:,.2f} ({porcentaje:.1f}%)", ln=True)

            pdf.ln(5)
            pdf.cell(0, 6, f"Total general: ${total_general:,.2f}", ln=True)
            conn.close()

            # Guardar y abrir
            nombre_archivo = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tickets", f"estadisticas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
            os.makedirs(os.path.dirname(nombre_archivo), exist_ok=True)
            pdf.output(nombre_archivo)

            if os.name == 'nt':
                os.startfile(nombre_archivo)
            messagebox.showinfo("Exportar", f"✅ Estadísticas exportadas a:\n{nombre_archivo}")

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar: {str(e)}")
    
    # =====================================================================
    # EMPLEADOS
    # =====================================================================
    def _crear_tab_empleados(self):
        tab = self.tabview.tab("👥 Empleados")
        frame_acciones = ctk.CTkFrame(tab, fg_color="transparent")
        frame_acciones.pack(fill="x", padx=20, pady=10)
        
        btn_nuevo = ctk.CTkButton(frame_acciones, text="➕ Nuevo Empleado", height=40,
                                 fg_color="#15803D", hover_color="#166534",
                                 corner_radius=10, command=self._abrir_empleado, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_nuevo.pack(side="left", padx=5)
        
        btn_refrescar = ctk.CTkButton(frame_acciones, text="🔄 Refrescar", height=40,
                                     fg_color="#64748B", hover_color="#D6DBE3",
                                     corner_radius=10, command=self._cargar_empleados, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_refrescar.pack(side="left", padx=5)
        
        self.frame_empleados = ctk.CTkScrollableFrame(tab, fg_color="#F4F6F9", corner_radius=10)
        self.frame_empleados.pack(fill="both", expand=True, padx=20, pady=20)
        self._cargar_empleados()
    
    def _cargar_empleados(self):
        for widget in self.frame_empleados.winfo_children():
            widget.destroy()
        try:
            from models.empleado import Empleado
            empleados = Empleado.obtener_todos()
            if not empleados:
                ctk.CTkLabel(self.frame_empleados, text="No hay empleados registrados.", 
                            font=("Roboto", 14), text_color="#8B93A3").pack(pady=20)
                return
            for emp in empleados:
                frame = ctk.CTkFrame(self.frame_empleados, fg_color="#F9FAFB", corner_radius=10, border_width=1, border_color="#B8C1CE")
                frame.pack(fill="x", pady=5)
                texto = f"{emp.nombre_completo} - {emp.rol} (DNI: {emp.dni})"
                ctk.CTkLabel(frame, text=texto, font=("Roboto", 14), text_color="#1A2233").pack(side="left", padx=10)
                if emp.estado == "Activo":
                    ctk.CTkLabel(frame, text="🟢 Activo", font=("Roboto", 12), text_color="#15803D").pack(side="left", padx=10)
                else:
                    ctk.CTkLabel(frame, text="🔴 Inactivo", font=("Roboto", 12), text_color="#DC2626").pack(side="left", padx=10)
                btn_ver = ctk.CTkButton(frame, text="Ver Detalles", height=25,
                                      fg_color="#2563EB", hover_color="#1D4ED8",
                                      corner_radius=5, command=lambda e=emp: self._ver_empleado(e), border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
                btn_ver.pack(side="right", padx=5)
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar empleados: {e}")
    
    def _abrir_empleado(self):
        self.controller.mostrar_pantalla("empleados")
    
    def _ver_empleado(self, empleado):
        self.controller.mostrar_pantalla("empleados", empleado=empleado)
    
    # =====================================================================
    # PRESUPUESTOS
    # =====================================================================
    def _crear_tab_presupuestos(self):
        tab = self.tabview.tab("📋 Presupuestos")
        frame_acciones = ctk.CTkFrame(tab, fg_color="transparent")
        frame_acciones.pack(fill="x", padx=20, pady=10)
        btn_nuevo = ctk.CTkButton(frame_acciones, text="➕ Nuevo Gasto Planificado", height=40,
                                 fg_color="#15803D", hover_color="#166534",
                                 corner_radius=10, command=self._abrir_presupuesto, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_nuevo.pack(side="left", padx=5)
        btn_refrescar = ctk.CTkButton(frame_acciones, text="🔄 Refrescar", height=40,
                                     fg_color="#64748B", hover_color="#D6DBE3",
                                     corner_radius=10, command=self._cargar_presupuestos, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_refrescar.pack(side="left", padx=5)
        self.frame_presupuestos = ctk.CTkScrollableFrame(tab, fg_color="#F4F6F9", corner_radius=10)
        self.frame_presupuestos.pack(fill="both", expand=True, padx=20, pady=20)
        self._cargar_presupuestos()
    
    def _cargar_presupuestos(self):
        for widget in self.frame_presupuestos.winfo_children():
            widget.destroy()
        try:
            from models.presupuesto import Presupuesto
            presupuestos = Presupuesto.obtener_todos()
            if not presupuestos:
                ctk.CTkLabel(self.frame_presupuestos, text="No hay gastos planificados.", 
                            font=("Roboto", 14), text_color="#8B93A3").pack(pady=20)
                return
            for p in presupuestos:
                frame = ctk.CTkFrame(self.frame_presupuestos, fg_color="#F9FAFB", corner_radius=10, border_width=1, border_color="#B8C1CE")
                frame.pack(fill="x", pady=5)
                texto = f"{p.categoria} - ${p.monto_planificado:.2f} ({p.mes}/{p.anio})"
                ctk.CTkLabel(frame, text=texto, font=("Roboto", 14), text_color="#1A2233").pack(side="left", padx=10)
                btn_editar = ctk.CTkButton(frame, text="✏️", width=30, height=25,
                                         fg_color="#2563EB", hover_color="#1D4ED8",
                                         corner_radius=5, command=lambda id=p.id: self._editar_presupuesto(id), border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
                btn_editar.pack(side="right", padx=5)
                btn_eliminar = ctk.CTkButton(frame, text="🗑️", width=30, height=25,
                                           fg_color="#DC2626", hover_color="#B91C1C",
                                           corner_radius=5, command=lambda id=p.id: self._eliminar_presupuesto(id), border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
                btn_eliminar.pack(side="right", padx=5)
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar presupuestos: {e}")
    
    def _abrir_presupuesto(self):
        self.controller.mostrar_pantalla("presupuestos")
    
    def _editar_presupuesto(self, id):
        self.controller.mostrar_pantalla("presupuestos", presupuesto_id=id)
    
    def _eliminar_presupuesto(self, id):
        if messagebox.askyesno("Confirmar", "¿Eliminar este gasto planificado?"):
            from models.presupuesto import Presupuesto
            Presupuesto.eliminar(id)
            self._cargar_presupuestos()
    
    # =====================================================================
    # CONFIGURACIÓN DE PAGOS
    # =====================================================================
    def _crear_tab_config_pagos(self):
        tab = self.tabview.tab("⚙️ Config. Pagos")
        frame_acciones = ctk.CTkFrame(tab, fg_color="transparent")
        frame_acciones.pack(fill="x", padx=20, pady=10)
        btn_nueva = ctk.CTkButton(frame_acciones, text="➕ Nueva Entidad de Pago", height=40,
                                 fg_color="#15803D", hover_color="#166534",
                                 corner_radius=10, command=self._abrir_entidad_pago, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_nueva.pack(side="left", padx=5)
        btn_refrescar = ctk.CTkButton(frame_acciones, text="🔄 Refrescar", height=40,
                                     fg_color="#64748B", hover_color="#D6DBE3",
                                     corner_radius=10, command=self._cargar_entidades_pago, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_refrescar.pack(side="left", padx=5)
        self.frame_entidades = ctk.CTkScrollableFrame(tab, fg_color="#F4F6F9", corner_radius=10)
        self.frame_entidades.pack(fill="both", expand=True, padx=20, pady=20)
        self._cargar_entidades_pago()
    
    def _cargar_entidades_pago(self):
        for widget in self.frame_entidades.winfo_children():
            widget.destroy()
        try:
            from models.entidad_pago import EntidadPago
            entidades = EntidadPago.obtener_todos()
            if not entidades:
                ctk.CTkLabel(self.frame_entidades, text="No hay entidades de pago configuradas.", 
                            font=("Roboto", 14), text_color="#8B93A3").pack(pady=20)
                return
            for ent in entidades:
                frame = ctk.CTkFrame(self.frame_entidades, fg_color="#F9FAFB", corner_radius=10, border_width=1, border_color="#B8C1CE")
                frame.pack(fill="x", pady=5)
                texto = f"{ent.nombre} ({ent.tipo}) - Cuotas máximas: {ent.cuotas_maximas}"
                if ent.activa:
                    texto += " ✅ Activa"
                else:
                    texto += " ❌ Inactiva"
                ctk.CTkLabel(frame, text=texto, font=("Roboto", 14), text_color="#1A2233").pack(side="left", padx=10)
                btn_editar = ctk.CTkButton(frame, text="✏️", width=30, height=25,
                                         fg_color="#2563EB", hover_color="#1D4ED8",
                                         corner_radius=5, command=lambda id=ent.id: self._editar_entidad_pago(id), border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
                btn_editar.pack(side="right", padx=5)
                btn_toggle = ctk.CTkButton(frame, text="🔄 Activar/Desactivar", height=25,
                                         fg_color="#C2410C", hover_color="#9A3412",
                                         corner_radius=5, command=lambda id=ent.id: self._toggle_entidad_pago(id), border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
                btn_toggle.pack(side="right", padx=5)
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar entidades: {e}")
    
    def _abrir_entidad_pago(self):
        self.controller.mostrar_pantalla("entidad_pago")
    
    def _editar_entidad_pago(self, id):
        self.controller.mostrar_pantalla("entidad_pago", entidad_id=id)
    
    def _toggle_entidad_pago(self, id):
        from models.entidad_pago import EntidadPago
        ent = EntidadPago.obtener_por_id(id)
        if ent:
            ent.activa = not ent.activa
            ent.guardar()
            self._cargar_entidades_pago()
    
    # =====================================================================
    # PROMOCIONES (CON SCROLL Y BOTONES VISIBLES)
    # =====================================================================
    def _crear_tab_promociones(self):
        tab = self.tabview.tab("🏷️ Promociones")
        frame_acciones = ctk.CTkFrame(tab, fg_color="transparent")
        frame_acciones.pack(fill="x", padx=20, pady=10)
        btn_nueva = ctk.CTkButton(frame_acciones, text="➕ Nueva Promoción", height=40,
                                 fg_color="#15803D", hover_color="#166534",
                                 corner_radius=10, command=self._crear_promocion, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_nueva.pack(side="left", padx=5)
        btn_refrescar = ctk.CTkButton(frame_acciones, text="🔄 Refrescar", height=40,
                                     fg_color="#64748B", hover_color="#D6DBE3",
                                     corner_radius=10, command=self._cargar_promociones, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_refrescar.pack(side="left", padx=5)
        self.frame_promociones = ctk.CTkScrollableFrame(tab, fg_color="#F4F6F9", corner_radius=10)
        self.frame_promociones.pack(fill="both", expand=True, padx=20, pady=20)
        self._cargar_promociones()
    
    def _cargar_promociones(self):
        for widget in self.frame_promociones.winfo_children():
            widget.destroy()
        promociones = Promocion.obtener_promociones_activas()
        if not promociones:
            ctk.CTkLabel(self.frame_promociones, text="No hay promociones activas.", 
                        font=("Roboto", 14), text_color="#8B93A3").pack(pady=20)
            return
        for promocion in promociones:
            frame_item = ctk.CTkFrame(self.frame_promociones, fg_color="#F9FAFB", corner_radius=10, border_width=1, border_color="#B8C1CE")
            frame_item.pack(fill="x", pady=5)
            texto = f"{promocion.tipo}"
            if promocion.producto_id:
                producto = Producto.buscar_por_codigo(promocion.producto_id)
                if producto:
                    texto += f" - {producto.nombre}"
            elif promocion.categoria_id:
                texto += f" - Categoría ID: {promocion.categoria_id}"
            if promocion.cantidad_minima:
                texto += f" (mínimo {promocion.cantidad_minima} unidades)"
            if promocion.descuento_aplicado > 0:
                texto += f" - Descuento: {promocion.descuento_aplicado}%"
            ctk.CTkLabel(frame_item, text=texto, font=("Roboto", 14), text_color="#1A2233").pack(side="left", padx=10)
            fechas = f"Vigencia: {promocion.fecha_inicio} hasta {promocion.fecha_fin}"
            ctk.CTkLabel(frame_item, text=fechas, font=("Roboto", 12), text_color="#6B7280").pack(side="left", padx=10)
            btn_desactivar = ctk.CTkButton(frame_item, text="Desactivar", height=25,
                                         fg_color="#DC2626", hover_color="#B91C1C",
                                         corner_radius=5, command=lambda p=promocion: self._desactivar_promocion(p), border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
            btn_desactivar.pack(side="right", padx=5)
    
    def _crear_promocion(self):
        """Diálogo para crear promoción con scroll y botones visibles."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Nueva Promoción")
        dialog.geometry("600x700")
        dialog.configure(fg_color="#F9FAFB")
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        dialog.lift()
        dialog.focus_force()
        dialog.grab_set()
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 300
        y = (dialog.winfo_screenheight() // 2) - 350
        dialog.geometry(f"600x700+{x}+{y}")

        frame_scroll = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        frame_scroll.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame_scroll, text="➕ Nueva Promoción", font=("Roboto", 20, "bold"), 
                    text_color="#1D4ED8").pack(pady=(0, 20))

        campos = [
            ("Tipo (3x2 / DescuentoCantidad / DescuentoCategoria / DescuentoProducto)", "tipo"),
            ("Producto ID (opcional)", "producto_id"),
            ("Categoría ID (opcional)", "categoria_id"),
            ("Cantidad Mínima", "cantidad_minima"),
            ("Descuento % (ej. 10 para 10%)", "descuento_aplicado"),
            ("Fecha Inicio (YYYY-MM-DD)", "fecha_inicio"),
            ("Fecha Fin (YYYY-MM-DD)", "fecha_fin"),
        ]

        entradas = {}
        for etiqueta, clave in campos:
            ctk.CTkLabel(frame_scroll, text=etiqueta, font=("Roboto", 12, "bold"),
                        text_color="#6B7280").pack(anchor="w", pady=(10, 5))
            entrada = ctk.CTkEntry(frame_scroll, font=("Roboto", 13), height=35,
                                  fg_color="#D6DBE3", text_color="#1A2233")
            entrada.pack(fill="x", padx=0, pady=(0, 5))
            if clave == 'tipo':
                entrada.insert(0, "3x2")
            entradas[clave] = entrada

        def guardar():
            try:
                datos = {}
                for clave, entrada in entradas.items():
                    valor = entrada.get().strip()
                    if clave == 'tipo' and not valor:
                        raise ValueError("El tipo es obligatorio.")
                    if clave in ['producto_id', 'categoria_id']:
                        datos[clave] = valor if valor else None
                    elif clave in ['cantidad_minima', 'descuento_aplicado']:
                        datos[clave] = int(valor) if valor else 0
                    else:
                        datos[clave] = valor
                if not datos.get('fecha_inicio') or not datos.get('fecha_fin'):
                    raise ValueError("Las fechas de inicio y fin son obligatorias.")
                nueva = Promocion(
                    tipo=datos['tipo'],
                    producto_id=datos.get('producto_id'),
                    categoria_id=datos.get('categoria_id'),
                    cantidad_minima=datos.get('cantidad_minima', 0),
                    descuento_aplicado=datos.get('descuento_aplicado', 0),
                    fecha_inicio=datos['fecha_inicio'],
                    fecha_fin=datos['fecha_fin']
                )
                if nueva.guardar():
                    messagebox.showinfo("Éxito", "✅ Promoción creada correctamente.")
                    dialog.destroy()
                    self._cargar_promociones()
                else:
                    messagebox.showerror("Error", "❌ No se pudo crear la promoción.")
            except ValueError as e:
                messagebox.showerror("Error", str(e))
            except Exception as e:
                messagebox.showerror("Error", f"Error: {e}")

        # Botones siempre visibles
        frame_botones = ctk.CTkFrame(frame_scroll, fg_color="transparent")
        frame_botones.pack(fill="x", pady=20)

        btn_guardar = ctk.CTkButton(frame_botones, text="💾 Guardar", height=40,
                                   fg_color="#15803D", hover_color="#166534",
                                   corner_radius=10, command=guardar, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_guardar.pack(side="left", fill="x", expand=True, padx=5)

        btn_cancelar = ctk.CTkButton(frame_botones, text="Cancelar", height=40,
                                    fg_color="#64748B", hover_color="#D6DBE3",
                                    corner_radius=10, command=dialog.destroy, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_cancelar.pack(side="left", fill="x", expand=True, padx=5)
    
    def _desactivar_promocion(self, promocion):
        if messagebox.askyesno("Confirmar", f"¿Desactivar promoción '{promocion.tipo}'?"):
            if promocion.cambiar_estado('Inactiva'):
                messagebox.showinfo("Éxito", "Promoción desactivada.")
                self._cargar_promociones()
            else:
                messagebox.showerror("Error", "No se pudo desactivar la promoción.")
    
    # =====================================================================
    # NOTIFICACIONES
    # =====================================================================
    def _crear_tab_notificaciones(self):
        tab = self.tabview.tab("🔔 Notificaciones")
        frame_acciones = ctk.CTkFrame(tab, fg_color="transparent")
        frame_acciones.pack(fill="x", padx=20, pady=10)
        btn_refrescar = ctk.CTkButton(frame_acciones, text="🔄 Refrescar", height=40,
                                     fg_color="#64748B", hover_color="#D6DBE3",
                                     corner_radius=10, command=self._cargar_notificaciones, border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
        btn_refrescar.pack(side="left", padx=5)
        self.frame_notificaciones = ctk.CTkScrollableFrame(tab, fg_color="#F4F6F9", corner_radius=10)
        self.frame_notificaciones.pack(fill="both", expand=True, padx=20, pady=20)
        self._cargar_notificaciones()
    
    def _cargar_notificaciones(self):
        for widget in self.frame_notificaciones.winfo_children():
            widget.destroy()
        notificaciones = Notificacion.obtener_notificaciones_por_usuario(self.usuario_actual.id)
        no_leidas = Notificacion.contar_no_leidas(self.usuario_actual.id)
        if not notificaciones:
            ctk.CTkLabel(self.frame_notificaciones, text="No hay notificaciones.", 
                        font=("Roboto", 14), text_color="#8B93A3").pack(pady=20)
            return
        ctk.CTkLabel(self.frame_notificaciones, text=f"📩 Notificaciones no leídas: {no_leidas}", 
                    font=("Roboto", 16, "bold"), text_color="#DC2626").pack(anchor="w", pady=(10, 20))
        for notificacion in notificaciones:
            frame_item = ctk.CTkFrame(self.frame_notificaciones, fg_color="#F9FAFB", corner_radius=10, border_width=1, border_color="#B8C1CE")
            frame_item.pack(fill="x", pady=5)
            icono = "🔒" if notificacion.tipo == "Seguridad" else "⚙️"
            estado = "📩" if notificacion.leida == 0 else "✅"
            ctk.CTkLabel(frame_item, text=f"{icono} [{notificacion.tipo}]", font=("Roboto", 12, "bold"), text_color="#6B7280").pack(side="left", padx=10)
            ctk.CTkLabel(frame_item, text=notificacion.mensaje, font=("Roboto", 14), text_color="#1A2233").pack(side="left", padx=10)
            ctk.CTkLabel(frame_item, text=f"{estado} {notificacion.fecha_hora}", font=("Roboto", 12), text_color="#8B93A3").pack(side="right", padx=10)
            if notificacion.leida == 0:
                btn_marcar = ctk.CTkButton(frame_item, text="Marcar como leída", height=25,
                                         fg_color="#15803D", hover_color="#166534",
                                         corner_radius=5, command=lambda n=notificacion: self._marcar_notificacion(n), border_width=1, border_color="#CBD2DC", text_color="#FFFFFF")
                btn_marcar.pack(side="right", padx=5)
    
    def _marcar_notificacion(self, notificacion):
        if notificacion.marcar_como_leida():
            messagebox.showinfo("Éxito", "Notificación marcada como leída.")
            self._cargar_notificaciones()
        else:
            messagebox.showerror("Error", "No se pudo marcar la notificación.")
    
    def _cargar_datos(self):
        self._cargar_balance()
        self._cargar_estadisticas()
        self._cargar_promociones()
        self._cargar_empleados()
        self._cargar_presupuestos()
        self._cargar_entidades_pago()
        self._cargar_notificaciones()