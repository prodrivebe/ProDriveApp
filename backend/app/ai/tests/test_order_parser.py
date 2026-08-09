"""Unit tests for Order Parser Agent."""

from app.ai.agents.order_parser import OrderParserAgent


def test_order_parser_extracts_customer_and_stops_with_confidence() -> None:
    agent = OrderParserAgent()
    result = agent.parse(
        "Customer: ACME Logistics\nPick up:\nBMW X5\nAmsterdam\nDeliver:\nBrussels"
    )

    assert result.customer_name == "ACME Logistics"
    assert result.field_confidence["customer_name"] >= 0.9
    assert len(result.pickup_stops) >= 1
    assert len(result.delivery_stops) >= 1
    assert len(result.vehicles) >= 1
    assert result.overall_confidence > 0


def test_order_parser_detects_vin_with_lower_confidence() -> None:
    agent = OrderParserAgent()
    vin = "1HGBH41JXMN109186"
    result = agent.parse(f"Pick up:\nAudi A4\nBerlin\nVIN {vin}\nDeliver:\nMunich")

    assert any(vehicle.vin == vin for vehicle in result.vehicles)
    assert result.field_confidence.get("vin", 0) < 0.9


def test_order_parser_output_json_is_serializable() -> None:
    agent = OrderParserAgent()
    payload = agent.parse("Pick up:\nToyota Yaris\nUtrecht\nDeliver:\nAntwerp").to_output_json()

    assert "field_confidence" in payload
    assert isinstance(payload["pickup_stops"], list)
    assert isinstance(payload["delivery_stops"], list)
