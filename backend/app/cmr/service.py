"""CMR document business logic."""

from __future__ import annotations

import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app.audit.service import AuditService
from app.cmr.generator import build_cmr_context, build_cmr_pdf
from app.common.enums import OrderDocumentType, OrderStatus, StopType, UserRole
from app.common.exceptions import NotFoundError, ValidationError
from app.common.execution_access import ensure_execution_access, get_order_for_company
from app.common.storage.local import LocalFileStorage
from app.companies.repository import CompanyRepository
from app.config.settings import Settings
from app.drivers.repository import DriverRepository
from app.notifications.service import NotificationService
from app.order_documents.models import OrderDocument
from app.order_documents.repository import OrderDocumentRepository
from app.order_stops.repository import OrderStopRepository
from app.order_timeline.service import OrderTimelineService
from app.order_vehicles.repository import OrderVehicleRepository
from app.orders.repository import OrderRepository
from app.realtime.publisher import publish_vehicle_execution_event
from app.realtime.schemas import RealtimeEventType
from app.trailers.repository import TrailerRepository
from app.trucks.repository import TruckRepository
from app.users.models import User
from app.vehicle_damage.repository import VehicleDamageRepository
from app.workflow.service import OrderWorkflowService


class CmrService:
    """CMR generation and preview at pickup loading stage."""

    def __init__(self, db: Session, settings: Settings) -> None:
        self._db = db
        self._settings = settings
        self._documents = OrderDocumentRepository(db)
        self._orders = OrderRepository(db)
        self._stops = OrderStopRepository(db)
        self._vehicles = OrderVehicleRepository(db)
        self._companies = CompanyRepository(db)
        self._drivers = DriverRepository(db)
        self._trucks = TruckRepository(db)
        self._trailers = TrailerRepository(db)
        self._damage = VehicleDamageRepository(db)
        self._timeline = OrderTimelineService(db)
        self._audit = AuditService(db)
        self._notifications = NotificationService(db)
        self._workflow = OrderWorkflowService(db)
        self._storage = LocalFileStorage(settings)

    def _load_order(self, current_user: User, order_id: uuid.UUID):
        order = get_order_for_company(self._orders, order_id, current_user.company_id)
        ensure_execution_access(current_user, order, self._drivers)
        return order

    def _validate_loading_stage(self, order) -> None:
        status = OrderStatus(order.status)
        if status != OrderStatus.LOADING:
            raise ValidationError(
                code="INVALID_ORDER_STATUS",
                message="CMR can only be generated during loading at pickup.",
            )

    def ensure_cmr_generated(self, current_user: User, order_id: uuid.UUID) -> None:
        """Raise when finish loading is attempted without a generated CMR."""
        order = self._load_order(current_user, order_id)
        if OrderStatus(order.status) != OrderStatus.LOADING:
            return
        if self._documents.has_document(
            order_id,
            current_user.company_id,
            OrderDocumentType.CMR,
        ):
            return
        raise ValidationError(
            code="CMR_REQUIRED",
            message="Generate the CMR before finishing loading.",
        )

    def _build_context(self, current_user: User, order) -> object:
        company = self._companies.get_by_id_for_company(current_user.company_id)
        if company is None:
            raise NotFoundError(code="COMPANY_NOT_FOUND", message="Company not found.")

        stops = self._stops.list_for_order(order.id, current_user.company_id)
        pickup_stop = next(
            (stop for stop in stops if stop.stop_type == StopType.PICKUP),
            None,
        )
        delivery_stop = next(
            (stop for stop in stops if stop.stop_type == StopType.DELIVERY),
            None,
        )

        driver_name = ""
        if order.assigned_driver_id is not None:
            driver = self._drivers.get_by_id_for_company(
                order.assigned_driver_id,
                current_user.company_id,
            )
            if driver is not None and driver.user is not None:
                driver_name = f"{driver.user.first_name} {driver.user.last_name}".strip()

        truck_plate = ""
        if order.assigned_truck_id is not None:
            truck = self._trucks.get_by_id_for_company(
                order.assigned_truck_id,
                current_user.company_id,
            )
            if truck is not None:
                truck_plate = truck.registration_number

        trailer_plate = ""
        if order.assigned_trailer_id is not None:
            trailer = self._trailers.get_by_id_for_company(
                order.assigned_trailer_id,
                current_user.company_id,
            )
            if trailer is not None:
                trailer_plate = trailer.registration_number

        vehicles = self._vehicles.list_for_order(order.id, current_user.company_id)
        damage_lines: list[str] = []
        for vehicle in vehicles:
            for damage in self._damage.list_for_vehicle(vehicle.id, current_user.company_id):
                label = f"{vehicle.make or ''} {vehicle.model or ''}".strip()
                detail = damage.description or damage.damage_type
                if label:
                    damage_lines.append(f"{label}: {detail}")
                else:
                    damage_lines.append(detail)

        order.vehicles = vehicles
        order.stops = stops
        return build_cmr_context(
            company=company,
            order=order,
            pickup_stop=pickup_stop,
            delivery_stop=delivery_stop,
            driver_name=driver_name,
            truck_plate=truck_plate,
            trailer_plate=trailer_plate,
            damage_notes="\n".join(damage_lines),
        )

    def generate_preview_pdf(self, current_user: User, order_id: uuid.UUID) -> bytes:
        """Generate a draft CMR PDF for driver review (not persisted)."""
        order = self._load_order(current_user, order_id)
        self._validate_loading_stage(order)
        context = self._build_context(current_user, order)
        return build_cmr_pdf(
            context,
            upload_root=Path(self._settings.upload_root_dir),
        )

    def generate_draft(self, current_user: User, order_id: uuid.UUID) -> OrderDocument:
        """Generate and persist a draft CMR PDF for an order at pickup loading."""
        order = self._load_order(current_user, order_id)
        self._validate_loading_stage(order)
        context = self._build_context(current_user, order)
        pdf_bytes = build_cmr_pdf(
            context,
            upload_root=Path(self._settings.upload_root_dir),
        )
        file_path, _, _ = self._storage.save_order_document(
            company_id=current_user.company_id,
            order_id=order_id,
            filename=f"cmr-{order.order_number}-draft.pdf",
            content=pdf_bytes,
            content_type="application/pdf",
        )
        next_version = self._documents.get_latest_version(
            order_id,
            current_user.company_id,
            OrderDocumentType.CMR,
        ) + 1
        document = self._documents.create(
            company_id=current_user.company_id,
            order_id=order_id,
            document_type=OrderDocumentType.CMR,
            file_path=file_path,
            file_name=f"cmr-{order.order_number}-draft.pdf",
            version=next_version,
            uploaded_by=current_user.id,
            is_locked=False,
        )
        self._timeline.record(
            current_user,
            order_id,
            "CMR_GENERATED",
            f"CMR draft generated for order {order.order_number}.",
        )
        return document

    def sign_and_finalize(
        self,
        current_user: User,
        order_id: uuid.UUID,
        signature_png_base64: str,
        ip_address: str | None = None,
    ) -> tuple[OrderDocument, object, object | None]:
        """Apply signature and company stamp, lock the CMR, and confirm delivery."""
        order = self._load_order(current_user, order_id)
        if OrderStatus(order.status) not in {
            OrderStatus.ARRIVED_DELIVERY,
            OrderStatus.DELIVERING,
        }:
            raise ValidationError(
                code="INVALID_ORDER_STATUS",
                message="CMR signing is only available during delivery.",
            )

        if self._documents.has_locked_document(
            order_id,
            current_user.company_id,
            OrderDocumentType.CMR,
        ):
            raise ValidationError(
                code="CMR_ALREADY_FINALIZED",
                message="A signed CMR is already attached to this order.",
            )

        context = self._build_context(current_user, order)
        pdf_bytes = build_cmr_pdf(
            context,
            upload_root=Path(self._settings.upload_root_dir),
        )
        file_path, _, _ = self._storage.save_order_document(
            company_id=current_user.company_id,
            order_id=order_id,
            filename=f"cmr-{order.order_number}-signed.pdf",
            content=pdf_bytes,
            content_type="application/pdf",
        )
        next_version = self._documents.get_latest_version(
            order_id,
            current_user.company_id,
            OrderDocumentType.CMR,
        ) + 1
        document = self._documents.create(
            company_id=current_user.company_id,
            order_id=order_id,
            document_type=OrderDocumentType.CMR,
            file_path=file_path,
            file_name=f"cmr-{order.order_number}-signed.pdf",
            version=next_version,
            uploaded_by=current_user.id,
            is_locked=True,
        )
        self._timeline.record(
            current_user,
            order_id,
            "CMR_SIGNED",
            f"Signed CMR finalized for order {order.order_number}.",
        )
        self._audit.record_order_document_uploaded(
            company_id=current_user.company_id,
            user_id=current_user.id,
            entity_id=str(document.id),
            action="CMR_SIGNED",
            ip_address=ip_address,
        )
        self._notifications.notify_staff(
            company_id=current_user.company_id,
            roles={UserRole.ADMIN, UserRole.DISPATCHER},
            title="CMR signed",
            message=f"Signed CMR attached for order {order.order_number}.",
            notification_type="CMR_UPLOADED",
            order_id=order.id,
        )
        publish_vehicle_execution_event(
            company_id=current_user.company_id,
            order_id=order_id,
            event_type=RealtimeEventType.CMR_UPLOADED,
            order_number=order.order_number,
            extra={
                "document_id": str(document.id),
                "document_type": OrderDocumentType.CMR.value,
                "is_locked": True,
            },
            driver_user_id=current_user.id,
        )
        updated_order, updated_stop = self._workflow.confirm_delivery_cmr(
            current_user,
            order_id,
            ip_address=ip_address,
        )
        return document, updated_order, updated_stop

    def get_latest_cmr(
        self,
        current_user: User,
        order_id: uuid.UUID,
        *,
        locked_only: bool = False,
    ) -> OrderDocument:
        """Return the latest CMR document for an order."""
        self._load_order(current_user, order_id)
        document = self._documents.get_latest_document(
            order_id,
            current_user.company_id,
            OrderDocumentType.CMR,
            locked_only=locked_only,
        )
        if document is None:
            raise NotFoundError(
                code="CMR_NOT_FOUND",
                message="CMR has not been generated yet.",
            )
        return document
