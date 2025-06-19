import * as dotenv from "dotenv";
dotenv.config();
import { z } from "zod";

const envVarsSchema = z.object({
  PORT: z.string().default("80").transform((str) => parseInt(str, 10)),  
  HOST: z.string(),
  DBUSER: z.string(),
  PASSWORD: z.string(),
  DATABASE: z.string(),
  DBPORT: z.string().default("5432").transform((str) => parseInt(str, 10)),
  SSL: z.enum(["true", "false"]).transform((str) => str === "true"),
  DB_URL: z.string(),
  GOOGLE_CLIENT_ID: z.string(),
  GOOGLE_CLIENT_SECRET: z.string(),
  REDIRECT_URI: z.string(),
  // FRONTEND_REDIRECT_URL_local: z.string().url(),
  // FRONTEND_REDIRECT_URL: z.string().url(),
  // FRONTEND_URL_local: z.string().url(),
  JWT_SECRET: z.string(),
  EXPIREATION_MINUTE:z.string(),
 
  

});

const envVars = envVarsSchema.parse(process.env);
export const envConfigs = {
  port: envVars.PORT || 8080,
  db: {
    host: envVars.HOST,
    user: envVars.DBUSER,
    password: envVars.PASSWORD,
    database:envVars.DATABASE,
    port: envVars.DBPORT,
    ssl: envVars.SSL,
  },
  databaseUrl:envVars.DB_URL,
  googleClientId: envVars.GOOGLE_CLIENT_ID,
  googleClientSecret: envVars.GOOGLE_CLIENT_SECRET,
  redirectUri: envVars.REDIRECT_URI,
  // frontendRedirectUrlLocal: envVars.FRONTEND_REDIRECT_URL_local,
  // frontendRedirectUrl: envVars.FRONTEND_REDIRECT_URL,
  // frontendUrlLocal: envVars.FRONTEND_URL_local,
  jwtsecret:envVars.JWT_SECRET,
  accessExpirationMinutes:envVars.EXPIREATION_MINUTE,
 
};

