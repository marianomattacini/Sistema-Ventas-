import os
import sys
import sqlite3
import psycopg2
from psycopg2 import Error
from dotenv import load_dotenv

# Permite ejecutar este archivo directamente (python database/config.py)
# sin depender de que la raíz del proyecto ya esté en el PYTHONPATH.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# =====================================================================
# DETECCIÓN DE ENTORNO (DESARROLLO O EJECUTABLE)
# =====================================================================
def get_base_dir():
    """Retorna el directorio base donde se encuentra el ejecutable o el proyecto."""
    if getattr(sys, 'frozen', False):
        # Estamos en un ejecutable de PyInstaller
        return os.path.dirname(sys.executable)
    else:
        # Estamos en entorno de desarrollo
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BASE_DIR = get_base_dir()
DB_LOCAL = os.path.join(BASE_DIR, 'supermercado.db')
ENV_PATH = os.path.join(BASE_DIR, '.env')

# Cargar variables de entorno desde .env (priorizando el .env junto al ejecutable)
load_dotenv(dotenv_path=ENV_PATH)

# Configuración PostgreSQL
PG_HOST = os.getenv('PG_HOST', 'localhost')
PG_PORT = os.getenv('PG_PORT', '5432')          # <-- AGREGADO
PG_DATABASE = os.getenv('PG_DATABASE', 'cajero_automatico')
PG_USER = os.getenv('PG_USER', 'postgres')
PG_PASSWORD = os.getenv('PG_PASSWORD', '')

# =====================================================================
# CONEXIONES
# =====================================================================
from database.base_datos import BaseDatos

# Instancia única de la clase BaseDatos, encargada de la conexión y de la
# ejecución de sentencias SQL contra la base local (ver database/base_datos.py).
_base_datos = BaseDatos(DB_LOCAL)


def get_base_datos():
    """Devuelve la instancia de BaseDatos usada por todo el sistema."""
    return _base_datos


def get_sqlite_connection():
    """
    Retorna una conexión a SQLite (con PRAGMA foreign_keys = ON y migración
    de esquema aplicada). Se mantiene esta función por compatibilidad: por
    debajo, delega en la clase BaseDatos, que es la única responsable de
    abrir conexiones y ejecutar SQL en todo el proyecto.
    """
    return _base_datos.conectar()

def get_postgres_connection():
    """
    Retorna una conexión a PostgreSQL usando variables de entorno.
    """
    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,                        # <-- AGREGADO
            database=PG_DATABASE,
            user=PG_USER,
            password=PG_PASSWORD
        )
        return conn
    except Error as e:
        print(f"❌ Error al conectar a PostgreSQL: {e}")
        return None

def test_connections():
    """
    Prueba ambas conexiones y retorna un diccionario con el estado.
    """
    resultados = {
        'sqlite': False,
        'postgresql': False
    }
    
    conn_sqlite = get_sqlite_connection()
    if conn_sqlite:
        conn_sqlite.close()
        resultados['sqlite'] = True
        print("✅ SQLite: Conexión exitosa")
    else:
        print("❌ SQLite: Falló la conexión")
    
    conn_pg = get_postgres_connection()
    if conn_pg:
        conn_pg.close()
        resultados['postgresql'] = True
        print("✅ PostgreSQL: Conexión exitosa")
    else:
        print("❌ PostgreSQL: Falló la conexión")
    
    return resultados

if __name__ == "__main__":
    print("🧪 Probando conexiones...")
    test_connections()