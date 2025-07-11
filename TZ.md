# 📌 Техническое задание

## Проект: **Memory Keeper**

---

## 🧠 Общая концепция

**Memory Keeper** — это веб-приложение, предназначенное для хранения и визуализации воспоминаний в виде фотографий и заметок. Пользователь может загружать изображения, указывать место и дату события, а затем просматривать воспоминания на карте с визуальными метками.

---

## 🎯 Цели проекта

- Создать простой и удобный сервис для хранения личных воспоминаний.
- Визуализировать места, связанные с фотографиями, на карте при помощи Yandex Maps API.
- Обеспечить надежную регистрацию и авторизацию пользователей.

---

## 🔧 Функциональные возможности

### 1. 📷 Загрузка и хранение воспоминаний

- Загрузка изображений с возможностью прикрепить описание, дату и **ввести адрес места**, где была сделана фотография.
- Адрес автоматически преобразуется в координаты с помощью геокодирования через API.
- Возможность добавления текстовых заметок и тегов к каждой фотографии.

### 2. 🗺️ Интерактивная карта воспоминаний

- Отображение фотографий на **карте Яндекса** с помощью **Yandex Maps API**.
- Каждая метка представляет собой **иконку-снимок** — уменьшенную версию загруженного изображения.
- При клике на метку открывается увеличенное изображение.

### 3. 👤 Регистрация и авторизация

- Регистрация пользователей по email и паролю.
- Авторизация и выход из аккаунта.
- Защита данных с помощью безопасного хранения паролей (хеширование).

### 4. 🗂️ Просмотр и управление воспоминаниями

- Личный кабинет с галереей всех загруженных пользователем воспоминаний.
- Возможность редактировать и удалять записи.

### 5. 📁 Экспорт данных

- Возможность **скачать все загруженные фото архивом .zip**.

---

## 🛠️ Технологии и стек

- **Backend:** Python + Flask  
- **ORM:** SQLAlchemy  
- **Frontend:** HTML, CSS (Bootstrap или Tailwind)  
- **Интерактивная карта:** Yandex Maps API (JavaScript SDK)  
- **Хранение данных:** SQLAlchemy  
- **Система аутентификации:** Flask-Login  

---

## 🔐 Требования к безопасности

- Ограничение на размер загружаемых изображений.
- Проверка формата и типа файлов.
- Защита от XSS и CSRF атак.
