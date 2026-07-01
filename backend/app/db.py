import sqlite3
import os

# Ruta de la base de datos SQLite
DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "finops.db")

def get_db_connection():
    """
    Establece y retorna una conexión a la base de datos SQLite.
    Configura row_factory para poder acceder a las columnas por su nombre.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Crea la tabla 'consumers' e inserta los datos iniciales de prueba.
    """
    print(f"Inicializando base de datos en: {os.path.abspath(DATABASE_PATH)}")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Crear la tabla de consumidores
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS consumers (
            id TEXT PRIMARY KEY,
            budget REAL NOT NULL,
            current_spend REAL NOT NULL DEFAULT 0.0
        )
    """)
    
    # Insertar consumidores de prueba (equipo-marketing, equipo-producto y consumidores de Mercedes)
    # Usamos INSERT OR IGNORE para no duplicar datos si se vuelve a correr el script
    test_consumers = [
        ("equipo-marketing", 10.00, 0.00),
        ("equipo-producto", 10.00, 0.00),
        ("mercedes-drive-assistant", 100.00, 0.00),
        ("mercedes-analytics-dashboard", 50.00, 0.00),
        ("mercedes-lab-experiments", 10.00, 0.00)
    ]
    
    cursor.executemany("""
        INSERT OR IGNORE INTO consumers (id, budget, current_spend)
        VALUES (?, ?, ?)
    """, test_consumers)
    
    # Crear la tabla de logs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL DEFAULT (datetime('now')),
            consumer_id TEXT NOT NULL,
            prompt TEXT NOT NULL,
            response TEXT NOT NULL,
            model_used TEXT NOT NULL,
            cost REAL NOT NULL,
            saved_by_cache INTEGER NOT NULL CHECK (saved_by_cache IN (0, 1)),
            FOREIGN KEY(consumer_id) REFERENCES consumers(id)
        )
    """)
    
    conn.commit()
    conn.close()
    print("Base de datos inicializada correctamente (tablas 'consumers' y 'logs').")

if __name__ == "__main__":
    init_db()
