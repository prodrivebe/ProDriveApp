"""CMR document generation — Belgian/Flemish international consignment note layout."""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from datetime import date
from html import escape
from pathlib import Path
from typing import TYPE_CHECKING

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

# Layout constants (A4 portrait, millimetres)
PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 8 * mm
CONTENT_WIDTH = PAGE_WIDTH - 2 * MARGIN
HALF_WIDTH = (CONTENT_WIDTH - 2 * mm) / 2
BORDER_COLOR = colors.HexColor("#2E7D32")
LABEL_COLOR = colors.HexColor("#1B5E20")
TEXT_COLOR = colors.black
HEADER_FILL = colors.HexColor("#E8F5E9")
LINE_WIDTH = 0.35

if TYPE_CHECKING:
    from app.companies.models import Company
    from app.orders.models import Order, OrderStop


@dataclass
class CmrVehicleRow:
    """Single vehicle row on the CMR."""

    stock_id: str = ""
    make: str = ""
    model: str = ""
    vin: str = ""
    license_plate: str = ""


def _parse_vehicle_identifiers(notes: str | None) -> tuple[str, str]:
    """Extract Stock ID and license plate stored in vehicle notes."""
    stock_id = ""
    license_plate = ""
    if not notes:
        return stock_id, license_plate
    for segment in notes.replace(";", "\n").split("\n"):
        segment = segment.strip()
        if not segment:
            continue
        lower = segment.lower()
        if lower.startswith("stock id:"):
            stock_id = segment.split(":", 1)[1].strip()
        elif lower.startswith("license plate:"):
            license_plate = segment.split(":", 1)[1].strip()
    return stock_id, license_plate


_INTERNAL_VEHICLE_NOTE_PREFIXES = (
    "stock id:",
    "license plate:",
    "vin:",
)


def _vehicle_remark_from_notes(notes: str | None) -> str:
    """Return free-text vehicle remarks excluding parsed CMR metadata lines."""
    if not notes:
        return ""
    remark_lines: list[str] = []
    for segment in notes.replace(";", "\n").split("\n"):
        segment = segment.strip()
        if not segment:
            continue
        lower = segment.lower()
        if any(lower.startswith(prefix) for prefix in _INTERNAL_VEHICLE_NOTE_PREFIXES):
            continue
        remark_lines.append(segment)
    return "\n".join(remark_lines).strip()


@dataclass
class CmrContext:
    """All data required to render a CMR document."""

    order_number: str
    customer_references: list[str] = field(default_factory=list)
    sender_name: str = ""
    sender_address: str = ""
    consignee_name: str = ""
    consignee_address: str = ""
    pickup_date: date | None = None
    delivery_date: date | None = None
    pickup_address: str = ""
    delivery_address: str = ""
    carrier_name: str = ""
    carrier_address: str = ""
    driver_name: str = ""
    truck_plate: str = ""
    trailer_plate: str = ""
    vehicle_count: int = 0
    vehicles: list[CmrVehicleRow] = field(default_factory=list)
    remarks: str = ""
    damage_notes: str = ""
    company_name: str = ""
    company_logo_path: str | None = None


def format_address(stop: OrderStop | None) -> str:
    """Format a stop into a multi-line postal address."""
    if stop is None:
        return ""
    parts = [
        stop.company_name or "",
        stop.address or "",
        " ".join(part for part in [stop.postal_code, stop.city] if part),
        stop.country or "",
    ]
    return "\n".join(part for part in parts if part.strip())


