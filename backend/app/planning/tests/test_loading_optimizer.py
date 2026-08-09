"""Planning module unit tests."""

import uuid

from app.planning.capacity_validator import CapacityValidator
from app.planning.loading_optimizer import LoadingOptimizer, VehicleLoadInput, PositionRecommendation


def test_loading_optimizer_assigns_bi_level_positions() -> None:
    vehicles = [
        VehicleLoadInput(
            vehicle_id=uuid.uuid4(),
            make="BMW",
            model="X5",
            weight_kg=2200,
            height_m=1.75,
            pickup_sequence=1,
            delivery_sequence=2,
        ),
        VehicleLoadInput(
            vehicle_id=uuid.uuid4(),
            make="Audi",
            model="A4",
            weight_kg=1500,
            height_m=1.45,
            pickup_sequence=1,
            delivery_sequence=1,
        ),
    ]
    result = LoadingOptimizer().optimize(
        trailer_capacity=5,
        trailer_max_height_m=4.0,
        trailer_max_weight_kg=10000,
        vehicles=vehicles,
    )
    assert len(result.positions) == 2
    assert result.confidence > 0
    assert result.estimated_total_weight_kg == 3700


def test_capacity_validator_detects_duplicate_positions() -> None:
    vehicle_id = uuid.uuid4()
    positions = [
        PositionRecommendation(
            vehicle_id=vehicle_id,
            vehicle_label="BMW X5",
            upper_deck=False,
            trailer_position=1,
            loading_order=1,
            unloading_order=2,
        ),
        PositionRecommendation(
            vehicle_id=uuid.uuid4(),
            vehicle_label="Audi A4",
            upper_deck=False,
            trailer_position=1,
            loading_order=2,
            unloading_order=1,
        ),
    ]
    result = CapacityValidator().validate(
        trailer_capacity=5,
        trailer_max_height_m=4.0,
        trailer_max_weight_kg=10000,
        trailer_type="car_carrier",
        positions=positions,
        vehicle_weights={vehicle_id: 2000},
        vehicle_heights={vehicle_id: 1.7},
    )
    assert result.is_valid is False
    assert any(item.code == "DUPLICATE_POSITION" for item in result.errors)


def test_capacity_validator_height_warning() -> None:
    vehicle_id = uuid.uuid4()
    positions = [
        PositionRecommendation(
            vehicle_id=vehicle_id,
            vehicle_label="Tall SUV",
            upper_deck=True,
            trailer_position=3,
            loading_order=1,
            unloading_order=1,
        )
    ]
    result = CapacityValidator().validate(
        trailer_capacity=3,
        trailer_max_height_m=4.0,
        trailer_max_weight_kg=10000,
        trailer_type="car_carrier",
        positions=positions,
        vehicle_weights={vehicle_id: 2200},
        vehicle_heights={vehicle_id: 1.8},
    )
    assert any(item.code == "UPPER_DECK_HEIGHT" for item in result.warnings)
