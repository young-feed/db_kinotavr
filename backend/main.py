import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI(title="KinoTavr Core API", version="1.0")

DB_HOST = os.getenv("DB_HOST", "db")
DB_NAME = os.getenv("DB_NAME", "movies_db")
DB_USER = os.getenv("DB_USER", "user_admin")
DB_PASS = os.getenv("DB_PASSWORD", "super_secure_password")

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS,
        cursor_factory=RealDictCursor
    )

class ColorResponse(BaseModel):
    id: int
    color_name: str
    hex_code: str
    mood_description: str

class MovieResponse(BaseModel):
    id: int
    kinopoisk_id: Optional[int]
    title: str
    year: Optional[int]
    description: Optional[str]
    poster_url: Optional[str]
    kp_url: Optional[str]
    rutube_url: Optional[str]

class UserActionSchema(BaseModel):
    telegram_user_id: int
    movie_id: int
    action_type: str

@app.get("/api/v1/colors", response_model=List[ColorResponse])
def get_colors():
    """Возвращает палитру для генерации кнопок в ТГ-боте"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, color_name, hex_code, mood_description FROM colors;")
        colors = cursor.fetchall()
        cursor.close()
        conn.close()
        return colors
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/movies/random-by-color", response_model=MovieResponse)
def get_random_movie_by_color(
    color_name: str, 
    telegram_user_id: Optional[int] = None
):
    """
    Выдает случайный фильм по цвету. 
    Если передан telegram_user_id, база автоматически исключит фильмы, 
    которые пользователь уже дизлайкнул.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Запрос с фильтрацией дизлайков пользователя
        query = """
            SELECT m.* FROM movies m
            JOIN movie_colors mc ON m.id = mc.movie_id
            JOIN colors c ON mc.color_id = c.id
            WHERE c.color_name = %s
            AND m.id NOT IN (
                SELECT movie_id FROM user_actions 
                WHERE telegram_user_id = %s AND action_type = 'dislike'
            )
            ORDER BY RANDOM()
            LIMIT 1;
        """
        cursor.execute(query, (color_name, telegram_user_id))
        movie = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not movie:
            raise HTTPException(status_code=404, detail="Нет подходящих фильмов в этой категории")
        return movie
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/users/actions")
def save_user_action(action: UserActionSchema):
    """Сборщик фидбека (лайки, дизлайки) из Telegram-интерфейса"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_actions (telegram_user_id, movie_id, action_type)
            VALUES (%s, %s, %s)
            ON CONFLICT (telegram_user_id, movie_id, action_type) DO NOTHING;
        """, (action.telegram_user_id, action.movie_id, action.action_type))
        conn.commit()
        cursor.close()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))