import { z } from "zod";

const stopSchema = z.object({
  stop_type: z.enum(["PICKUP", "DELIVERY"]),
  sequence: z.number().min(1),
  city: z.string().optional(),
});

export const createOrderSchema = z.object({
  customer_id: z.string().min(1, "Select a customer"),
  pickup_stops: z.array(stopSchema).min(1),
  delivery_stops: z.array(stopSchema).min(1),
  vehicles: z
    .array(
      z.object({
        make: z.string().optional(),
        model: z.string().optional(),
      }),
    )
    .min(1),
});

export type CreateOrderFormValues = z.infer<typeof createOrderSchema>;
