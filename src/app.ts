import express, { Response } from "express";
import router from "./routes";
import cors from "cors"
import passport from "passport";
import multer from "multer";

import { jwtStrategy } from "./config/token";
import { envConfigs } from "./config/envconfig";

import swaggerUi from 'swagger-ui-express';
import swaggerSpec from "./config/swaggerConfig"

const app = express();

app.use(express.json());
app.use(express.urlencoded({ extended: true }));

app.use(cors({ origin: "*"}));

// Global error handler for multer and other errors
app.use((err: any, req, res, next) => {
  if (err instanceof multer.MulterError || err.statusCode) {
    return res.status(err.statusCode || 400).json({
      status: false,
      error: err.message || "File upload error",
    });
  }

  // Handle unexpected errors
  return res.status(500).json({
    status: false,
    error: "Internal server error",
  });
});

passport.use('jwt', jwtStrategy);


app.use("/", router);
app.use("/api-docs", swaggerUi.serve, swaggerUi.setup(swaggerSpec));



app.get('/', (req, res) => {
  res.send("Server is running")
})



app.listen(envConfigs.port, () => {
  console.log(`Server started on ${envConfigs.port}`);
});

