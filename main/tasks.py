import logging
from random import randint
import random
import time as time_s
from datetime import datetime, date, time, timedelta
from django.utils.timezone import make_aware

from django.urls import reverse
from grammer.celery import app
from main.utils import Grammer
from main.utils import ClientError


from main.models import Conn_acc_details
from main.models import Conn_inst_acc
from main.models import Inst_accounts
from main.models import Conn_inst_followers
from main.models import Acts_like
from main.models import Acts_follow
from main.models import Stat
from main.models import Config_instagram_work
from main.models import Acc_in_act





@app.task
def get_full_data(login):
    data_user = Conn_inst_acc.objects.get(login = login)
    a = Grammer()
    api = a.init_grammer(data_user.pk)
    my_id = api.authenticated_user_id
    info = api.user_info(my_id)
    details, created = Conn_acc_details.objects.update_or_create(id_login = data_user,
                        defaults={'full_name' : info['user']['full_name'],
                                  'avatar_link' : info['user']['profile_pic_url']})




@app.task
def add_follow(login):
    data_for_followers = Conn_inst_acc.objects.get(login = login)
    today = datetime.now()
    units = []

    a = Grammer()
    api = a.init_grammer(data_for_followers.id)
    my_id = api.authenticated_user_id
    rank_tok = api.generate_uuid()
    units.extend(a.get_followers(api, my_id, rank_tok))
    units.extend(a.get_following(api, my_id, rank_tok))
    #проходим по каждому подписчику
    for unit in units:
        insta_user, inst_acc_created = Inst_accounts.objects.get_or_create(login_inst = unit['username'],
                              defaults={'id_inst' : unit['pk'],
                              'full_name_inst' : unit['full_name'],
                              'avatar_link_inst' : unit['link_avatar']})
        data_follow, follow_created = Conn_inst_followers.objects.update_or_create(id_conn = data_for_followers,
                                                                                   id_inst = insta_user,
                                                                                   type_follow = unit['type_follow'],
                                                                                   defaults={'last_update' : make_aware(today)})
        #если создан новый фолловер
        if follow_created == True:
            print('Новый пользователь {0} ({1}) last_update({2}) - ему поставим галку на лайк'.format(data_follow.id_inst.login_inst, data_follow.type_follow, data_follow.last_update))
            data_follow.like_it = True
            data_follow.save()
        #если фолловер уже есть в базе
        else:
            print('Пользователь существует - его будем проверять в зависимости от даты последнего лайка')
            print('  -Обновим дату последнего обновления инфо на текущую дату и время ({0})'.format(make_aware(today)))
            print()
            data_follow.last_update = make_aware(today)
            data_follow.save()

            like_last_date_day = datetime.date(data_follow.like_last_date).day
            like_last_date_month = datetime.date(data_follow.like_last_date).month
            like_last_date_year = datetime.date(data_follow.like_last_date).year
            delta_date = today.day - like_last_date_day

            if delta_date > 2:
                print('  -Прошло более двух дней с момента последнего лайка, будем ставить лайк еще раз')
                data_follow.like_it = True
                data_follow.save()

        last_update_day = datetime.date(data_follow.last_update).day
        last_update_month = datetime.date(data_follow.last_update).month
        last_update_year = datetime.date(data_follow.last_update).year

        if (last_update_year == today.year and last_update_month == today.month and last_update_day == today.day):
            print('Пользоватеь обновлен , что тут скажешь')
        else:
            # print('Пользователь {0} ушел от нас? надо проверить'.format(data_follow.id_inst.login_inst))
            data_follow.type_follow = 'unfollow'
            data_follow.save()

    data_for_followers.first_load = False
    data_for_followers.save()



################    обновленные ф-ции    #####################################

#лайкинг

