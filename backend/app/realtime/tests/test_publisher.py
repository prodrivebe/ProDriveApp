"""Realtime publisher helper tests."""

from app.realtime.publisher import _notification_severity, publish_notification_created


def test_notification_severity_mapping() -> None:
    assert _notification_severity("ORDER_ASSIGNED") == "info"
    assert _notification_severity("ORDER_REJECTED") == "warning"
    assert _notification_severity("ORDER_COMPLETED") == "success"


def test_publish_notification_created_does_not_raise() -> None:
    import uuid

    publish_notification_created(
        company_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        notification_id=uuid.uuid4(),
        title="New order assignment",
        message="Order ORD-001 has been assigned to you.",
        notification_type="ORDER_ASSIGNED",
        order_id=uuid.uuid4(),
    )
