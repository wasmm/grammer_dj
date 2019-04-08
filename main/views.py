from django.http import HttpResponse

from datetime import datetime, date, time
from main.utils import Grammer

from django.shortcuts import render
from django.http import HttpResponseRedirect


from .forms import Add_Act_Form

from main.models import Conn_inst_acc
from main.models import Conn_inst_followers
from main.models import Stat
from main.models import Acts_follow
from main.models import Acc_in_act

def index(request):
    inst_login = Conn_inst_acc.objects.all()


    return render(request, 'main/index.html', {'data' : inst_login})

def intagram_user_info(request, id_acc):
    datauser = Conn_inst_acc.objects.get(pk = id_acc)
    followers = Conn_inst_followers.objects.filter(id_conn_id = datauser, type_follow = 'follower').count()
    following = Conn_inst_followers.objects.filter(id_conn_id = datauser, type_follow = 'following').count()
    unfollow = Conn_inst_followers.objects.filter(id_conn_id = datauser, type_follow = 'unfollow').count()
    like_it = Conn_inst_followers.objects.filter(id_conn_id = datauser, like_it = True).count()
    try:
        acts = Acts_follow.objects.filter(id_conn = datauser, status = 'follows')
        pot_follow = 0
        for act in acts:
            cnt_follow = Acc_in_act.objects.filter(target = act).count()
            pot_follow += cnt_follow

    except Acts_follow.DoesNotExist:
        pot_follow = 0





    today = datetime.now()
    try:
        stat = Stat.objects.get(id_conn = datauser,
                                date_stat__day = today.day,
                                date_stat__month = today.month,
                                date_stat__year = today.year)

        cnt_likes = stat.count_like
        cnt_follow = stat.count_follow
    except Stat.DoesNotExist:
        cnt_likes = 0
        cnt_follow = 0






    if request.method == 'POST':
        form = Add_Act_Form(request.POST)
        if form.is_valid():
            is_acts = Acts_follow.objects.filter(id_conn_id = id_acc, status = 'added', locked = False, act = request.POST.get('act')).count()
            if is_acts == 0:
                err = 'Ошибок нет'
                datauser = Conn_inst_acc.objects.get(pk = id_acc)
                post = form.save(commit=False)
                post.id_conn = datauser
                r = post.save()
            else:
                err = 'Такое задание уже есть-' + str(is_acts)
                r = 'добавление не выполнено - задание есть'
        else:
            r = 'добавление не выполнено - форма невалидная'
    else:
        r = 'добавление не выполнено - запрос не ПОСТ блять'

        err = 'Ошибки есть'
        form = Add_Act_Form()



    return render(request, 'main/userinfo.html', {'count_followers' : followers,
                                                      'count_following' : following,
                                                      'username' : datauser.login,
                                                      'likes' : cnt_likes,
                                                      'follow' : cnt_follow,
                                                      'form': form,
                                                      'err': err,
                                                      'unfollow': unfollow,
                                                      'like_it': like_it,
                                                      'pot_follow': pot_follow,
                                                      'm_likes': datauser.mass_likes,
                                                      'm_follow_acc' : datauser.mass_follow_acc,
                                                      'm_follow_geo' : datauser.mass_follow_geo,
                                                      'm_follow_tag' : datauser.mass_follow_tag,})



# def act_add(request, id_acc):
#     if request.method == 'POST':
#         form = Add_Act_Form(request.POST)
#         if form.is_valid():
#             is_acts = Acts_follow.objects.filter(id_conn_id = id_acc, status = 'added', locked = False, act = request.POST.get('act')).count()
#             if is_acts == 0:
#                 err = 'Ошибок нет'
#                 datauser = Conn_inst_acc.objects.get(pk = id_acc)
#                 post = form.save(commit=False)
#                 post.id_conn = datauser
#
#                 r = post.save()
#             else:
#                 err = 'Такое задание уже есть-' + str(is_acts)
#                 r = 'добавление не выполнено - задание есть'
#         else:
#             r = 'добавление не выполнено - форма невалидная'
#     else:
#         r = 'добавление не выполнено - запрос не ПОСТ блять'
#
#
#
#
#
#     # else:
#         err = 'Ошибки есть'
#         form = Add_Act_Form()
#
#
#
#
#     return render(request, 'main/includes/f_act.html', {'form': form, 'err': err, 'r': request.POST})
