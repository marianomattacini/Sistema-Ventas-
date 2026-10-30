"""
insertar_clientes_bancarios.py

Script de siembra (seed) para PostgreSQL: carga 10 cuentas bancarias y
tarjetas de crédito de PRUEBA, usadas solo para desarrollo y demos locales
del sistema.

⚠️ TODOS los datos de abajo (DNI, usuarios, contraseñas, números de tarjeta,
   CVV, CBU, alias) son INVENTADOS. Tienen el formato típico de estos campos
   para que el sistema los pueda validar y mostrar en pantalla, pero no
   corresponden a ninguna persona, cuenta ni tarjeta real.
"""
import os
import sys

# Permite ejecutar este archivo directamente (python database/setup_postgresql.py)
# sin depender de que la raíz del proyecto ya esté en el PYTHONPATH.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from database.config import get_postgres_connection, crear_base_postgresql_si_no_existe
from database.setup_postgresql import crear_tablas_postgresql
from datetime import datetime

def insertar_cuentas():
    """Inserta 10 cuentas bancarias y tarjetas de crédito de PRUEBA (datos ficticios)."""
    
    clientes = [
        # (dni, usuario, contrasena, tipo_cuenta, saldo, numero_debito, pin_debito, alias, cbu,
        #  numero_tarjeta_credito, cvv, vencimiento_credito, limite_un_pago, limite_cuotas, banco, promocion)
        # --- Todos los valores de esta lista son ficticios, ver aclaracion arriba ---
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
    
    # Asegura que la base, las tablas y todas sus columnas existan (también en bases viejas)
    if not crear_base_postgresql_si_no_existe() or not crear_tablas_postgresql():
        return False
    conn = get_postgres_connection()
    if not conn:
        print("❌ No se pudo conectar a PostgreSQL.")
        return False
    
    cursor = conn.cursor()
    insertados = 0
    errores = 0
    
    for (dni, usuario, contrasena, tipo_cuenta, saldo, numero_debito, pin_debito, alias, cbu,
         numero_tarjeta_credito, cvv, vencimiento_credito, limite_un_pago, limite_cuotas, banco, promocion) in clientes:
        
        try:
            cursor.execute("SAVEPOINT cliente")
            cursor.execute('''
                INSERT INTO cuentas_bancarias 
                (dni_cuil, usuario, contrasena, tipo_cuenta, saldo, numero_debito, pin_debito, alias, cbu, estado)
                SELECT %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                WHERE NOT EXISTS (SELECT 1 FROM cuentas_bancarias WHERE usuario = %s)
                RETURNING id
            ''', (dni, usuario, contrasena, tipo_cuenta, saldo, numero_debito, pin_debito, alias, cbu, 'Activo', usuario))
            
            row = cursor.fetchone()
            if row:
                cuenta_id = row[0]
                # Insertar tarjeta de crédito con promoción
                cursor.execute('''
                    INSERT INTO tarjetas_credito 
                    (cuenta_id, banco, numero_tarjeta, cvv, vencimiento_credito, limite_un_pago, limite_cuotas, promocion, estado)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (cuenta_id, banco, numero_tarjeta_credito, cvv, vencimiento_credito, limite_un_pago, limite_cuotas, promocion, 'Activo'))
                insertados += 1
                print(f"✅ Cuenta {usuario} creada (ID: {cuenta_id})")
            else:
                print(f"ℹ️ Usuario {usuario} ya existía.")
        except Exception as e:
            cursor.execute("ROLLBACK TO SAVEPOINT cliente")
            errores += 1
            print(f"❌ Error al insertar {usuario}: {e}")
    
    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ {insertados} nuevas cuentas insertadas correctamente.")
    if errores:
        print(f"❌ {errores} cliente(s) no se pudieron insertar (ver detalle arriba).")
    return errores == 0

if __name__ == "__main__":
    print("💳 Insertando clientes bancarios de prueba...")
    ok = insertar_cuentas()
    print("✅ Proceso completado." if ok else "❌ El proceso terminó con errores (ver mensajes de arriba).")
    sys.exit(0 if ok else 1)