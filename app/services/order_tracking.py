from app.models.order import OrderStatus

STATUS_RANK = {
    OrderStatus.NEW.value: 0,
    OrderStatus.IN_PROGRESS.value: 1,
    OrderStatus.PACKED.value: 2,
    OrderStatus.SHIPPED.value: 3,
    OrderStatus.DONE.value: 4,
}

STATUS_TITLES = {
    OrderStatus.NEW.value: "Новый",
    OrderStatus.IN_PROGRESS.value: "Принят в работу",
    OrderStatus.PACKED.value: "Собран",
    OrderStatus.SHIPPED.value: "Отправлен",
    OrderStatus.DONE.value: "Выполнен",
    OrderStatus.CANCELLED.value: "Отменён",
}

ROADMAP_STAGES = (
    (OrderStatus.IN_PROGRESS.value, "Принят в работу"),
    (OrderStatus.PACKED.value, "Собран"),
    (OrderStatus.SHIPPED.value, "Отправлен"),
)

MINIAPP_ROADMAP_STAGES = (
    *ROADMAP_STAGES,
    (OrderStatus.DONE.value, "Выполнен"),
)

USER_STATUS_NOTIFICATIONS = {
    OrderStatus.IN_PROGRESS.value: "🟢 Ваш заказ №{order_id} принят в работу!",
    OrderStatus.PACKED.value: "📦 Ваш заказ №{order_id} собран и передан в доставку!",
    OrderStatus.SHIPPED.value: "🚚 Ваш заказ №{order_id} отправлен!",
    OrderStatus.DONE.value: "🏁 Ваш заказ №{order_id} выполнен. Спасибо за покупку!",
}


def status_title(order_status: str) -> str:
    return STATUS_TITLES.get(order_status, order_status)


def tracking_line(tracking_number: str | None) -> str | None:
    if tracking_number is None:
        return None
    value = tracking_number.strip()
    if not value:
        return None
    return f"📮 Трек-номер: {value}"


def generate_roadmap_text(order_status: str, tracking_number: str | None = None) -> str:
    if order_status == OrderStatus.CANCELLED.value:
        return "❌ Заказ отменён"
    current_rank = STATUS_RANK.get(order_status, 0)
    lines: list[str] = []
    for index, (status, title) in enumerate(ROADMAP_STAGES):
        mark = "🟢" if STATUS_RANK[status] <= current_rank else "🔴"
        if index > 0:
            lines.append("⬇️")
        lines.append(f"{mark} {title}")
    if STATUS_RANK.get(order_status, 0) >= STATUS_RANK[OrderStatus.SHIPPED.value]:
        line = tracking_line(tracking_number)
        if line is not None:
            lines.append("")
            lines.append(line)
    return "\n".join(lines)


def generate_roadmap_stages(order_status: str) -> list[dict[str, str | bool]]:
    current_rank = STATUS_RANK.get(order_status, 0)
    return [
        {
            "status": status,
            "title": title,
            "done": STATUS_RANK[status] <= current_rank,
        }
        for status, title in MINIAPP_ROADMAP_STAGES
    ]


def user_status_notification(
    order_id: int,
    status: str,
    tracking_number: str | None = None,
) -> str:
    if status == OrderStatus.SHIPPED.value:
        line = tracking_line(tracking_number)
        if line is not None:
            return f"🚚 Ваш заказ №{order_id} отправлен! Трек-номер: {tracking_number.strip()}"
    template = USER_STATUS_NOTIFICATIONS.get(status)
    if template is None:
        return f"Статус заказа №{order_id} обновлён."
    return template.format(order_id=order_id)
