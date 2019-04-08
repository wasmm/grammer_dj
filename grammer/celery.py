import os
from celery import Celery
from celery.schedules import crontab

from datetime import timedelta

from kombu import Exchange, Queue

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grammer.settings')

app = Celery('grammer')
app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.worker_max_tasks_per_child = 100

app.conf.task_queues = (
    #очередь добавления доп инфо в базу
    Queue('svc_get_acc_info', Exchange('svc_get_acc_info'), routing_key='svc_get_acc_info'),
    #очередь добавления подписчиков и подписок в базу
    Queue('svc_add_follower', Exchange('svc_add_follower'), routing_key='svc_add_follower'),
    #очередь расстановки лайков
    Queue('like_action', Exchange('like_action'), routing_key='like_action'),
    # очередь добавления подписчиков из указанных источников
    Queue('target_f_add', Exchange('target_f_add'), routing_key='target_f_add'),
    #очередь обработки(фолловинга) добавленых подписчиков
    Queue('flw_add', Exchange('flw_add'), routing_key='flw_add'),
)




app.conf.task_routes = {
    'main.tasks.get_full_data': {'queue' : 'svc_get_acc_info'},
    'main.tasks.add_follow': {'queue' : 'svc_add_follower'},

    'main.tasks.scaner_acts_like': {'queue' : 'like_action'},
    'main.tasks.like': {'queue' : 'like_action'},

    'main.tasks.scaner_acts_follow': {'queue' : 'target_f_add'},
    'main.tasks.mas_add_following': {'queue' : 'target_f_add'},
    'main.tasks.mas_add_following_tag_or_geo': {'queue' : 'target_f_add'},

    'main.tasks.scaner_acts_add_follow': {'queue' : 'flw_add'},
    'main.tasks.follow_it': {'queue' : 'flw_add'},
}
#
#
#
app.conf.beat_schedule = {
#     ###########   масс лайк   ################################
#     #цикличное задание на расстановку лайков
    'scan-acts-like-every-1-minutes':{
        'task' : 'main.tasks.scaner_acts_like',
        'schedule' : timedelta(seconds=30),
    },
    #Цикличное задание на добавление подписчиков целевого аккаунта в базу для
    #дальнейшего фолловинга
    'scan-acts-follow-acc-every-30-seconds':{
        'task' : 'main.tasks.scaner_acts_follow',
        'schedule' : timedelta(seconds=30),
        'args' : (['follow_acc'])
    },
    'scan-acts-follow-geo-every-30-seconds':{
        'task' : 'main.tasks.scaner_acts_follow',
        'schedule' : timedelta(seconds=35),
        'args' : (['follow_geo'])
    },
    'scan-acts-follow-geo-every-30-seconds':{
        'task' : 'main.tasks.scaner_acts_follow',
        'schedule' : timedelta(seconds=40),
        'args' : (['follow_tag'])
    },
#
#
#
    'processing-follow-act-every-45-sec':{
        'task' : 'main.tasks.scaner_acts_add_follow',
        'schedule' : timedelta(seconds=35),
         'args' : (['follow_acc'])
    },
    'processing-follow-act-every-46-sec':{
        'task' : 'main.tasks.scaner_acts_add_follow',
        'schedule' : timedelta(seconds=40),
         'args' : (['follow_geo'])
    },
    'processing-follow-act-every-47-sec':{
        'task' : 'main.tasks.scaner_acts_add_follow',
        'schedule' : timedelta(seconds=45),
         'args' : (['follow_tag'])
    },
}
