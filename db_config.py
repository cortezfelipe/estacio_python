import psycopg2
from psycopg2 import pool
import sys

# Configurações de conexão com o banco de dados
def get_db_connection():
    try:
        connection_pool = psycopg2.pool.SimpleConnectionPool(
            1, 20,
            dbname="sgdb_estacio",
            user="estacio",
            password="gTuq3iM4Z1J8Y2Je",
            host="108.181.92.67",
            port="5432"
        )
        if connection_pool:
            return connection_pool
        else:
            print("Erro ao criar o pool de conexões")
            sys.exit(1)
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        sys.exit(1)