from django.http import JsonResponse
from django.templatetags.static import static
import json

from rest_framework.decorators import api_view
from rest_framework.response import Response
import phonenumbers
from phonenumbers import is_valid_number
from phonenumbers.phonenumberutil import NumberParseException

from .models import Product, Order, OrderItem


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


@api_view(['POST'])
def register_order(request):
    try:
        data = request.data
    except json.JSONDecodeError:
        return Response({"error": "Invalid JSON"}, status=400)

    fields = [
        "products",
        "firstname",
        "phonenumber",
        "address",
    ]
    errors = {}

    for field in fields:
        if not data.get(field):
            errors[f"{field}"] = f"The {field} field is missing or empty."
    if errors:
        return Response({"error": errors}, status=400)

    if not isinstance(data["products"], list):
        return Response({"error": "The products list is not a list."}, status=400)

    if not isinstance(data["firstname"], str):
        return Response({"error": "Firstname is not a valid string."}, status=400)

    try:
        phonenumber = phonenumbers.parse(data["phonenumber"], "RU")
    except NumberParseException:
        return Response({"error": "Invalid phone number"}, status=400)
    if not is_valid_number(phonenumber):
        return Response({"error": "Invalid phone number"}, status=400)

    order = Order.objects.create(
        address=data["address"],
        firstname=data["firstname"],
        lastname=data["lastname"],
        phonenumber=data["phonenumber"],
    )
    for product in data["products"]:
        try:
            order_item = Product.objects.get(id=product["product"])
        except Product.DoesNotExist:
            order.delete()
            return Response({"error": "No product with such id"}, status=404)

        OrderItem.objects.create(
            product=order_item,
            order=order,
            quantity=product["quantity"],
        )
    return Response({"status": "ok", "data": data})
