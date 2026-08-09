"""Order Parser Agent — deterministic extraction with confidence scores."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime

from app.common.enums import StopType
from app.orders.schemas import OrderStopCreateRequest, OrderVehicleCreateRequest

PROMPT_VERSION = "v1"
MODEL_VERSION = "prodrive-heuristic-parser-1.0"

VEHICLE_LINE_PATTERN = re.compile(
    r"^\s*(?:\d+[\).:-]\s*)?([A-Za-z]+(?:\s+[A-Za-z0-9.-]+)+)\s*$"
)
SECTION_PATTERN = re.compile(
    r"(?is)(pick\s*up|pickup|collection)\s*:?\s*(.*?)(deliver|delivery|drop\s*off|$)"
)
VIN_PATTERN = re.compile(r"\b([A-HJ-NPR-Z0-9]{17})\b", re.IGNORECASE)
DATE_PATTERN = re.compile(r"\b(\d{4}-\d{2}-\d{2}|\d{1,2}[./-]\d{1,2}[./-]\d{2,4})\b")
CUSTOMER_PATTERN = re.compile(
    r"(?is)(?:customer|client|from)\s*:?\s*([^\n\r]{2,80})"
)


@dataclass
class OrderParserResult:
    """Structured parser output with per-field confidence."""

    customer_name: str | None = None
    pickup_stops: list[OrderStopCreateRequest] = field(default_factory=list)
    delivery_stops: list[OrderStopCreateRequest] = field(default_factory=list)
    vehicles: list[OrderVehicleCreateRequest] = field(default_factory=list)
    planned_pickup_date: date | None = None
    planned_delivery_date: date | None = None
    notes: str | None = None
    missing_fields: list[str] = field(default_factory=list)
    field_confidence: dict[str, float] = field(default_factory=dict)
    overall_confidence: float = 0.0

    def to_output_json(self) -> dict[str, object]:
        return {
            "customer_name": self.customer_name,
            "pickup_stops": [stop.model_dump(mode="json") for stop in self.pickup_stops],
            "delivery_stops": [stop.model_dump(mode="json") for stop in self.delivery_stops],
            "vehicles": [vehicle.model_dump(mode="json") for vehicle in self.vehicles],
            "planned_pickup_date": (
                self.planned_pickup_date.isoformat() if self.planned_pickup_date else None
            ),
            "planned_delivery_date": (
                self.planned_delivery_date.isoformat() if self.planned_delivery_date else None
            ),
            "notes": self.notes,
            "missing_fields": self.missing_fields,
            "field_confidence": self.field_confidence,
            "overall_confidence": self.overall_confidence,
        }


class OrderParserAgent:
    """Extract structured order drafts from unstructured text."""

    prompt_version = PROMPT_VERSION
    model_version = MODEL_VERSION

    def parse(self, message: str) -> OrderParserResult:
        """Parse customer message into structured suggestion output."""
        normalized = message.strip()
        result = OrderParserResult()

        customer_match = CUSTOMER_PATTERN.search(normalized)
        if customer_match:
            result.customer_name = customer_match.group(1).strip()
            result.field_confidence["customer_name"] = 0.98
        else:
            result.field_confidence["customer_name"] = 0.2

        section_match = SECTION_PATTERN.search(normalized)
        if section_match:
            pickup_text = section_match.group(2)
            delivery_text = normalized[section_match.end(2) :]
            result.pickup_stops = self._extract_stops(pickup_text, StopType.PICKUP)
            result.delivery_stops = self._extract_stops(delivery_text, StopType.DELIVERY)
            result.vehicles = self._extract_vehicles(pickup_text)
            result.field_confidence["pickup"] = 0.94 if result.pickup_stops else 0.25
            result.field_confidence["delivery"] = 0.92 if result.delivery_stops else 0.25
            result.field_confidence["vehicles"] = 0.88 if result.vehicles else 0.3
        else:
            result.field_confidence["pickup"] = 0.15
            result.field_confidence["delivery"] = 0.15
            result.field_confidence["vehicles"] = 0.15

        vins = VIN_PATTERN.findall(normalized)
        if vins:
            updated_vehicles: list[OrderVehicleCreateRequest] = []
            for index, vehicle in enumerate(result.vehicles):
                vin = vins[index].upper() if index < len(vins) else vehicle.vin
                updated_vehicles.append(vehicle.model_copy(update={"vin": vin}))
            for index in range(len(result.vehicles), len(vins)):
                updated_vehicles.append(OrderVehicleCreateRequest(vin=vins[index].upper()))
            result.vehicles = updated_vehicles
            result.field_confidence["vin"] = 0.61 if len(vins) == 1 else 0.75
        else:
            result.field_confidence["vin"] = 0.1

        dates = DATE_PATTERN.findall(normalized)
        if dates:
            parsed_dates = [self._parse_date(value) for value in dates]
            parsed_dates = [value for value in parsed_dates if value is not None]
            if parsed_dates:
                result.planned_pickup_date = parsed_dates[0]
                result.field_confidence["planned_pickup_date"] = 0.72
            if len(parsed_dates) > 1:
                result.planned_delivery_date = parsed_dates[1]
                result.field_confidence["planned_delivery_date"] = 0.68
        else:
            result.field_confidence["planned_pickup_date"] = 0.1
            result.field_confidence["planned_delivery_date"] = 0.1

        if len(normalized) > 120:
            result.notes = normalized[:500]
            result.field_confidence["notes"] = 0.7

        if not result.pickup_stops:
            result.missing_fields.append("pickup_stops")
        if not result.delivery_stops:
            result.missing_fields.append("delivery_stops")
        if not result.vehicles:
            result.missing_fields.append("vehicles")

        confidences = [value for value in result.field_confidence.values() if value > 0]
        result.overall_confidence = round(sum(confidences) / len(confidences), 2) if confidences else 0.1
        return result

    def _extract_stops(self, text: str, stop_type: StopType) -> list[OrderStopCreateRequest]:
        stops: list[OrderStopCreateRequest] = []
        sequence = 1
        for line in [item.strip() for item in text.splitlines() if item.strip()]:
            if VIN_PATTERN.search(line):
                continue
            vehicle_match = VEHICLE_LINE_PATTERN.match(line)
            if vehicle_match and not self._looks_like_location(line):
                continue
            if self._looks_like_location(line):
                stops.append(
                    OrderStopCreateRequest(
                        stop_type=stop_type,
                        sequence=sequence,
                        city=line,
                    )
                )
                sequence += 1
        return stops

    def _extract_vehicles(self, text: str) -> list[OrderVehicleCreateRequest]:
        vehicles: list[OrderVehicleCreateRequest] = []
        for line in [item.strip() for item in text.splitlines() if item.strip()]:
            vehicle_match = VEHICLE_LINE_PATTERN.match(line)
            if vehicle_match and not self._looks_like_location(line):
                parts = vehicle_match.group(1).split(maxsplit=1)
                vehicles.append(
                    OrderVehicleCreateRequest(
                        make=parts[0],
                        model=parts[1] if len(parts) > 1 else None,
                    )
                )
        return vehicles

    @staticmethod
    def _looks_like_location(line: str) -> bool:
        normalized = line.strip()
        if len(normalized.split()) == 1 and normalized[0].isalpha():
            return True
        location_keywords = {"street", "str", "road", "rd", "avenue", "ave", "city"}
        lowered = normalized.lower()
        return any(keyword in lowered for keyword in location_keywords)

    @staticmethod
    def _parse_date(value: str) -> date | None:
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"):
            try:
                if fmt == "%Y-%m-%d":
                    return date.fromisoformat(value)
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
        return None
