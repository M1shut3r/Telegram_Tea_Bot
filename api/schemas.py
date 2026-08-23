import re
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

PHONE_PATTERN = re.compile(r"^\+?[0-9][0-9\-\s()]{8,20}$")
COUNTRY_RUSSIA = "Россия"
ALLOWED_COUNTRIES = {COUNTRY_RUSSIA, "RU", "RUS", "Russia"}


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    composition: str
    price: Decimal
    photo_url: str
    is_active: bool

    @field_serializer("price")
    def serialize_price(self, value: Decimal) -> str:
        return f"{Decimal(value).quantize(Decimal('0.01')):.2f}"


class CartAddIn(BaseModel):
    product_id: int = Field(gt=0)


class CartQuantityIn(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(ge=0, le=99)


class CartItemOut(BaseModel):
    id: int
    product_id: int
    name: str
    price: Decimal
    quantity: int
    photo_url: str
    line_total: Decimal

    @field_serializer("price", "line_total")
    def serialize_money(self, value: Decimal) -> str:
        return f"{Decimal(value).quantize(Decimal('0.01')):.2f}"


class CartOut(BaseModel):
    items: list[CartItemOut]
    total: Decimal
    count: int

    @field_serializer("total")
    def serialize_total(self, value: Decimal) -> str:
        return f"{Decimal(value).quantize(Decimal('0.01')):.2f}"


class CheckoutIn(BaseModel):
    customer_name: str = Field(min_length=2, max_length=255)
    phone: str
    city: str = Field(min_length=2, max_length=128)
    address: str = Field(min_length=5, max_length=512)
    country: str = COUNTRY_RUSSIA

    @field_validator("customer_name", "phone", "city", "address", "country")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        if not PHONE_PATTERN.match(value):
            raise ValueError("Введите телефон в формате +79991234567")
        return value

    @field_validator("country")
    @classmethod
    def validate_country(cls, value: str) -> str:
        if value not in ALLOWED_COUNTRIES:
            raise ValueError("Доставка доступна только по России")
        return COUNTRY_RUSSIA


class OrderOut(BaseModel):
    id: int
    status: str
    status_title: str
    total_price: Decimal
    customer_name: str
    phone: str
    country: str
    city: str
    address: str
    tracking_number: str | None = None
    can_cancel: bool = False
    created_at: datetime | None

    @field_serializer("total_price")
    def serialize_total_price(self, value: Decimal) -> str:
        return f"{Decimal(value).quantize(Decimal('0.01')):.2f}"


class CheckoutOut(BaseModel):
    order: OrderOut


class RoadmapStageOut(BaseModel):
    status: str
    title: str
    done: bool


class OrderLineOut(BaseModel):
    product_id: int
    name: str
    quantity: int
    price: Decimal
    line_total: Decimal

    @field_serializer("price", "line_total")
    def serialize_line_money(self, value: Decimal) -> str:
        return f"{Decimal(value).quantize(Decimal('0.01')):.2f}"


class OrderDetailOut(OrderOut):
    items: list[OrderLineOut]
    roadmap: list[RoadmapStageOut]
