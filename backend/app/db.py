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
    
    # Insertar consumidores de prueba (los 12 equipos departamentales con sus presupuestos)
    test_consumers = [
        ("equipo-marketing", 10.00, 0.00),
        ("equipo-producto", 10.00, 0.00),
        # Alta Prioridad
        ("ingenieria-desarrollo", 150.00, 0.00),
        ("legal-compliance", 100.00, 0.00),
        ("datos-ia", 100.00, 0.00),
        ("direccion-estrategia", 200.00, 0.00),
        # Media Prioridad
        ("marketing-contenidos", 50.00, 0.00),
        ("ventas", 50.00, 0.00),
        ("producto", 50.00, 0.00),
        ("finanzas", 75.00, 0.00),
        # Baja Prioridad
        ("atencion-cliente", 15.00, 0.00),
        ("recursos-humanos", 15.00, 0.00),
        ("soporte-ti", 15.00, 0.00),
        ("administracion-operaciones", 20.00, 0.00)
    ]
    
    cursor.executemany("""
        INSERT OR IGNORE INTO consumers (id, budget, current_spend)
        VALUES (?, ?, ?)
    """, test_consumers)
    
    # Crear la tabla de logs con columnas extendidas para FinOps
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
            prompt_tokens INTEGER NOT NULL DEFAULT 0,
            completion_tokens INTEGER NOT NULL DEFAULT 0,
            savings REAL NOT NULL DEFAULT 0.0,
            routing_reason TEXT NOT NULL DEFAULT '',
            event_type TEXT NOT NULL DEFAULT 'success',
            FOREIGN KEY(consumer_id) REFERENCES consumers(id)
        )
    """)
    
    # Migración automática para bases de datos existentes
    cursor.execute("PRAGMA table_info(logs)")
    columns = [row["name"] for row in cursor.fetchall()]
    
    if "prompt_tokens" not in columns:
        print("[MIGRATION] Añadiendo columna 'prompt_tokens' a la tabla 'logs'")
        cursor.execute("ALTER TABLE logs ADD COLUMN prompt_tokens INTEGER NOT NULL DEFAULT 0")
    if "completion_tokens" not in columns:
        print("[MIGRATION] Añadiendo columna 'completion_tokens' a la tabla 'logs'")
        cursor.execute("ALTER TABLE logs ADD COLUMN completion_tokens INTEGER NOT NULL DEFAULT 0")
    if "savings" not in columns:
        print("[MIGRATION] Añadiendo columna 'savings' a la tabla 'logs'")
        cursor.execute("ALTER TABLE logs ADD COLUMN savings REAL NOT NULL DEFAULT 0.0")
    if "routing_reason" not in columns:
        print("[MIGRATION] Añadiendo columna 'routing_reason' a la tabla 'logs'")
        cursor.execute("ALTER TABLE logs ADD COLUMN routing_reason TEXT NOT NULL DEFAULT ''")
    if "event_type" not in columns:
        print("[MIGRATION] Añadiendo columna 'event_type' a la tabla 'logs'")
        cursor.execute("ALTER TABLE logs ADD COLUMN event_type TEXT NOT NULL DEFAULT 'success'")
    
    conn.commit()
    conn.close()
    print("Base de datos inicializada y migrada correctamente (tablas 'consumers' y 'logs').")

if __name__ == "__main__":
    init_db()
