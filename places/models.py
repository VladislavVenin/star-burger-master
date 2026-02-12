from django.db import models


class Coordinates(models.Model):
    address = models.CharField('Адрес', max_length=200, blank=False, null=False, unique=True)
    lat = models.DecimalField("Широта", max_digits=5, decimal_places=2)
    lon = models.DecimalField("Долгота", max_digits=5, decimal_places=2)
    created_at = models.DateTimeField('Создано', auto_now_add=True)

    class Meta:
        verbose_name = 'Координаты'
        verbose_name_plural = 'Координаты'

    def __str__(self):
        return self.address
