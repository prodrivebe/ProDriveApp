import { apiGet, apiGetList } from "./apiClient";
import type { Customer, CustomerContact } from "../types/api";

export const customersService = {
  list: (params: { page?: number; page_size?: number; search?: string } = {}) =>
    apiGetList<Customer>("/customers", params),

  get: (customerId: string) => apiGet<Customer>(`/customers/${customerId}`),

  contacts: (customerId: string) =>
    apiGet<CustomerContact[]>(`/customers/${customerId}/contacts`),
};
