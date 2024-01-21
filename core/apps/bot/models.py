from datetime import timedelta

from django.db import models
from django.utils.translation import gettext_lazy as _
from core.apps.bot.constants.users_type import UserTypes, USER_TYPES_CHOICES


class BotUser(models.Model):
    class Meta:
        verbose_name = 'Пользователь бота'
        verbose_name_plural = 'Пользователи бота'

    tg_id = models.PositiveBigIntegerField(_('ID Телеграм'), unique=True, blank=True, null=True)
    first_name = models.CharField(_('Имя'), max_length=150, blank=True)
    last_name = models.CharField(_('Фамилия'), max_length=150, blank=True)
    username = models.CharField(_('Имя пользователя'), max_length=150, blank=True, null=True)
    status = models.IntegerField(
        _('Статус'), default=UserTypes.REGULAR.value, choices=USER_TYPES_CHOICES
    )
    vk_user = models.ForeignKey('VKUser', verbose_name=_('ВК Профиль'), blank=True, null=True,
                                on_delete=models.SET_NULL)
    is_admin = models.BooleanField(_('Являеться администратором?'), default=False)

    def __str__(self):
        return self.username or f"{self.first_name} {self.last_name}"


class VKUser(models.Model):
    class Meta:
        verbose_name = 'ВК Пользователь'
        verbose_name_plural = 'ВК Пользователи'

    vk_id = models.BigIntegerField(_('ВК ID'), unique=True, blank=True)
    vk_page_url = models.URLField(_('Ссылка на ВК Профиль'), max_length=150, unique=True, blank=True)

    def __str__(self):
        return str(self.vk_page_url)


class VKLink(models.Model):
    class Meta:
        verbose_name = 'ВК Ссылка'
        verbose_name_plural = 'ВК Ссылки'

    vk_link = models.CharField(_('ВК Ссылка'), max_length=255)
    vk_user = models.ForeignKey('VKUser', related_name='vk_links', verbose_name=_('ВК Профиль'),
                                on_delete=models.SET_NULL, blank=True, null=True)
    bot_user = models.ForeignKey('BotUser', related_name='vk_links', verbose_name=_('Пользователь'),
                                 on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return self.vk_link


class VIPCode(models.Model):
    class Meta:
        verbose_name = 'VIP Код'
        verbose_name_plural = 'VIP Коды'

    vip_code = models.CharField(_('VIP Код'), max_length=100, unique=True)
    bot_user = models.OneToOneField(BotUser, related_name='vip_code', verbose_name=_('Пользователь'), null=True,
                                    blank=True, on_delete=models.SET_NULL)
    added_at = models.DateTimeField(_('Действителен от'), auto_now_add=True)

    def __str__(self):
        return self.vip_code

    def expiration_datetime(self):
        expiration_date = self.added_at + timedelta(days=30)
        return expiration_date

    expiration_datetime.short_description = 'Дата окончания ВИП Кода'
