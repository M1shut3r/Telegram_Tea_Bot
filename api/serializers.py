from decimal import Decimal

from api.schemas import CartItemOut, CartOut, OrderDetailOut, OrderLineOut, OrderOut, ProductOut, RoadmapStageOut
from app.models.cart import Cart
from app.models.order import CANCELLABLE_ORDER_STATUSES, Order
from app.models.product import Product
from app.services.order_tracking import generate_roadmap_stages, status_title


def product_photo_url(product_id: int) -> str:
    return f"/api/products/{product_id}/photo"


def serialize_product(product: Product) -> ProductOut:
    return ProductOut(
        id=product.id,
        name=product.name,
        description=product.description,
        composition=product.composition,
        price=product.price,
        photo_url=product_photo_url(product.id),
        is_active=product.is_active,
    )


def serialize_cart_item(item: Cart) -> CartItemOut:
    product = item.product
    price = Decimal(product.price) if product is not None else Decimal("0.00")
    name = product.name if product is not None else f"Товар #{item.product_id}"
    return CartItemOut(
        id=item.id,
        product_id=item.product_id,
        name=name,
        price=price,
        quantity=item.quantity,
        photo_url=product_photo_url(item.product_id),
        line_total=price * item.quantity,
    )


def serialize_cart(items: list[Cart]) -> CartOut:
    payload = [serialize_cart_item(item) for item in items]
    total = sum((item.line_total for item in payload), Decimal("0.00"))
    count = sum(item.quantity for item in payload)
    return CartOut(items=payload, total=total, count=count)


def serialize_order(order: Order) -> OrderOut:
    return OrderOut(
        id=order.id,
        status=order.status,
        status_title=status_title(order.status),
        total_price=order.total_price,
        customer_name=order.customer_name,
        phone=order.phone,
        country=order.country,
        city=order.city,
        address=order.address,
        tracking_number=order.tracking_number,
        can_cancel=order.status in CANCELLABLE_ORDER_STATUSES,
        created_at=order.created_at,
    )


def serialize_order_detail(order: Order) -> OrderDetailOut:
    items: list[OrderLineOut] = []
    for item in order.items:
        price = Decimal(item.price_at_purchase)
        name = item.product.name if item.product is not None else f"Товар #{item.product_id}"
        items.append(
            OrderLineOut(
                product_id=item.product_id,
                name=name,
                quantity=item.quantity,
                price=price,
                line_total=price * item.quantity,
            )
        )
    roadmap = [RoadmapStageOut.model_validate(stage) for stage in generate_roadmap_stages(order.status)]
    base = serialize_order(order)
    return OrderDetailOut(**base.model_dump(), items=items, roadmap=roadmap)
