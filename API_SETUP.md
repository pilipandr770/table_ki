# Настройка API ключей

## 🔑 Stripe Configuration

Для работы с платежами нужно настроить Stripe:

1. **Создайте аккаунт Stripe:**
   - Перейдите на https://stripe.com
   - Зарегистрируйтесь или войдите в аккаунт

2. **Получите API ключи:**
   - В Dashboard перейдите в Developers → API keys
   - Скопируйте **Publishable key** и **Secret key**

3. **Создайте продукты и цены:**
   - В Dashboard перейдите в Products
   - Создайте два продукта:
     - "Single Table Access" (доступ к одной таблице)
     - "Multi Table Access" (доступ к нескольким таблицам)
   - Скопируйте Price ID для каждого продукта

4. **Настройте webhook:**
   - В Developers → Webhooks создайте новый endpoint
   - URL: `http://ваш-домен/auth/stripe-webhook`
   - Events: `payment_intent.succeeded`, `invoice.payment_succeeded`
   - Скопируйте webhook secret

5. **Обновите .env файл:**
```bash
STRIPE_PUBLISHABLE_KEY=pk_test_ваш_publishable_key
STRIPE_SECRET_KEY=sk_test_ваш_secret_key
STRIPE_WEBHOOK_SECRET=whsec_ваш_webhook_secret
STRIPE_SINGLE_TABLE_PRICE_ID=price_ваш_single_table_price_id
STRIPE_MULTI_TABLE_PRICE_ID=price_ваш_multi_table_price_id
```

## 🤖 OpenAI Configuration

Для работы с AI чатом нужно настроить OpenAI:

1. **Создайте аккаунт OpenAI:**
   - Перейдите на https://platform.openai.com
   - Зарегистрируйтесь или войдите в аккаунт

2. **Получите API ключ:**
   - Перейдите в User menu → View API keys
   - Создайте новый секретный ключ
   - Скопируйте ключ (он показывается только один раз!)

3. **Обновите .env файл:**
```bash
OPENAI_API_KEY=sk-ваш_openai_api_key
```

## 📧 Email Configuration (опционально)

Для отправки email уведомлений:

1. **Gmail (рекомендуется для тестирования):**
```bash
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=ваш-email@gmail.com
MAIL_PASSWORD=ваш-app-password  # Не обычный пароль!
```

2. **Для Gmail нужно создать App Password:**
   - Перейдите в Google Account settings
   - Security → 2-Step Verification → App passwords
   - Создайте новый app password для "Mail"

## 🔒 Security

⚠️ **ВАЖНО**: Никогда не коммитьте реальные API ключи в Git!

- Файл `.env` уже добавлен в `.gitignore`
- Используйте разные ключи для разработки и продакшена
- Регулярно ротируйте API ключи

## 🧪 Тестирование без API ключей

Приложение будет работать и без настроенных API ключей:
- ✅ Регистрация и авторизация
- ✅ Загрузка Excel файлов  
- ✅ Базовый интерфейс
- ❌ AI чат (нужен OpenAI API)
- ❌ Платежи (нужен Stripe API)
- ❌ Email уведомления (нужна настройка почты)

## 📋 Проверка конфигурации

Посетите `/status` для проверки статуса конфигурации.
