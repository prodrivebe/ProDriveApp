import { describe, expect, it } from "vitest";
import { login } from "./authService";

describe("authService", () => {
  it("exports login helper", () => {
    expect(typeof login).toBe("function");
  });
});
