"""Unit tests for CMR vehicle identifier parsing and row rendering."""

from app.cmr.generator import (
    CmrContext,
    CmrVehicleRow,
    _parse_vehicle_identifiers,
    _stock_id_lines,
    _vehicle_remark_from_notes,
    _vin_lines,
)


def test_parse_vehicle_identifiers_from_notes() -> None:
    stock_id, plate = _parse_vehicle_identifiers(
        "Stock ID: HN60935\nLicense plate: 1WST863"
    )
    assert stock_id == "HN60935"
    assert plate == "1WST863"


def test_stock_id_lines_include_stock_id_and_plate_per_vehicle() -> None:
    context = CmrContext(
        order_number="ORD-100",
        vehicle_count=2,
        vehicles=[
            CmrVehicleRow(
                stock_id="HN60935",
                make="Renault",
                model="Trafic 1.9 Diesel",
                vin="VF1FLACA66Y130037",
                license_plate="1WST863",
            ),
            CmrVehicleRow(
                stock_id="HN60936",
                make="Peugeot",
                model="208",
                vin="VF3XXXXXXXXXXXXXX",
                license_plate="1ABC123",
            ),
        ],
    )

    stock_lines = _stock_id_lines(context)
    vin_lines = _vin_lines(context)

    assert "HN60935" in stock_lines
    assert "1WST863" in stock_lines
    assert "HN60936" in stock_lines
    assert "31MGBE4985" not in stock_lines
    assert "VF1FLACA66Y130037" in vin_lines
    assert "VF3XXXXXXXXXXXXXX" in vin_lines


def test_vehicle_remark_from_notes_excludes_internal_metadata() -> None:
    assert _vehicle_remark_from_notes("Stock ID: HN60935\nLicense plate: 1WST863") == ""
    assert (
        _vehicle_remark_from_notes(
            "Handle with care\nStock ID: HN60935\nLicense plate: 1WST863"
        )
        == "Handle with care"
    )
    assert _vehicle_remark_from_notes("VIN: VF1FLACA66Y130037") == ""
    assert _vehicle_remark_from_notes("Driver note: keys in glovebox") == "Driver note: keys in glovebox"
