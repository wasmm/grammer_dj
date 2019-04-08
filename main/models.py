from django.db import models
from django.shortcuts import reverse

import django.dispatch
add_users = django.dispatch.Signal(providing_args=["login"])
add_data = django.dispatch.Signal(providing_args=["login"])
add_mass_like = django.dispatch.Signal(providing_args=["id"])
close_mass_like = django.dispatch.Signal(providing_args=["id"])




class Config_instagram_work(models.Model):
    START_SLEEP_TIME_LIKE = models.IntegerField(default=20)#20
    #конечное исло сна в секундах между лайками
    FINISH_SLEEP_TIME_LIKE = models.IntegerField(default=35)#35
    #стартовое число сна в секундах между переходами по подписчикам
    START_SLEEP_TIME_FOLLOWER = models.IntegerField(default=5)#5
    #конечное число сна в секундах между переходами по подписчикам
    FINISH_SLEEP_TIME_FOLLOWER = models.IntegerField(default=12)#12
    #стартовое число постов в штуках для лайкинга подписчика
    START_COUNT_POSTS = models.IntegerField(default=4)#4
    #конечное число постов в штуках для лайкинга подписчиков
    FINISH_COUNT_POSTS = models.IntegerField(default=9)#9
    #ограничение инстаграма по количеству лайков в сутки
    MAX_LIKE_PER_DAY = models.IntegerField(default=1000)#1000
    #сколько должно пройти времени с момента последнего лайка в секундах,
    #сейчас выставлена 21 день (1814400 сек)
    TIME_LAST_ACTIVITY_LIKE = models.IntegerField(default=1814400)#1814400
    #начальное количество секунд ожидания между добавлениями в друзья
    START_SLEEP_TIME_TO_FOLLOW = models.IntegerField(default=30)#30
    #конечное количество секунд ожидания между добавлениями в друзья
    FINISH_SLEEP_TIME_TO_FOLLOW = models.IntegerField(default=40)#40
    #начальное количество секунд ожидания между удалениями из друзей
    START_SLEEP_TIME_TO_UNFOLLOW = models.IntegerField(default=15)#15
    #конечное количество секунд ожидания между удалениями из друзей
    FINISH_SLEEP_TIME_TO_UNFOLLOW = models.IntegerField(default=25)#25
    #максимальное коичество добавленых друзей в час
    MAX_FOLLOWING_USERS_PER_HOUR = models.IntegerField(default=200)#200
    #максимальное коичество добавленых друзей в сутки
    MAX_FOLLOWING_USERS_PER_DAY = models.IntegerField(default=1000)#1000
    #максимально количество отписок от взаимных подписок
    MAX_RELATIVE_UNFOLLOWING_USERS_PER_DAY = models.IntegerField(default=1000)#1000
    #максимальное количество отписок от невзаимных подписок
    MAX_UNRELATED_UNFOLLOWING_USERS_PER_DAY = models.IntegerField(default=1000)#1000



#подключенные на раскрутку аккаунты
class Conn_inst_acc(models.Model):
    login = models.CharField(max_length = 32, db_index = True, unique = True)
    passwd = models.CharField(max_length = 32)
    mass_likes = models.BooleanField(default = False)
    mass_follow_acc = models.BooleanField(default = False)
    mass_follow_geo = models.BooleanField(default = False)
    mass_follow_tag = models.BooleanField(default = False)
    mass_resort = models.BooleanField(default = False)
    first_load =  models.BooleanField(default = True)
    config = models.ForeignKey(Config_instagram_work, on_delete = models.CASCADE, default='')

    def __str__(self):
        return self.login

    def get_absolute_url(self):
        return reverse('main:inst_acc_info', args=[str(self.id)])

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)




        if self.first_load == True:
            print('Сигнал на добавление данных пользователя')
            add_data.send_robust(sender=self.__class__, login=self.login)

        if self.mass_likes == True:
            add_mass_like.send_robust(sender=self.__class__, id=self.pk)

        elif self.mass_likes == False:
            close_mass_like.send_robust(sender=self.__class__, id=self.pk)

        # if self.mass_follow == True:
        # if self.mass_resort == True:


