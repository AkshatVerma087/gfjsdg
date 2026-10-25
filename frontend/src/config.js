import { z } from "zod";

const configSchema = z.object({
  apiBaseUrl: z
    .string()
    .trim()
    .refine(
      (val) => val === "" || val.startsWith("http://") || val.startsWith("https://"),
      {
        message: "VITE_API_BASE_URL must be empty or start with http:// or https://",
      }
    ),
});

export function parseConfig(env) {
  const result = configSchema.safeParse({
    apiBaseUrl: env?.VITE_API_BASE_URL ?? "",
  });

  if (!result.success) {
    const errorMsg = result.error.errors.map((e) => e.message).join(", ");
    throw new Error(`Frontend configuration error: ${errorMsg}`);
  }

  return result.data;
}

export const config = parseConfig(import.meta.env);
