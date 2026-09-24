import sqlite3
import bcrypt
from database.config import get_sqlite_connection

def crear_cajero():
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    
    # Generar hash bcrypt para PIN '0000'
    pin = "0000"
    pin_bytes = pin.encode('utf-8')
    salt = bcrypt.gensalt()
    hash_pin = bcrypt.hashpw(pin_bytes, salt).decode('utf-8')
    
    # Insertar usuario cajero si no existe
    cursor.execute('''
        INSERT OR IGNORE INTO usuarios (nombre_usuario, pin_hash, rol, estado)
        VALUES (?, ?, ?, 'Activo')
    ''', ('cajero1', hash_pin, 'Cajero'))
    
    conn.commit()
    conn.close()
    print("✅ Usuario cajero1 creado con PIN 0000")

if __name__ == "__main__":
    crear_cajero()