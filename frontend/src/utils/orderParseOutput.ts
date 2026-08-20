import type { OrderParseOutput, OrderParseTableRow, OrderParseVehicleDraft } from "../types/api";

function parseNoteField(notes: string | null | undefined, label: string): string | null {
  if (!notes) return null;
  const pattern = new RegExp(`${label}:\\s*([^;]+)`, "i");
  const match = notes.match(pattern);
  return match?.[1]?.trim() ?? null;
}

export function vehicleToTableRow(
  vehicle: OrderParseVehicleDraft,
  index: number,
  output: OrderParseOutput,
): OrderParseTableRow {
  const pickupLocation = output.pickup_stops?.[0]?.city ?? output.pickup_stops?.[0]?.address ?? null;
  const reference = output.reference_numbers?.[index] ?? output.reference_numbers?.[0] ?? null;
  const autoheroScore = output.field_confidence?.autohero_stock ?? 0;

  return {
    stock_id: vehicle.stock_id ?? parseNoteField(vehicle.notes, "Stock ID"),
    vin: vehicle.vin ?? null,
    make: vehicle.make ?? null,
    model: vehicle.model ?? null,
    license_plate: vehicle.license_plate ?? parseNoteField(vehicle.notes, "License plate"),
    location: vehicle.location ?? pickupLocation,
    ll_id: vehicle.ll_id ?? reference,
    autohero_car: vehicle.autohero_car ?? autoheroScore >= 0.85,
  };
}

export function buildTableRows(output: OrderParseOutput): OrderParseTableRow[] {
  if (output.table_rows?.length) {
    return output.table_rows.map((row) => ({ ...row }));
  }
  return (output.vehicles ?? []).map((vehicle, index) => vehicleToTableRow(vehicle, index, output));
}

export function tableRowsToVehicles(rows: OrderParseTableRow[]): OrderParseVehicleDraft[] {
  return rows.map((row) => {
    const noteParts: string[] = [];
    if (row.stock_id) noteParts.push(`Stock ID: ${row.stock_id}`);
    if (row.license_plate) noteParts.push(`License plate: ${row.license_plate}`);

    return {
      make: row.make ?? null,
      model: row.model ?? null,
      vin: row.vin ?? null,
      stock_id: row.stock_id ?? null,
      license_plate: row.license_plate ?? null,
      location: row.location ?? null,
      ll_id: row.ll_id ?? null,
      autohero_car: row.autohero_car ?? null,
      notes: noteParts.length > 0 ? noteParts.join("; ") : null,
    };
  });
}

export function collectParseValidationMessages(output: OrderParseOutput): {
  errors: string[];
  warnings: string[];
  vehicleCount: number;
} {
  const errors = [...(output.validation_errors ?? []), ...(output.missing_fields ?? [])];
  const warnings = [...(output.warnings ?? [])];

  const lowConfidenceFields = Object.entries(output.field_confidence ?? {})
    .filter(([key, score]) => score < 0.7 && !["overall", "autohero_stock"].includes(key))
    .map(([key]) => `Low confidence: ${key.replaceAll("_", " ")}`);

  warnings.push(...lowConfidenceFields);

  const vehicleCount = output.vehicle_count ?? output.vehicles?.length ?? buildTableRows(output).length;

  return { errors, warnings, vehicleCount };
}

export function applyTableRowsToOutput(
  output: OrderParseOutput,
  rows: OrderParseTableRow[],
): OrderParseOutput {
  const vehicles = tableRowsToVehicles(rows);
  const referenceNumbers = rows
    .map((row) => row.ll_id)
    .filter((value): value is string => Boolean(value?.trim()));

  return {
    ...output,
    table_rows: rows,
    vehicles,
    vehicle_count: rows.length,
    reference_numbers: referenceNumbers.length > 0 ? referenceNumbers : output.reference_numbers,
  };
}
