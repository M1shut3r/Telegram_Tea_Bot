from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class OrderStatus(str, Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    PACKED = "packed"
    SHIPPED = "shipped"
    DONE = "done"
    CANCELLED = "cancelled"


CANCELLABLE_ORDER_STATUSES = (
    OrderStatus.NEW.value,
    OrderStatus.IN_PROGRESS.value,
    OrderStatus.PACKED.value,
)

ACTIVE_ORDER_STATUSES = (
    *CANCELLABLE_ORDER_STATUSES,
    OrderStatus.SHIPPED.value,
)

ARCHIVED_ORDER_STATUSES = (
    OrderStatus.DONE.value,
    OrderStatus.CANCELLED.value,
)


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    customer_name: Mapped[str] = mapped_column(String(255))
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    status: Mapped[str] = mapped_column(String(32), default=OrderStatus.NEW.value)
    country: Mapped[str] = mapped_column(String(128), default="Россия")
    city: Mapped[str] = mapped_column(String(128), default="")
    address: Mapped[str] = mapped_column(String(512))
    phone: Mapped[str] = mapped_column(String(64))
    tracking_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[int] = mapped_column(Integer)
    price_at_purchase: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    order: Mapped["Order"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship(back_populates="order_items")
