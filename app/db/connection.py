import psycopg2

DB_HOST = "localhost"
DB_NAME = "project"
DB_USER = "postgres"
DB_PASSWORD = "password"
DB_PORT = 5432


def get_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        cur = conn.cursor()
        print("✅ Veritabanına başarıyla bağlanıldı.")
        return conn, cur
    except Exception as e:
        print("❌ Bağlantı hatası:", e)
        return None, None