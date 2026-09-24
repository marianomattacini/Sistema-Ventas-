import sys
import os

# Permite ejecutar este archivo directamente (python database/setup_db.py)
# sin depender de que la raíz del proyecto ya esté en el PYTHONPATH.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from database.config import get_sqlite_connection, DB_LOCAL

# =====================================================================
# CREACIÓN DE TABLAS
# =====================================================================
def crear_tablas():
    """
    Crea todas las tablas de la base de datos operativa (SQLite)
    si no existen. Activa las claves foráneas antes de crear.
    """
    try:
        conn = get_sqlite_connection()
        cursor = conn.cursor()

        # Tabla: usuarios
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre_usuario TEXT UNIQUE NOT NULL,
                pin_hash TEXT NOT NULL,
                rol TEXT NOT NULL,
                estado TEXT DEFAULT 'Activo',
                fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
                ultimo_login TEXT
            )
        ''')

        # Tabla: categorias
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                estado TEXT DEFAULT 'Activo'
            )
        ''')

        # Tabla: productos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS productos (
                codigo_barras TEXT PRIMARY KEY,
                nombre TEXT NOT NULL,
                categoria_id INTEGER REFERENCES categorias(id),
                precio_venta REAL NOT NULL,
                stock_actual INTEGER DEFAULT 0,
                stock_minimo INTEGER DEFAULT 0,
                tipo_garantia TEXT DEFAULT 'comestible',
                estado TEXT DEFAULT 'Activo',
                precio_costo REAL NOT NULL
            )
        ''')

        # Tabla: clientes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clientes (
                dni_cuil TEXT PRIMARY KEY,
                nombre TEXT NOT NULL,
                telefono TEXT,
                email TEXT,
                puntos_acumulados INTEGER DEFAULT 0,
                estado TEXT DEFAULT 'Activo',
                fecha_registro TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tabla: proveedores
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS proveedores (
                cuit TEXT PRIMARY KEY,
                razon_social TEXT NOT NULL,
                telefono TEXT NOT NULL,
                email TEXT NOT NULL,
                estado TEXT DEFAULT 'Activo'
            )
        ''')

        # Tabla: turnos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS turnos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER REFERENCES usuarios(id),
                fecha_hora_apertura TEXT NOT NULL,
                fecha_hora_cierre TEXT,
                fondo_inicial REAL NOT NULL,
                total_ventas_efectivo REAL DEFAULT 0,
                total_ventas_debito REAL DEFAULT 0,
                total_ventas_credito REAL DEFAULT 0,
                total_ventas_transferencia REAL DEFAULT 0,
                total_sangrias REAL DEFAULT 0,
                estado TEXT DEFAULT 'Abierto'
            )
        ''')

        # Tabla: ventas_cabecera
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ventas_cabecera (
                nro_ticket TEXT PRIMARY KEY,
                turno_id INTEGER REFERENCES turnos(id),
                dni_cliente TEXT REFERENCES clientes(dni_cuil),
                fecha_hora TEXT NOT NULL,
                total_facturado REAL NOT NULL,
                descuento_total REAL DEFAULT 0,
                puntos_sumados INTEGER DEFAULT 0,
                estado TEXT DEFAULT 'En Curso'
            )
        ''')

        # Tabla: ventas_detalle
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ventas_detalle (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nro_ticket TEXT REFERENCES ventas_cabecera(nro_ticket),
                codigo_producto TEXT REFERENCES productos(codigo_barras),
                cantidad INTEGER NOT NULL,
                subtotal REAL NOT NULL,
                descuento REAL DEFAULT 0
            )
        ''')

        # Tabla: ventas_pagos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ventas_pagos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nro_ticket TEXT REFERENCES ventas_cabecera(nro_ticket),
                metodo_pago TEXT NOT NULL,
                monto_abonado REAL NOT NULL,
                monto_recibido REAL DEFAULT 0,
                monto_vuelto REAL DEFAULT 0,
                cuotas INTEGER,
                interes_aplicado REAL DEFAULT 0,
                promocion_aplicada TEXT
            )
        ''')

        # Tabla: sangrias
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sangrias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                turno_id INTEGER REFERENCES turnos(id),
                cajero_id INTEGER REFERENCES usuarios(id),
                supervisor_id INTEGER REFERENCES usuarios(id),
                fecha_hora TEXT NOT NULL,
                monto_retirado REAL NOT NULL,
                motivo TEXT NOT NULL DEFAULT 'Retiro de efectivo por máximo alcanzado'
            )
        ''')

        # Tabla: compras_cabecera
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compras_cabecera (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nro_factura TEXT UNIQUE NOT NULL,
                proveedor_id TEXT REFERENCES proveedores(cuit),
                supervisor_id INTEGER REFERENCES usuarios(id),
                fecha_hora TEXT NOT NULL,
                total_factura REAL NOT NULL,
                estado TEXT DEFAULT 'Ingresado'
            )
        ''')

        # Tabla: compras_detalle
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compras_detalle (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                compra_id INTEGER REFERENCES compras_cabecera(id),
                codigo_producto TEXT REFERENCES productos(codigo_barras),
                cantidad_ingresada INTEGER NOT NULL,
                precio_costo REAL NOT NULL,
                subtotal REAL NOT NULL
            )
        ''')

        # Tabla: cupones_devolucion
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cupones_devolucion (
                codigo_alfanumerico TEXT PRIMARY KEY,
                ticket_origen TEXT REFERENCES ventas_cabecera(nro_ticket),
                dni_cliente TEXT REFERENCES clientes(dni_cuil),
                fecha_emision TEXT NOT NULL,
                estado TEXT DEFAULT 'Pendiente',
                fecha_uso TEXT
            )
        ''')

        # Tabla: registro_descansos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS registro_descansos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                turno_id INTEGER REFERENCES turnos(id),
                fecha_hora_inicio TEXT NOT NULL,
                fecha_hora_fin TEXT,
                motivo TEXT NOT NULL
            )
        ''')

        # Tabla: logs_auditoria
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs_auditoria (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER REFERENCES usuarios(id),
                fecha_hora TEXT DEFAULT CURRENT_TIMESTAMP,
                accion TEXT NOT NULL,
                detalle TEXT,
                ip_origen TEXT
            )
        ''')

        # Tabla: gastos_planificados
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gastos_planificados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                categoria TEXT NOT NULL,
                monto_planificado REAL NOT NULL,
                periodo TEXT NOT NULL,
                fecha_registro TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tabla: promociones
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS promociones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT NOT NULL,
                producto_id TEXT REFERENCES productos(codigo_barras),
                categoria_id INTEGER REFERENCES categorias(id),
                cantidad_minima INTEGER,
                descuento_aplicado REAL,
                fecha_inicio TEXT NOT NULL,
                fecha_fin TEXT NOT NULL,
                estado TEXT DEFAULT 'Activa'
            )
        ''')

        # Tabla: notificaciones
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notificaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_destino INTEGER REFERENCES usuarios(id),
                tipo TEXT NOT NULL,
                mensaje TEXT NOT NULL,
                fecha_hora TEXT DEFAULT CURRENT_TIMESTAMP,
                leida INTEGER DEFAULT 0
            )
        ''')

        # ===== NUEVAS TABLAS =====
        # Tabla: empleados
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS empleados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre_completo TEXT NOT NULL,
                dni TEXT UNIQUE NOT NULL,
                fecha_nacimiento TEXT,
                fecha_ingreso TEXT NOT NULL,
                rol TEXT NOT NULL,
                salario REAL,
                telefono TEXT,
                email TEXT,
                estado TEXT DEFAULT 'Activo'
            )
        ''')

        # Tabla: empleados_licencias
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS empleados_licencias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                empleado_id INTEGER REFERENCES empleados(id),
                fecha_inicio TEXT NOT NULL,
                fecha_fin TEXT,
                tipo TEXT NOT NULL,
                motivo TEXT,
                estado TEXT DEFAULT 'Pendiente'
            )
        ''')

        # Tabla: presupuestos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS presupuestos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                categoria TEXT NOT NULL,
                monto_planificado REAL NOT NULL,
                mes INTEGER NOT NULL,
                anio INTEGER NOT NULL,
                fecha_registro TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tabla: entidades_pago
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS entidades_pago (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                tipo TEXT NOT NULL,
                activa INTEGER DEFAULT 1,
                cuotas_maximas INTEGER DEFAULT 12,
                descuento_porcentaje REAL DEFAULT 0,
                cuotas_sin_interes INTEGER DEFAULT 0,
                promocion_descripcion TEXT
            )
        ''')

	        # Tabla: configuracion
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS configuracion (
                clave TEXT PRIMARY KEY,
                valor TEXT NOT NULL,
                descripcion TEXT
            )
        ''')
        # Datos iniciales
        cursor.execute('''
            INSERT OR IGNORE INTO configuracion (clave, valor, descripcion)
            VALUES 
                ('iva', '21.0', 'Porcentaje de IVA'),
                ('puntos_por_100', '1.0', 'Puntos por cada $100 de compra'),
                ('max_cuotas_predeterminado', '12', 'Cuotas máximas permitidas'),
                ('tiempo_descanso_min', '15', 'Duración mínima del descanso en minutos')
        ''')

	# Tabla: roles (para empleados)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL,
                permisos TEXT
            )
        ''')

        conn.commit()
        conn.close()
        print("✅ Todas las tablas de SQLite fueron creadas correctamente.")

    except sqlite3.Error as e:
        print(f"❌ Error al crear tablas en SQLite: {e}")

# =====================================================================
# POBLADO INICIAL MÍNIMO
# =====================================================================
def insertar_datos_prueba():
    """
    Inserta datos de prueba mínimos para empezar a trabajar.
    Usa INSERT OR IGNORE para no duplicar si ya existen.
    """
    try:
        import bcrypt
        conn = get_sqlite_connection()
        cursor = conn.cursor()

        # Usuario de prueba (Gerente General con PIN 1234). El sistema de
        # login valida con bcrypt.checkpw, así que el hash tiene que ser
        # un hash bcrypt real (antes había un SHA-256 en texto plano acá,
        # que rompía el login en cualquier instalación nueva).
        hash_admin = bcrypt.hashpw("1234".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute('''
            INSERT OR IGNORE INTO usuarios (nombre_usuario, pin_hash, rol, estado)
            VALUES ('admin', ?, 'Gerente General', 'Activo')
        ''', (hash_admin,))

        # Usuario cajero de prueba (Cajero con PIN 0000)
        hash_cajero = bcrypt.hashpw("0000".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute('''
            INSERT OR IGNORE INTO usuarios (nombre_usuario, pin_hash, rol, estado)
            VALUES ('cajero1', ?, 'Cajero', 'Activo')
        ''', (hash_cajero,))

        # Categoría de prueba
        cursor.execute('INSERT OR IGNORE INTO categorias (nombre) VALUES (?)', ('Bebidas',))

        # Producto de prueba
        cursor.execute('''
            INSERT OR IGNORE INTO productos (codigo_barras, nombre, categoria_id, precio_venta, stock_actual, stock_minimo, tipo_garantia, precio_costo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('123456', 'Agua Mineral', 1, 1.50, 100, 10, 'comestible', 0.80))

        # Cliente de prueba
        cursor.execute('''
            INSERT OR IGNORE INTO clientes (dni_cuil, nombre, telefono, email)
            VALUES (?, ?, ?, ?)
        ''', ('12345678', 'Cliente Test', '123456789', 'cliente@test.com'))

        # Proveedor de prueba
        cursor.execute('''
            INSERT OR IGNORE INTO proveedores (cuit, razon_social, telefono, email)
            VALUES (?, ?, ?, ?)
        ''', ('30-12345678-9', 'Proveedor Test', '123456789', 'proveedor@test.com'))

        # Entidades de pago (bancos, entidades financieras y billeteras virtuales
        # ficticias) con sus promociones de cuotas sin interés y/o descuentos.
        cursor.execute("SELECT COUNT(*) FROM entidades_pago")
        if cursor.fetchone()[0] == 0:
            entidades = [
                # (nombre, tipo, cuotas_maximas, descuento%, cuotas_sin_interes, descripción)
                ("Banco Cuyo Sur", "Banco", 12, 0, 3, "3 cuotas sin interés todos los días"),
                ("Banco Andes Plata", "Banco", 18, 10, 6, "10% de descuento los lunes"),
                ("Banco Mendocino", "Banco", 12, 0, 6, "6 cuotas sin interés"),
                ("Banco del Oeste", "Banco", 6, 15, 0, "15% de descuento pagando en 1 pago"),
                ("Banco Nueva Era", "Banco", 12, 0, 0, "Sin promociones vigentes"),
                ("Banco Vendimia", "Banco", 24, 0, 12, "12 cuotas sin interés en electro/almacén"),
                ("Banco Confianza", "Banco", 12, 5, 3, "5% + 3 cuotas sin interés los jueves"),
                ("Banco Río Claro", "Banco", 12, 0, 1, "Sin cuotas, pago único"),
                ("Banco Cordillera", "Banco", 18, 0, 9, "9 cuotas sin interés fin de semana"),
                ("Banco Sol Naciente", "Banco", 12, 20, 0, "20% de descuento los miércoles"),
                ("Credicuyo Financiera", "Entidad Financiera", 12, 0, 3, "3 cuotas sin interés"),
                ("Financiera El Sol", "Entidad Financiera", 6, 8, 0, "8% de descuento"),
                ("Financiera Vendimia Plus", "Entidad Financiera", 12, 0, 6, "6 cuotas sin interés"),
                ("Credimax Financiera", "Entidad Financiera", 9, 0, 0, "Sin promociones vigentes"),
                ("Financiera Andina", "Entidad Financiera", 12, 5, 2, "5% + 2 cuotas sin interés"),
                ("Financiera Confía", "Entidad Financiera", 6, 0, 3, "3 cuotas sin interés"),
                ("Financiera Rápida Cash", "Entidad Financiera", 3, 0, 3, "Todas las cuotas sin interés"),
                ("PagoYa", "Billetera Virtual", 0, 15, 0, "15% de descuento pagando con QR"),
                ("WalletCuyo", "Billetera Virtual", 0, 10, 0, "10% de reintegro los fines de semana"),
                ("QRPay Argentina", "Billetera Virtual", 0, 0, 0, "Sin promociones vigentes"),
                ("MonedaDigital", "Billetera Virtual", 0, 12, 0, "12% de descuento los viernes"),
                ("PagoFácil Virtual", "Billetera Virtual", 0, 5, 0, "5% de descuento todos los días"),
                ("CyberPay", "Billetera Virtual", 0, 20, 0, "20% de descuento (tope $5000)"),
                ("BilleteraAndes", "Billetera Virtual", 0, 0, 0, "Sin promociones vigentes"),
                ("InstantPay", "Billetera Virtual", 0, 7, 0, "7% de descuento pagando con alias"),
            ]
            cursor.executemany('''
                INSERT INTO entidades_pago (nombre, tipo, activa, cuotas_maximas,
                    descuento_porcentaje, cuotas_sin_interes, promocion_descripcion)
                VALUES (?, ?, 1, ?, ?, ?, ?)
            ''', entidades)

        conn.commit()
        conn.close()
        print("✅ Datos de prueba mínimos insertados correctamente.")

    except sqlite3.Error as e:
        print(f"❌ Error al insertar datos de prueba: {e}")

# =====================================================================
# EJECUCIÓN DIRECTA
# =====================================================================
if __name__ == "__main__":
    print("=" * 50)
    print("📦 CONFIGURANDO BASE DE DATOS SQLITE")
    print("=" * 50)
    crear_tablas()
    insertar_datos_prueba()
    print("=" * 50)
    print("✅ Proceso completado.")