import { describe, expect, it } from "vitest";

import { formatDriverName } from "./driverDisplay";

describe("formatDriverName", () => {
  it("prefers display_name from the API", () => {
    expect(
      formatDriverName({
        id: "df04890e-0000-4000-8000-000000000001",
        display_name: "Vadym Seniv",
        first_name: null,
        last_name: null,
        email: null,
        phone: null,
      }),
    ).toBe("Vadym Seniv");
  });

  it("builds a name from first and last name", () => {
    expect(
      formatDriverName({
        id: "651e9fcf-0000-4000-8000-000000000002",
        first_name: "Emma",
        last_name: "Wouters",
        email: null,
        phone: null,
      }),
    ).toBe("Emma Wouters");
  });

  it("does not fall back to UUID fragments", () => {
    expect(
      formatDriverName({
        id: "af9ddd06-0000-4000-8000-000000000003",
        first_name: null,
        last_name: null,
        email: null,
        phone: null,
      }),
    ).toBe("Unknown driver");
  });
});
