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


def test_order_parser_handles_dutch_belgian_transport_message() -> None:
    agent = OrderParserAgent()
    message = """
Klant: TransAuto BV
Ophalen 12/08/2026:
1x VW Golf - VIN WVWZZZ1KZAW123456
Den Haag, Laan van Meerdervoort 12
Aflevering 14/08/2026:
Bruxelles, Rue de la Loi 16
2x BMW X3
Antwerpen
"""
    result = agent.parse(message)

    assert result.customer_name == "TransAuto BV"
    assert len(result.pickup_stops) >= 1
    assert len(result.delivery_stops) >= 1
    assert len(result.vehicles) >= 2
    assert result.planned_pickup_date is not None
    assert result.planned_delivery_date is not None
    assert any(stop.city and "Bruxelles" in stop.city for stop in result.delivery_stops)


def test_order_parser_handles_french_transport_message() -> None:
    agent = OrderParserAgent()
    message = """
Client: LuxCar SA
Enlèvement:
Peugeot 308
Liège, Boulevard d'Avroy 5
Livraison:
Anvers
"""
    result = agent.parse(message)

    assert result.customer_name == "LuxCar SA"
    assert len(result.pickup_stops) >= 1
    assert len(result.delivery_stops) >= 1
    assert any(vehicle.make == "Peugeot" for vehicle in result.vehicles)


def test_order_parser_handles_dutch_ophaling_levering_message() -> None:
    agent = OrderParserAgent()
    message = """
Klant: Autosphere Brussels
Ophaling 05/08/2026:
1x Mercedes C-Klasse - VIN WDD2050471F123456
Adresse: Industrieweg 12, 9000 Gent
Levering 07/08/2026:
Adresse: Chaussée de Louvain 45, 1000 Bruxelles
"""
    result = agent.parse(message)

    assert result.customer_name == "Autosphere Brussels"
    assert len(result.pickup_stops) >= 1
    assert len(result.delivery_stops) >= 1
    assert len(result.vehicles) >= 1
    assert result.planned_pickup_date is not None
    assert result.planned_delivery_date is not None


def test_order_parser_handles_vin_only_message() -> None:
    agent = OrderParserAgent()
    vin_one = "WVWZZZ1KZAW123456"
    vin_two = "WDD2050471F123456"
    result = agent.parse(f"{vin_one}\n{vin_two}")

    assert len(result.vehicles) == 2
    assert {vehicle.vin for vehicle in result.vehicles} == {vin_one, vin_two}
    assert "vehicles" not in result.missing_fields


def test_order_parser_handles_address_only_message() -> None:
    agent = OrderParserAgent()
    message = """
Industrieweg 12, 9000 Gent
Chaussée de Louvain 45, 1000 Bruxelles
"""
    result = agent.parse(message)

    assert len(result.pickup_stops) >= 1
    assert len(result.delivery_stops) >= 1


def test_order_parser_handles_multiple_pickups_and_deliveries() -> None:
    agent = OrderParserAgent()
    message = """
Pick up:
BMW X5
Gent
Audi A4
Antwerpen
Deliver:
Toyota Yaris
Brussels
Peugeot 308
Liège
"""
    result = agent.parse(message)

    assert len(result.pickup_stops) >= 2
    assert len(result.delivery_stops) >= 2
    assert len(result.vehicles) >= 2


def test_order_parser_expands_vehicle_quantity_prefix() -> None:
    agent = OrderParserAgent()
    result = agent.parse("Pick up:\n3x BMW X3\nGent\nDeliver:\nBrussels")

    assert len(result.vehicles) == 3
    assert all(vehicle.make == "BMW" for vehicle in result.vehicles)
    assert all(vehicle.model == "X3" for vehicle in result.vehicles)


def test_order_parser_handles_mixed_language_message() -> None:
    agent = OrderParserAgent()
    message = """
Client: Euro Transport NV
Ophaling:
Renault Clio
Gent
Livraison:
Bruxelles
"""
    result = agent.parse(message)

    assert result.customer_name == "Euro Transport NV"
    assert len(result.pickup_stops) >= 1
    assert len(result.delivery_stops) >= 1
    assert any(vehicle.make == "Renault" for vehicle in result.vehicles)


WHATSAPP_DISPATCH_MESSAGE = """
Vlissingen zagruzko
2 ref nomer
31MGBE4985 + 31MGBE5029

1 adres vigruzke
Rijksweg 147
3650 Dilsen-Stokkem

2 cars

LSJWP4396TZ174225 MG3
LSJWP4U94TZ221556 MG3

2roi vigruzko
Rue de Sauheid 78
4032 Liège
"""


