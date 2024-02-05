from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from core.apps.bot.constants.users_type import UserTypes, USER_TYPES_CHOICES
from core.apps.bot.constants.bot_label import BotLabel, BOT_LABEL_CHOICES
from core.apps.bot.constants.state_type import StateTypes, USER_STATES_CHOICES


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
    vk_id = models.BigIntegerField(_('ВК ID'), unique=True, blank=True, null=True)
    vk_user_url = models.URLField(_('Ссылка на ВК Профиль'), max_length=150, unique=True, blank=True, null=True)
    is_admin = models.BooleanField(_('Является администратором?'), default=False)
    state_menu = models.IntegerField(_('Состояние'), default=StateTypes.DEFAULT.value, choices=USER_STATES_CHOICES)
    vip_code = models.ForeignKey("VIPCode", related_name='bot_users', verbose_name=_('VIP Код'), null=True,
                                 blank=True, on_delete=models.SET_NULL)
    vip_end_date = models.DateField(blank=True, null=True, verbose_name=_('Дата окончания VIP кода'))

    def __str__(self):
        return self.username or f"{self.first_name} {self.last_name}"

    def update_vip_status(self):
        if self.status == UserTypes.VIP and self.vip_end_date:
            now_date = timezone.now().date()

            if self.vip_end_date < now_date:
                self.status = 0
                self.vip_end_date = None
                self.vip_code_id = None
                self.save()


class VIPCode(models.Model):
    class Meta:
        verbose_name = 'VIP Код'
        verbose_name_plural = 'VIP Коды'

    vip_code = models.CharField(_('VIP Код'), max_length=100, unique=True)

    def __str__(self):
        return self.vip_code


class LinkStorage(models.Model):
    class Meta:
        verbose_name_plural = 'Хранилище ссылок'

    bot_user = models.ForeignKey('BotUser', related_name='vk_links', verbose_name=_('Пользователь'),
                                 on_delete=models.SET_NULL, blank=True, null=True)
    # code = models.CharField(_("Код ссылки"), max_length=128)
    vk_link = models.CharField(_('ВК Ссылка'), max_length=255)
    added_at = models.DateTimeField(_('Дата отправки'), auto_now_add=True)
    is_approved = models.BooleanField(_('Ссылка подтверждена'), default=False)

    def __str__(self):
        return self.vk_link


class LinksQueue(models.Model):
    class Meta:
        verbose_name_plural = 'Очередь ссылок'

    bot_user = models.ForeignKey('BotUser', related_name='links_queues', verbose_name=_('Пользователь'),
                                 on_delete=models.SET_NULL, blank=True, null=True)
    vk_link = models.CharField(_('ВК Ссылка'), max_length=255)
    approved_at = models.DateTimeField(_('Дата подтверждения'), auto_now_add=True)
    queue_number = models.CharField(_('Номер в очереди'), max_length=10, unique=True)
    link_priority = models.BooleanField(_('Приоритет ссылки'), default=False)

    def save(self, *args, **kwargs):
        if not self.queue_number:
            last_queue_number = LinksQueue.objects.order_by('-queue_number').first()
            if last_queue_number:
                current_number = int(last_queue_number.queue_number) + 1
            else:
                current_number = 1
            self.queue_number = f"{current_number:06d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.queue_number} - {self.vk_link}"


class UserDoneLinks(models.Model):
    class Meta:
        verbose_name_plural = 'Выполненные ссылки'

    bot_user = models.ForeignKey('BotUser', related_name='done_links', verbose_name=_('Пользователь'),
                                 on_delete=models.SET_NULL, blank=True, null=True)
    link = models.ForeignKey(LinksQueue, related_name='done_by_user', verbose_name=_('Выполненная ссылка'),
                             on_delete=models.CASCADE)

    def __str__(self):
        return self.link.vk_link


class TaskStorage(models.Model):
    class Meta:
        verbose_name_plural = 'Хранилище заданий'

    bot_user = models.ForeignKey('BotUser', related_name='task_storage', verbose_name=_('Пользователь'),
                                 on_delete=models.SET_NULL, blank=True, null=True)
    code = models.CharField(_('Код задания'), max_length=10, unique=True)
    message_text = models.TextField(_('Текст сообщения'))
    added_at = models.DateTimeField(_('Дата добавления'), auto_now_add=True)
    chat_task = models.CharField(_('Наименовании группы'), max_length=50, blank=True)

    def __str__(self):
        return f"{self.code} - {self.added_at}"


class BotSettings(models.Model):
    class Meta:
        verbose_name_plural = 'Настройки Бота'

    chat_label = models.IntegerField(
        _('Тип Чата'), default=BotLabel.DEFAULT.value, choices=BOT_LABEL_CHOICES
    )
    bot_chats = models.CharField(_('Чат'), max_length=150, blank=True)
    chat_id = models.BigIntegerField(_('Чат ID'), unique=True, blank=True, null=True)

    def __str__(self):
        return self.bot_chats