@app.task
def scaner_acts_like():
    users_for_like = Conn_inst_acc.objects.filter(mass_likes = True)
    acts_for_work = Acts_like.objects.filter(id_conn__in = users_for_like, status__in = ['added', 'processing'], locked = False).order_by('-date_stop')
    if acts_for_work.count() > 0:
        p = 0
        for act in acts_for_work:
            #проверяем, нет ли в данный момент на выполнении у пользователя
            #задания на масс фолловинг, одновременно может быть запущено только
            #одно задание, масс фолловинг или масс лайкинг во избежание бана
            follow_act = Acts_follow.objects.filter(id_conn = act.id_conn, locked = True)
            if follow_act.count() == 0:
                print('запускаем процесс лайка на пользовател {0} (ID задания {1})'.format(act.id_conn.login, act.pk))
                like.delay(act.pk, act.id_conn.login)
                p += 1
                tl = randint(2, 5)
                time_s.sleep(tl)
        return 'Запущено %s заданий на лайк' % (p)
    else:
        return 'mass_likes Нет заданий на обработку'

@app.task
def like(id, login):
    print('Ставим лайк по заданию c ИД {0}, Логин: {1}'.format(id, login))
    try:
        act = Acts_like.objects.get(pk = id)
        today = make_aware(datetime.now())
        act.locked = True
        act.status = 'processing'
        act.date_start = today
        act.save()
        print('задание есть')
        config = Config_instagram_work.objects.get(pk = act.id_conn.config_id)
        data_stat, is_created = Stat.objects.get_or_create(id_conn = act.id_conn,
                                                           date_stat__day = today.day,
                                                           date_stat__month = today.month,
                                                           date_stat__year = today.year,
                                                           defaults={'date_stat' : today})
        followers = Conn_inst_followers.objects.filter(id_conn = act.id_conn, like_it = True).order_by('-like_last_date')
        follower = followers.first()
        print('Найдено {0} аккаунтов'.format(followers.count()))

        pk = follower.id_inst.id_inst
        print('Будем лайкать пользователя {0}(ID: {1})'.format(follower, pk))

        a = Grammer()
        api = a.init_grammer(act.id_conn.pk)
        print('ID instagram пользователя: {0}'.format(pk))
        try:
            feed_user = api.user_feed(pk)
            i = 0
            while True:
                try:
                    feed = random.choice(feed_user['items'])
                except IndexError:
                    follower.like_it = False
                    follower.save()
                    mes = 'Лайк не поставлен'
                    break
                if feed['has_liked'] == False:
                    print('Лайкнем этот пост')
                    id_media = feed['id']
                    like_it = api.post_like(id_media)
                    if like_it['status'] == 'ok':
                        mes = 'Лайк поставлен'
                        #после того как лайк поставлен убираем с пользователя
                        #признак надобности лайка (Like_it)
                        date_like = make_aware(datetime.now())
                        follower.like_it = False
                        follower.like_last_date = date_like
                        follower.save()
                        print('Отметка с пользователя о лайке снята')
                        #увеличиваем параметр количества лайков в
                        #статистике для пользователя
                        count_likes = data_stat.count_like + 1
                        data_stat.count_like = count_likes
                        data_stat.save()
                        print('данные статистики обновлены')
                        #лайк поставлен - выходим их цикла
                        break
                    else:
                        #если лайк лайк не поставлен то запускаем следующую
                        #итерацию, чтобы поставить лайк
                        print('лайк не поставлен - выбираем другой пост')
                        i += 1
                        print('Итерация {0}'.format(i))
                        if i == 4:
                            mes = 'Все попытки исчерпаны, пропускаем'
                            follower.like_it = False
                            follower.save()
                            break
                        tl = randint(config.START_SLEEP_TIME_LIKE, config.FINISH_SLEEP_TIME_LIKE)
                        print('Ждем {0} сек'.format(tl))
                        time_s.sleep(tl)
                        continue
                else:
                    #если пост был пролайкан то запускаем следующую
                    #итерацию, чтобы поставить лайк
                    print('Этот пост пролайкан - выбираем другой пост({0})'.format(feed['has_liked']))
                    i += 1
                    print('Итерация {0}'.format(i))
                    if i == 4:
                        mes = 'Все попытки исчерпаны, пропускаем'
                        follower.like_it = False
                        follower.save()
                        break
                    tl = randint(config.START_SLEEP_TIME_LIKE, config.FINISH_SLEEP_TIME_LIKE)
                    print('Ждем {0} сек'.format(tl))
                    time_s.sleep(tl)
                    continue

            print('Завершение ф-ции лайка')
            date_stop = make_aware(datetime.now())
            act.locked = False

            is_liked = Conn_inst_followers.objects.filter(id_conn = act.id_conn, like_it = True)
            if is_liked.count() == 0:
                act.status = 'processed'
            act.date_stop = date_stop
            act.save()
            tl = randint(2, 9)
            time_s.sleep(tl)
            return '%s: %s' % (login, mes)

        except ClientError:
            follower.like_it = False
            follower.save()
            act.locked = False
            act.save()
            return 'Лайк не поставлен: ошибка'
        except ConnectionResetError:
            date_stop = make_aware(datetime.now())
            act.status = 'processed'
            act.date_stop = date_stop
            act.locked = False
            act.save()
            return 'Лайк не поставлен: Соединение закрыто, задание зевершено'

    except Acts_like.DoesNotExist:
        return 'Задания с ИД %s нет в БД' % (id)






