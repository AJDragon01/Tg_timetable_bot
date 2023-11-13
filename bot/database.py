import sqlite3

class DatabaseManager:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.create_table()

    def create_table(self):
        # Создание таблицы, если она ещё не существует
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shifts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                location TEXT NOT NULL,
                date TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL
            )
        """)
        # Создание таблицы users
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def add_user_to_db(self, name):
        # Добавление пользователя в базу данных
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO users (name) VALUES (?)
        """, (name,))
        self.conn.commit()

    def add_shift_to_db(self, user_id, location, date, start_time, end_time):
        # Добавление смены в базу данных
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO shifts (user_id, location, date, start_time, end_time) 
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, location, date, start_time, end_time))
        self.conn.commit()

    def remove_shift_from_db(self, shift_id):
        # Удаление смены из базы данных
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM shifts WHERE id = ?", (shift_id,))
        self.conn.commit()

    def get_shifts_from_db(self, user_id, date):
        # Получение смен из базы данных на определенную дату
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM shifts WHERE user_id = ? AND date = ?", (user_id, date))
        return cursor.fetchall()
    
    def get_users(self):
         # Получение списка пользователей из базы данных
         cursor = self.conn.cursor()
         cursor.execute("SELECT * FROM users")
         return cursor.fetchall()