def test_order_parser_handles_whatsapp_dispatch_message() -> None:
    agent = OrderParserAgent()
    result = agent.parse(WHATSAPP_DISPATCH_MESSAGE)

    assert len(result.vehicles) == 2
    vins = {vehicle.vin for vehicle in result.vehicles}
    assert vins == {"LSJWP4396TZ174225", "LSJWP4U94TZ221556"}
    assert all(vehicle.model == "MG3" for vehicle in result.vehicles)
    assert all(vehicle.make == "MG" for vehicle in result.vehicles)
    assert len(result.pickup_stops) >= 1
    assert any("Vlissingen" in (stop.city or "") for stop in result.pickup_stops)
    assert any(
        "Dilsen" in (stop.city or "")
        and stop.address
        and "Rijksweg" in stop.address
        for stop in result.pickup_stops
    )
    assert len(result.delivery_stops) >= 1
    assert any("Liège" in (stop.city or "") or "Liege" in (stop.city or "") for stop in result.delivery_stops)
    assert not any("Dilsen" in (stop.city or "") for stop in result.delivery_stops)
    assert result.overall_confidence > 0
    assert "31MGBE4985" in (result.notes or "")
    assert "31MGBE5029" in (result.notes or "")
    assert result.reference_numbers == ["31MGBE4985", "31MGBE5029"]


def test_order_parser_does_not_crash_on_garbage_input() -> None:
    agent = OrderParserAgent()
    result = agent.parse("??? ### @@@ random noise without structure")

    assert isinstance(result.overall_confidence, float)
    assert result.overall_confidence >= 0
    assert isinstance(result.to_output_json()["vehicles"], list)
    assert isinstance(result.to_output_json()["pickup_stops"], list)
    assert isinstance(result.to_output_json()["delivery_stops"], list)


TABULAR_DISPATCH_MESSAGE = """
Location  Stock_ID  VIN  Model
Gent      ST001     WVWZZZ1KZAW123456  Golf
Gent      ST002     WDD2050471F123456  C-Klasse
Gent      ST003     1HGBH41JXMN109186  Accord
Gent      ST004     LSJWP4396TZ174225  MG3
Gent      ST005     LSJWP4U94TZ221556  MG3
Gent      ST006     WBAFR9C50BC123456  X5
Gent      ST007     JM1BL1SF7A1234567  Mazda3
"""


def test_order_parser_handles_tabular_vin_list() -> None:
    agent = OrderParserAgent()
    result = agent.parse(TABULAR_DISPATCH_MESSAGE)

    assert len(result.vehicles) == 7
    vins = {vehicle.vin for vehicle in result.vehicles}
    assert "WVWZZZ1KZAW123456" in vins
    assert "JM1BL1SF7A1234567" in vins
    assert any(stop.city == "Gent" for stop in result.pickup_stops)
    assert result.field_confidence.get("vin", 0) > 0
    assert isinstance(result.overall_confidence, float)
    assert result.overall_confidence > 0


AUTOHERO_SINGLE_ROW = (
    "Wanze AS19517 6FPPXXMJ2PPL53082 Ford Ranger 3.0 EcoBlue 2FOA296 8100-20260814-507"
)

AUTOHERO_MULTI_ROW_MESSAGE = """
Wanze AS19517 6FPPXXMJ2PPL53082 Ford Ranger 3.0 EcoBlue 2FOA296 8100-20260814-507
Wanze AS19518 6FPPXXMJ2PPL53083 Ford Ranger 3.0 EcoBlue 2FOA297 8100-20260814-508
Gent AS19519 1HGBH41JXMN109186 Honda Civic 1.5 Turbo 1ABC123 8100-20260815-509

Delivery: Brussels
"""


def test_order_parser_handles_autohero_single_stock_row() -> None:
    agent = OrderParserAgent()
    result = agent.parse(AUTOHERO_SINGLE_ROW)

    assert len(result.vehicles) == 1
    vehicle = result.vehicles[0]
    assert vehicle.vin == "6FPPXXMJ2PPL53082"
    assert vehicle.make == "Ford"
    assert vehicle.model == "Ranger 3.0 EcoBlue"
    assert vehicle.notes is not None
    assert "AS19517" in vehicle.notes
    assert "2FOA296" in vehicle.notes
    assert any(stop.city == "Wanze" for stop in result.pickup_stops)
    assert result.reference_numbers == ["8100-20260814-507"]
    assert result.field_confidence.get("make", 0) >= 0.9
    assert result.field_confidence.get("model", 0) >= 0.9
    assert result.field_confidence.get("autohero_stock", 0) >= 0.95
    assert isinstance(result.overall_confidence, float)
    assert result.overall_confidence > 0.85


def test_order_parser_handles_autohero_multi_row_stock_list() -> None:
    agent = OrderParserAgent()
    result = agent.parse(AUTOHERO_MULTI_ROW_MESSAGE)

    assert len(result.vehicles) == 3
    assert {vehicle.vin for vehicle in result.vehicles} == {
        "6FPPXXMJ2PPL53082",
        "6FPPXXMJ2PPL53083",
        "1HGBH41JXMN109186",
    }
    assert all(vehicle.make for vehicle in result.vehicles)
    assert all(vehicle.model for vehicle in result.vehicles)
    assert any(stop.city == "Wanze" for stop in result.pickup_stops)
    assert any(stop.city == "Brussels" for stop in result.delivery_stops)
    assert result.reference_numbers == [
        "8100-20260814-507",
        "8100-20260814-508",
        "8100-20260815-509",
    ]
    assert result.overall_confidence > 0.85
