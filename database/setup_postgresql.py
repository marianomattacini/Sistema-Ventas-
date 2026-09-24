import psycopg2
from psycopg2 import Error
from database.config import get_postgres_connection

# =====================================================================
# CREACIÓN DE TABLAS EN POSTGRESQL
# =====================================================================
def crear_tablas_postgresql():
    """
    Crea las tablas financieras en PostgreSQL si no existen.
    """
    try:
        conn = get_postgres_connection()
        if conn is None:
            print("❌ No se pudo conectar a PostgreSQL. Verificá las credenciales en .env")
            return False

        cursor = conn.cursor()

        # 1. Cuentas Bancarias
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cuentas_bancarias (
                id SERIAL PRIMARY KEY,
                dni_cuil VARCHAR(20) UNIQUE NOT NULL,
                usuario VARCHAR(50) NOT NULL,
                contrasena VARCHAR(50) NOT NULL,
                tipo_cuenta VARCHAR(30),
                saldo NUMERIC(15, 2) DEFAULT 0.0,
                cbu VARCHAR(22) UNIQUE,
                alias VARCHAR(50) UNIQUE,
                numero_debito VARCHAR(16) UNIQUE,
                pin_debito VARCHAR(4),
                vencimiento_debito VARCHAR(5),
                limite_extraccion_mensual NUMERIC(15, 2),
                estado VARCHAR(20) DEFAULT 'Activo'
            )
        ''')

        # 2. Tarjetas de Crédito (con promocion)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tarjetas_credito (
                id SERIAL PRIMARY KEY,
                cuenta_id INTEGER REFERENCES cuentas_bancarias(id),
                banco VARCHAR(50),
                numero_tarjeta VARCHAR(16) UNIQUE,
                cvv VARCHAR(4),
                vencimiento_credito VARCHAR(5),
                limite_un_pago NUMERIC(15, 2),
                consumo_un_pago NUMERIC(15, 2) DEFAULT 0.0,
                limite_cuotas NUMERIC(15, 2),
                consumo_cuotas NUMERIC(15, 2) DEFAULT 0.0,
                limite_extraccion NUMERIC(15, 2),
                consumo_extraccion NUMERIC(15, 2) DEFAULT 0.0,
                saldo_total_a_pagar NUMERIC(15, 2) DEFAULT 0.0,
                promocion TEXT,
                estado VARCHAR(20) DEFAULT 'Activo'
            )
        ''')

        # 3. Movimientos (Auditoría)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS movimientos (
                id SERIAL PRIMARY KEY,
                cuenta_id INTEGER REFERENCES cuentas_bancarias(id),
                tipo_operacion VARCHAR(50),
                monto NUMERIC(15, 2),
                descripcion TEXT,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        print("✅ Tablas financieras creadas (o ya existían) en PostgreSQL.")
        return True

    except Error as e:
        print(f"❌ Error al crear tablas en PostgreSQL: {e}")
        return False
    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()

