from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from django.core.validators import MinValueValidator
from django.db.models import Sum, F, Prefetch


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class OrderQuerySet(models.QuerySet):
    def manager_filter(self):
        return self.annotate(
                total_price=Sum(F('products__quantity') * F('products__price'))
            ).prefetch_related('products__product').exclude(status='completed')

    def with_available_restaurants(self):
        restaurants = Restaurant.objects.prefetch_related(
            Prefetch(
                'menu_items',
                queryset=RestaurantMenuItem.objects.filter(availability=True),
                to_attr='available_menu'
            )
        )

        orders = self.prefetch_related('products__product').order_by('-status')

        for order in orders:
            order_product_ids = {item.product_id for item in order.products.all()}

            order.available_restaurants = [
                restaurant for restaurant in restaurants
                if order_product_ids.issubset({item.product_id for item in restaurant.available_menu})
            ]
        return orders


class Order(models.Model):
    STATUS_CHOICES = [
        ('new', 'Необработан'),
        ('in_progress', 'Обработан'),
        ('completed', 'Завершён'),
    ]
    address = models.CharField('Адрес', max_length=200, blank=False, null=False)
    firstname = models.CharField('Имя', max_length=50, blank=False, null=False)
    lastname = models.CharField('Фамилия', max_length=50, blank=False, null=False)
    phonenumber = PhoneNumberField('Телефон', region='RU',  blank=False, null=False)
    status = models.CharField(
        'Статус',
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        db_index=True,
    )
    payment = models.CharField(
        'Способ оплаты',
        max_length=20,
        choices=[
            ('none', 'Не выбран'),
            ('epay', 'Электронно'),
            ('cash', 'Наличностью'),
        ],
        default='none',
    )
    restaurant_branch = models.ForeignKey(
        Restaurant,
        verbose_name='Ресторан',
        on_delete=models.CASCADE,
        default=None,
        blank=False,
        null=True,
        related_name='orders',
    )
    notes = models.TextField('Комментарий', blank=True, null=True)
    created_at = models.DateTimeField('Заказ сформирован', auto_now_add=True)
    called_at = models.DateTimeField('Заказ обработан', blank=True, null=True, db_index=True,)
    delivered_at = models.DateTimeField('Заказ доставлен', blank=True, null=True, db_index=True,)

    objects = OrderQuerySet.as_manager()

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return f'[{self.created_at:%d.%m.%y} - {self.created_at:%H:%M}] - {self.address}'


class OrderItem(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name='продукт',
        db_index=True,
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name='заказ',
        db_index=True,
    )
    quantity = models.PositiveIntegerField('Количество', default=0)
    price = models.DecimalField(
        'Цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    class Meta:
        verbose_name = 'Позиция заказа'
        verbose_name_plural = 'Позиции заказа'

    def save(self, *args, **kwargs):
        if not self.price:
            self.price = self.product.price
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.product.name} - {self.quantity}'
