from core.bot.constants.bot_label import BotLabel, BOT_LABEL_CHOICES
from core.bot.constants.state_type import StateTypes, USER_STATES_CHOICES
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.bot.constants.users_type import UserTypes, USER_TYPES_CHOICES

USER_VERBOSE_NAME = 'Пользователь'
VIP_CODE = 'VIP Код'


class BotUser(models.Model):
    """ Модель пользователя Телеграмм бота """

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    tg_id = models.PositiveBigIntegerField(_('ID Телеграм'), unique=True, blank=True, null=True)
    first_name = models.CharField(_('Имя'), max_length=150, blank=True)
    last_name = models.CharField(_('Фамилия'), max_length=150, blank=True)
    username = models.CharField(_('Имя пользователя'), max_length=150, blank=True)
    status = models.IntegerField(
        _('Статус'),
        default=UserTypes.REGULAR.value,
        choices=USER_TYPES_CHOICES
    )
    vk_id = models.BigIntegerField(
        _('ВК ID'),
        unique=True,
        blank=True,
        null=True
    )
    vk_user_url = models.URLField(
        _('Ссылка на ВК Профиль'),
        max_length=150,
        unique=True,
        blank=True,
        null=True
    )
    is_admin = models.BooleanField(_('Является администратором?'), default=False)
    state_menu = models.IntegerField(
        _('Состояние'),
        default=StateTypes.DEFAULT.value,
        choices=USER_STATES_CHOICES
    )
    vip_code = models.ForeignKey(
        "VIPCode",
        related_name='bot_users',
        verbose_name=VIP_CODE,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    vip_end_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Дата окончания VIP кода')
    )
    mute = models.BooleanField(_('Блокировка чата'), default=False)

    def __str__(self):
        return self.username or f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        if self.vip_code and not self.vip_end_date:
            now_date = timezone.now().date()
            self.vip_end_date = now_date + timezone.timedelta(days=30)
            self.status = UserTypes.VIP
        super().save(*args, **kwargs)


class VIPCode(models.Model):
    """ Модель ВИП код """

    class Meta:
        verbose_name = 'VIP Код'
        verbose_name_plural = 'VIP Коды'

    vip_code = models.CharField(_('VIP Код'), max_length=100, unique=True)

    def __str__(self):
        return self.vip_code


class LinksQueue(models.Model):
    """ Модель ссылки ВК """

    class Meta:
        verbose_name = 'Ссылка'
        verbose_name_plural = 'Ссылки'

    bot_user = models.ForeignKey(
        'BotUser',
        related_name='links_queues',
        verbose_name=USER_VERBOSE_NAME,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )
    vk_link = models.CharField(_('ВК Ссылка'), max_length=255)
    approved_at = models.DateTimeField(_('Дата подтверждения'), auto_now_add=True)
    queue_number = models.CharField(_('Номер в очереди'), max_length=10, unique=True)
    link_priority = models.BooleanField(_('Приоритет ссылки'), default=False)
    send_count = models.IntegerField(_('Текущее количество отправок'), default=0)
    total_count = models.IntegerField(_('Количество отправок ссылки'), default=0)
    chat_type = models.ForeignKey(
        "Chat",
        verbose_name=_('Тип чата'),
        related_name='chat_type',
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )
    comment = models.TextField(_("Комментарий"), blank=True, null=True)
    owner_id = models.BigIntegerField(_('ID Владельца'), default=0)
    post_id = models.BigIntegerField(_('ID Поста'), default=0)
    is_approved = models.BooleanField(_('Ссылка подтверждена'), default=False)

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


class TaskStorage(models.Model):
    """ Модель задания """

    class Meta:
        verbose_name = 'Задание'
        verbose_name_plural = 'Задания'

    bot_user = models.ForeignKey(
        'BotUser',
        related_name='task_storage',
        verbose_name=USER_VERBOSE_NAME,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )
    link = models.ForeignKey(
        LinksQueue,
        related_name='link',
        verbose_name='Проверяемая ссылка',
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )
    added_at = models.DateTimeField(_('Дата добавления'), auto_now_add=True)
    links = models.ManyToManyField(
        LinksQueue,
        verbose_name=_('Ссылки задания'),
        related_name='task_links',
        blank=True,
        null=True
    )
    chat_type = models.ForeignKey(
        "Chat",
        verbose_name=_('Тип чата'),
        related_name='chat_task_type',
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )
    task_completed = models.BooleanField(_('Задание выполнено'), default=False)
    order_number = models.PositiveIntegerField(_('Порядковый номер'), unique=True)

    def save(self, *args, **kwargs):
        if not self.order_number:
            last_task = TaskStorage.objects.order_by('-order_number').first()
            if last_task:
                self.order_number = last_task.order_number + 1
            else:
                self.order_number = 1

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order_number} for {self.bot_user} - {self.added_at}"


class Chat(models.Model):
    """ Модель группы """

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'

    chat_label = models.IntegerField(
        _('Тип группы'),
        default=BotLabel.DEFAULT.value,
        choices=BOT_LABEL_CHOICES
    )
    bot_chats = models.CharField(
        _('Ссылка на группу'),
        max_length=150,
        blank=True
    )
    chat_id = models.BigIntegerField(
        _('Чат ID'),
        unique=True,
        blank=True,
        null=True
    )
    reply_link_count = models.IntegerField(
        _('Разрешена повторная отправка ссылки через: '),
        default=0
    )
    link_count = models.IntegerField(_('Количество раздач ссылки'), default=0)
    task_link_count = models.IntegerField(_('Количество ссылок в задании'), default=0)

    def __str__(self):
        label = dict(BOT_LABEL_CHOICES).get(self.chat_label)
        return label


class BotSettings(models.Model):
    class Meta:
        verbose_name = 'Настройки Бота'
        verbose_name_plural = 'Настройки Бота'

    name = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name


class MessageText(models.Model):
    """ Модель для хранения сообщений Бота """

    class Meta:
        verbose_name = 'Текст сообщения'
        verbose_name_plural = 'Тексты сообщений'

    settings = models.ForeignKey(
        BotSettings,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    key = models.CharField(max_length=100, unique=True, verbose_name='Ключ')
    message = models.TextField(verbose_name='Сообщение')

    def __str__(self):
        return self.key


class MessageLog(models.Model):
    chat = models.ForeignKey(
        "Chat",
        verbose_name=_('Тип чата'),
        related_name='chat_instance_log',
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )
    message_data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