@app.task
def scaner_acts_follow(type_follow):
    if type_follow == 'follow_acc':
        users_for_follow = Conn_inst_acc.objects.filter(mass_follow_acc = True)
        type_act = 'follow_acc_acc'

    elif type_follow == 'follow_geo':
        users_for_follow = Conn_inst_acc.objects.filter(mass_follow_geo = True)
        type_act = 'follow_acc_geo'

    elif type_follow == 'follow_tag':
        users_for_follow = Conn_inst_acc.objects.filter(mass_follow_tag = True)
        type_act = 'follow_acc_tag'
    else:
        return 'Ошибочное значение при запуске задания на добавление потенциальных фолловеров'


    # users_for_follow = Conn_inst_acc.objects.filter(mass_follow_acc = True)
    acts_for_work = Acts_follow.objects.filter(id_conn__in = users_for_follow, status = 'added', locked = False, act = type_act).order_by('-date_add')

    p = 0
    if acts_for_work.count() > 0:

        for act in acts_for_work:
            #проверяем, нет ли в данный момент на выполнении у пользователя
            #задания на масс фолловинг, одновременно может быть запущено только
            #одно задание, масс фолловинг или масс лайкинг во избежание бана
            # follow_act = Acts_like.objects.filter(id_conn = act.id_conn, locked = True)
            # if follow_act.count() == 0:
            print('запускаем процесс фолловинга на пользовател {0} (ID задания {1})'.format(act.id_conn.login, act.pk))

            if type_follow == 'follow_acc':
                print('Запуск задания фолловинга по аккаунту %s' % (act.pk))
                mas_add_following.delay(act.pk, type_follow)
            elif type_follow == 'follow_geo':
                print('Запуск задания фолловинга по гео %s' % (act.pk))
                mas_add_following_tag_or_geo.delay(act.pk, type_follow)
            elif type_follow == 'follow_tag':
                print('Запуск задания фолловинга по тегу %s' % (act.pk))
                mas_add_following_tag_or_geo.delay(act.pk, type_follow)

                # mas_add_following.delay(act.pk)
            p += 1
            tl = randint(2, 5)
            time_s.sleep(tl)
            # else:
            #     return 'Присутствуют задания like на выполнении'

        return 'Запущено %s заданий %s на добавление аккаунтов' % (p, type_follow)
    else:
        return '%s Нет заданий на добавление аккаунтов' % (type_follow)



