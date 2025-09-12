# Аутентификация Telegram Web App и усиление безопасности

## Обзор
Документ описывает реализацию аутентификации через Telegram Web App в данном проекте, а также слои безопасности, применённые (и рекомендуемые для продакшена).

## Краткое описание потока
1. Telegram открывает ваше Мини-приложение и внедряет `initData` — строку в формате key=value с добавлением `hash`.
2. Фронтенд отправляет `initData` на бэкенд по эндпоинту `POST /api/v1/auth/telegram`.
3. Бэкенд проверяет подпись (HMAC-SHA256 от отсортированных пар ключ=значение с секретом = SHA256(bot_token)).
4. Бэкенд проверяет свежесть (`auth_date` не старше лимита), применяет лимитирование по IP и защищает от повторного использования (replay protection).
5. При успешной проверке бэкенд выдаёт JWT (HS256) и устанавливает его как httpOnly, Secure cookie.
6. Последующие запросы включают этот cookie; защищённые эндпоинты используют зависимость `get_current_user`.

## Участвующие файлы
- `app/api/v1/endpoints/auth_telegram.py` — основной эндпоинт аутентификации + лимитирование + защита от повторного использования.
- `app/api/v1/deps/current_user.py` — извлечение и валидация JWT из cookie.
- `app/api/v1/router.py` — регистрирует защищённый эндпоинт `/me`.
- `app/main.py` — добавляет middleware для заголовков безопасности.
- `app/core/cache.py` — обёртка над Redis, используемая для лимитирования и хранения replay-фingerprint’ов.

## Алгоритм проверки подписи
```
secret_key = SHA256(bot_token)
data_pairs = отсортированные строки k=v, исключая hash
data_check_string = "\n".join(pairs)
calc = HMAC_SHA256(secret_key, data_check_string).hexdigest()
сравнить calc == полученный hash (постоянное время)
```
Отклонить, если:
- Отсутствует `hash` или `auth_date`.
- Подпись не совпадает.
- `auth_date` старше настроенного максимума (по умолчанию 86400 секунд).

## Лимитирование запросов
Реализовано вручную с использованием Redis:
- Ключ: `rl:auth:{ip}` — инкрементируется при каждом запросе.
- TTL = 60 секунд, лимит = 10 попыток (HTTP 429 при превышении).
Настройка через константы `RATE_LIMIT_WINDOW` и `RATE_LIMIT_MAX`.

## Защита от повторного использования (Replay Protection)
Хранит «отпечаток» (`user_id`, `auth_date`, `hash`) в Redis на 1 час (`REPLAY_WINDOW`).
Если такая же комбинация появляется повторно → ответ 401: Replay detected.

## JWT и Cookie
- Алгоритм: HS256; секрет: `settings.secret_key` (в продакшене меняйте через переменную окружения).
- Заявки (claims): `sub`, `user`, `iat`, `exp`.
- Флаги cookie: HttpOnly, Secure (только в продакшене), SameSite (lax по умолчанию), путь `/`.
- Срок действия: `settings.access_token_expire_minutes`.

## Middleware для заголовков безопасности
Добавляет:
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- Referrer-Policy: strict-origin-when-cross-origin
- Content-Security-Policy: строгий базовый набор
- Strict-Transport-Security (только если не в режиме отладки)

Настройте CSP, если загружаете внешние скрипты — явно добавьте их в разрешённые источники.

## Пример использования на фронтенде (JS)
```js
// Предполагается, что объект Telegram.WebApp доступен глобально
const initData = window.Telegram.WebApp.initData; // сырая строка

async function telegramLogin() {
  const res = await fetch('/api/v1/auth/telegram', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ init_data: initData }),
    credentials: 'include'
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error('Аутентификация не удалась: ' + (err.detail || res.status));
  }
  return res.json();
}

async function fetchWithAuth(url, options = {}) {
  const res = await fetch(url, { ...options, credentials: 'include' });
  if (res.status === 401) {
    // Опционально: повторить telegramLogin() или показать ошибку аутентификации
    throw new Error('Не авторизован');
  }
  return res.json();
}

// Пример вызова защищённого эндпоинта
(async () => {
  try {
    await telegramLogin();
    const me = await fetchWithAuth('/api/v1/me');
    console.log('Текущий пользователь', me.user);
  } catch (e) {
    console.error(e);
  }
})();
```

## Модель угроз и меры защиты
| Угроза | Мера защиты |
|--------|------------|
| Подмена initData | Проверка HMAC-подписи |
| Повторное использование старого initData | Кэширование отпечатка в Redis |
| Перебор подписи | Лимитирование по IP |
| Украсть токен через XSS | HttpOnly cookie + CSP |
| MITM (перехват трафика) | HTTPS + HSTS |
| Фиксация cookie | Новый cookie при каждой аутентификации, ротация секрета при необходимости |
| Повторное использование JWT после выхода | Короткий срок жизни + (опционально) чёрный список в Redis |
| Утечка данных в логах | Не логировать полный initData/hash |

## Рекомендуемые дополнительные меры усиления
1. Ротируйте `secret_key` и поддерживайте несколько ключей (с использованием `kid`).
2. Добавьте структурированное аудит-логирование событий аутентификации.
3. Внедрите опциональный refresh token с ротацией и детекцией повторного использования.
4. Реализуйте детекцию аномалий (например, резкий скачок попыток входа).
5. Интегрируйте сканер уязвимостей зависимостей (например, safety, pip-audit).
6. Добавьте Sentry (или аналог) для мониторинга ошибок в реальном времени.
7. Внедрите базовое лимитирование по пользователю, а не только по IP.

## Советы для локальной разработки
- Если разрабатываете без HTTPS, установите `TOKEN_COOKIE_SECURE=false` в `.env`, чтобы cookie работали.
- Используйте тестовый бот-токен с ограниченными правами.
- Очищайте Redis между запусками, если replay-защита блокирует ручные тесты.

## Переменные окружения (рекомендуемые)
```
BOT_TOKEN=123456:ABC_DEF
SECRET_KEY=ваш-длинный-случайный-секрет
TOKEN_COOKIE_SECURE=false  # только для dev
DEBUG=true
```

## Тестирование
- См. `test_auth_telegram.py` и `test_me_protected.py`.
- Расширьте тесты fuzz-тестами на некорректные строки initData.

## Поддержка
- Регулярно проверяйте документацию Telegram Bot API на предмет изменений в аутентификации WebApp.
- Поддерживайте библиотеки в актуальном состоянии (FastAPI, jose, redis).