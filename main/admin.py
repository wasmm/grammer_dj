from django.contrib import admin

from main.models import Conn_inst_acc
from main.models import Conn_acc_details
from main.models import Inst_accounts
from main.models import Conn_inst_followers
from main.models import Acts_like
from main.models import Acts_follow
from main.models import Config_instagram_work
from main.models import Stat
from main.models import Notices
from main.models import Acc_in_act

admin.site.register(Conn_inst_acc)
admin.site.register(Conn_acc_details)
admin.site.register(Inst_accounts)
admin.site.register(Conn_inst_followers)
admin.site.register(Acts_like)
admin.site.register(Acts_follow)
admin.site.register(Config_instagram_work)
admin.site.register(Stat)
admin.site.register(Notices)
admin.site.register(Acc_in_act)
