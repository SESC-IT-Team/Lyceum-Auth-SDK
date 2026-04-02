# Lyceum Auth SDK
Пакет, упрощающий разработчикам бэкенда в **СУНЦ УрФУ** взаимодействие с сервисом авторизации.
## 1. Интеграция в проект
  - ### Установка пакета в проект  
    Сначала в pyproject.toml добавить:
    ```toml
    [tool.uv.workspace]
    members = ["packages/other-package"]
  
    [tool.uv.sources]
    sesc-auth-sdk = { git = "https://github.com/SESC-IT-Team/Lyceum-Auth-SDK.git" }
    ```
    Теперь пакет можно добавить в uv как обычный пакет с PyPI или другого источника, просто написав команду в консоль:  
    ```bash
    uv add sesc-auth-sdk
    ```
  - ### Конфигурация .env
    В вашем проекте должен быть .env файл со следующими переменными:
    ```dotenv
    AUTH_BASE_URL=<URL сервиса авторизации>
    ```
    .env.example — пример .env файла.  
      
    _Примечание: в .env файле могут быть и другие переменные нужные в Вашем проекте._
## 2. Использование
  Пусть у вас есть эндпоинт / и вы хотите, чтобы он был доступен только авторизованным пользователям, то делайте так:
  ```python
from fastapi import FastAPI, Depends
from sesc_auth_sdk.dependencies import LyceumAuth
from sesc_auth_sdk.schemas.jwt import JwtPayload
  
app = FastAPI()

@app.get("/")
def index(payload: JwtPayload = Depends(LyceumAuth())):
    ...
  ```
  Если пользователь неавторизован или если токен невалиден, сервис ответит с кодом 401.  
  Если вы хотите допустить до эндпоинта только определенные роли, то делайте так:
  ```python
from fastapi import FastAPI, Depends
from sesc_auth_sdk.dependencies import LyceumAuth
from sesc_auth_sdk.schemas.jwt import JwtPayload
from sesc_auth_sdk.enums.role import Role
   
app = FastAPI()
  
@app.get("/")
def index(payload: JwtPayload = Depends(LyceumAuth(allowed_roles=[Role.admin]))):
    ...
  ```
Теперь если у пользователя неподходящая роль, то сервер ответит с кодом 403.  
В обеих реализациях выше в payload будет лежать только информация, которая хранится в JWT.  
Если вы хотите при этом получить полную информацию о пользователе, то делайте так:
  ```python
from fastapi import FastAPI, Depends
from sesc_auth_sdk.dependencies import LyceumAuth
from sesc_auth_sdk.schemas.user import UserSchema
from sesc_auth_sdk.enums.role import Role
   
app = FastAPI()
  
@app.get("/")
def index(user: UserSchema = Depends(LyceumAuth(allowed_roles=[Role.admin]).return_user)):
    ...
  ```
  Разница в том, что в первом и втором случаях токен валидируется локально (в большинстве случаев без запросов к бэкенду авторизации, запросы к бэку придётся делать только для обновления ключей), в то же время в третьем случае, когда возвращается пользователь, точно нужно будет запросить у бэка авторизации данные этого пользователя.
