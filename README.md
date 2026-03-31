# Электронная библиотека (Python backend)

Готовая серверная часть для проекта «Электронная библиотека» с автоматическим сканированием указанной папки на сервере.

## Что реализовано

- Автосканирование каталога `ELIBRARY_ROOT` и индексация книг форматов: PDF, EPUB, FB2, DJVU, DOCX.
- Раскладка книг по **направлениям** и **программам** на основе структуры папок:
  - `root/<направление>/<программа>/<файл-книги>`
- Глубокий анализ метаданных:
  - sidecar JSON (`book.pdf.json`),
  - извлечение заголовка из PDF/EPUB/FB2/DOCX,
  - fallback к анализу имени файла.
- Поиск по каталогу с базовой морфологической нормализацией русского текста.
- Привязка медиафайлов к книге (изображения/аудио/видео с тем же именем файла).
- Генерация динамической ссылки на скачивание (TTL по умолчанию 5 минут).

## API

- `GET /health`
- `GET /version` — версия сервиса (для проверки успешного обновления).
- `POST /scan` — пересканировать каталог.
- `GET /books` — список/фильтрация/поиск.
- `GET /books/{book_id}` — карточка книги.
- `GET /books/{book_id}/dynamic-link` — временная ссылка.
- `GET /download?...` — проверка динамической ссылки.

## Локальный запуск

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export ELIBRARY_ROOT=/absolute/path/to/library
export ELIBRARY_SIGNING_KEY=$(openssl rand -hex 32)
uvicorn app.main:app --reload
```

## Пример структуры папок

```text
/library
  /Информатика
    /Python
      Гвидо ван Россум - Введение в Python.pdf
      Гвидо ван Россум - Введение в Python.mp4
```

## Развертывание на Linux через systemd + Apache (доступ в локальной сети)

### 1) Установка зависимостей ОС (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install -y python3 python3-venv apache2
sudo a2enmod proxy proxy_http headers
```

### 2) Подготовка проекта

```bash
sudo mkdir -p /opt/e_library
sudo cp -R . /opt/e_library
cd /opt/e_library
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3) Подготовка папки с книгами

```bash
sudo mkdir -p /srv/e_library/library
sudo chown -R www-data:www-data /srv/e_library
```

### 4) Настройка systemd

1. Скопируйте шаблон сервиса:
```bash
sudo cp deploy/systemd/e_library.service /etc/systemd/system/e_library.service
```
2. Отредактируйте `/etc/systemd/system/e_library.service`:
   - `ELIBRARY_ROOT` (путь к папке книг)
   - `ELIBRARY_SIGNING_KEY` (длинный секрет)
   - `WorkingDirectory` и `ExecStart`, если путь другой
3. Запустите сервис:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now e_library
sudo systemctl status e_library
```

### 5) Настройка Apache как reverse proxy

```bash
sudo cp deploy/apache/e_library.conf /etc/apache2/sites-available/e_library.conf
sudo a2ensite e_library.conf
sudo systemctl reload apache2
```

По умолчанию Apache слушает `*:80`, а backend работает на `127.0.0.1:8085`.
Для доступа по локальной сети откройте в браузере: `http://<IP_СЕРВЕРА>/docs`

### 6) Если используется UFW

```bash
sudo ufw allow 80/tcp
sudo ufw reload
```

## Проверка

```bash
curl http://127.0.0.1:8085/health
curl http://<IP_СЕРВЕРА>/health
```

> Рекомендуется явно задать `ELIBRARY_SIGNING_KEY`; иначе будет сгенерирован эфемерный ключ на каждый запуск.

## Тесты

```bash
pytest -q
```
