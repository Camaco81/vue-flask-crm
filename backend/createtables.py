import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Get your database connection string from the environment variables
# It's a good practice to not hardcode sensitive information
DB_CONNECTION_STRING = os.environ.get("DATABASE_URL")

def create_additional_tables():
    """Crea las tablas 'customers' y 'products' en la base de datos de Neon."""
    
    # SQL para crear la tabla de clientes (NUEVA)
    create_customers_table_query = """
    CREATE TABLE IF NOT EXISTS customers (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name VARCHAR(255) NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        phone VARCHAR(50),
        address TEXT,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    """

    # SQL para crear la tabla de productos (NUEVA)
    create_products_table_query = """
    CREATE TABLE IF NOT EXISTS products (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name VARCHAR(255) NOT NULL,
        price NUMERIC(10, 2) NOT NULL,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    """

    conn = None
    try:
        # Connect to the Neon database
        print("Conectando a la base de datos de Neon...")
        conn = psycopg2.connect(DB_CONNECTION_STRING)
        cur = conn.cursor()
        
        # Execute the queries to create the new tables
        print("Creando la tabla 'customers'...")
        cur.execute(create_customers_table_query)
        print("Creando la tabla 'products'...")
        cur.execute(create_products_table_query)
        
        # Commit the changes
        conn.commit()
        print("Tablas 'customers' y 'products' creadas con éxito.")

    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error al conectar o crear las tablas: {error}")
    finally:
        if conn is not None:
            cur.close()
            conn.close()
            print("Conexión a la base de datos cerrada.")

if __name__ == '__main__':
    # Set the DATABASE_URL environment variable for local testing
    os.environ['DATABASE_URL'] = 'postgresql://neondb_owner:npg_AnUI5S0uDtbk@ep-still-haze-adr0zxp4-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'
    
    if 'DATABASE_URL' not in os.environ:
      print("¡Atención! La variable de entorno 'DATABASE_URL' no está configurada. Por favor, asegúrate de establecerla con tu cadena de conexión de Neon.")
    else:
      create_additional_tables()