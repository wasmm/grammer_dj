############################################################################
#Небольшая документация
# - для начала работы вызываем init_grammer(id) где id - ид пользователя в базе
# - get_follow(api, 'following', my_id, rank_tok) - дает массив
#     подписчиков или подписок, в зависимости от
#     параметров(followers или following)
# - resort_users(api, pages) - производит чистку в подписках и подписчиках
#     удаляет невзаинмные подписки и подписывается на тех,
#     кто подписан на меня, если я не подписан на страницу
########################

#мас фолловинг
#нам нужно собирать пользователей в таблицу при помощи
# - поиск по месту
# - поиск по тегам
# - подписчики конкурентов
#
#
###
###
#невзаимные подписки
#нам нужно собрать список из подписчиков и подписок
#затем по почереди сверять статус дружбы
#я подписан и на меня подпиан - ок
#я подписан, на меня не подписан - отписка
#я не подписан, на меня подписан - подписка
###
from .models import Conn_inst_acc

from random import randint
import time

from .instaconf import *
import psycopg2
import json
import codecs
import datetime
import os.path
import logging
import argparse
import geocoder
try:
    from instagram_private_api import (
        Client, ClientCompatPatch, ClientError, ClientLoginError,
        ClientCookieExpiredError, ClientLoginRequiredError,
        __version__ as client_version)
except ImportError:
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from instagram_private_api import (
        Client, ClientCompatPatch, ClientError, ClientLoginError,
        ClientCookieExpiredError, ClientLoginRequiredError,
        __version__ as client_version)


