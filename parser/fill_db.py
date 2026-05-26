import os
import time
import requests
import psycopg2

# Настройки подключения из переменных окружения Docker
DB_HOST = os.getenv("DB_HOST", "db")
DB_NAME = os.getenv("DB_NAME", "movies_db")
DB_USER = os.getenv("DB_USER", "user_admin")
DB_PASS = os.getenv("DB_PASSWORD", "super_secure_password")

KP_API_KEY = os.getenv("KP_API_KEY", "YOUR_KP_API_KEY")

def get_db_connection():
    return psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)

def determine_movie_colors(genres: list, description: str = "") -> list:
    """
    Автоматическая раскладка фильмов по цветам (настроениям) KinoTavr на основе жанров.
    В будущем этот блок можно заменить вызовом локального ИИ.
    """
    assigned_colors = []
    genres = [g.lower() for g in genres]
    desc = description.lower() if description else ""
    
    if any(g in genres for g in ["ужасы", "хоррор"]):
        assigned_colors.append("black")       # Страх
        
    if any(g in genres for g in ["боевик", "криминал"]):
        if any(w in desc for w in ["убийство", "месть", "мафия", "банды", "оружие"]):
            assigned_colors.append("crimson") # Жестокость
            
    if any(g in genres for g in ["драма", "мелодрама"]):
        assigned_colors.append("deep_blue")   # Грусть
        
    if any(g in genres for g in ["комедия", "семейный", "мультфильм"]):
        assigned_colors.append("yellow")      # Радость
        
    if any(g in genres for g in ["фантастика", "фэнтези", "приключения"]):
        assigned_colors.append("purple")      # Загадочность
        
    if any(g in genres for g in ["детектив", "триллер"]):
        assigned_colors.append("emerald")     # Интрига
        
    if not assigned_colors:
        assigned_colors.append("emerald")     # Дефолт, если ничего не подошло
        
    return list(set(assigned_colors))

def search_rutube_link(title: str, year: int) -> str:
    """ Скрипт автоматического поиска зеркал на Rutube по названию """
    try:
        query = f"{title} {year} смотреть фильм"
        url = f"https://rutube.ru/api/search/video/?query={requests.utils.quote(query)}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            results = response.json().get("results", [])
            # Защита от трейлеров: ищем видео длительностью больше 40 минут (2400 секунд)
            for video in results:
                if video.get("duration", 0) > 2400: 
                    return video.get("video_url")
            if results:
                return results[0].get("video_url")
    except Exception as e:
        print(f"Ошибка Rutube поиска для '{title}': {e}")
    return None

def fetch_movies_from_api():
    """ Имитация ответа от KinoPoisk API Unofficial / kinopoisk.dev """
    return [
        {
            "id": 535341, "name": "1+1", "year": 2011,
            "description": "Пострадав в результате несчастного случая, богатый аристократ Филипп нанимает в помощники человека...",
            "poster": {"url": "https://avatars.mds.yandex.net/get-kinopoisk-image/.../orig"},
            "genres": [{"name": "комедия"}, {"name": "драма"}]
        },
        {
            "id": 448, "name": "Начало", "year": 2010,
            "description": "Кобб — талантливый вор, лучший в опасном искусстве извлечения ценных секретов из подсознания во время сна.",
            "poster": {"url": "https://avatars.mds.yandex.net/get-kinopoisk-image/.../orig"},
            "genres": [{"name": "фантастика"}, {"name": "триллер"}]
        }
    ]

def save_to_database(conn, movie_data):
    cursor = conn.cursor()
    kp_id = movie_data["id"]
    title = movie_data["name"]
    year = movie_data["year"]
    desc = movie_data["description"]
    poster = movie_data["poster"]["url"]
    kp_url = f"https://www.kinopoisk.ru/film/{kp_id}/"
    genres_list = [g["name"] for g in movie_data["genres"]]
    
    rutube_url = search_rutube_link(title, year)
    
    try:
        cursor.execute("""
            INSERT INTO movies (kinopoisk_id, title, year, description, poster_url, kp_url, rutube_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT (kinopoisk_id) DO UPDATE SET rutube_url = EXCLUDED.rutube_url
            RETURNING id;
        """, (kp_id, title, year, desc, poster, kp_url, rutube_url))
        
        movie_id = cursor.fetchone()[0]
        detected_colors = determine_movie_colors(genres_list, desc)
        
        for color_name in detected_colors:
            cursor.execute("SELECT id FROM colors WHERE color_name = %s;", (color_name,))
            color_res = cursor.fetchone()
            if color_res:
                cursor.execute("INSERT INTO movie_colors (movie_id, color_id) VALUES (%s, %s) ON CONFLICT DO NOTHING;", (movie_id, color_res[0]))
                
        conn.commit()
        print(f"Фильм '{title}' успешно добавлен и окрашен: {detected_colors}")
    except Exception as e:
        conn.rollback()
        print(f"Ошибка сохранения {title}: {e}")
    finally:
        cursor.close()

def main():
    try:
        conn = get_db_connection()
        movies = fetch_movies_from_api()
        for movie in movies:
            save_to_database(conn, movie)
            time.sleep(1)
        conn.close()
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    main()