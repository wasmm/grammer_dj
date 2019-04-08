import time
from django.db.models.signals import post_save

from main.models import add_users
from main.models import add_data
from main.models import add_mass_like
from main.models import close_mass_like


from django.dispatch import receiver


from main.models import Conn_acc_details
from main.models import Conn_inst_acc
from main.models import Inst_accounts
from main.models import Conn_inst_followers
from main.models import Acts_like

from main.utils import Grammer

from main.tasks import get_full_data
from main.tasks import add_follow
# from main.tasks import collect_for_mass_like






@receiver(add_data, sender = Conn_inst_acc)
def add_info_user(sender, login, **kwargs):
    get_full_data.delay(login)

@receiver(add_users, sender = Conn_acc_details)
def add_info(sender, login, **kwargs):
    print()
    print('*********************************************************************')
    print('Сигнал добавления подписчиков и подписок, ИД: {0}'.format(login))
    print('*********************************************************************')
    print()
    add_follow.delay(login)




#Эта ф-ция запускается по сигналу, когда меняется параметр mass_likes на True
#в таблице Conn_inst_acc, задание добавляет запись в Acts_like задание
#на масс лайкинг, если такого нет, если есть то ничего не делает
@receiver(add_mass_like, sender = Conn_inst_acc)
def mass_liker(sender, id, **kwargs):
    user = Conn_inst_acc.objects.get(pk = id)
    acts_ad = Acts_like.objects.filter(id_conn = user, status__in=['added', 'processing'])
    if acts_ad.count() == 0:
        to_act = Acts_like(id_conn = user, act = 'like', status = 'added')
        to_act.save()
        res = 'Задание добавлено'
    else:
        res = 'У пользователя уже есть задание'
    print('{0} : {1}'.format(user.login, res))


#Эта ф-ция запускается по сигналу, когда меняется параметр mass_likes на False
#в таблице Conn_inst_acc, ф-ция отключает все назначенные задания со статусом
#added, остаются только те, что выполняются в даное время
@receiver(close_mass_like, sender = Conn_inst_acc)
def del_mass_liker(sender, id, **kwargs):
    user = Conn_inst_acc.objects.get(pk = id)
    acts_close = Acts_like.objects.filter(id_conn = user, status__in=['added', 'processing'], locked = False)
    print(acts_close)
    print('count acts: {0}'.format(acts_close.count()))
    cnt_acts = 0
    for act in acts_close:
        act.status = 'processed'
        act.save()
        cnt_acts += 1
    res = 'отменено заданий: '+str(cnt_acts)
    print('{0} : {1}'.format(user.login, res))