# =====================================================================
# INSERCIÓN DE 10 CLIENTES REALISTAS
# =====================================================================
def insertar_clientes_bancarios():
    """
    Inserta 10 cuentas bancarias y tarjetas de crédito de prueba.
    """
    clientes = [
        ("20123456789", "cliente_galicia", "pass123", "Caja de Ahorro", 150000.00, "4000111122223333", "1234", "mariano.galicia", "0000111122223333444455",
         "4509111122223333", "123", "12/26", 1000000.00, 800000.00, "Galicia", "3 cuotas sin interés"),
        ("20234567890", "cliente_nacion", "pass123", "Cuenta Corriente", 50000.00, "4000999988887777", "4321", "compras.nacion", "0000999988887777666655",
         "4509999988887777", "456", "10/27", 500000.00, 400000.00, "Nación", "6 cuotas con interés reducido"),
        ("20345678901", "cliente_normal", "pass123", "Caja de Ahorro", 30000.00, "4000555544443333", "0000", "sin.promo", "0000555544443333222211",
         "4509555544443333", "789", "08/25", 300000.00, 200000.00, "Sin promo", "Sin promociones"),
        ("20456789012", "cliente_mp", "pass123", "Billetera Virtual", 25000.00, "4000777744445555", "1111", "pago.mp", "0000777744445555666677",
         "4509777744445555", "321", "06/27", 200000.00, 150000.00, "Mercado Pago", "10% descuento QR"),
        ("20567890123", "cliente_santander", "pass123", "Cuenta Corriente", 80000.00, "4000888844446666", "2222", "santander.promo", "0000888844446666777788",
         "4509888844446666", "654", "11/26", 600000.00, 500000.00, "Santander", "2 cuotas sin interés"),
        ("20678901234", "cliente_uala", "pass123", "Billetera Virtual", 12000.00, "4000999944447777", "3333", "uala.pay", "0000999944447777888899",
         "4509999944447777", "987", "09/27", 100000.00, 80000.00, "Ualá", "Sin promociones"),
        ("20789012345", "cliente_bbva", "pass123", "Caja de Ahorro", 60000.00, "4000111133338888", "4444", "bbva.promo", "0000111133338888999900",
         "4509111133338888", "147", "04/26", 400000.00, 350000.00, "BBVA", "6 cuotas sin interés en electrónica"),
        ("20890123456", "cliente_naranja", "pass123", "Billetera Virtual", 8000.00, "4000222244449999", "5555", "naranja.x", "0000222244449999000011",
         "4509222244449999", "258", "02/28", 50000.00, 30000.00, "Naranja X", "Puntos dobles"),
        ("20901234567", "cliente_patagonia", "pass123", "Cuenta Corriente", 45000.00, "4000333355550000", "6666", "patagonia.pay", "0000333355550000111122",
         "4509333355550000", "369", "07/25", 250000.00, 200000.00, "Patagonia", "3 cuotas sin interés"),
        ("21012345678", "cliente_personal", "pass123", "Billetera Virtual", 7000.00, "4000444466661111", "7777", "personal.pay", "0000444466661111222233",
         "4509444466661111", "741", "05/27", 60000.00, 40000.00, "Personal Pay", "Sin promociones"),
    ]
    
    conn = get_postgres_connection()
    if not conn:
        print("❌ No se pudo conectar a PostgreSQL.")
        return False
    
    cursor = conn.cursor()
    insertados = 0
    
    for (dni, usuario, contrasena, tipo_cuenta, saldo, numero_debito, pin_debito, alias, cbu,
         numero_tarjeta_credito, cvv, vencimiento_credito, limite_un_pago, limite_cuotas, banco, promocion) in clientes:
        
        try:
            cursor.execute('''
                INSERT INTO cuentas_bancarias 
                (dni_cuil, usuario, contrasena, tipo_cuenta, saldo, numero_debito, pin_debito, alias, cbu, estado)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (dni_cuil) DO NOTHING
                RETURNING id
            ''', (dni, usuario, contrasena, tipo_cuenta, saldo, numero_debito, pin_debito, alias, cbu, 'Activo'))
            
            row = cursor.fetchone()
            if row:
                cuenta_id = row[0]
                cursor.execute('''
                    INSERT INTO tarjetas_credito 
                    (cuenta_id, banco, numero_tarjeta, cvv, vencimiento_credito, limite_un_pago, limite_cuotas, promocion, estado)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (cuenta_id, banco, numero_tarjeta_credito, cvv, vencimiento_credito, limite_un_pago, limite_cuotas, promocion, 'Activo'))
                insertados += 1
                print(f"✅ Cuenta {usuario} creada (ID: {cuenta_id})")
            else:
                print(f"ℹ️ Usuario {usuario} ya existía (DNI {dni}).")
        except Exception as e:
            print(f"❌ Error al insertar {usuario}: {e}")
    
    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ {insertados} nuevas cuentas insertadas correctamente.")
    return True

# =====================================================================
# EJECUCIÓN DIRECTA
# =====================================================================
if __name__ == "__main__":
    print("=" * 50)
    print("🏦 CONFIGURANDO BASE DE DATOS FINANCIERA (POSTGRESQL)")
    print("=" * 50)
    
    if crear_tablas_postgresql():
        insertar_clientes_bancarios()
    
    print("=" * 50)
    print("✅ Proceso completado.")