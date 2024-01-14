from django.db import models
from django.utils.translation import gettext_lazy as _
from core.apps.bot.constants.users_type import UserTypes, USER_TYPES_CHOICES


class BotUser(models.Model):
    class Meta:
        verbose_name = 'Пользователь бота'
        verbose_name_plural = 'Пользователи бота'

    tg_id = models.PositiveBigIntegerField(_('ID Telegram'), unique=True, blank=True, null=True)
    first_name = models.CharField(_('First name'), max_length=150, blank=True)
    last_name = models.CharField(_('Last name'), max_length=150, blank=True)
    username = models.CharField(_('Username'), max_length=150, blank=True, null=True)
    status = models.IntegerField(
        _('User status'), default=UserTypes.UNKNOWN.value, choices=USER_TYPES_CHOICES
    )
    vip_code = models.CharField(_('VIP code'), max_length=100, blank=True)
    vk_user = models.ForeignKey('VKUser', verbose_name=_('Linked VK User'), blank=True, null=True,
                                on_delete=models.SET_NULL)
    is_admin = models.BooleanField(_('Is Admin'), default=False)

    def __str__(self):
        return str(self.id)


class VKUser(models.Model):
    class Meta:
        verbose_name = 'Пользователь ВК'
        verbose_name_plural = 'Пользователи ВК'

    vk_id = models.BigIntegerField(_('ID Vkontakte'),unique=True, blank=True)
    vk_page_url = models.URLField(_('VK page URL'), max_length=150, unique=True, blank=True)

    def __str__(self):
        return str(self.id)
