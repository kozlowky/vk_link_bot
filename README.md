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

```bash
cp -rf .env_prod .env
```

#### Установка зависимостей

```bash
pip install -r requirements.txt
```

## Ошибка - ModuleNotFoundError: No module named 'core'
```bash
export DJANGO_SETTINGS_MODULE=core.settings
```
```bash
pwd
```
Скопировать путь до директории
```bash
export PYTHONPATH="${PYTHONPATH}:/путь из pwd"
```