class Grammer:
    def to_json(self, python_object):
        if isinstance(python_object, bytes):
            return {'__class__': 'bytes',
                    '__value__': codecs.encode(python_object, 'base64').decode()}
        raise TypeError(repr(python_object) + ' is not JSON serializable')

    def from_json(self, json_object):
        if '__class__' in json_object and json_object['__class__'] == 'bytes':
            return codecs.decode(json_object['__value__'].encode(), 'base64')
        return json_object

    def onlogin_callback(self, api, new_settings_file):
        cache_settings = api.settings
        with open(new_settings_file, 'w') as outfile:
            json.dump(cache_settings, outfile, default=self.to_json)
            print('SAVED: {0!s}'.format(new_settings_file))

    def get_auth_data(self):
        inst_login = Conn_inst_acc.objects.get(pk = self.id_user)
        if inst_login == None:
            return False
        else:
            return ({'login' : inst_login.login, 'passwd' : inst_login.passwd, 'cookie': inst_login.login +'.json'})


    #ф-ция преобразует массив, отдаваемый инстаграмом в массив, нужного мне формата
    #в ф-цию передается массив людей и тип(follower или following)
    def little_converter(self, mas, type_follow):
        elements = []
        for element in mas['users']:
            pk = element['pk']
            username = element['username']
            full_name = element['full_name']
            link_avatar = element['profile_pic_url']
            is_private = element['is_private']
            elements.append({'pk': pk,
                             'username' : username,
                             'full_name' : full_name,
                             'link_avatar': link_avatar,
                             'type_follow' : type_follow,
                             'is_private' : is_private})
        return elements
    #ф-ция для возврата полного списка подписчиков
    def get_followers(self, api, id, rank_token):
        users = []
        followers = api.user_followers(id, rank_token)
        users.extend(self.little_converter(followers, 'follower'))
        mid = followers['next_max_id']
        while True:
            followers_pagin = api.user_followers(id, rank_token, max_id = mid)
            users.extend(self.little_converter(followers_pagin, 'follower'))
            mid = followers_pagin['next_max_id']
            tl = randint(11, 24)
            time.sleep(tl)
            if mid == None:
                break
        return users

    #ф-ция для возврата полного списка подписок
    def get_following(self, api, id, rank_token):
        users = []
        following = api.user_following(id, rank_token)
        users.extend(self.little_converter(following, 'following'))
        return users


    def convert(self, mas, type_follow):
        elements = []
        for post in mas:
            qw = any(post['user']['username'] == x['username'] for x in elements)
            if qw == False:
                elements.append({'pk': post['user']['pk'],
                                 'username' : post['user']['username'],
                                 'full_name' : post['user']['full_name'],
                                 'link_avatar': post['user']['profile_pic_url'],
                                 'type_follow' : type_follow,
                                 'is_private' : post['user']['is_private']})
        return elements



    def get_users_by_geo(self, location, api):
        #получаю координаты места
        g = geocoder.yandex(location)
        #получаю список мест, связанных с нужным мне местом
        data = api.location_search(g.json['lat'], g.json['lng'], query=None)
        acc_by_geo = []
        #идем в цикле по каждому месту
        for mesto in data['venues']:
            #идентификатор места
            id_point = mesto['external_id']
            #новостная лента
            fl = api.feed_location(id_point)
            #если в массиве данных по месту есть посты то идем их собирать
            try:
                acc_by_geo.extend(self.convert(fl['ranked_items'], 'following'))
                    #посты выдаются массивами по N штук
                    #потому мы берем next_max_id чтобы получить следующий набор
                    #так продолжаем в цикле пока не соберем все посты в этом месте
                mid = fl['next_max_id']
                while mid:
                    try:
                        mfl = api.feed_location(id_point, max_id = mid)
                        mid = mfl['next_max_id']
                        acc_by_geo.extend(self.convert(mfl['items'], 'following'))
                        tt = randint(6, 13)
                        time.sleep(tt)
                    except KeyError as e:
                        # return 'Error in %s' % (e)
                        break
            except KeyError as e:
                continue
            # tl = randint(3, 6)
            # time.sleep(tl)
        return acc_by_geo


    def get_users_by_tag(self, tag, rank_tok, api):
        acc_by_tag = []
        ft = api.feed_tag(tag, rank_tok)
        acc_by_tag.extend(self.convert(ft['ranked_items'], 'following'))
        acc_by_tag.extend(self.convert(ft['items'], 'following'))
        mid = ft['next_max_id']
        i = 0
        while mid:
            try:
                mft = api.feed_tag(tag, rank_tok, max_id = mid)
                mid = mft['next_max_id']
                acc_by_tag.extend(self.convert(mft['items'], 'following'))
                i += 1
                tt = randint(5, 11)
                time.sleep(tt)
            except KeyError:
                break
            if i == 40:
                break
            # tl = randint(3, 6)
            # time.sleep(tl)
        return acc_by_tag





























    def resort_users(self, api, pages):
        s_podpiska = 1 #счетчик подписок
        s_otpiska = 1 #счетчик отписок
        for page in pages:
            pk = page['pk']
            username = page['username']
            data_follow = api.friendships_show(pk)
            if data_follow['following'] == True and data_follow['followed_by'] == True:
                #пропускаем пользователя
                t1 = 1
                t2 = 2
            else:
                if data_follow['following'] == True and data_follow['followed_by'] == False:
                    #отписка от пользователя
                    try:
                        api.friendships_destroy(pk)#потом включить
                        s_otpiska += 1
                    except ClientError as e:
                        #print('Лимит подписок исчерпан')
                        return False
                elif data_follow['following'] == False and data_follow['followed_by'] == True:
                    #подписка на пользователя
                    try:
                        api.friendships_create(pk)#потом включить
                        s_podpiska += 1
                    except ClientError as e:
                        #print('Лимит отписок исчерпан')
                        return False
                t1 = config.START_SLEEP_TIME_TO_FOLLOW
                t2 = config.FINISH_SLEEP_TIME_TO_FOLLOW

            t = randint(t1, t2)
            time.sleep(t)
        return True

    def init_grammer(self, iduser):
        self.id_user = iduser

        self.datauser = self.get_auth_data()

        instalogin = self.datauser['login']
        instapwd = self.datauser['passwd']
        instacookie = self.datauser['cookie']

        device_id = None

        settings_file = instacookie
        try:
            if not os.path.isfile(settings_file):
                # settings file does not exist
                #если файл куки не найден то он создается
                #print('Невозможно найти файл: {0!s}'.format(settings_file))
                # login new
                api = Client(
                    instalogin, instapwd,
                    on_login=lambda x: self.onlogin_callback(x, instacookie))
                return api
            else:
                #если куки найдены то они используются
                with open(settings_file) as file_data:
                    cached_settings = json.load(file_data, object_hook = self.from_json)
                #print('Повторное использование настроек: {0!s}'.format(settings_file))
                device_id = cached_settings.get('device_id')
                # reuse auth settings
                api = Client(
                    instalogin, instapwd,
                    settings=cached_settings)
                return api
        except (ClientCookieExpiredError, ClientLoginRequiredError) as e:
            print('ClientCookieExpiredError/ClientLoginRequiredError: {0!s}'.format(e))
                #если куки просрочены или нужна авторизация то
                #происходит перезапись куков и авторизация

                # Login expired
                # Do relogin but use default ua, keys and such
            api = Client(
                instalogin, instapwd,
                device_id=device_id,
                on_login=lambda x: self.onlogin_callback(x, instacookie))

            return api

        except ClientLoginError as e:
            print('ClientLoginError {0!s}'.format(e))
            exit(9)
        except ClientError as e:
            print('ClientError {0!s} (Code: {1:d}, Response: {2!s})'.format(e.msg, e.code, e.error_response))
            exit(9)
        except Exception as e:
            print('Unexpected Exception: {0!s}'.format(e))
            exit(99)
