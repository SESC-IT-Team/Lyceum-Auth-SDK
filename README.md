# Lyceum Auth SDK

**Lyceum Auth SDK** — Python-пакет для интеграции бэкенд-сервисов **СУНЦ УрФУ** с сервисом авторизации.

SDK предоставляет готовые FastAPI-зависимости для:

* проверки access token;
* валидации JWT;
* проверки `scopes`;
* получения текущего пользователя;
* ограничения доступа по ролям;
* получения access token;
* интеграции с OAuth 2.0 в качестве BFF.

---

## Содержание

* [Установка](#1-установка)
* [Проверка авторизации](#2-проверка-авторизации)

  * [Создание зависимости](#21-создание-зависимости)
  * [Защита эндпоинта](#22-защита-эндпоинта)
  * [Проверка scopes](#23-проверка-scopes)
* [Получение access token](#3-получение-access-token)
* [Получение текущего пользователя](#4-получение-текущего-пользователя)
* [Ограничение доступа по ролям](#5-ограничение-доступа-по-ролям)
* [OAuth 2.0 BFF](#6-oauth-20-bff)
* [Настройки](#7-настройки)
* [Краткая памятка](#8-краткая-памятка)

---

# 1. Установка

Добавьте Git-репозиторий SDK в `pyproject.toml`:

```toml
[tool.uv.sources]
sesc-auth-sdk = { git = "https://github.com/SESC-IT-Team/Lyceum-Auth-SDK.git" }
```

Затем установите пакет:

```shell
uv add sesc-auth-sdk
```

После установки пакет будет доступен в проекте как обычная Python-зависимость.

---

# 2. Проверка авторизации

## Важно: `LyceumAuth` нельзя использовать напрямую

`LyceumAuth` является **базовым классом для создания зависимости авторизации**.

Использование:

```python
Depends(LyceumAuth())
```

**не допускается**.

Необходимо создать собственный класс-наследник `LyceumAuth`, настроить в нём `JWKSManager`, а затем использовать уже этот класс.

---

## 2.1. Создание зависимости

Создайте собственный класс, унаследованный от `LyceumAuth`.

Для валидации JWT необходимо настроить `JWKSManager`:

```python
from sesc_auth_sdk.dependencies import (
    LyceumAuth,
    create_jwks_manager_dependency,
)
from sesc_auth_sdk.services.jwks_manager import JWKSManager
from sesc_auth_sdk.settings import TokenValidationSettings


jwks_manager = JWKSManager(
    TokenValidationSettings(...)
)


class Auth(LyceumAuth):
    get_jwks_manager = create_jwks_manager_dependency(
        jwks_manager
    )

    # Необходимо только для зависимостей,
    # работающих с объектом пользователя.
    user_service_url = "<URL API пользователей>"
```

Именно класс `Auth` является зависимостью, которую следует использовать в приложении.

---

## 2.2. Защита эндпоинта

После создания класса `Auth` его можно использовать в FastAPI:

```python
from fastapi import Depends, FastAPI

from sesc_auth_sdk.schemas.token import AccessTokenPayload

from app.auth import Auth


app = FastAPI()


@app.get("/")
def index(
    payload: AccessTokenPayload = Depends(Auth()),
):
    return {
        "message": "Hello!",
        "subject": payload.sub,
    }
```

При обращении к эндпоинту SDK:

1. получает access token из запроса;
2. проверяет его наличие;
3. валидирует JWT;
4. проверяет необходимые параметры токена;
5. передаёт `AccessTokenPayload` в обработчик.

Если пользователь не авторизован или токен невалиден, сервер возвращает:

```text
401 Unauthorized
```

---

## 2.3. Проверка scopes

Чтобы ограничить доступ к эндпоинту по `scopes`, передайте необходимые scopes через параметр `required_scopes`.

Например:

```python
from fastapi import Depends, FastAPI

from sesc_auth_sdk.enums.scope import Scope
from sesc_auth_sdk.schemas.token import AccessTokenPayload

from app.auth import Auth


app = FastAPI()


@app.get("/")
def index(
    payload: AccessTokenPayload = Depends(
        Auth(
            required_scopes=[
                Scope.profile,
            ],
        )
    ),
):
    return {
        "message": "Hello!",
    }
```

Можно указать несколько scopes:

```python
Auth(
    required_scopes=[
        Scope.profile,
        Scope.email,
    ]
)
```

Для доступа к эндпоинту токен должен содержать все указанные scopes.

Если в токене отсутствует хотя бы один из требуемых scopes, сервер возвращает:

```text
403 Forbidden
```

### `401 Unauthorized` и `403 Forbidden`

| Код                | Причина                                          |
| ------------------ | ------------------------------------------------ |
| `401 Unauthorized` | Пользователь не авторизован или токен невалиден  |
| `403 Forbidden`    | Токен валиден, но не содержит необходимых scopes |

---

# 3. Получение access token

Если зависимость должна возвращать непосредственно access token, используйте:

```python
Auth(...).return_token
```

Пример:

```python
@app.get("/token")
def token(
    access_token: str = Depends(
        Auth().return_token,
    ),
):
    ...
```

`return_token` удобно использовать, когда полученный access token необходимо передать другому внутреннему сервису.

> **Важно:** access token является чувствительными данными. Не возвращайте его клиенту без необходимости.

---

# 4. Получение текущего пользователя

Если endpoint должен получить объект текущего пользователя, используйте:

```python
Auth(...).return_user
```

Возвращаемый тип:

```python
sesc_auth_sdk.schemas.user.User
```

Пример:

```python
from fastapi import Depends

from app.auth import Auth


@app.get("/me")
def me(
    user = Depends(
        Auth().return_user,
    ),
):
    return user
```

## Настройка `user_service_url`

Для использования `return_user` в классе `Auth` необходимо указать URL API пользователей:

```python
class Auth(LyceumAuth):
    get_jwks_manager = create_jwks_manager_dependency(
        jwks_manager
    )

    user_service_url = "<URL API пользователей>"
```

Без `user_service_url` зависимость `return_user` использовать нельзя.

### Производительность

Каждый вызов `return_user` выполняет HTTP-запрос к API пользователей.

Схематично это выглядит так:

```text
Client
  │
  ▼
Your API
  │
  ▼
Lyceum Auth SDK
  │
  │ HTTP request
  ▼
User API
```

Поэтому `return_user` следует использовать только тогда, когда действительно необходим объект пользователя.

Если достаточно данных из токена, предпочтительнее использовать:

```python
Depends(Auth())
```

и работать с `AccessTokenPayload`.

---

# 5. Ограничение доступа по ролям

Если доступ к endpoint должен быть разрешён только пользователям с определёнными ролями, используйте:

```python
Auth(...).restrict_roles_and_return_user(
    allowed_roles=[...],
)
```

Пример:

```python
@app.get("/admin")
def admin(
    user = Depends(
        Auth().restrict_roles_and_return_user(
            allowed_roles=[
                ...
            ],
        )
    ),
):
    return user
```

Зависимость:

1. проверяет access token;
2. получает текущего пользователя;
3. проверяет его роли;
4. возвращает объект пользователя, если доступ разрешён.

Возвращаемый тип:

```python
sesc_auth_sdk.schemas.user.User
```

Для использования этой зависимости необходимо указать:

```python
class Auth(LyceumAuth):
    get_jwks_manager = create_jwks_manager_dependency(
        jwks_manager
    )

    user_service_url = "<URL API пользователей>"
```

> **Важно:** каждый вызов зависимости выполняет запрос к API пользователей.

---

# 6. OAuth 2.0 BFF

SDK также можно использовать для создания **OAuth 2.0 Backend for Frontend (BFF)**.

BFF следует использовать для приложений, в которых backend выступает посредником между пользовательским интерфейсом и сервисом авторизации.

Для этого необходимо подключить встроенный `auth_router`.

```python
from fastapi import FastAPI

from sesc_auth_sdk.routers.auth_router import create_auth_router
from sesc_auth_sdk.settings import AuthRouterSettings


app = FastAPI()


auth_router = create_auth_router(
    AuthRouterSettings(...)
)

app.include_router(auth_router, prefix='/auth')
```

После этого OAuth 2.0 endpoints будут доступны через подключённый router.

---

# 7. Настройки

SDK использует отдельные классы настроек для разных частей авторизации:

* `TokenValidationSettings` — настройки проверки JWT;
* `AuthRouterSettings` — настройки OAuth 2.0 BFF;
* `M2MSettings` — настройки service-to-service авторизации.

Все классы основаны на `pydantic-settings`, поэтому значения можно передавать напрямую или загружать из переменных окружения и `.env`.

---

## 7.1. Настройки проверки токена

Для настройки `JWKSManager` используется `TokenValidationSettings`:

```python
from sesc_auth_sdk.services.jwks_manager import JWKSManager
from sesc_auth_sdk.settings import TokenValidationSettings

jwks_manager = JWKSManager(
    TokenValidationSettings(
        allowed_issuers=[
            "https://auth.example.com/application/o/my-app/",
        ],
        jwks_ttl=900,
    )
)
```

### Поля `TokenValidationSettings`

| Поле              | Тип         | По умолчанию       | Описание                                                                                                                 |
| ----------------- | ----------- | ------------------ | ------------------------------------------------------------------------------------------------------------------------ |
| `allowed_issuers` | `list[str]` | `—` (обязательный) | Список доверенных `issuer` (`iss`) в JWT. Только токены, выпущенные этими issuer, считаются валидными.                   |
| `jwks_ttl`        | `int`       | `900`              | Время кеширования JWKS в секундах. Определяет, как долго публичные ключи используются из кеша перед повторной загрузкой. |

---

## 7.2. Настройки OAuth 2.0 BFF

Для `create_auth_router()` используется `AuthRouterSettings`:

```python
from sesc_auth_sdk.routers.auth_router import create_auth_router
from sesc_auth_sdk.settings import AuthRouterSettings

auth_router = create_auth_router(
    AuthRouterSettings(
        authentik_url="https://auth.example.com",
        client_id="...",
        client_secret="...",
        application_slug="my-app",
        login_redirect_uri="https://example.com/auth/callback",
        router_path="/auth",
    )
)
```

### Поля `AuthRouterSettings`

#### Основные OAuth-параметры

| Поле                 | Тип   | По умолчанию       | Описание                                                                                                        |
| -------------------- | ----- | ------------------ | --------------------------------------------------------------------------------------------------------------- |
| `authentik_url`      | `str` | `—` (обязательный) | Базовый URL сервиса авторизации (Authentik). Используется для OAuth-запросов.                                   |
| `client_id`          | `str` | `—` (обязательный) | OAuth Client ID приложения.                                                                                     |
| `client_secret`      | `str` | `—` (обязательный) | OAuth Client Secret. Используется для обмена authorization code на токены.                                      |
| `application_slug`   | `str` | `—` (обязательный) | Идентификатор приложения в Authentik.                                                                           |
| `login_redirect_uri` | `str` | `—` (обязательный) | URI, на который пользователь перенаправляется после успешной авторизации.                                       |
| `router_path`        | `str` | `—` (обязательный) | Базовый путь auth router, например `/auth`. На него выставляются временные oauth cookie и refresh token cookie. |

#### Cookie и безопасность

| Поле              | Тип                                        | По умолчанию | Описание                                                                                |
| ----------------- | ------------------------------------------ | ------------ | --------------------------------------------------------------------------------------- |
| `cookie_domain`   | `str \| None`                              | `None`       | Домен, для которого устанавливаются cookies.                                            |
| `cookie_secure`   | `bool`                                     | `False`      | Если `True`, cookies передаются только по HTTPS. Для production рекомендуется включить. |
| `cookie_samesite` | `Literal["lax", "strict", "none"] \| None` | `None`       | Политика `SameSite` для cookies.                                                        |

#### TTL токенов и OAuth flow cookies

| Поле                                        | Тип   | По умолчанию | Описание                                                                  |
| ------------------------------------------- | ----- | ------------ | ------------------------------------------------------------------------- |
| `refresh_token_ttl`                         | `int` | `2592000`    | Время жизни refresh token cookie в секундах.                              |
| `access_token_ttl`                          | `int` | `300`        | Время жизни access token cookie в секундах.                               |
| `oauth_initial_oauth_code_flow_cookies_ttl` | `int` | `300`        | TTL временных cookies OAuth code flow: `state`, `nonce`, `code_verifier`. |

#### Поведение ответа

| Поле                                 | Тип    | По умолчанию | Описание                                              |
| ------------------------------------ | ------ | ------------ | ----------------------------------------------------- |
| `send_access_token_in_json_response` | `bool` | `True`       | Если `True`, access token возвращается в JSON-ответе. |
| `send_access_token_as_cookie`        | `bool` | `False`      | Если `True`, access token сохраняется в cookie.       |

---

## 7.3. Настройки M2M

Для service-to-service авторизации используется `M2MSettings`:

```python
from sesc_auth_sdk.settings import M2MSettings

m2m_settings = M2MSettings(
    authentik_url="https://auth.example.com",
    client_id="...",
    application_slug="my-service",
    service_account_username="my-service-account",
    service_account_app_password="...",
)
```

### Поля `M2MSettings`

| Поле                           | Тип   | По умолчанию       | Описание                                                                       |
| ------------------------------ | ----- | ------------------ | ------------------------------------------------------------------------------ |
| `authentik_url`                | `str` | `—` (обязательный) | Базовый URL сервиса авторизации.                                               |
| `client_id`                    | `str` | `—` (обязательный) | OAuth Client ID сервиса.                                                       |
| `application_slug`             | `str` | `—` (обязательный) | Slug приложения в Authentik.                                                   |
| `service_account_username`     | `str` | `—` (обязательный) | Имя service account, от имени которого выполняется авторизация.                |
| `service_account_app_password` | `str` | `—` (обязательный) | App password service account. Используется для machine-to-machine авторизации. |
| `scope`                        | `str` | `""`               | Запрашиваемый OAuth scope.                                                     |

`service_account_app_password` является чувствительным значением и не должен храниться непосредственно в исходном коде.

---

## 7.4. Переменные окружения

Поскольку настройки SDK основаны на `pydantic-settings`, значения полей можно задавать через переменные окружения или `.env`.

Например:

```env
AUTHENTIK_URL=https://auth.example.com
CLIENT_ID=...
CLIENT_SECRET=...
APPLICATION_SLUG=my-app
```

### `_env_file`

Параметр `_env_file` позволяет явно указать файл, из которого будут загружаться настройки:

```python
from sesc_auth_sdk.settings import TokenValidationSettings

settings = TokenValidationSettings(
    _env_file=".env",
)
```

Это удобно, если конфигурация хранится в нескольких файлах:

```python
TokenValidationSettings(
    _env_file=".env.production",
)
```

При этом `_env_file` можно указывать непосредственно при создании настроек SDK или задать общий `env_file` в `model_config` собственного класса `Settings`:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )
```

### `_env_prefix`

Параметр `_env_prefix` позволяет добавить префикс к именам переменных окружения.

Например:

```python
TokenValidationSettings(
    _env_prefix="auth_",
)
```

В этом случае значения настроек будут искаться с соответствующим префиксом:

```env
AUTH_ALLOWED_ISSUERS=...
AUTH_JWKS_TTL=900
```

Это особенно удобно, если приложение использует несколько наборов настроек и необходимо избежать конфликтов между одинаковыми именами переменных.

Например:

```python
token_validation_settings = TokenValidationSettings(
    _env_file=".env",
    _env_prefix="AUTH_",
)
```

```env
AUTH_ALLOWED_ISSUERS=["https://auth.example.com/application/o/my-app/"]
AUTH_JWKS_TTL=900
```

> **Рекомендация:** для небольших приложений достаточно общего `.env` и `_env_file`. Если в приложении много компонентов с собственными настройками, рекомендуется использовать `_env_prefix`, чтобы явно разделить переменные окружения разных компонентов.

---

## 7.5. Краткая памятка по настройкам

| Задача                         | Класс                     |
| ------------------------------ | ------------------------- |
| Проверка JWT                   | `TokenValidationSettings` |
| OAuth 2.0 BFF                  | `AuthRouterSettings`      |
| Управление cookies и сессией   | `AuthRouterSettings`      |
| Service-to-service авторизация | `M2MSettings`             |

---

## 7.6. Рекомендуемая организация настроек

Рекомендуется хранить настройки SDK вместе с остальными настройками приложения в едином классе `Settings`.

Например:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

from sesc_auth_sdk.settings import TokenValidationSettings


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    authentik_url: str = "http://localhost:9000"
    user_service_url: str = "http://localhost:8000"

    token_validation_settings: TokenValidationSettings = TokenValidationSettings(
        _env_file=".env",
    )


settings = Settings()
```

После этого настройки SDK можно использовать из общего объекта `settings`:

```python
from sesc_auth_sdk.dependencies import (
    LyceumAuth,
    create_jwks_manager_dependency,
)
from sesc_auth_sdk.services.jwks_manager import JWKSManager

from app.settings import settings


jwks_manager = JWKSManager(
    settings.token_validation_settings,
)


class Auth(LyceumAuth):
    get_jwks_manager = create_jwks_manager_dependency(
        jwks_manager,
    )

    user_service_url = settings.user_service_url
```

Такой подход позволяет:

* централизовать конфигурацию приложения;
* разделить настройки по окружениям;
* использовать типизацию и валидацию `pydantic-settings`;
* не хранить секреты непосредственно в исходном коде;
* передавать готовую конфигурацию в компоненты SDK.

> **Рекомендация:** не создавайте отдельные глобальные `BaseSettings` для каждой части приложения. Предпочтительнее иметь один объект `Settings`, который содержит настройки приложения и необходимые настройки `sesc_auth_sdk`.

---

# 8. Краткая памятка

> **`LyceumAuth` — только базовый класс. Использовать его напрямую нельзя.**

Сначала создайте собственную зависимость:

```python
class Auth(LyceumAuth):
    get_jwks_manager = create_jwks_manager_dependency(
        jwks_manager
    )
```

Затем используйте её:

| Задача                                 | Использование                                   |
| -------------------------------------- |-------------------------------------------------|
| Проверить авторизацию                  | `Auth()`                                        |
| Проверить scopes                       | `Auth(required_scopes=[...])`                   |
| Получить access token                  | `Auth(...).return_token`                        |
| Получить пользователя                  | `Auth(...).return_user`                         |
| Проверить роли и получить пользователя | `Auth(...).restrict_roles_and_return_user(...)` |
| Подключить OAuth 2.0 BFF               | `create_auth_router(...)`                       |

### Коды ответов

| Код                | Причина                                         |
| ------------------ | ----------------------------------------------- |
| `401 Unauthorized` | Пользователь не авторизован или токен невалиден |
| `403 Forbidden`    | Токен валиден, но недостаточно прав/scopes      |

---

## Полный минимальный пример

### `auth.py`

```python
from sesc_auth_sdk.dependencies import (
    LyceumAuth,
    create_jwks_manager_dependency,
)
from sesc_auth_sdk.services.jwks_manager import JWKSManager
from sesc_auth_sdk.settings import TokenValidationSettings


jwks_manager = JWKSManager(
    TokenValidationSettings(...)
)


class Auth(LyceumAuth):
    get_jwks_manager = create_jwks_manager_dependency(
        jwks_manager
    )
```

### `main.py`

```python
from fastapi import Depends, FastAPI

from sesc_auth_sdk.schemas.token import AccessTokenPayload

from app.auth import Auth


app = FastAPI()


@app.get("/")
def index(
    payload: AccessTokenPayload = Depends(Auth()),
):
    return {
        "subject": payload.sub,
    }
```

Главное правило интеграции:

```text
LyceumAuth
    │
    │ наследование
    ▼
  Auth
    │
    │ Depends(...)
    ▼
FastAPI endpoint
```

`LyceumAuth` отвечает за базовую реализацию авторизации, а `Auth` — за конфигурацию этой реализации для конкретного приложения.
