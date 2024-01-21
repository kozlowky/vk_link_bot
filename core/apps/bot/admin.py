from django.contrib import admin

from core.apps.bot.constants.users_type import UserTypes
from core.apps.bot.models import BotUser, VKLink, VIPCode


class TGUserModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'username_with_at', 'first_name', 'last_name',
                    *[field.name for field in BotUser._meta.fields if
                      field.name not in ['id', 'first_name',
                                         'last_name', 'username']]]
    search_fields = ['id', 'get_username', 'first_name', 'last_name', 'username']
    list_filter = ['id', 'first_name', 'last_name', 'username',
                   *[field.name for field in BotUser._meta.fields if
                     field.name not in ['id', 'first_name', 'last_name',
                                        'username']]]

    def get_username(self, obj):
        return obj.username or f"{obj.first_name} {obj.last_name}"

    get_username.short_description = 'Username'
    get_username.admin_order_field = 'username'

    def username_with_at(self, obj):
        return f"@{obj.username}"

    username_with_at.short_description = 'Username'


class VKLinkModelAdmin(admin.ModelAdmin):
    list_display = ['bot_user', 'vk_link']
    search_fields = ['id', 'bot_user__username']
    list_filter = ['bot_user__username']


class VIPCodeModelAdmin(admin.ModelAdmin):
    list_display = ['bot_user', 'vip_code', 'expiration_datetime']
    search_fields = ['id', 'bot_user__username', 'vip_code']
    list_filter = ['bot_user__username']

    def save_model(self, request, obj, form, change):
        obj.bot_user.status = UserTypes.VIP.value
        obj.bot_user.save()

        super().save_model(request, obj, form, change)


admin.site.register(BotUser, TGUserModelAdmin)
admin.site.register(VKLink, VKLinkModelAdmin)
admin.site.register(VIPCode, VIPCodeModelAdmin)