@app.task
def mas_add_following(id, type_follow):
    acts = Acts_follow.objects.get(pk = id)
    acts.locked = True
    acts.status = 'processing'
    nowdate = make_aware(datetime.now())
    acts.date_start = nowdate
    acts.save()

    acc_login = acts.id_conn.pk
    target = acts.target
    print('Целевой аккаунт {0}'.format(target))

    a = Grammer()
    api = a.init_grammer(acc_login)

    #проверяем наличие целевого аккаунта в базе - если есть то работаем с ним,
    #если нет то подписываемся на аккаунт
    try:
        inst_acc = Inst_accounts.objects.get(login_inst = target)
        print('Пользователь найден в общей базе')
        pk = inst_acc.id_inst
        try:
            #получаем данные о подписке(подписчике)

            is_follow = Conn_inst_followers.objects.filter(id_conn = acts.id_conn, id_inst = inst_acc).first()
            print('Целевой пользователь связан с аккаунтом')
        except Conn_inst_followers.DoesNotExist:
            print('Целевой пользователь не связан с аккаунтом')

            data_follow = api.friendships_show(pk)
            #если на пользователя нет подписки
            if data_follow['following'] == False:
                print('Нет подписки на целевой акк - выполняем подписку')
                try:
                    friend = api.friendships_create(pk)
                    print('Подписка на целевой акк выполнена')
                except ClientError:
                    print('что то пошло не так')
                    return 'ClientError: Подписка не выполнена'

            new_follow = Conn_inst_followers(id_conn = acts.id_conn, id_inst = inst_acc, type_follow = 'following', last_update = nowdate )
            new_follow.save()
            is_follow = Conn_inst_followers.objects.get(id_conn = acts.id_conn, id_inst = inst_acc)
            print('Пользователь добавлен в бд')

        print('ИД цели: {0}'.format(is_follow.id_inst.id_inst))
        rank_tok = api.generate_uuid()
        target_followers = a.get_followers(api, is_follow.id_inst.id_inst, rank_tok)
        i = 0
        for follower in target_followers:
            potential_follower, is_created = Inst_accounts.objects.get_or_create(login_inst = follower['username'],
                                                                                 defaults={'id_inst' : follower['pk'],
                                                                                           'full_name_inst' : follower['full_name'],
                                                                                           'avatar_link_inst' : follower['link_avatar']})
            add_pot_follower, is_create_flw = Acc_in_act.objects.update_or_create(target = acts, id_inst = potential_follower)
        acts.locked = False
        acts.status = 'follows'
        acts.save()
        return 'Задание выполнено'

    except Inst_accounts.DoesNotExist:
        print('аккаунта в базе нет - следует подписаться на целевой аккаунт и обновить список подписок и подписчиков')
        return 'аккаунта в базе нет - следует подписаться на целевой аккаунт и обновить список подписок и подписчиков'

@app.task
def mas_add_following_tag_or_geo(id, type_follow):
    print('Запуск задания с ИД {0}'.format(id))

    acts = Acts_follow.objects.get(pk = id)
    acts.locked = True
    acts.status = 'processing'
    nowdate = make_aware(datetime.now())
    acts.date_start = nowdate
    acts.save()

    acc_login = acts.id_conn.pk
    target = acts.target
    print('Целевая локация {0}'.format(target))

    a = Grammer()
    api = a.init_grammer(acc_login)

    if type_follow == 'follow_geo':
        followers = a.get_users_by_geo(target, api)
    elif type_follow == 'follow_tag':
        rank_tok = api.generate_uuid()
        followers = a.get_users_by_tag(target, rank_tok, api)

    print('найдено фолловеров по гео: {0}'.format(len(followers)))
    i = 0
    ii = 0
    for follower in followers:
        potential_follower, is_created = Inst_accounts.objects.get_or_create(login_inst = follower['username'],
                                                                             defaults={'id_inst' : follower['pk'],
                                                                                       'full_name_inst' : follower['full_name'],
                                                                                       'avatar_link_inst' : follower['link_avatar']})


        add_pot_follower, is_create_flw = Acc_in_act.objects.update_or_create(target = acts, id_inst = potential_follower)
        if is_create_flw == True:
            ii += 1
        i += 1

    acts.locked = False
    acts.status = 'follows'
    acts.save()
    print('Количество итераций {0}'.format(i))
    print('Количество созданных записей {0}'.format(ii))
    return 'Задание выполнено'

















