

import { param } from "drizzle-orm";
import { z } from "zod";

const PlatformValues = ["facebook", "linkedin", "instagram_threads","x.com","medium","blogger"] as const;
const ImagePlatformValues = ["facebook", "linkedin", "instagram","x.com","pinterest"] as const;



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


  static generateImageValidator = z.object({
    body: z.object({
      platforms: z
        .string({ required_error: "platforms is required" })
        .refine(
          (val) => {
            const values = val.split(',').map((v) => v.trim().toLowerCase());
            return values.every((v) => ImagePlatformValues.includes(v as any));
          },
          {
            message: `Invalid platform value. Must be one of: ${ImagePlatformValues.join(", ")}`,
          }
        ),
      description: z
        .string({ required_error: "description is required" })
        .min(3, "description must be at least 3 characters long"),
      useAI: z
        .string({ required_error: "useAI is required" }) // coming from req.body, so it's a string
        .refine((val) => val === "true" || val === "false", {
          message: "useAI must be 'true' or 'false'",
        }),
      styleChoice: z
        .preprocess((val) => Number(val), z
          .number({ required_error: "styleChoice is required" })
          .min(1, "styleChoice must be at least 1")
          .max(7, "styleChoice must be at most 7")
        ),
      colorChoice: z
        .union([
          z
            .preprocess((val) => Number(val), z.number().min(1).max(15)),
          z.literal(undefined),
        ])
        .optional(),
    })
    .refine((data) => {
      const style = Number(data.styleChoice);
      const color = Number(data.colorChoice);
      if (style === 7) {
        return !isNaN(color) && color >= 1 && color <= 15;
      }
      return true;
    }, {
      message: "colorChoice is required and must be between 1 and 15 when styleChoice is 7",
      path: ["colorChoice"],
    }),
    params: z.object({}).strict(),
    query: z.object({}).strict(),
  });


}
