import express from "express";
import router from "./routes";
import cors from "cors"
import passport from "passport";

import { jwtStrategy } from "./config/token";
import { envConfigs } from "./config/envconfig";

import swaggerUi from 'swagger-ui-express';
import swaggerSpec from "./config/swaggerConfig"

const app = express();

app.use(express.json());
app.use(express.urlencoded({ extended: true }));

app.use(cors({ origin: "*"}));
passport.use('jwt', jwtStrategy);


app.use("/", router);
app.use("/api-docs", swaggerUi.serve, swaggerUi.setup(swaggerSpec));


app.listen(envConfigs.port, () => {
  console.log(`Server started on ${envConfigs.port}`);
});

