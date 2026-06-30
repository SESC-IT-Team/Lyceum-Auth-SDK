from enum import Enum


class Scope(Enum, str):
    profile = 'profile'
    user = 'user'
    openid = 'openid'
    email = 'email'
    offline_access = 'offline_access'
    spravki_orders_create = 'spravki:orders:create'
    spravki_orders_get = 'spravki:orders:get'
    spravki_orders_get_my = 'spravki:orders:get_my'
