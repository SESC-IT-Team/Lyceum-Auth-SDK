from enum import Enum


class Scope(str, Enum):
    profile = 'profile'
    openid = 'openid'
    email = 'email'
    offline_access = 'offline_access'
    spravki_orders_create = 'spravki:orders:create'
    spravki_orders_get = 'spravki:orders:get'
    spravki_orders_get_my = 'spravki:orders:get_my'
    auth_users_create = 'auth:users:create'
    auth_users_read = 'auth:users:read'
    auth_users_update = 'auth:users:update'
    auth_users_delete = 'auth:users:delete'

    technical_support_orders_create = 'technical_support:orders:create'
    technical_support_orders_set_department = 'technical_support:orders:set_department'
    technical_support_orders_get = 'technical_support:orders:get'
    technical_support_orders_set_status = 'technical_support:orders:set_status'
    technical_support_orders_set_worker = 'technical_support:orders:set_worker'
