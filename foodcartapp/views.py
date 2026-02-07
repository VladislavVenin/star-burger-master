from django.http import JsonResponse
from django.templatetags.static import static
import json
from rest_framework.decorators import api_view
from rest_framework.response import Response


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

    if type(data["products"]) is not list or not data.get("products"):
        return Response({"error": "The product list is empty or not a list."}, status=400)

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
            return Response({"error": "No such product with this id"}, status=400)

        OrderItem.objects.create(
            product=order_item,
            order=order,
            quantity=product["quantity"],
        )
    return Response({"status": "ok", "data": data})
