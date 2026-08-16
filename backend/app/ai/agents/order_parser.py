"""Order Parser Agent — Belgian transport heuristic extraction with confidence scores."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime

from app.common.enums import StopType
from app.orders.schemas import OrderStopCreateRequest, OrderVehicleCreateRequest
from app.orders.validators import MAX_ORDER_VEHICLES

PROMPT_VERSION = "v2"
MODEL_VERSION = "prodrive-heuristic-parser-2.1-mixed-logistics"

VIN_PATTERN = re.compile(r"\b([A-HJ-NPR-Z0-9]{17})\b", re.IGNORECASE)
VIN_FIRST_LINE = re.compile(
    r"^\s*([A-HJ-NPR-Z0-9]{17})\s*(.*?)\s*$",
    re.IGNORECASE,
)
REF_NUMBER_PATTERN = re.compile(
    r"\b(\d{2}[A-Z]{2,6}\d{3,6})\b",
    re.IGNORECASE,
)
AUTOHERO_REFERENCE_PATTERN = re.compile(r"\b(\d{4}-\d{8}-\d{3})\b")
AUTOHERO_STOCK_ID_PATTERN = re.compile(r"\b([A-Z]{2}\d{5})\b")
AUTOHERO_ROW_PREFIX_PATTERN = re.compile(
    r"^\s*"
    r"(?P<pickup_city>[A-Za-zÀ-ÿ][\w\-]*)\s+"
    r"(?P<stock_id>[A-Z]{2}\d{5})\s+"
    r"(?P<vin>[A-HJ-NPR-Z0-9]{17})\s+"
    r"(?P<remainder>.+)$",
    re.IGNORECASE,
)
VEHICLE_COUNT_LINE = re.compile(
    r"(?is)^\s*(\d+)\s*(?:cars?|voertuigen?|auto(?:s)?|wagen|vehicles?)\s*$",
)
LOGISTICS_KEYWORD = re.compile(
    r"(?is)\b("
    r"zagruzko|zagruzka|zagruska|vigruzke|vigruzko|vygruzk[ae]|"
    r"ref(?:erence)?(?:\s*(?:nomer|nummer|number|nr|no))?|adres\s+vigruz"
    r")\b",
)
PICKUP_LOCATION_LINE = re.compile(
    r"(?is)^\s*([A-Za-zÀ-ÿ][\w\- ]+?)\s+"
    r"(?:zagruzko|zagruzka|zagruska|loading|laden|ophalen|ophaling|afhalen)\s*$",
)
DELIVERY_SECTION_START = re.compile(
    r"(?im)^\s*(?:\d+\s*(?:roi|ro[iy]|ème|e|er|de|ste)?\s*)?"
    r"(?:adres\s+)?(?:vigruzke|vigruzko|vygruzk[ae]|vigruz|vygruz|unload|unloading|aflever|livraison|delivery|levering)\b",
)
DATE_PATTERN = re.compile(
    r"\b(\d{4}-\d{2}-\d{2}|\d{1,2}[./-]\d{1,2}[./-]\d{2,4})\b"
)
POSTCODE_PATTERN = re.compile(r"\b(?:B-)?(\d{4})\b", re.IGNORECASE)
CUSTOMER_PATTERN = re.compile(
    r"(?is)(?:customer|client|klant|opdrachtgever|maatschappij|transport\s+voor|opdracht|from)\s*:?\s*([^\n\r]{2,120})"
)
VEHICLE_LINE_PATTERN = re.compile(
    r"^\s*(?:\d+\s*[x×]\s*|\d+[\).:-]\s*|-\s*)?"
    r"(?:voertuig\s*:?\s*)?"
    r"([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9.\-/ ]{1,60}?)"
    r"(?:\s*[-–—]\s*(?:VIN\s*)?([A-HJ-NPR-Z0-9]{17}))?\s*$",
    re.IGNORECASE,
)
VEHICLE_COUNT_PREFIX = re.compile(r"^\s*(\d+)\s*[x×]\s*", re.IGNORECASE)
PICKUP_HEADER = re.compile(
    r"(?is)\b("
    r"pick\s*up|pickup|collection|ophalen|ophaling|afhalen|afhaal(?:adres)?|lading|laden|"
    r"chargement|enl[èe]vement|loading|loading\s+address|collection\s+point|"
    r"zagruzko|zagruzka|zagruska"
    r")\b"
)
DELIVERY_HEADER = re.compile(
    r"(?is)\b("
    r"deliver(?:y|ies)?|drop\s*off|aflevering|aflever(?:adres)?|livraison|levering|"
    r"lossing|unload|unloading|delivery\s+address|"
    r"vigruzke|vigruzko|vygruzk[ae]|adres\s+vigruz"
    r")\b"
)
STREET_KEYWORDS = {
    "street",
    "str",
    "straat",
    "ste",
    "road",
    "rd",
    "weg",
    "laan",
    "avenue",
    "av",
    "av.",
    "rue",
    "chaussée",
    "chaussee",
    "boulevard",
    "blvd",
    "place",
    "plein",
    "markt",
    "square",
}
KNOWN_CITIES = {
    "brussels",
    "bruxelles",
    "brussel",
    "anvers",
    "antwerp",
    "antwerpen",
    "ghent",
    "gent",
    "gand",
    "liège",
    "liege",
    "luik",
    "charleroi",
    "bruges",
    "brugge",
    "namur",
    "namen",
    "leuven",
    "louvain",
    "mechelen",
    "malines",
    "mons",
    "bergen",
    "hasselt",
    "kortrijk",
    "courtrai",
    "ostend",
    "oostende",
    "ostende",
    "genk",
    "turnhout",
    "roeselare",
    "aalst",
    "mouscron",
    "moeskroen",
    "verviers",
    "sint-niklaas",
    "den haag",
    "the hague",
    "rotterdam",
    "amsterdam",
    "utrecht",
    "eindhoven",
    "paris",
    "lille",
    "luxembourg",
    "vlissingen",
    "dilsen-stokkem",
    "dilsen",
    "stokkem",
}
DUTCH_CITIES = {
    "vlissingen",
    "rotterdam",
    "amsterdam",
    "utrecht",
    "eindhoven",
    "den haag",
    "the hague",
}
VEHICLE_PREFIXES = {
    "bmw",
    "mercedes",
    "mercedes-benz",
    "audi",
    "vw",
    "volkswagen",
    "volvo",
    "peugeot",
    "renault",
    "citroen",
    "citroën",
    "ford",
    "opel",
    "toyota",
    "skoda",
    "seat",
    "porsche",
    "jaguar",
    "land",
    "range",
    "mini",
    "fiat",
    "dacia",
    "tesla",
    "mb",
    "mg",
}
TABULAR_HEADER_PATTERN = re.compile(
    r"(?i)\b(location|locatie|pickup|stock[_\s-]?id|vin|model|make|merk)\b"
)
TABULAR_COLUMN_ALIASES: dict[str, tuple[str, ...]] = {
    "location": ("location", "locatie", "pickup", "pick up", "pick-up", "ophalen", "laden"),
    "stock_id": ("stock_id", "stock id", "stockid", "stock", "ref", "reference"),
    "vin": ("vin", "chassis", "chassisnummer"),
    "model": ("model", "type", "vehicle"),
    "make": ("make", "merk", "brand", "fabrikant"),
}


@dataclass
class TabularVehicleParse:
    """Vehicles and optional pickup location from a tabular paste."""

    vehicles: list[OrderVehicleCreateRequest] = field(default_factory=list)
    pickup_location: str | None = None


@dataclass
class AutoheroStockRow:
    """Single Autohero stock-list row."""

    pickup_city: str
    stock_id: str
    vin: str
    make: str
    model: str | None
    license_plate: str
    reference: str


@dataclass
class AutoheroStockParse:
    """Vehicles and metadata from Autohero stock-list rows."""

    vehicles: list[OrderVehicleCreateRequest] = field(default_factory=list)
    pickup_location: str | None = None
    reference_numbers: list[str] = field(default_factory=list)
    rows_parsed: int = 0
    rows_complete: int = 0


@dataclass
class OrderParserResult:
    """Structured parser output with per-field confidence."""

    customer_name: str | None = None
    pickup_stops: list[OrderStopCreateRequest] = field(default_factory=list)
    delivery_stops: list[OrderStopCreateRequest] = field(default_factory=list)
    vehicles: list[OrderVehicleCreateRequest] = field(default_factory=list)
    planned_pickup_date: date | None = None
    planned_delivery_date: date | None = None
    reference_numbers: list[str] = field(default_factory=list)
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
            "reference_numbers": self.reference_numbers,
            "notes": self.notes,
            "missing_fields": self.missing_fields,
            "field_confidence": self.field_confidence,
            "overall_confidence": self.overall_confidence,
        }


class OrderParserAgent:
    """Extract structured order drafts from unstructured Belgian transport messages."""

    prompt_version = PROMPT_VERSION
    model_version = MODEL_VERSION

    def parse(self, message: str) -> OrderParserResult:
        """Parse customer message into structured suggestion output."""
        normalized = message.strip()
        result = OrderParserResult()

        try:
            self._populate_parse_result(result, normalized)
        except Exception:
            result.vehicles = self._safe_extract_vins_as_vehicles(normalized)
            result.field_confidence["vehicles"] = 0.35 if result.vehicles else 0.1
            result.field_confidence["vin"] = 0.5 if result.vehicles else 0.1
            if not result.notes and normalized:
                result.notes = normalized[:500]

        if not result.pickup_stops:
            result.missing_fields.append("pickup_stops")
        if not result.delivery_stops:
            result.missing_fields.append("delivery_stops")
        if not result.vehicles:
            result.missing_fields.append("vehicles")

        confidences = [value for value in result.field_confidence.values() if value > 0]
        result.overall_confidence = round(sum(confidences) / len(confidences), 2) if confidences else 0.1

        autohero_score = result.field_confidence.get("autohero_stock")
        if autohero_score is not None and autohero_score >= 0.98:
            autohero_fields = (
                "autohero_stock",
                "vehicles",
                "vin",
                "make",
                "model",
                "pickup",
                "reference_numbers",
            )
            focused = [
                result.field_confidence[field]
                for field in autohero_fields
                if result.field_confidence.get(field, 0) > 0
            ]
            if focused:
                result.overall_confidence = round(sum(focused) / len(focused), 2)

        return result

    def _populate_parse_result(self, result: OrderParserResult, normalized: str) -> None:
        customer_match = CUSTOMER_PATTERN.search(normalized)
        if customer_match:
            result.customer_name = customer_match.group(1).strip().strip("-–—,")
            result.field_confidence["customer_name"] = 0.96
        else:
            result.field_confidence["customer_name"] = 0.2

        pickup_text, delivery_text = self._split_sections(normalized)
        result.pickup_stops = self._extract_stops(pickup_text, StopType.PICKUP)
        result.delivery_stops = self._extract_stops(delivery_text, StopType.DELIVERY)

        tabular = self._extract_tabular_vehicles(normalized)
        autohero = self._parse_autohero_stock_rows(normalized)
        autohero_parsed = bool(autohero.vehicles)
        if autohero.vehicles:
            result.vehicles = autohero.vehicles
            if autohero.pickup_location:
                city = autohero.pickup_location.strip()
                has_pickup_city = any(
                    (stop.city or "").strip().lower() == city.lower()
                    for stop in result.pickup_stops
                )
                if not has_pickup_city:
                    pickup_stop = OrderStopCreateRequest(
                        stop_type=StopType.PICKUP,
                        sequence=len(result.pickup_stops) + 1,
                        city=city,
                        country=self._country_for_city(city),
                    )
                    result.pickup_stops = [pickup_stop, *result.pickup_stops]
            if autohero.reference_numbers:
                result.reference_numbers = autohero.reference_numbers
                ref_note = f"Reference numbers: {', '.join(autohero.reference_numbers)}"
                result.notes = ref_note if not result.notes else f"{ref_note}\n{result.notes}"
                result.field_confidence["reference_numbers"] = 0.94
            completeness = (
                autohero.rows_complete / autohero.rows_parsed if autohero.rows_parsed else 0.0
            )
            result.field_confidence["vehicles"] = 0.94 if completeness >= 1.0 else 0.88
            result.field_confidence["vin"] = 0.96 if completeness >= 1.0 else 0.9
            result.field_confidence["make"] = 0.93 if completeness >= 1.0 else 0.85
            result.field_confidence["model"] = 0.93 if completeness >= 1.0 else 0.85
            result.field_confidence["autohero_stock"] = round(0.88 + 0.1 * completeness, 2)
        elif tabular.vehicles:
            result.vehicles = tabular.vehicles
            if tabular.pickup_location:
                city = tabular.pickup_location.strip()
                has_pickup_city = any(
                    (stop.city or "").strip().lower() == city.lower()
                    for stop in result.pickup_stops
                )
                if not has_pickup_city:
                    pickup_stop = OrderStopCreateRequest(
                        stop_type=StopType.PICKUP,
                        sequence=len(result.pickup_stops) + 1,
                        city=city,
                        country=self._country_for_city(city),
                    )
                    result.pickup_stops = [pickup_stop, *result.pickup_stops]
        else:
            result.vehicles = self._extract_vehicles(normalized)

        result.field_confidence["pickup"] = 0.92 if result.pickup_stops else 0.25
        result.field_confidence["delivery"] = 0.9 if result.delivery_stops else 0.25
        if not autohero_parsed:
            result.field_confidence["vehicles"] = 0.86 if result.vehicles else 0.3

        vins = [value.upper() for value in VIN_PATTERN.findall(normalized)]
        if vins:
            result.vehicles = self._merge_vins_into_vehicles(result.vehicles, vins)
            if not autohero_parsed:
                result.field_confidence["vin"] = 0.78 if len(vins) == 1 else 0.84
        elif not autohero_parsed:
            result.field_confidence["vin"] = 0.1

        expected_count = self._extract_vehicle_count(normalized)
        if expected_count and not autohero_parsed:
            result.vehicles = self._normalize_vehicle_count(result.vehicles, expected_count, vins)

        reference_numbers = self._extract_reference_numbers(normalized)
        if reference_numbers and not autohero_parsed:
            result.reference_numbers = reference_numbers
            ref_note = f"Reference numbers: {', '.join(reference_numbers)}"
            result.notes = ref_note if not result.notes else f"{ref_note}\n{result.notes}"
            result.field_confidence["reference_numbers"] = 0.82

        pickup_date, delivery_date = self._extract_dates(normalized, pickup_text, delivery_text)
        result.planned_pickup_date = pickup_date
        result.planned_delivery_date = delivery_date
        result.field_confidence["planned_pickup_date"] = 0.78 if pickup_date else 0.1
        result.field_confidence["planned_delivery_date"] = 0.76 if delivery_date else 0.1

        if len(normalized) > 120 and not result.notes:
            result.notes = normalized[:500]
            result.field_confidence["notes"] = 0.7

        self._balance_unsectioned_stops(result)

    @staticmethod
    def _safe_extract_vins_as_vehicles(message: str) -> list[OrderVehicleCreateRequest]:
        return [
            OrderVehicleCreateRequest(vin=vin)
            for vin in dict.fromkeys(value.upper() for value in VIN_PATTERN.findall(message))
        ][:MAX_ORDER_VEHICLES]

    @staticmethod
    def _extract_reference_numbers(message: str) -> list[str]:
        refs: list[str] = []
        seen: set[str] = set()
        for pattern in (AUTOHERO_REFERENCE_PATTERN, REF_NUMBER_PATTERN):
            for match in pattern.finditer(message):
                value = match.group(1).upper()
                if value in seen:
                    continue
                seen.add(value)
                refs.append(value)
        return refs

    @staticmethod
    def _extract_vehicle_count(message: str) -> int | None:
        match = VEHICLE_COUNT_LINE.search(message)
        if match:
            return min(int(match.group(1)), MAX_ORDER_VEHICLES)
        return None

    @staticmethod
    def _merge_vins_into_vehicles(
        vehicles: list[OrderVehicleCreateRequest],
        vins: list[str],
    ) -> list[OrderVehicleCreateRequest]:
        if not vins:
            return vehicles[:MAX_ORDER_VEHICLES]

        if not vehicles:
            return [OrderVehicleCreateRequest(vin=vin) for vin in vins[:MAX_ORDER_VEHICLES]]

        merged: list[OrderVehicleCreateRequest] = []
        vin_queue = list(vins)
        for vehicle in vehicles:
            vin = vehicle.vin
            if not vin and vin_queue:
                vin = vin_queue.pop(0)
            merged.append(vehicle.model_copy(update={"vin": vin}) if vin else vehicle)

        used_vins = {vehicle.vin for vehicle in merged if vehicle.vin}
        for vin in vins:
            if vin in used_vins:
                continue
            if len(merged) >= MAX_ORDER_VEHICLES:
                break
            merged.append(OrderVehicleCreateRequest(vin=vin))
            used_vins.add(vin)

        return merged[:MAX_ORDER_VEHICLES]

    @staticmethod
    def _normalize_vehicle_count(
        vehicles: list[OrderVehicleCreateRequest],
        expected_count: int,
        vins: list[str],
    ) -> list[OrderVehicleCreateRequest]:
        if expected_count <= 0:
            return vehicles

        if len(vehicles) > expected_count:
            return vehicles[:expected_count]

        expanded = list(vehicles)
        used_vins = {vehicle.vin for vehicle in expanded if vehicle.vin}
        vin_iter = iter(vin for vin in vins if vin not in used_vins)
        while len(expanded) < expected_count and len(expanded) < MAX_ORDER_VEHICLES:
            next_vin = next(vin_iter, None)
            expanded.append(OrderVehicleCreateRequest(vin=next_vin))
        return expanded

    def _balance_unsectioned_stops(self, result: OrderParserResult) -> None:
        """Move the last pickup stop to delivery when no delivery section was detected."""
        if result.delivery_stops or len(result.pickup_stops) < 2:
            return

        last_stop = result.pickup_stops.pop()
        delivery_stop = last_stop.model_copy(
            update={"stop_type": StopType.DELIVERY, "sequence": 1},
        )
        result.delivery_stops = [delivery_stop]
        for index, stop in enumerate(result.pickup_stops, start=1):
            result.pickup_stops[index - 1] = stop.model_copy(update={"sequence": index})

        if result.field_confidence.get("delivery", 0) <= 0.25:
            result.field_confidence["delivery"] = 0.75
        if result.field_confidence.get("pickup", 0) <= 0.25 and result.pickup_stops:
            result.field_confidence["pickup"] = 0.7

    @staticmethod
    def _vehicle_content_end(message: str) -> int:
        """Return the end index of the last VIN or explicit vehicle-count line."""
        end = 0
        for match in VIN_PATTERN.finditer(message):
            end = max(end, match.end())
        count_match = VEHICLE_COUNT_LINE.search(message)
        if count_match:
            end = max(end, count_match.end())
        return end

    @staticmethod
    def _delivery_split_index(message: str, delivery_markers: list[re.Match[str]]) -> int:
        """Prefer the delivery header that appears after vehicle lines (e.g. 2roi vigruzko)."""
        if not delivery_markers:
            return len(message)

        vehicle_end = OrderParserAgent._vehicle_content_end(message)
        post_vehicle = [marker for marker in delivery_markers if marker.start() >= vehicle_end]
        if post_vehicle:
            return post_vehicle[0].start()
        return delivery_markers[-1].start()

    def _split_sections(self, message: str) -> tuple[str, str]:
        delivery_markers = list(DELIVERY_SECTION_START.finditer(message))
        first_line = next((line.strip() for line in message.splitlines() if line.strip()), "")
        if PICKUP_LOCATION_LINE.match(first_line) and delivery_markers:
            split_at = self._delivery_split_index(message, delivery_markers)
            return message[:split_at].strip(), message[split_at:].strip()

        pickup_match = PICKUP_HEADER.search(message)
        delivery_match = DELIVERY_HEADER.search(message)

        if pickup_match and delivery_match and delivery_match.start() > pickup_match.start():
            if PICKUP_LOCATION_LINE.match(first_line):
                pickup_text = message[: delivery_match.start()]
            else:
                pickup_text = message[pickup_match.end() : delivery_match.start()]
            delivery_text = message[delivery_match.end() :]
            return pickup_text.strip(), delivery_text.strip()

        if pickup_match:
            pickup_text = message[pickup_match.end() :]
            if delivery_match and delivery_match.start() > pickup_match.start():
                return pickup_text[: delivery_match.start() - pickup_match.end()], message[delivery_match.end() :]
            return pickup_text.strip(), ""

        if delivery_markers:
            split_at = self._delivery_split_index(message, delivery_markers)
            return message[:split_at].strip(), message[split_at:].strip()

        if delivery_match and not pickup_match:
            return message[: delivery_match.start()].strip(), message[delivery_match.start() :].strip()

        english_match = re.search(
            r"(?is)(pick\s*up|pickup|collection)\s*:?\s*(.*?)(deliver|delivery|drop\s*off|$)",
            message,
        )
        if english_match:
            return english_match.group(2).strip(), message[english_match.end(2) :].strip()

        route_match = re.search(
            r"(?is)(?:van|from)\s*:?\s*(.+?)\s*(?:naar|to|→|->)\s*(.+)",
            message,
        )
        if route_match:
            return route_match.group(1).strip(), route_match.group(2).strip()

        return message, ""

    def _extract_stops(self, text: str, stop_type: StopType) -> list[OrderStopCreateRequest]:
        lines = [
            raw_line.strip(" \t-•*")
            for raw_line in text.splitlines()
            if raw_line.strip(" \t-•*")
        ]
        stops: list[OrderStopCreateRequest] = []
        index = 0

        while index < len(lines):
            line = lines[index]
            if self._is_noise_line(line):
                index += 1
                continue

            pickup_match = (
                stop_type == StopType.PICKUP and PICKUP_LOCATION_LINE.match(line)
            )
            if pickup_match:
                city = pickup_match.group(1).strip()
                stops.append(
                    OrderStopCreateRequest(
                        stop_type=stop_type,
                        sequence=len(stops) + 1,
                        city=city,
                        country=self._country_for_city(city),
                    )
                )
                index += 1
                continue

            if self._looks_like_vehicle(line):
                index += 1
                continue

            if DELIVERY_SECTION_START.match(line):
                header_stop = self._parse_location_line(line, stop_type, len(stops) + 1)
                if header_stop is not None:
                    stops.append(header_stop)
                index += 1
                continue

            if (
                index + 1 < len(lines)
                and self._looks_like_street(line)
                and not POSTCODE_PATTERN.search(line)
                and POSTCODE_PATTERN.search(lines[index + 1])
                and not self._looks_like_vehicle(lines[index + 1])
            ):
                stop = self._parse_address_block(line, lines[index + 1], stop_type, len(stops) + 1)
                if stop is not None:
                    stops.append(stop)
                index += 2
                continue

            stop = self._parse_location_line(line, stop_type, len(stops) + 1)
            if stop is not None:
                stops.append(stop)
            index += 1

        return stops

    def _parse_address_block(
        self,
        street_line: str,
        postcode_line: str,
        stop_type: StopType,
        sequence: int,
    ) -> OrderStopCreateRequest | None:
        postcode_match = POSTCODE_PATTERN.search(postcode_line)
        if not postcode_match:
            return None

        postal_code = postcode_match.group(1)
        city = postcode_line[postcode_match.end() :].strip(" ,-") or postcode_line.strip()
        if not city:
            city = street_line

        return OrderStopCreateRequest(
            stop_type=stop_type,
            sequence=sequence,
            city=city,
            address=street_line.strip(),
            postal_code=postal_code,
            country=self._country_for_city(city),
        )

    def _extract_vehicles(self, full_message: str) -> list[OrderVehicleCreateRequest]:
        vehicles: list[OrderVehicleCreateRequest] = []
        seen_vins: set[str] = set()
        for line in full_message.splitlines():
            for vehicle in self._parse_vehicle_line(line):
                if vehicle.vin:
                    vin_key = vehicle.vin.upper()
                    if vin_key in seen_vins:
                        continue
                    seen_vins.add(vin_key)
                vehicles.append(vehicle)
                if len(vehicles) >= MAX_ORDER_VEHICLES:
                    return vehicles
        return vehicles

    def _extract_tabular_vehicles(self, full_message: str) -> TabularVehicleParse:
        lines = [line.strip() for line in full_message.splitlines() if line.strip()]
        if len(lines) < 2:
            return TabularVehicleParse()

        header_index = -1
        column_map: dict[str, int] = {}
        for index, line in enumerate(lines):
            if not TABULAR_HEADER_PATTERN.search(line):
                continue
            columns = self._split_tabular_columns(line)
            if len(columns) < 2:
                continue
            mapped = self._map_tabular_columns(columns)
            if "vin" not in mapped:
                continue
            header_index = index
            column_map = mapped
            break

        if header_index < 0:
            return TabularVehicleParse()

        vehicles: list[OrderVehicleCreateRequest] = []
        seen_vins: set[str] = set()
        pickup_location: str | None = None

        for line in lines[header_index + 1 :]:
            if self._is_noise_line(line) or DELIVERY_SECTION_START.match(line):
                break
            if TABULAR_HEADER_PATTERN.fullmatch(line.replace("_", " ")):
                continue

            columns = self._split_tabular_columns(line)
            vin = self._vin_from_tabular_row(line, columns, column_map)
            if not vin:
                continue
            if vin in seen_vins:
                continue
            seen_vins.add(vin)

            make = self._tabular_cell(columns, column_map, "make")
            model = self._tabular_cell(columns, column_map, "model")
            location = self._tabular_cell(columns, column_map, "location")
            if location and not pickup_location:
                pickup_location = location

            if model and not make:
                make, model = self._split_make_model(model)

            vehicles.append(
                OrderVehicleCreateRequest(
                    vin=vin,
                    make=make,
                    model=model,
                )
            )
            if len(vehicles) >= MAX_ORDER_VEHICLES:
                break

        return TabularVehicleParse(vehicles=vehicles, pickup_location=pickup_location)

    def _parse_autohero_stock_rows(self, full_message: str) -> AutoheroStockParse:
        """Parse Autohero stock-list rows: City StockID VIN Make Model Plate Ref."""
        parsed_rows: list[AutoheroStockRow] = []
        seen_vins: set[str] = set()

        for raw_line in full_message.splitlines():
            line = raw_line.strip()
            if not line or self._is_noise_line(line):
                continue
            row = self._parse_autohero_stock_row(line)
            if row is None:
                continue
            vin_key = row.vin.upper()
            if vin_key in seen_vins:
                continue
            seen_vins.add(vin_key)
            parsed_rows.append(row)
            if len(parsed_rows) >= MAX_ORDER_VEHICLES:
                break

        if not parsed_rows:
            return AutoheroStockParse()

        pickup_city = self._most_common_pickup_city(parsed_rows)
        reference_numbers = list(dict.fromkeys(row.reference for row in parsed_rows))
        vehicles: list[OrderVehicleCreateRequest] = []
        rows_complete = 0

        for row in parsed_rows:
            is_complete = bool(
                row.pickup_city
                and row.stock_id
                and row.vin
                and row.make
                and row.model
                and row.license_plate
                and row.reference
            )
            if is_complete:
                rows_complete += 1

            note_parts = [f"Stock ID: {row.stock_id}", f"License plate: {row.license_plate}"]
            vehicles.append(
                OrderVehicleCreateRequest(
                    vin=row.vin,
                    make=row.make,
                    model=row.model,
                    notes="; ".join(note_parts),
                )
            )

        return AutoheroStockParse(
            vehicles=vehicles,
            pickup_location=pickup_city,
            reference_numbers=reference_numbers,
            rows_parsed=len(parsed_rows),
            rows_complete=rows_complete,
        )

    @staticmethod
    def _parse_autohero_stock_row(line: str) -> AutoheroStockRow | None:
        prefix_match = AUTOHERO_ROW_PREFIX_PATTERN.match(line)
        if not prefix_match:
            return None

        remainder = prefix_match.group("remainder").strip()
        ref_match = AUTOHERO_REFERENCE_PATTERN.search(remainder)
        if not ref_match:
            return None

        reference = ref_match.group(1)
        before_ref = remainder[: ref_match.start()].strip()
        tokens = before_ref.split()
        if len(tokens) < 2:
            return None

        license_plate = tokens[-1]
        make = tokens[0]
        model = " ".join(tokens[1:-1]).strip() if len(tokens) > 2 else None
        if not make:
            return None

        return AutoheroStockRow(
            pickup_city=prefix_match.group("pickup_city").strip(),
            stock_id=prefix_match.group("stock_id").upper(),
            vin=prefix_match.group("vin").upper(),
            make=make,
            model=model or None,
            license_plate=license_plate,
            reference=reference,
        )

    @staticmethod
    def _most_common_pickup_city(rows: list[AutoheroStockRow]) -> str | None:
        if not rows:
            return None
        counts: dict[str, int] = {}
        for row in rows:
            city = row.pickup_city.strip()
            if not city:
                continue
            key = city.lower()
            counts[key] = counts.get(key, 0) + 1
        if not counts:
            return rows[0].pickup_city
        most_common_key = max(counts, key=counts.get)
        for row in rows:
            if row.pickup_city.lower() == most_common_key:
                return row.pickup_city
        return rows[0].pickup_city

    @staticmethod
    def _split_tabular_columns(line: str) -> list[str]:
        if "\t" in line:
            return [part.strip() for part in line.split("\t") if part.strip()]
        if re.search(r"\s{2,}", line):
            return [part.strip() for part in re.split(r"\s{2,}", line.strip()) if part.strip()]
        return [part.strip() for part in line.split() if part.strip()]

    @staticmethod
    def _normalize_tabular_header(value: str) -> str:
        return re.sub(r"[\s_-]+", " ", value.strip().lower())

    @classmethod
    def _map_tabular_columns(cls, headers: list[str]) -> dict[str, int]:
        mapped: dict[str, int] = {}
        for index, header in enumerate(headers):
            normalized = cls._normalize_tabular_header(header)
            for field, aliases in TABULAR_COLUMN_ALIASES.items():
                if normalized in aliases or any(alias in normalized for alias in aliases):
                    mapped.setdefault(field, index)
                    break
        return mapped

    @staticmethod
    def _tabular_cell(columns: list[str], column_map: dict[str, int], field: str) -> str | None:
        index = column_map.get(field)
        if index is None or index >= len(columns):
            return None
        value = columns[index].strip()
        return value or None

    @staticmethod
    def _vin_from_tabular_row(
        line: str,
        columns: list[str],
        column_map: dict[str, int],
    ) -> str | None:
        vin_index = column_map.get("vin")
        if vin_index is not None and vin_index < len(columns):
            match = VIN_PATTERN.search(columns[vin_index])
            if match:
                return match.group(1).upper()

        match = VIN_PATTERN.search(line)
        if match:
            return match.group(1).upper()
        return None

    def _parse_vehicle_line(self, raw_line: str) -> list[OrderVehicleCreateRequest]:
        line = raw_line.strip(" \t-•*")
        if not line or self._is_noise_line(line) or self._looks_like_location(line):
            return []

        if LOGISTICS_KEYWORD.search(line) or PICKUP_LOCATION_LINE.match(line):
            return []

        vin_first = VIN_FIRST_LINE.match(line)
        if vin_first:
            vin = vin_first.group(1).upper()
            remainder = (vin_first.group(2) or "").strip()
            if remainder and " " not in remainder:
                token = remainder.strip()
                if token.upper().startswith("MG"):
                    return [OrderVehicleCreateRequest(vin=vin, make="MG", model=token)]
                if token.lower() in VEHICLE_PREFIXES:
                    return [OrderVehicleCreateRequest(vin=vin, make=token)]
                return [OrderVehicleCreateRequest(vin=vin, model=token)]
            make, model = self._split_make_model(remainder) if remainder else (None, None)
            return [OrderVehicleCreateRequest(vin=vin, make=make, model=model)]

        quantity = 1
        count_match = VEHICLE_COUNT_PREFIX.match(line)
        if count_match:
            quantity = min(int(count_match.group(1)), MAX_ORDER_VEHICLES)
            line = line[count_match.end() :].strip()

        match = VEHICLE_LINE_PATTERN.match(line)
        if match:
            label = match.group(1).strip()
            vin = match.group(2).upper() if match.group(2) else None
            make, model = self._split_make_model(label)
            if make:
                vehicle = OrderVehicleCreateRequest(make=make, model=model, vin=vin)
                return [vehicle.model_copy() for _ in range(quantity)]

        make, model = self._split_make_model(line)
        if make and make.lower() in VEHICLE_PREFIXES:
            vehicle = OrderVehicleCreateRequest(make=make, model=model)
            return [vehicle.model_copy() for _ in range(quantity)]
        return []

    def _parse_location_line(
        self,
        line: str,
        stop_type: StopType,
        sequence: int,
    ) -> OrderStopCreateRequest | None:
        normalized = line.strip()
        header_city_match = re.match(
            r"(?is)^(?:deliver(?:y|ies)?|drop\s*off|aflever(?:ing)?|livraison|levering)\s*:?\s*(.+)$",
            normalized,
        )
        if header_city_match:
            city = header_city_match.group(1).strip(" ,-")
            if city:
                return OrderStopCreateRequest(
                    stop_type=stop_type,
                    sequence=sequence,
                    city=city,
                    country=self._country_for_city(city),
                )

        if not self._looks_like_location(line):
            return None

        postal_code = None
        postcode_match = POSTCODE_PATTERN.search(line)
        if postcode_match:
            postal_code = postcode_match.group(1)

        city = line
        address = None
        if "," in line:
            parts = [part.strip() for part in line.split(",") if part.strip()]
            if len(parts) >= 2:
                if parts[0].lower() in KNOWN_CITIES:
                    city = parts[0]
                    address = ", ".join(parts[1:])
                else:
                    city = parts[-1]
                    address = ", ".join(parts[:-1])
            else:
                city = parts[0]
        elif postcode_match:
            before = line[: postcode_match.start()].strip(" ,-")
            after = line[postcode_match.end() :].strip(" ,-")
            if before and self._looks_like_street(before):
                address = before
                city = after or before
            elif after:
                city = after
            else:
                city = before or line

        city = city.strip(" -–—")
        if not city:
            return None

        return OrderStopCreateRequest(
            stop_type=stop_type,
            sequence=sequence,
            city=city,
            address=address,
            postal_code=postal_code,
            country=self._country_for_city(city),
        )

    @staticmethod
    def _country_for_city(city: str) -> str:
        normalized = city.strip().lower()
        if normalized in DUTCH_CITIES:
            return "NL"
        return "BE"

    def _extract_dates(
        self,
        message: str,
        pickup_text: str,
        delivery_text: str,
    ) -> tuple[date | None, date | None]:
        pickup_date = self._first_labeled_date(message, pickup_text, PICKUP_HEADER)
        delivery_date = self._first_labeled_date(message, delivery_text, DELIVERY_HEADER)

        all_dates = [self._parse_date(value) for value in DATE_PATTERN.findall(message)]
        all_dates = [value for value in all_dates if value is not None]

        if pickup_date is None and all_dates:
            pickup_date = all_dates[0]
        if delivery_date is None and len(all_dates) > 1:
            delivery_date = all_dates[1]
        elif delivery_date is None and len(all_dates) == 1 and pickup_date != all_dates[0]:
            delivery_date = all_dates[0]

        return pickup_date, delivery_date

    def _first_labeled_date(
        self,
        message: str,
        section_text: str,
        header_pattern: re.Pattern[str],
    ) -> date | None:
        for source in (section_text, message):
            header_match = header_pattern.search(source)
            if not header_match:
                continue
            window = source[header_match.start() : header_match.start() + 80]
            date_match = DATE_PATTERN.search(window)
            if date_match:
                parsed = self._parse_date(date_match.group(1))
                if parsed is not None:
                    return parsed
        return None

    @staticmethod
    def _split_make_model(label: str) -> tuple[str | None, str | None]:
        cleaned = re.sub(r"\b(vin|voertuig|vehicle|auto|wagen)\b", "", label, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"\s{2,}", " ", cleaned)
        if not cleaned:
            return None, None
        parts = cleaned.split(maxsplit=2)
        if not parts:
            return None, None
        make = parts[0]
        model = " ".join(parts[1:3]).strip() if len(parts) > 1 else None
        return make, model or None

    @staticmethod
    def _is_noise_line(line: str) -> bool:
        lowered = line.lower().strip()
        if lowered in {"n/a", "na", "tbd", "—", "-"}:
            return True
        if VEHICLE_COUNT_LINE.match(line):
            return True
        if DELIVERY_SECTION_START.match(line):
            trailing = re.sub(
                r"(?is)^\s*(?:\d+\s*(?:roi|ro[iy]|ème|e|er|de|ste)?\s*)?"
                r"(?:adres\s+)?(?:vigruzke|vigruzko|vygruzk[ae]|vigruz|vygruz|unload|unloading|aflever|livraison|delivery|levering)\s*:?\s*",
                "",
                line,
                count=1,
            ).strip(" ,-")
            if trailing:
                return False
            return True
        if LOGISTICS_KEYWORD.search(line) and not POSTCODE_PATTERN.search(line):
            if not PICKUP_LOCATION_LINE.match(line):
                return True
        return bool(PICKUP_HEADER.fullmatch(lowered) or DELIVERY_HEADER.fullmatch(lowered))

    def _looks_like_vehicle(self, line: str) -> bool:
        if VIN_FIRST_LINE.match(line.strip()):
            return True
        if VIN_PATTERN.search(line):
            return True
        make, _ = self._split_make_model(line)
        if not make:
            return False
        first = make.lower()
        if first in VEHICLE_PREFIXES:
            return True
        return bool(VEHICLE_LINE_PATTERN.match(line) and not self._looks_like_location(line))

    def _looks_like_location(self, line: str) -> bool:
        normalized = line.strip()
        if not normalized:
            return False
        if PICKUP_LOCATION_LINE.match(normalized):
            return True
        if re.match(r"(?is)^(?:adresse?|address|locatie|location)\s*:", normalized):
            return True
        if DELIVERY_SECTION_START.match(normalized):
            return True
        if POSTCODE_PATTERN.search(normalized):
            return True
        if self._looks_like_street(normalized):
            return True

        lowered = normalized.lower()
        if lowered in KNOWN_CITIES:
            return True
        for city in KNOWN_CITIES:
            if city in lowered and not self._looks_like_vehicle(normalized):
                return True

        words = normalized.split()
        if len(words) == 1 and normalized[0].isalpha() and normalized[0].isupper():
            return True
        if len(words) == 2 and all(word[0].isupper() for word in words if word):
            if words[0].lower() in {"sint", "den", "het", "la", "le"}:
                return True
        return False

    @staticmethod
    def _looks_like_street(line: str) -> bool:
        lowered = line.lower()
        return any(keyword in lowered for keyword in STREET_KEYWORDS)

    @staticmethod
    def _parse_date(value: str) -> date | None:
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%d/%m/%y", "%d-%m-%y", "%d.%m.%y"):
            try:
                if fmt == "%Y-%m-%d":
                    return date.fromisoformat(value)
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
        return None
