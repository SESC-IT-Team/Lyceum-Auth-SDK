# Lyceum Auth SDK
Пакет, упрощающий разработчикам бэкенда в **СУНЦ УрФУ** взаимодействие с сервисом авторизации.
## 1. Интеграция в проект
  - ### Установка пакета в проект  
    Сначала в ```pyproject.toml``` добавить:
    ```toml
    [tool.uv.workspace]
    members = ["packages/other-package"]
  
    [tool.uv.sources]
    sesc-auth-sdk = { git = "https://github.com/SESC-IT-Team/Lyceum-Auth-SDK.git" }
    ```
    Теперь пакет можно добавить в ```uv``` как обычный пакет с ```PyPI``` или другого источника, просто написав команду в консоль:  
    ```bash
    uv add sesc-auth-sdk
    ```
  - ### Конфигурация ```.env.auth```
    В вашем проекте должен быть ```.env``` файл с переменными, описанными в ```.env.example```  
    _Примечание: в ```.env``` файле могут быть и другие переменные нужные в Вашем проекте._
## 2. Использование
  Пусть у вас есть эндпоинт ```/``` и вы хотите, чтобы он был доступен только авторизованным пользователям, то делайте так:
  ```python
from fastapi import FastAPI, Depends
from sesc_auth_sdk.dependencies import LyceumAuth
from sesc_auth_sdk.schemas.token import AccessTokenPayload
  
app = FastAPI()

@app.get("/")
def index(payload: AccessTokenPayload = Depends(LyceumAuth())):
    ...
  ```
  Если пользователь неавторизован или если токен невалиден, сервис ответит с кодом ```401 Unauthorized```.  
  Если вы хотите допустить до эндпоинта только токены, имеющие определённые ```scopes```, то делайте так:

  ```python
from fastapi import FastAPI, Depends
from sesc_auth_sdk.dependencies import LyceumAuth
from sesc_auth_sdk.schemas.token import AccessTokenPayload
from sesc_auth_sdk.enums.scope import Scope

app = FastAPI()


@app.get("/")
def index(payload: AccessTokenPayload = Depends(LyceumAuth(required_scopes=[Scope.profile]))):
    ...
  ```
  Теперь, если в токене недостаёт каких-то требуемых scope'ов, то сервер ответит с кодом ```403 Forbidden```.  
  Если вашему приложению нужна авторизацию пользователя (это не просто ```API``` нужное для других приложений, а полноценное приложение), 
  вы должны использовать встроенный в ```SDK``` ```auth_router``` описанный в ```sesc_auth_sdk.auth_rouer```. Не забудьте добавить ```.env.auth``` переменные, требуемые для его работы.