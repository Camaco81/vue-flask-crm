import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Get your database connection string from the environment variables
DB_CONNECTION_STRING = os.environ.get("DATABASE_URL")

def create_additional_tables():
    """Crea las tablas 'orders' y 'order_items' en la base de datos de Neon."""
    
    # SQL para crear la tabla de pedidos (NUEVA)
    create_orders_table_query = """
    CREATE TABLE IF NOT EXISTS orders (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
        order_date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        status VARCHAR(50) NOT NULL DEFAULT 'Pendiente',
        total_amount NUMERIC(10, 2) NOT NULL
    );
    """

    # SQL para crear la tabla de elementos de pedido (NUEVA)
    create_order_items_table_query = """
    CREATE TABLE IF NOT EXISTS order_items (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        order_id UUID REFERENCES orders(id) ON DELETE CASCADE,
        product_id UUID REFERENCES products(id) ON DELETE CASCADE,
        quantity INTEGER NOT NULL,
        price NUMERIC(10, 2) NOT NULL
    );
    """

    conn = None
    try:
        # Connect to the Neon database
        print("Conectando a la base de datos de Neon...")
        conn = psycopg2.connect(DB_CONNECTION_STRING)
        cur = conn.cursor()
        
        # Execute the queries to create the new tables
        print("Creando la tabla 'orders'...")
        cur.execute(create_orders_table_query)
        print("Creando la tabla 'order_items'...")
        cur.execute(create_order_items_table_query)
        
        # Commit the changes
        conn.commit()
        print("Tablas 'orders' y 'order_items' creadas con éxito.")

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