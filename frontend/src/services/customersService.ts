import { apiDelete, apiGet, apiGetList, apiPost, apiPut } from "./apiClient";
import type { Customer, CustomerContact, CustomerCreatePayload, CustomerUpdatePayload } from "../types/api";

export const customersService = {
  list: (params: { page?: number; page_size?: number; search?: string } = {}) =>
    apiGetList<Customer>("/customers", params),

  get: (customerId: string) => apiGet<Customer>(`/customers/${customerId}`),

  create: (payload: CustomerCreatePayload) => apiPost<Customer>("/customers", payload),

  update: (customerId: string, payload: CustomerUpdatePayload) =>
    apiPut<Customer>(`/customers/${customerId}`, payload),

  delete: (customerId: string) => apiDelete<{ message: string }>(`/customers/${customerId}`),

  contacts: (customerId: string) =>
    apiGet<CustomerContact[]>(`/customers/${customerId}/contacts`),
};
