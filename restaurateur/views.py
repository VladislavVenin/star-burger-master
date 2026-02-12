from django import forms
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views

from requests.exceptions import HTTPError
from geopy import distance


from foodcartapp.models import Product, Restaurant, Order
from places.models import Coordinates
from django.conf import settings
from places.utils import fetch_coordinates


def get_coords_from_map(address, coords_map):
    return coords_map.get(address)


class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    products_with_restaurant_availability = []
    for product in products:
        availability = {item.restaurant_id: item.availability for item in product.menu_items.all()}
        ordered_availability = [availability.get(restaurant.id, False) for restaurant in restaurants]

        products_with_restaurant_availability.append(
            (product, ordered_availability)
        )

    return render(request, template_name="products_list.html", context={
        'products_with_restaurant_availability': products_with_restaurant_availability,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name="restaurants_list.html", context={
        'restaurants': Restaurant.objects.all(),
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    current_url = request.path

    orders = Order.objects.prefetch_related('restaurant_branch')\
        .manager_filter()\
        .with_available_restaurants()

    addresses = set()
    for order in orders:
        if not order.restaurant_branch:
            addresses.add(order.address)
            for restaurant in order.available_restaurants:
                addresses.add(restaurant.address)

    coords_map = {
        c.address: (c.lon, c.lat)
        for c in Coordinates.objects.filter(address__in=addresses)
    }
    missing_addresses = addresses - coords_map.keys()

    for address in missing_addresses:
        try:
            coords = fetch_coordinates(settings.YANDEX_API_KEY, address)
        except HTTPError:
            coords = None
        if coords:
            Coordinates.objects.create(
                address=address,
                lon=coords[0],
                lat=coords[1],
            )
            coords_map[address] = coords

    for order in orders:
        if order.restaurant_branch:
            continue
        distances = {}

        order_coords = get_coords_from_map(order.address, coords_map)
        for restaurant in order.available_restaurants:
            restaurant_coords = get_coords_from_map(restaurant.address, coords_map)
            if restaurant_coords is None or order_coords is None:
                distances[restaurant] = "Ошибка при определении координат"
                continue

            distances[restaurant] = round(distance.distance(order_coords, restaurant_coords).km, 2)
        order.distances = dict(sorted(distances.items(), key=lambda item: item[1]))

    context = {
        "order_items": orders,
        "next": current_url,
    }
    return render(request, template_name='order_items.html', context=context)