def build_cmr_context(
    *,
    company: Company,
    order: Order,
    pickup_stop: OrderStop | None,
    delivery_stop: OrderStop | None,
    driver_name: str = "",
    truck_plate: str = "",
    trailer_plate: str = "",
    damage_notes: str = "",
) -> CmrContext:
    """Build CMR context from order and related entities."""
    active_vehicles = [vehicle for vehicle in order.vehicles if vehicle.deleted_at is None]
    refs = list(order.customer_reference_numbers or [])
    remarks_parts: list[str] = []
    if order.notes:
        remarks_parts.append(order.notes.strip())
    for vehicle in active_vehicles:
        remark = _vehicle_remark_from_notes(vehicle.notes)
        if not remark:
            continue
        label = " ".join(part for part in [vehicle.make, vehicle.model] if part).strip()
        if label:
            remarks_parts.append(f"{label}: {remark}")
        else:
            remarks_parts.append(remark)

    vehicle_rows: list[CmrVehicleRow] = []
    for vehicle in active_vehicles:
        stock_id, license_plate = _parse_vehicle_identifiers(vehicle.notes)
        vehicle_rows.append(
            CmrVehicleRow(
                stock_id=stock_id,
                make=vehicle.make or "",
                model=vehicle.model or "",
                vin=vehicle.verified_vin or vehicle.vin or "",
                license_plate=license_plate,
            )
        )

    return CmrContext(
        order_number=order.order_number,
        customer_references=refs,
        sender_name=pickup_stop.company_name if pickup_stop else "",
        sender_address=format_address(pickup_stop),
        consignee_name=delivery_stop.company_name if delivery_stop else "",
        consignee_address=format_address(delivery_stop),
        pickup_date=order.planned_pickup_date,
        delivery_date=order.planned_delivery_date,
        pickup_address=format_address(pickup_stop),
        delivery_address=format_address(delivery_stop),
        carrier_name=company.name,
        carrier_address="\n".join(
            part for part in [company.address, company.country] if part
        ),
        driver_name=driver_name,
        truck_plate=truck_plate,
        trailer_plate=trailer_plate,
        vehicle_count=len(active_vehicles),
        vehicles=vehicle_rows,
        remarks="\n".join(remarks_parts),
        damage_notes=damage_notes,
        company_name=company.name,
        company_logo_path=company.logo_url,
    )


def _customer_refs_text(context: CmrContext) -> str:
    if not context.customer_references:
        return ""
    return " / ".join(context.customer_references)


