# Менеджер Подписок

---

### Краткое описание

Веб-приложение для управления подписками, разработанное с использованием **Vue.js** на фронтенде и **FastAPI** на бекенде. Приложение позволяет пользователям покупать подписки, а администраторам — управлять тарифными планами и пользователями.

---

### 🚀 Предварительные требования

Прежде чем начать, убедитесь, что у вас установлены:

* **Node.js** 18+
* **Python** 3.10+
* **MongoDB** 5.0+

---

## 🛠 Технологии


**Frontend**:
[![Vue](https://img.shields.io/badge/Vue-3.5-green?logo=vue.js)](https://vuejs.org/)
[![JavaScript](https://img.shields.io/badge/JavaScript-ESNext-yellow?logo=javascript)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
[![Vite](https://img.shields.io/badge/Vite-6.0-purple?logo=vite)](https://vitejs.dev/)

**Backend**:
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-lightgrey?logo=fastapi)](https://fastapi.tiangolo.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-5.0-green?logo=mongodb)](https://www.mongodb.com/)
[![Motor](https://img.shields.io/badge/Motor-3.0-blue)](https://motor.readthedocs.io/)

---

### 📦 Установка

Для запуска проекта выполните следующие шаги:

1.  **Клонируйте репозиторий:**

    ```bash
    git clone https://github.com/Vergil23416/9.project-template-python.git
    cd 9.project-template-python
    ```

2.  **Настройте Backend:**

    В корне проекта выполните команды:

    ```bash
    python -m venv .venv
    # Для Linux/macOS:
    source .venv/bin/activate
    # Для Windows:
    .\.venv\Scripts\activate
    pip install -r requirements.txt
    ```

3.  **Настройте Frontend:**

    В корне проекта выполните команду:

    ```bash
    npm install
    ```

4.  **Конфигурация:**

    Создайте файл `.env` в **корне проекта** со следующими параметрами:

    ```env
    JWT_SECRET=ВАШ_СЕКРЕТНЫЙ_КЛЮЧ_ДЛЯ_JWT_ТОКЕНОВ # Используйте HS256
    REFRESH_SECRET=ВАШ_СЕКРЕТНЫЙ_КЛЮЧ_ДЛЯ_REFRESH_ТОКЕНОВ # Используйте HS256, ключ отличен от JWT_SECRET
    MONGO_URI=mongodb://127.0.0.1:27017/8_films # Или ваша ссылка на MongoDB
    PORT=3005 # Порт, на котором будет работать Backend
    CLIENT_URL=http://localhost:5173 # URL, на котором будет работать Frontend
    STATIC_FILES_DIR=./public # Путь к статическим файлам
    MONGO_DB_NAME=8_films # Название вашей базы данных MongoDB
    ```

---

### ▶️ Запуск

Откройте **два отдельных терминала**: один для Backend, другой для Frontend.

**Backend:**

```bash
# Активируйте виртуальное окружение
# Для Linux/macOS:
source .venv/bin/activate
# Для Windows:
.\.venv\Scripts\activate

# Запустите FastAPI сервер
uvicorn backend.main:app --reload --host 0.0.0.0 --port 3005
```

**Frontend:**
```bash
# В отдельном терминале
# Запустите Vue сервер
npm run dev
```
