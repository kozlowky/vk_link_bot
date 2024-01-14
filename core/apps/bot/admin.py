from django.contrib import admin
from django.db import models
from core.apps.bot.models import BotUser


class TGUserModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'first_name', 'last_name', 'username_with_at', *[field.name for field in BotUser._meta.fields if
                                                                           field.name not in ['id', 'first_name',
                                                                                              'last_name', 'username']]]
    search_fields = ['id', 'first_name', 'last_name', 'username']
    list_filter = ['id', 'first_name', 'last_name', 'username', *[field.name for field in BotUser._meta.fields if
                                                                  field.name not in ['id', 'first_name', 'last_name',
                                                                                     'username']]]

    def username_with_at(self, obj):
        return f"@{obj.username}"

    username_with_at.short_description = 'Username'


admin.site.register(BotUser, TGUserModelAdmin)