def build_cmr_html(*, company: Company, customer: object, order: Order) -> str:
    """Build a printable CMR HTML document (legacy fallback)."""
    pickup = next(
        (stop for stop in order.stops if stop.stop_type == "PICKUP" and stop.deleted_at is None),
        None,
    )
    delivery = next(
        (stop for stop in order.stops if stop.stop_type == "DELIVERY" and stop.deleted_at is None),
        None,
    )
    context = build_cmr_context(
        company=company,
        order=order,
        pickup_stop=pickup,
        delivery_stop=delivery,
    )
    refs = _customer_refs_text(context)
    vehicle_rows = "".join(
        (
            "<tr>"
            f"<td>{escape(row.make)}</td>"
            f"<td>{escape(row.model)}</td>"
            f"<td>{escape(row.vin)}</td>"
            "</tr>"
        )
        for row in context.vehicles
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>CMR {escape(context.order_number)}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; color: #1b3a5f; }}
    h1 {{ margin-bottom: 8px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
  th {{ background: #E8F5E9; color: #1B5E20; }}
    th, td {{ border: 1px solid #2E7D32; padding: 8px; text-align: left; }}
  </style>
</head>
<body>
  <h1>CMR Consignment Note</h1>
  <p><strong>ProDrive order:</strong> {escape(context.order_number)}</p>
  {f"<p><strong>Customer reference:</strong> {escape(refs)}</strong></p>" if refs else ""}
  <p><strong>Carrier:</strong> {escape(context.carrier_name)}</p>
  <h2>Vehicles ({context.vehicle_count})</h2>
  <table>
    <thead><tr><th>Make</th><th>Model</th><th>VIN</th></tr></thead>
    <tbody>{vehicle_rows or '<tr><td colspan="3">No vehicles recorded</td></tr>'}</tbody>
  </table>
  <p>Generated by ProDrive.</p>
</body>
</html>
"""


def _set_border_style(pdf: canvas.Canvas) -> None:
    pdf.setStrokeColor(BORDER_COLOR)
    pdf.setLineWidth(LINE_WIDTH)


def _draw_rect(pdf: canvas.Canvas, x: float, y: float, width: float, height: float) -> None:
    _set_border_style(pdf)
    pdf.rect(x, y, width, height, stroke=1, fill=0)


def _draw_box_label(
    pdf: canvas.Canvas,
    x: float,
    y: float,
    width: float,
    height: float,
    box_number: int,
    fr_label: str,
    nl_label: str,
) -> None:
    """Draw bilingual box number label in the top-left corner."""
    pdf.setFillColor(LABEL_COLOR)
    pdf.setFont("Helvetica-Bold", 6)
    pdf.drawString(x + 1.5 * mm, y + height - 3.5 * mm, str(box_number))
    pdf.setFont("Helvetica", 5)
    label_y = y + height - 6.5 * mm
    pdf.drawString(x + 5 * mm, label_y, fr_label)
    pdf.drawString(x + 5 * mm, label_y - 2.5 * mm, nl_label)


def _draw_box(
    pdf: canvas.Canvas,
    x: float,
    y: float,
    width: float,
    height: float,
    box_number: int,
    fr_label: str,
    nl_label: str,
    value: str = "",
    *,
    value_size: int = 8,
    label_height: float = 9 * mm,
) -> None:
    """Draw a numbered CMR box with bilingual label and optional content."""
    _draw_rect(pdf, x, y, width, height)
    _draw_box_label(pdf, x, y, width, height, box_number, fr_label, nl_label)
    if not value.strip():
        return
    pdf.setFillColor(TEXT_COLOR)
    pdf.setFont("Helvetica", value_size)
    text_obj = pdf.beginText(x + 2 * mm, y + height - label_height)
    text_obj.setLeading(value_size + 1.5)
    for line in value.split("\n"):
        trimmed = line.strip()
        if trimmed:
            text_obj.textLine(trimmed[:160])
    pdf.drawText(text_obj)


def _draw_header(pdf: canvas.Canvas, context: CmrContext, top_y: float) -> float:
    """Draw CMR title bar; return y below header."""
    header_height = 11 * mm
    y = top_y - header_height
    _draw_rect(pdf, MARGIN, y, CONTENT_WIDTH, header_height)
    pdf.setFillColor(HEADER_FILL)
    pdf.rect(MARGIN, y, CONTENT_WIDTH, header_height, stroke=0, fill=1)
    _draw_rect(pdf, MARGIN, y, CONTENT_WIDTH, header_height)

    pdf.setFillColor(LABEL_COLOR)
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawCentredString(MARGIN + CONTENT_WIDTH / 2, y + 7 * mm, "CMR")
    pdf.setFont("Helvetica-Bold", 7)
    pdf.drawString(MARGIN + 3 * mm, y + 3 * mm, "LETTRE DE VOITURE INTERNATIONALE")
    pdf.drawRightString(
        MARGIN + CONTENT_WIDTH - 3 * mm,
        y + 3 * mm,
        "INTERNATIONAAL VERVOERDOCUMENT",
    )

    refs = _customer_refs_text(context)
    pdf.setFont("Helvetica", 6.5)
    meta = f"ProDrive {context.order_number}"
    if refs:
        meta = f"{meta}  ·  Ref. {refs}"
    pdf.drawCentredString(MARGIN + CONTENT_WIDTH / 2, y + 1.2 * mm, meta)
    return y


def _format_date(value: date | None) -> str:
    if value is None:
        return ""
    return value.strftime("%d/%m/%Y")


def _vehicle_nature_lines(context: CmrContext) -> str:
    lines: list[str] = []
    for vehicle in context.vehicles:
        label = " ".join(part for part in [vehicle.make, vehicle.model] if part).strip()
        lines.append(label or "Véhicule / Voertuig")
    return "\n".join(lines)


def _stock_id_lines(context: CmrContext) -> str:
    """Stock IDs for box 6 — one per vehicle row."""
    if not context.vehicles:
        return ""
    lines: list[str] = []
    for index, vehicle in enumerate(context.vehicles, start=1):
        stock = vehicle.stock_id.strip()
        plate = vehicle.license_plate.strip()
        if stock and plate:
            lines.append(f"{index}. {stock} · {plate}")
        elif stock:
            lines.append(f"{index}. {stock}")
        elif plate:
            lines.append(f"{index}. {plate}")
        else:
            lines.append(f"{index}. —")
    return "\n".join(lines)


def _vin_lines(context: CmrContext) -> str:
    """One VIN per numbered line for box 10."""
    if not context.vehicles:
        return ""
    return "\n".join(
        f"{index}. {row.vin}"
        for index, row in enumerate(context.vehicles, start=1)
        if row.vin
    )


def _remarks_text(context: CmrContext) -> str:
    parts: list[str] = []
    if context.remarks:
        parts.append(context.remarks)
    if context.damage_notes:
        parts.append(f"Dommages / Schade:\n{context.damage_notes}")
    return "\n\n".join(parts)


def _carrier_text(context: CmrContext) -> str:
    lines = [context.carrier_name]
    if context.carrier_address:
        lines.append(context.carrier_address)
    if context.driver_name:
        lines.append(f"Chauffeur / Bestuurder: {context.driver_name}")
    if context.truck_plate:
        lines.append(f"Tracteur / Trekker: {context.truck_plate}")
    if context.trailer_plate:
        lines.append(f"Remorque / Oplegger: {context.trailer_plate}")
    return "\n".join(line for line in lines if line.strip())


def _pickup_place_date(context: CmrContext) -> str:
    lines = []
    if context.pickup_address:
        lines.append(context.pickup_address)
    pickup_date = _format_date(context.pickup_date)
    if pickup_date:
        lines.append(f"Date / Datum: {pickup_date}")
    return "\n".join(lines)


def build_cmr_pdf(
    context: CmrContext,
    *,
    upload_root: Path | None = None,
) -> bytes:
    """Render a Belgian/Flemish CMR PDF draft for hand signing at pickup."""
    del upload_root
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)

    top_y = PAGE_HEIGHT - MARGIN
    y = _draw_header(pdf, context, top_y)

    row_h = 28 * mm
    y -= row_h
    sender = f"{context.sender_name}\n{context.sender_address}".strip()
    consignee = f"{context.consignee_name}\n{context.consignee_address}".strip()
    _draw_box(pdf, MARGIN, y, HALF_WIDTH, row_h, 1, "Expéditeur", "Afzender", sender)
    _draw_box(
        pdf, MARGIN + HALF_WIDTH + 2 * mm, y, HALF_WIDTH, row_h, 2,
        "Destinataire", "Geadresseerde", consignee,
    )

    row_h = 13 * mm
    y -= row_h
    delivery_place = context.delivery_address
    delivery_date = _format_date(context.delivery_date)
    if delivery_date:
        delivery_place = f"{delivery_place}\nDate / Datum: {delivery_date}".strip()
    _draw_box(
        pdf, MARGIN, y, CONTENT_WIDTH, row_h, 3,
        "Lieu prévu pour la livraison des marchandises",
        "Plaats bestemd voor aflevering van de goederen",
        delivery_place,
    )

    row_h = 13 * mm
    y -= row_h
    refs = _customer_refs_text(context)
    docs_value = f"ProDrive {context.order_number}"
    if refs:
        docs_value = f"{docs_value}\nRef. {refs}"
    _draw_box(
        pdf, MARGIN, y, HALF_WIDTH, row_h, 4,
        "Lieu et date de prise en charge",
        "Plaats en datum van inontvangstneming",
        _pickup_place_date(context),
    )
    _draw_box(
        pdf, MARGIN + HALF_WIDTH + 2 * mm, y, HALF_WIDTH, row_h, 5,
        "Documents annexés", "Bijgevoegde documenten", docs_value, value_size=7,
    )

    goods_h = max(46 * mm, (10 + max(len(context.vehicles), 1) * 8) * mm)
    y -= goods_h
    _draw_rect(pdf, MARGIN, y, CONTENT_WIDTH, goods_h)

    col_widths = [24 * mm, 12 * mm, 16 * mm, 24 * mm, 62 * mm, 14 * mm, 14 * mm]
    used = sum(col_widths)
    if used < CONTENT_WIDTH:
        col_widths[4] += CONTENT_WIDTH - used

    header_h = 10 * mm
    header_y = y + goods_h - header_h
    pdf.setFillColor(HEADER_FILL)
    pdf.rect(MARGIN, header_y, CONTENT_WIDTH, header_h, stroke=0, fill=1)
    pdf.line(MARGIN, header_y, MARGIN + CONTENT_WIDTH, header_y)

    col_x = MARGIN
    goods_headers = [
        (6, "Marques et numéros", "Merken en nummers"),
        (7, "Nombre de colis", "Aantal colli"),
        (8, "Mode d'emballage", "Wijze van verpakking"),
        (9, "Nature de la marchandise", "Aard der goederen"),
        (10, "Numéro statistique / VIN", "Statistisch nummer / VIN"),
        (11, "Poids brut, kg", "Brutogewicht, kg"),
        (12, "Volume m³", "Volume m³"),
    ]
    for index, (box_no, fr, nl) in enumerate(goods_headers):
        width = col_widths[index]
        if index > 0:
            pdf.line(col_x, y, col_x, y + goods_h)
        _draw_box_label(pdf, col_x, header_y, width, header_h, box_no, fr, nl)
        col_x += width

    body_y = y + 2 * mm
    body_h = goods_h - header_h - 2 * mm
    vehicle_count = max(len(context.vehicles), 1)
    value_font_size = 7.0 if vehicle_count <= 4 else 6.5
    vin_font_size = 6.5 if vehicle_count <= 4 else 6.0
    col_x = MARGIN
    goods_values = [
        _stock_id_lines(context) or "—",
        str(context.vehicle_count) if context.vehicle_count else "—",
        "Véhicule\nVoertuig",
        _vehicle_nature_lines(context) or "—",
        _vin_lines(context) or "—",
        "—",
        "—",
    ]
    for index, value in enumerate(goods_values):
        width = col_widths[index]
        pdf.setFillColor(TEXT_COLOR)
        font_size = vin_font_size if index == 4 else value_font_size
        pdf.setFont("Helvetica", font_size)
        leading = font_size + 1.5
        text_obj = pdf.beginText(col_x + 1.5 * mm, body_y + body_h - 3 * mm)
        text_obj.setLeading(leading)
        for line in value.split("\n"):
            text_obj.textLine(line[:120])
        pdf.drawText(text_obj)
        col_x += width

    row_h = 17 * mm
    y -= row_h
    _draw_box(
        pdf, MARGIN, y, HALF_WIDTH, row_h, 13,
        "Instructions de l'expéditeur", "Instructies van de afzender",
        _remarks_text(context), value_size=7,
    )
    _draw_box(
        pdf, MARGIN + HALF_WIDTH + 2 * mm, y, HALF_WIDTH, row_h, 14,
        "Prescriptions d'affranchissement", "Frankeringsvoorschriften",
        "Port payé / Franco", value_size=7,
    )

    row_h = 24 * mm
    y -= row_h
    _draw_box(pdf, MARGIN, y, HALF_WIDTH, row_h, 15, "Remboursement", "Terug te betalen", "")
    _draw_box(
        pdf, MARGIN + HALF_WIDTH + 2 * mm, y, HALF_WIDTH, row_h, 16,
        "Transporteur", "Vervoerder", _carrier_text(context), value_size=7,
    )

    row_h = 9 * mm
    y -= row_h
    _draw_box(
        pdf, MARGIN, y, CONTENT_WIDTH, row_h, 17,
        "Transporteurs successifs", "Opeenvolgende vervoerders", "",
    )

    row_h = 13 * mm
    y -= row_h
    _draw_box(
        pdf, MARGIN, y, HALF_WIDTH, row_h, 18,
        "Réserves et observations du transporteur",
        "Voorbehoud en opmerkingen van de vervoerder", "",
    )
    _draw_box(
        pdf, MARGIN + HALF_WIDTH + 2 * mm, y, HALF_WIDTH, row_h, 19,
        "Conventions particulières", "Bijzondere overeenkomsten",
        f"Véhicules: {context.vehicle_count}" if context.vehicle_count else "",
        value_size=7,
    )

    row_h = 7 * mm
    y -= row_h
    _draw_box(
        pdf, MARGIN, y, CONTENT_WIDTH, row_h, 20,
        "À payer par / Te betalen door", "Expéditeur · Destinataire · Autre", "",
        value_size=7,
    )

    row_h = 20 * mm
    y -= row_h
    established = ""
    if context.pickup_address:
        first_line = context.pickup_address.split("\n")[0]
        established = f"{first_line}, {_format_date(context.pickup_date)}".strip(", ")
    _draw_box(
        pdf, MARGIN, y, HALF_WIDTH, row_h, 21,
        "Établi à / Opgemaakt te", "", established, value_size=7,
    )
    _draw_box(
        pdf, MARGIN + HALF_WIDTH + 2 * mm, y, HALF_WIDTH, row_h, 22,
        "Signature et timbre de l'expéditeur",
        "Handtekening en stempel van de afzender", "",
    )

    row_h = 20 * mm
    y -= row_h
    _draw_box(
        pdf, MARGIN, y, HALF_WIDTH, row_h, 23,
        "Signature et timbre du transporteur",
        "Handtekening en stempel van de vervoerder", "",
    )
    _draw_box(
        pdf, MARGIN + HALF_WIDTH + 2 * mm, y, HALF_WIDTH, row_h, 24,
        "Marchandises reçues, date, signature",
        "Goederen ontvangen, datum, handtekening", "",
    )

    row_h = 11 * mm
    y -= row_h
    quarter = (CONTENT_WIDTH - 3 * 2 * mm) / 4
    extras = [
        (25, "N° tracteur", "Trekker", context.truck_plate),
        (26, "N° remorque", "Oplegger", context.trailer_plate),
        (27, "Chauffeur", "Bestuurder", context.driver_name),
        (28, "N° commande", "Ordernr.", context.order_number),
    ]
    for index, (box_no, fr, nl, value) in enumerate(extras):
        x = MARGIN + index * (quarter + 2 * mm)
        _draw_box(pdf, x, y, quarter, row_h, box_no, fr, nl, value, value_size=7)

    pdf.setFillColor(LABEL_COLOR)
    pdf.setFont("Helvetica", 5)
    pdf.drawCentredString(
        MARGIN + CONTENT_WIDTH / 2,
        MARGIN - 2 * mm,
        "ProDrive — document CMR provisoire pour signature manuscrite",
    )

    pdf.save()
    return buffer.getvalue()
