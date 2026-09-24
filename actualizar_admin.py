import sqlite3
import bcrypt
from database.config import get_sqlite_connection

def actualizar_hash_admin():
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    
    # Generar hash bcrypt para '1234'
    pin = "1234"
    pin_bytes = pin.encode('utf-8')
    salt = bcrypt.gensalt()
    nuevo_hash = bcrypt.hashpw(pin_bytes, salt).decode('utf-8')
    
    # Actualizar el usuario admin
    cursor.execute('''
        UPDATE usuarios
        SET pin_hash = ?
        WHERE nombre_usuario = 'admin'
    ''', (nuevo_hash,))
    
    conn.commit()
    conn.close()
    print("✅ Hash de admin actualizado correctamente con bcrypt.")

if __name__ == "__main__":
    actualizar_hash_admin()