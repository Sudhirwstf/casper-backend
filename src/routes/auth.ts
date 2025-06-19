import express from "express"
import controllers from "../controllers";
import validators from "../validators";
import { validateRequest } from "../middleware";
const router=express.Router()

router.get('/google',controllers.auth.googleSignInSignUp);



export default router