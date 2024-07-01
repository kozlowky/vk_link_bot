from django.contrib import admin

from core.bot.models import (
    BotUser,
    VIPCode,
    LinksQueue,
    Chat,
    TaskStorage,
    MessageText,
    BotSettings
)


class TGUserModelAdmin(admin.ModelAdmin):
    exclude = ["mute", "state_menu"]
    list_display = (
        'id',
        'username_with_at',
        'first_name',
        'last_name',
        'tg_id',
        'status',
        'vk_user_url',
        'vip_end_date',
        'is_admin'
    )
    search_fields = ['id', 'username', 'first_name', 'last_name', 'username']

    def username_with_at(self, obj):
        return f"@{obj.username}"

    username_with_at.short_description = 'Username'


class TaskStorageModelAdmin(admin.ModelAdmin):
    list_display = [
        'bot_user',
        'order_number',
        'chat_type',
        'task_completed',
    ]
    search_fields = [
        'bot_user__username',
        'order_number',
    ]
    readonly_fields = ['bot_user', 'order_number', 'chat_type', 'link', 'links']


class LinksQueueModelAdmin(admin.ModelAdmin):
    exclude = ['link_priority']
    list_display = [
        'bot_user',
        'vk_link',
        'comment',
        'queue_number',
        'send_count',
        'total_count',
        'is_approved',
    ]
    search_fields = [
        'id',
        'bot_user__username',
        'queue_number'
    ]
    list_filter = [
        'bot_user__username',
        'queue_number',
        'is_approved',
    ]
    readonly_fields = ['owner_id', 'post_id']


class VIPCodeModelAdmin(admin.ModelAdmin):
    list_display = ['vip_code']
    search_fields = ['id', 'vip_code']


class ChatAdmin(admin.ModelAdmin):
    list_display = ['bot_chats', 'chat_label']
    readonly_fields = ['chat_id']

    fieldsets = (
        (None, {
            'fields': ('chat_label', 'bot_chats')
        }),
        ('Настройки', {
            'fields': ('reply_link_count', 'link_count', 'task_link_count')
        }),
    )


class MessageTextInline(admin.TabularInline):
    model = MessageText
    extra = 0
    readonly_fields = ['key']


class BotSettingsAdmin(admin.ModelAdmin):
    list_display = ['name']
    readonly_fields = ('name',)
    inlines = [MessageTextInline]


admin.site.register(BotUser, TGUserModelAdmin)
admin.site.register(Chat, ChatAdmin)
admin.site.register(LinksQueue, LinksQueueModelAdmin)
admin.site.register(VIPCode, VIPCodeModelAdmin)
admin.site.register(TaskStorage, TaskStorageModelAdmin)
# admin.site.register(MessageText, MessageTextAdmin)
admin.site.register(BotSettings, BotSettingsAdmin)
