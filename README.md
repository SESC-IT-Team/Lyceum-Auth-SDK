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
* [Конфигурация](#2-конфигурация)
* [Проверка авторизации](#3-проверка-авторизации)

  * [Создание зависимости](#31-создание-зависимости)
  * [Защита эндпоинта](#32-защита-эндпоинта)
  * [Проверка scopes](#33-проверка-scopes)
* [Получение access token](#4-получение-access-token)
* [Получение текущего пользователя](#5-получение-текущего-пользователя)
* [Ограничение доступа по ролям](#6-ограничение-доступа-по-ролям)
* [OAuth 2.0 BFF](#7-oauth-20-bff)
* [Пример структуры проекта](#8-пример-структуры-проекта)
* [Краткая памятка](#9-краткая-памятка)

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

# 2. Конфигурация

SDK использует переменные окружения для своей работы.

В проекте должен присутствовать `.env` с переменными, указанными в `.env.example` SDK.

При этом `.env` может содержать и другие переменные, необходимые вашему приложению.

Пример:

```text
.env
.env.example
```

> **Важно:** не добавляйте `.env` в репозиторий, если он содержит секреты или другие чувствительные данные.

---

# 3. Проверка авторизации

## Важно: `LyceumAuth` нельзя использовать напрямую

`LyceumAuth` является **базовым классом для создания зависимости авторизации**.

Использование:

```python
Depends(LyceumAuth())
```

**не допускается**.

Необходимо создать собственный класс-наследник `LyceumAuth`, настроить в нём `JWKSManager`, а затем использовать уже этот класс.

---

## 3.1. Создание зависимости

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
    _get_jwks_manager = create_jwks_manager_dependency(
        jwks_manager
    )

    # Необходимо только для зависимостей,
    # работающих с объектом пользователя.
    user_service_url = "<URL API пользователей>"
```

Именно класс `Auth` является зависимостью, которую следует использовать в приложении.

---

## 3.2. Защита эндпоинта

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

## 3.3. Проверка scopes

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

# 4. Получение access token

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

# 5. Получение текущего пользователя

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
    _get_jwks_manager = create_jwks_manager_dependency(
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

# 6. Ограничение доступа по ролям

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
    _get_jwks_manager = create_jwks_manager_dependency(
        jwks_manager
    )

    user_service_url = "<URL API пользователей>"
```

> **Важно:** каждый вызов зависимости выполняет запрос к API пользователей.

---

# 7. OAuth 2.0 BFF

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

app.include_router(auth_router)
```

После этого OAuth 2.0 endpoints будут доступны через подключённый router.

Необходимые для работы роутера настройки должны быть указаны в `.env` согласно `.env.example`.

---

# 8. Пример структуры проекта

Рекомендуемая структура:

```text
project/
├── app/
│   ├── __init__.py
│   ├── auth.py
│   └── main.py
│
├── .env
├── .env.example
├── .gitignore
├── pyproject.toml
└── uv.lock
```

### `app/auth.py`

В этом файле находится единственный класс авторизации приложения:

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
    _get_jwks_manager = create_jwks_manager_dependency(
        jwks_manager
    )

    user_service_url = "<URL API пользователей>"
```

### `app/main.py`

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

---

# 9. Краткая памятка

> **`LyceumAuth` — только базовый класс. Использовать его напрямую нельзя.**

Сначала создайте собственную зависимость:

```python
class Auth(LyceumAuth):
    _get_jwks_manager = create_jwks_manager_dependency(
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
    _get_jwks_manager = create_jwks_manager_dependency(
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
