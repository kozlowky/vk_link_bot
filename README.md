# Стэк:
Django>=4.2.2\
PostgreSQL\
pyTelegramBotAPI

# Настройки перед запуском
## Отредактируйте «.env_prod».
### Django settings
SECRET_KEY - Сгенерируйте [ключ](https://djecrety.ir/)\
DEBUG - Установите режим DEBUG - True/False

### Database settings
DB_NAME - Имя базы данных\
DB_USER - Пользователь базы данных\
DB_PASSWORD - Пароль базы данных\
DB_HOST - Хост базы данных\
DB_PORT - Порт базы данных\

### Telegram Token
TOKEN_BOT - Телеграм токен

### VK Token
VK_ACCESS_TOKEN - VK_API токе

## Создание .env
Скопируйте файл конфигурации в определенное место для вашей среды.\
Этот шаг следует выполнять каждый раз при изменении «.env_prod».\

## Настройка проекта

Проект настраивается через переменные окружения, указанные в файле src/.env

Пример .env файла указан в .env.example:

| Ключ                | Значение                           | По умолчанию          |
|---------------------|------------------------------------|-----------------------|
| `SECRET_KEY`        | Секретный ключ                     | `the-most-secret-key` |
| `DEBUG`             | Режим дебага                       | `True`                |
| `POSTGRES_DB`       | Имя БД                             | `fgos`                |
| `POSTGRES_USER`     | Пользователь БД                    | `postgres`            |
| `POSTGRES_PASSWORD` | Пароль пользователя БД             | `postgres`            |
| `POSTGRES_HOST`     | Адрес СУБД                         | `db`                  |
| `POSTGRES_PORT`     | Порт СУБД                          | `5432`                |
| `REDIS_HOST `       | Адрес брокера                      | `redis`               |
| `RREDIS_PORT `      | Порт брокера                       | `6379`                |
| `STATIC_PATH`       | Путь до статических файлов         | `/project/static`     |
| `MEDIA_PATH`        | Путь до медиа файлов               | `/project/media`      |
| `APP_PROXY_PORT`    | Порт контейнера с бэкендом         | `8000`                |
| `APP_PROXY_LINK`    | Наименование контейнера с бэкендом | `app`                 |

```bash
cp -rf .env_prod .env
```

#### Установка зависимостей

```bash
pip install -r requirements.txt
```
