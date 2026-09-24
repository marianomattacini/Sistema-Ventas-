import sqlite3
from database.config import get_sqlite_connection

def crear_categorias():
    """Crea las categorías necesarias si no existen."""
    categorias = [
        ("Aceites y Vinagres",),
        ("Vinos",),
        ("Panadería",),
        ("Bebidas",),
        ("Pescados y Mariscos",),
        ("Dulces y Golosinas",),
        ("Limpieza",),
        ("Frutas",),
        ("Verduras",),
        ("Carnes",),
        ("Granos y Cereales",),
        ("Almacén",)
    ]
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    for cat in categorias:
        cursor.execute("INSERT OR IGNORE INTO categorias (nombre) VALUES (?)", cat)
    conn.commit()
    conn.close()
    print("✅ Categorías creadas/verificadas.")

def obtener_id_categoria(nombre):
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM categorias WHERE nombre = ?", (nombre,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def insertar_productos():
    """Inserta los productos del catálogo."""
    productos = [
        # (codigo_barras, nombre, categoria, precio_venta, stock_actual, stock_minimo, precio_costo)
        ("7791234560011", "Aceite de Oliva Virgen Ex", "Aceites y Vinagres", 4500.00, 50, 10, 3800.00),
        ("7791234560028", "Vino Malbec Reserva Mendo", "Vinos", 8500.00, 30, 5, 7000.00),
        ("7791234560035", "Pan casero (Unidad)", "Panadería", 1200.00, 100, 20, 900.00),
        ("7791234560042", "Coca-Cola 2L", "Bebidas", 2500.00, 80, 15, 2000.00),
        ("7791234560073", "Salmón rosado Marca 11", "Pescados y Mariscos", 5909.26, 20, 5, 4500.00),
        ("7791234560103", "Chocolate con almendras M", "Dulces y Golosinas", 1315.25, 60, 10, 1000.00),
        ("7791234560134", "Caramelos surtidos Marca", "Dulces y Golosinas", 6430.82, 40, 8, 5000.00),
        ("7791234560165", "Detergente Marca 14", "Limpieza", 9571.69, 25, 5, 8000.00),
        ("7791234560554", "Manzana Marca 5", "Frutas", 1249.63, 100, 20, 900.00),
        ("7791234560615", "Carne picada Marca 12", "Carnes", 1650.19, 30, 5, 1200.00),
        ("7791234560622", "Lechuga Marca 8", "Verduras", 4863.90, 30, 10, 3500.00),
        ("7791234560639", "Chupetín Marca 11", "Dulces y Golosinas", 8544.88, 20, 5, 7000.00),
        ("7791234560646", "Jabón en polvo Marca 13", "Limpieza", 6312.43, 15, 5, 5000.00),
        ("7791234560653", "Jabón en polvo Marca 8", "Limpieza", 3337.34, 20, 5, 2500.00),
        ("7791234560660", "Banana Marca 2", "Frutas", 8838.56, 25, 5, 7000.00),
        ("7791234560677", "Trapo de piso Marca 1", "Limpieza", 3855.44, 15, 5, 3000.00),
        ("7791234560684", "Turrón Marca 10", "Dulces y Golosinas", 6247.81, 20, 5, 5000.00),
        ("7791234560691", "Filet de merluza Marca 10", "Pescados y Mariscos", 4871.00, 15, 3, 3800.00),
        ("7791234560707", "Papa Marca 13", "Verduras", 5617.77, 50, 10, 4500.00),
        ("7791234560714", "Arroz blanco Marca 15", "Granos y Cereales", 10830.96, 40, 10, 9000.00),
        ("7791234560721", "Calamar Marca 13", "Pescados y Mariscos", 4536.65, 15, 3, 3500.00),
        ("7791234561667", "Chocolate con almendras M", "Dulces y Golosinas", 12734.82, 10, 2, 10000.00),
        ("7791234561674", "Azúcar Marca 6", "Granos y Cereales", 997.52, 80, 15, 700.00),
        ("7791234561681", "Jabón de tocador Marca 12", "Limpieza", 13454.68, 10, 2, 11000.00),
        ("7791234561698", "Azúcar Marca 1", "Granos y Cereales", 10906.98, 30, 5, 9000.00),
        ("7791234561704", "Caramelos surtidos Marca", "Dulces y Golosinas", 9518.09, 15, 3, 8000.00),
        ("7791234561711", "Caramelos surtidos Marca", "Dulces y Golosinas", 7416.88, 15, 3, 6000.00),
        ("7791234561728", "Caramelos surtidos Marca", "Dulces y Golosinas", 7771.97, 15, 3, 6500.00),
        ("7791234561735", "Caramelos surtidos Marca", "Dulces y Golosinas", 2047.93, 20, 5, 1500.00),
        ("7791234561742", "Yerba Mate Marca 14", "Granos y Cereales", 12374.01, 25, 5, 10000.00),
        ("7791234561759", "Salmón rosado Marca 3", "Pescados y Mariscos", 680.90, 30, 5, 500.00),
        ("7791234561766", "Banana Marca 5", "Frutas", 14999.27, 10, 2, 12000.00),
        ("7791234561773", "Jabón en polvo Marca 10", "Limpieza", 11555.63, 10, 2, 9500.00),
        ("7791234563043", "Jabón en polvo Marca 4", "Limpieza", 3473.57, 20, 5, 2800.00),
    ]

    conn = get_sqlite_connection()
    cursor = conn.cursor()
    creados = 0
    for codigo, nombre, categoria, precio_venta, stock_actual, stock_minimo, precio_costo in productos:
        categoria_id = obtener_id_categoria(categoria)
        if not categoria_id:
            print(f"❌ Categoría '{categoria}' no encontrada. Saltando producto {nombre}")
            continue
        cursor.execute('''
            INSERT OR IGNORE INTO productos 
            (codigo_barras, nombre, categoria_id, precio_venta, stock_actual, stock_minimo, precio_costo, tipo_garantia, estado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (codigo, nombre, categoria_id, precio_venta, stock_actual, stock_minimo, precio_costo, 'comestible', 'Activo'))
        if cursor.rowcount > 0:
            creados += 1
    conn.commit()
    conn.close()
    print(f"✅ {creados} productos insertados correctamente.")

if __name__ == "__main__":
    print("📦 Cargando productos del catálogo...")
    crear_categorias()
    insertar_productos()
    print("✅ Proceso completado.")