#таблица информации об аккаунте
class Conn_acc_details(models.Model):
    id_login = models.ForeignKey(Conn_inst_acc, on_delete = models.CASCADE,)
    full_name  = models.CharField(max_length = 32, default='')
    avatar_link = models.CharField(max_length = 256, default='')
    date_add = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.id_login.login

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        print('Сигнал на добавление подписчиков и подписок')
        add_users.send_robust(sender=self.__class__, login=self.id_login.login)


#таблица инстаграм аккантов, которые в друзьях у тех, кто на раскрутке
class Inst_accounts(models.Model):
    login_inst = models.CharField(max_length = 32, db_index = True, unique = True)
    id_inst = models.CharField(max_length = 32, default='')
    full_name_inst = models.CharField(max_length = 32, default='')
    avatar_link_inst = models.CharField(max_length = 256, default='')

    def __str__(self):
        return self.login_inst

#таблица друзей и подписчиков привязанных акков
class Conn_inst_followers(models.Model):
    id_conn = models.ForeignKey(Conn_inst_acc, on_delete = models.CASCADE,)
    id_inst = models.ForeignKey(Inst_accounts, on_delete = models.CASCADE,)
    type_follow = models.CharField(max_length = 10)
    date_add = models.DateTimeField(auto_now_add=True)
    last_update  = models.DateTimeField(blank=True, null=True)
    like_it = models.BooleanField(default = False)
    like_last_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '%s' % (self.id_inst.login_inst)

#Действия с подключенными аккаунтами
#статусы записей
#added - добавлен
#processing - в работе
#processed - обработан
#типы действий
#like
class Acts_like(models.Model):
    id_conn = models.ForeignKey(Conn_inst_acc, on_delete = models.CASCADE,)
    act = models.CharField(max_length = 12)#like, follow, mass_resort
    status = models.CharField(max_length = 10, default = 'added')
    locked = models.BooleanField(default = False)
    date_add = models.DateTimeField(auto_now_add=True)
    date_start = models.DateTimeField(blank=True, null=True)
    date_stop = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return '%s: %s -- %s' % (self.id_conn.login, self.act, self.status)


#типы действий(act)
#follow_acc - в поле target указывается логин, у которого будут браться подписчики
#follow_geo - в поле target указывается местоположение
#follow_tag - в поле target указывается хештэг
class Acts_follow(models.Model):
    ACT_CHOICES = (
            ('follow_acc_acc', 'Целевой аккаунт'),
            ('follow_acc_geo', 'Целевая локация'),
            ('follow_acc_tag', 'Целевой тег')
    )
    id_conn = models.ForeignKey(Conn_inst_acc, on_delete = models.CASCADE,)
    act = models.CharField(max_length = 20, choices=ACT_CHOICES)
    status = models.CharField(max_length = 10, default = 'added')
    locked = models.BooleanField(default = False)
    target = models.CharField(max_length = 32, default = '')
    date_add = models.DateTimeField(auto_now_add=True)
    date_start = models.DateTimeField(blank=True, null=True)
    date_stop = models.DateTimeField(blank=True, null=True)

    # def add_act(self):
    # def get_absolute_url(self):
    #     return reverse('main:Acts_follow', args=[str(self.id)])

    def __str__(self):
        return '%s: %s - %s' % (self.id_conn.login, self.status, self.act)




#таблица фолловеров целевых аккаунтов, гео или тегов
class Acc_in_act(models.Model):
    target = models.ForeignKey(Acts_follow, on_delete = models.CASCADE,)
    id_inst = models.ForeignKey(Inst_accounts, on_delete = models.CASCADE,)



#таблица дневной статистики по подключенным пользователям
#нужна для сверки с ограничениями
class Stat(models.Model):
    id_conn = models.ForeignKey(Conn_inst_acc, on_delete = models.CASCADE,)
    count_like = models.IntegerField(default=0)
    count_follow = models.IntegerField(default=0)
    count_follow_geo = models.IntegerField(default=0)
    count_follow_tag = models.IntegerField(default=0)
    count_unfollow = models.IntegerField(default=0)
    date_stat = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return '%s: %s' % (self.id_conn.login, self.date_stat)


# type notice:
# info
# warn
# err
class Notices(models.Model):
    id_conn  = models.ForeignKey(Conn_inst_acc, on_delete = models.CASCADE,)
    type  = models.CharField(max_length = 10, default = '')
    message = models.CharField(max_length = 512, default = '')
    dt_motice = models.DateTimeField(blank=True, null=True)
