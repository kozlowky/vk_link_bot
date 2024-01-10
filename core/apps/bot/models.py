from django.db import models

from django.db import models


class User(models.Model):
    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    tg_id = models.IntegerField(unique=True, blank=True)
    first_name = models.CharField(max_length=256, blank=True)
    last_name = models.CharField(max_length=256, blank=True)
    username = models.CharField(max_length=256, unique=True, blank=True)
    vk_id = models.CharField(max_length=100, unique=True, blank=True)
    # status
    # vip - bool

    def __str__(self):
        return str(self.id)