@app.task
def scaner_acts_add_follow(type_follow):
    if type_follow == 'follow_acc':
        users_for_follow = Conn_inst_acc.objects.filter(mass_follow_acc = True)
        type_act = 'follow_acc_acc'
    elif type_follow == 'follow_geo':
        users_for_follow = Conn_inst_acc.objects.filter(mass_follow_geo = True)
        type_act = 'follow_acc_geo'
    elif type_follow == 'follow_tag':
        users_for_follow = Conn_inst_acc.objects.filter(mass_follow_tag = True)
        type_act = 'follow_acc_tag'

    # users_for_follow = Conn_inst_acc.objects.filter(mass_follow_acc = True)
    acts_for_work = Acts_follow.objects.filter(id_conn__in = users_for_follow, status = 'follows', locked = False, act = type_act).order_by('-date_add')
    if acts_for_work.count() > 0:
        p = 0
        for act in acts_for_work:
            #проверяем, нет ли в данный момент на выполнении у пользователя
            #задания на масс фолловинг, одновременно может быть запущено только
            #одно задание, масс фолловинг или масс лайкинг во избежание бана
            follow_act_f = Acts_follow.objects.filter(id_conn = act.id_conn, locked = True)
            follow_act_l = Acts_like.objects.filter(id_conn = act.id_conn, locked = True)
            if (follow_act_f.count() == 0 and follow_act_l.count() == 0):
                print('ТИП: {0}'.format(act.act))
                print('запускаем процесс фолловинга на пользовател {0} (ID задания {1})'.format(act.id_conn.login, act.pk))
                follow_it.delay(act.pk)
                p += 1
                tl = randint(2, 5)
                time_s.sleep(tl)
        return 'Запущено %s заданий %s на фолловинг добавленых аккаунтов' % (p, type_follow)
    else:
        return '%s Нет заданий на фолловинг добавленых аккаунтов' % (type_follow)



@app.task
def follow_it(id):
    # flw = Acts_follow.objects.filter(id_conn__in = users_for_follow, status = 'follows', locked = False).first()
    flw = Acts_follow.objects.get(pk = id)
    if flw != None:
        today = make_aware(datetime.now())
        flw.locked = True
        flw.date_start = today
        flw.save()
        print('задание есть')

        config = Config_instagram_work.objects.get(pk = flw.id_conn.config_id)
        data_stat, is_created = Stat.objects.get_or_create(id_conn = flw.id_conn,
                                                           date_stat__day = today.day,
                                                           date_stat__month = today.month,
                                                           date_stat__year = today.year,
                                                           defaults={'date_stat' : today})

        acc_id = flw.id_conn.pk
        a = Grammer()
        api = a.init_grammer(acc_id)
        sum_followers = 0
        mes = ''
        i = 0
        while True:
            potential_follower = Acc_in_act.objects.filter(target = flw).first()
            print('Потенциальный фолловер: {0}'.format(potential_follower.id_inst.login_inst))
            id_target_follower = potential_follower.id_inst.id_inst
            try:
                friend = api.friendships_create(id_target_follower)
                if friend['status'] == 'ok':
                    print('Фолловер добавлен')
                    sum_followers = data_stat.count_follow + 1
                    data_stat.count_follow = sum_followers
                    data_stat.save()
                    potential_follower.delete()

                    print('Запись удалена из Acc_in_act')
                    mes = 'Фолловинг совершен'
                    break
                else:
                    print('Что-то пошло не так, попробуем еще раз')
                    tl = randint(config.START_SLEEP_TIME_TO_FOLLOW, config.FINISH_SLEEP_TIME_TO_FOLLOW)
                    time_s.sleep(tl)
                    continue
            except ClientError:
                print('Аккаунт фолловера недоступен - пропускаем')
                potential_follower.delete()
                print('Запись удалена из Acc_in_act')
                i += 1
                if i == 3:
                    mes = 'задание не выполнено, 3 попытки на проведение истекли'
                    break
                tl = randint(config.START_SLEEP_TIME_TO_FOLLOW, config.FINISH_SLEEP_TIME_TO_FOLLOW)
                time_s.sleep(tl)
                continue
        print('Завершение ф-ции фолловинга')
        date_stop = make_aware(datetime.now())
        flw.locked = False
        cnt_potential_followers = Acc_in_act.objects.filter(target = flw)
        if cnt_potential_followers.count() == 0:
            flw.status = 'processed'
        flw.date_stop = date_stop
        flw.save()
        tl = randint(3, 8)
        time_s.sleep(tl)
        return mes
    else:
        return 'На обработку ничего нет'






































































            #
