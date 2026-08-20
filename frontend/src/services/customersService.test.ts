import { describe, expect, it, vi, beforeEach } from "vitest";
import { customersService } from "./customersService";

const apiPost = vi.fn();
const apiPut = vi.fn();
const apiDelete = vi.fn();

vi.mock("./apiClient", () => ({
  apiGet: vi.fn(),
  apiGetList: vi.fn(),
  apiPost: (...args: unknown[]) => apiPost(...args),
  apiPut: (...args: unknown[]) => apiPut(...args),
  apiDelete: (...args: unknown[]) => apiDelete(...args),
}));

describe("customersService", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("creates a customer with operational fields", async () => {
    apiPost.mockResolvedValue({ id: "cust-1", company_name: "Acme GmbH" });

    await customersService.create({
      company_name: "Acme GmbH",
      street: "Main Street",
      house_number: "12",
      postal_code: "1000",
      invoice_email: "billing@acme.test",
      dispatch_phone: "+32 2 000 00 00",
      is_active: true,
    });

    expect(apiPost).toHaveBeenCalledWith("/customers", {
      company_name: "Acme GmbH",
      street: "Main Street",
      house_number: "12",
      postal_code: "1000",
      invoice_email: "billing@acme.test",
      dispatch_phone: "+32 2 000 00 00",
      is_active: true,
    });
  });

  it("updates and deletes customers", async () => {
    apiPut.mockResolvedValue({ id: "cust-1" });
    apiDelete.mockResolvedValue({ message: "Customer deleted successfully." });

    await customersService.update("cust-1", { company_name: "Acme Updated", is_active: false });
    await customersService.delete("cust-1");

    expect(apiPut).toHaveBeenCalledWith("/customers/cust-1", {
      company_name: "Acme Updated",
      is_active: false,
    });
    expect(apiDelete).toHaveBeenCalledWith("/customers/cust-1");
  });
});
