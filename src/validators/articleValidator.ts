

import { z } from "zod";

const PlatformValues = ["facebook", "linkedin", "instagram_threads","x.com","medium","blogger"] as const;

const lowercaseEnum = <T extends readonly string[]>(values: T) =>
  z
    .string({ required_error: "Field is required" })
    .transform((val) => val.toLowerCase())
    .refine((val): val is T[number] => (values as readonly string[]).includes(val), {
      message: `Must be one of: ${values.join(", ")}`,
    });

export class articleValidator {
  static textGenerationValidator = z.object({
       body: z
      .object({
        userPrompt: z.string({ required_error: "prompt is required" }).min(3,"prompt must be at least 3 characters long"),

        platform: z
          .array(lowercaseEnum(PlatformValues), {
            required_error: "platform is required",
          })
          .nonempty("At least one platform is required"),

        isImageRequired: z.array(lowercaseEnum(PlatformValues), {
          required_error: "isImageRequired is required",
        }),

        compile: z
          .string({ required_error: "compile is required" })
          .transform((val) => val.toLowerCase())
          .refine((val): val is "yes" | "no" => ["yes", "no"].includes(val), {
            message: "Compile must be 'yes' or 'no'",
          }),
      })
      .strict()
      .refine(
        (data) =>
          data.isImageRequired.every((imgPlatform) =>
            data.platform.includes(imgPlatform)
          ),
        {
          message: "All isImageRequired values must also be present in platform array",
          path: ["isImageRequired"], 
        }
      ),

    params: z.object({}).strict(),
    query: z.object({}).strict(),
  });
}