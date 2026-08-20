import type { Driver } from "../types/api";

/** Human-readable driver label from enriched /drivers API fields. */
export function formatDriverName(
  driver: Pick<Driver, "display_name" | "first_name" | "last_name" | "email" | "phone" | "id">,
): string {
  if (driver.display_name?.trim()) return driver.display_name.trim();

  const name = [driver.first_name, driver.last_name].filter(Boolean).join(" ").trim();
  if (name) return name;
  if (driver.email?.trim()) return driver.email.trim();
  if (driver.phone?.trim()) return driver.phone.trim();
  return "Unknown driver";
}
