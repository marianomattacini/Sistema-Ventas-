import os
import datetime
from fpdf import FPDF
import subprocess

# =====================================================================
# CONFIGURACIÓN DEL TICKET
# =====================================================================
EMPRESA = "KWIK-E-MART"
DIRECCION = "AV. SAN MARTIN 420"
CUIT = "30-68731043-4"
IIBB = "30-68731043-4"
INICIO_ACTIVIDAD = "11/30/1995"
TELEFONO = "11-5555-7030 / 0-800-666-1518"
CONDICION_IVA = "IVA RESPONSABLE INSCRIPTO"
TIPO_FACTURA = "FACTURA B (Cod.006)"
PUNTO_VENTA = "14335"

# Obtener directorio base del proyecto (donde está main.py)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TICKETS_DIR = os.path.join(BASE_DIR, "tickets")

def generar_ticket_pdf(datos_venta, abrir=True):
    """
    Genera un ticket en PDF.
    - abrir: si es True, abre el PDF automáticamente.
    Retorna la ruta del archivo generado.
    """
    os.makedirs(TICKETS_DIR, exist_ok=True)
    nombre_archivo = os.path.join(TICKETS_DIR, f"ticket_{datos_venta['nro_ticket']}.pdf")

    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Courier", size=10)
    pdf.set_margins(left=10, top=10, right=10)

    # Encabezado
    pdf.set_font("Courier", 'B', 14)
    pdf.cell(0, 6, EMPRESA, ln=True, align='C')
    pdf.set_font("Courier", size=10)
    pdf.cell(0, 5, DIRECCION, ln=True, align='C')
    pdf.cell(0, 5, f"CUIT Nro: {CUIT}", ln=True, align='C')
    pdf.cell(0, 5, f"IIBB {IIBB}", ln=True, align='C')
    pdf.cell(0, 5, f"Inicio actividad comercial: {INICIO_ACTIVIDAD}", ln=True, align='C')
    pdf.cell(0, 5, "ORIENTACION AL CONSUMIDOR", ln=True, align='C')
    pdf.cell(0, 5, "MENDOZA", ln=True, align='C')
    pdf.cell(0, 5, f"CELU {TELEFONO}", ln=True, align='C')
    pdf.cell(0, 5, CONDICION_IVA, ln=True, align='C')

    pdf.ln(3)
    pdf.set_font("Courier", 'B', 10)
    pdf.cell(0, 5, f" {TIPO_FACTURA}", ln=True, align='C')
    pdf.set_font("Courier", size=10)
    pdf.cell(0, 5, f"P.V. Nro.:{PUNTO_VENTA} Nro T. {datos_venta['nro_ticket']}", ln=True, align='C')

    fecha_hora = datos_venta.get('fecha_hora', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    fecha_partes = fecha_hora.split()
    fecha = fecha_partes[0] if fecha_partes else "Fecha"
    hora = fecha_partes[1] if len(fecha_partes) > 1 else "Hora"
    pdf.cell(0, 5, f"Fecha {fecha} Hora {hora}", ln=True, align='C')
    pdf.cell(0, 5, f"Caja 001 Cajero/a: {datos_venta.get('cajero', 'Sin cajero')}", ln=True, align='C')

    cliente = datos_venta.get('cliente', "Consumidor Final")
    pdf.cell(0, 5, f"DNI Cliente: {cliente}", ln=True, align='C')

    pdf.ln(3)
    pdf.cell(0, 5, "-" * 45, ln=True)

    subtotal = 0.0
    descuento_items = 0.0
    for item in datos_venta['productos']:
        cantidad = item.get('cantidad', 1)
        nombre = item.get('nombre', 'Producto')
        precio = item.get('precio', 0.0)
        subtotal_item = item.get('subtotal', precio * cantidad)
        descuento_item = item.get('descuento', 0.0)
        codigo = item.get('codigo', '')
        iva = 21.0
        precio_con_iva = precio

        texto = f"{nombre} ({codigo if codigo else 'S/C'})"
        pdf.cell(0, 5, texto, ln=True)
        pdf.cell(0, 5, f"{cantidad} x {precio_con_iva:.2f} ({iva:.2f}%) {subtotal_item:.2f}", ln=True)
        if descuento_item > 0:
            pdf.cell(0, 5, f"  Descuento/Promoción: -$ {descuento_item:.2f}", ln=True)
        pdf.cell(0, 3, "-" * 45, ln=True)
        subtotal += subtotal_item
        descuento_items += descuento_item

    descuento_total = datos_venta.get('descuento_total', descuento_items)
    total_final = round(subtotal - descuento_total, 2)

    pdf.ln(3)
    pdf.set_font("Courier", 'B', 10)
    pdf.cell(0, 5, f"SUBTOTAL SIN DESCUENTOS $ {subtotal:.2f}", ln=True, align='C')
    if descuento_total > 0:
        pdf.cell(0, 5, f"DESCUENTOS / PROMOCIONES -$ {descuento_total:.2f}", ln=True, align='C')
    pdf.cell(0, 5, "=" * 45, ln=True, align='C')
    pdf.set_font("Courier", 'B', 12)
    pdf.cell(0, 6, f"TOTAL $ {total_final:.2f}", ln=True, align='C')
    pdf.set_font("Courier", 'B', 10)
    pdf.cell(0, 5, "=" * 45, ln=True, align='C')

    pdf.ln(2)
    pdf.set_font("Courier", size=8)
    pdf.cell(0, 4, "REGIMEN DE TRANSPARENCIA FISCAL AL CONSUMIDOR", ln=True, align='C')
    iva_contenido = total_final * 0.21 / 1.21
    pdf.cell(0, 4, f"IVA Contenido {iva_contenido:.2f}", ln=True, align='C')
    pdf.cell(0, 4, "LOS IMPUESTOS INFORMADOS SON SOLO LOS QUE", ln=True, align='C')
    pdf.cell(0, 4, "CORRESPONDEN A NIVEL NACIONAL", ln=True, align='C')

    pdf.ln(2)
    pdf.set_font("Courier", size=10)
    for pago in datos_venta.get('pagos', []):
        texto = f"Pago {pago['metodo']} $ {pago['monto']:.2f}"
        pdf.cell(0, 5, texto, ln=True, align='C')

        if pago.get('cuotas'):
            pdf.cell(0, 5, f" {pago['cuotas']} cuotas de ${pago['monto']/pago['cuotas']:.2f}", ln=True, align='C')
        if pago.get('promocion'):
            pdf.cell(0, 5, f" Promoción: {pago['promocion']}", ln=True, align='C')
        if pago['metodo'] == 'Efectivo':
            recibido = pago.get('recibido', pago['monto'])
            pdf.cell(0, 5, f" Recibido: $ {recibido:.2f}", ln=True, align='C')
            pdf.cell(0, 5, f" Vuelto: $ {pago.get('vuelto', 0):.2f}", ln=True, align='C')
        pdf.cell(0, 3, "-" * 45, ln=True, align='C')

    puntos = datos_venta.get('puntos_ganados', 0)
    if puntos > 0:
        pdf.ln(2)
        pdf.set_font("Courier", 'B', 10)
        pdf.cell(0, 5, f"? ¡Sumaste {puntos} puntos con esta compra! ?", ln=True, align='C')

    pdf.ln(2)
    pdf.set_font("Courier", size=8)
    pdf.cell(0, 4, " FACTURA ELECTRONICA", ln=True, align='C')
    cae = f"744{datos_venta['nro_ticket']}186289"
    pdf.cell(0, 4, f"CAE {cae} Vto: 18/08/26", ln=True, align='C')

    pdf.output(nombre_archivo)

    # Abrir el PDF automáticamente solo si se solicita
    if abrir:
        try:
            if os.name == 'nt':
                os.startfile(nombre_archivo)
            else:
                subprocess.run(['xdg-open', nombre_archivo])
        except Exception as e:
            print(f"⚠️ No se pudo abrir el PDF automáticamente: {e}")

    return nombre_archivo

def generar_reporte_turno_pdf(datos_turno):
    """
    Genera un reporte en PDF con los datos de un turno.
    """
    os.makedirs(TICKETS_DIR, exist_ok=True)
    nombre_archivo = os.path.join(TICKETS_DIR, f"reporte_turno_{datos_turno['turno_id']}.pdf")

    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Courier", size=10)
    pdf.set_margins(left=10, top=10, right=10)

    pdf.set_font("Courier", 'B', 16)
    pdf.cell(0, 10, "KWIK-E-MART", ln=True, align='C')
    pdf.set_font("Courier", 'B', 14)
    pdf.cell(0, 8, f"REPORTE DE TURNO #{datos_turno['turno_id']}", ln=True, align='C')
    pdf.ln(5)

    pdf.set_font("Courier", 'B', 12)
    pdf.cell(0, 6, "DATOS DEL TURNO", ln=True, align='C')
    pdf.set_font("Courier", size=10)
    pdf.cell(0, 5, f"Cajero: {datos_turno['cajero']}", ln=True)
    pdf.cell(0, 5, f"Apertura: {datos_turno['apertura']}", ln=True)
    pdf.cell(0, 5, f"Cierre: {datos_turno['cierre']}", ln=True)
    pdf.cell(0, 5, f"Estado: {datos_turno['estado']}", ln=True)
    pdf.cell(0, 5, f"Fondo inicial: ${datos_turno['fondo_inicial']:.2f}", ln=True)
    pdf.ln(3)

    pdf.set_font("Courier", 'B', 12)
    pdf.cell(0, 6, "VENTAS POR MÉTODO DE PAGO", ln=True, align='C')
    pdf.set_font("Courier", size=10)
    pdf.cell(0, 5, f"Efectivo: ${datos_turno['total_efectivo']:.2f}", ln=True)
    pdf.cell(0, 5, f"Débito: ${datos_turno['total_debito']:.2f}", ln=True)
    pdf.cell(0, 5, f"Crédito: ${datos_turno['total_credito']:.2f}", ln=True)
    pdf.cell(0, 5, f"Transferencia: ${datos_turno['total_transferencia']:.2f}", ln=True)
    pdf.cell(0, 5, "-" * 30, ln=True)
    pdf.set_font("Courier", 'B', 10)
    pdf.cell(0, 5, f"TOTAL VENTAS: ${datos_turno['total_ventas']:.2f}", ln=True)
    pdf.ln(3)

    pdf.set_font("Courier", 'B', 12)
    pdf.cell(0, 6, "SANGRÍAS", ln=True, align='C')
    pdf.set_font("Courier", size=10)
    pdf.cell(0, 5, f"Total sangrías: ${datos_turno['total_sangrias']:.2f}", ln=True)
    pdf.ln(3)

    pdf.set_font("Courier", 'B', 12)
    pdf.cell(0, 6, "RESUMEN DE CAJA", ln=True, align='C')
    pdf.set_font("Courier", size=10)
    efectivo_final = datos_turno['fondo_inicial'] + datos_turno['total_ventas'] - datos_turno['total_sangrias']
    pdf.cell(0, 5, f"Efectivo en caja: ${efectivo_final:.2f}", ln=True)
    pdf.ln(5)
    pdf.cell(0, 5, f"Reporte generado: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)

    pdf.output(nombre_archivo)

    try:
        if os.name == 'nt':
            os.startfile(nombre_archivo)
        else:
            subprocess.run(['xdg-open', nombre_archivo])
    except Exception as e:
        print(f"⚠️ No se pudo abrir el PDF automáticamente: {e}")