from django.urls import path

from . import views

app_name = 'main'

urlpatterns = [
    path('index/', views.index, name='index'),
    path('index/<id_acc>/', views.intagram_user_info, name='inst_acc_info'),
    # path('index/<id_acc>/act_add/', views.act_add, name='act_add'),

]
