import redis

def get_redis_connection():
    try:
        # Redis bağlantısını oluştur
        r = redis.Redis(
            host='localhost',      # Redis sunucu adresi
            port=6379,             # Varsayılan port
            password=None,         # Şifre varsa buraya yaz
            db=0,                  # Kullanılacak veritabanı numarası
            decode_responses=True  # Verileri string olarak almak için
        )

        # Bağlantıyı test et
        r.ping()
        print("✅ Redis bağlantısı başarılı!")
        return r

    except redis.ConnectionError as e:
        print("❌ Redis bağlantı hatası:", e)
        return None

def set_cache(cache_key: str, uuid: str) -> bool:
    redis_client = get_redis_connection()
    if redis_client:
        try:
            return redis_client.set(cache_key, uuid, ex=10800)
        except Exception as e:
            print("Redis set hatası:", e)
            return False
    return False

def get_cache(cache_key: str):
    redis_client = get_redis_connection()
    if redis_client:
        try:
            value = redis_client.get(cache_key)
            return value
        except Exception as e:
            print("Redis get hatası:", e)
            return None