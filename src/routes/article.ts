import express from "express"
import controllers from "../controllers";
import validators from "../validators";
import { authenticateUser, validateRequest } from "../middleware";
import articleController from "../controllers/article";
import { auth } from "../controllers/auth";
import path from 'path';
import { v4 as uuidv4 } from 'uuid';
import fs from 'fs'
import multer from 'multer';




const uploadDir=fs.existsSync("uploads")?"uploads":fs.mkdirSync("uploads");

const storage = multer.diskStorage({
  destination: function (req, file, cb) {
    cb(null, uploadDir);
  },
  filename: function (req, file, cb) {
    const uniqueName = `${uuidv4()}${path.extname(file.originalname)}`;
    cb(null, uniqueName);
  },
});

export const upload = multer({ storage });

const router=express.Router()

/**
 * @swagger
 * /article/generate-article:
 *   post:
 *     summary: Generate articles for selected social media platforms
 *     tags:
 *       - Article
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - userPrompt
 *               - platform
 *               - isImageRequired
 *               - compile
 *             properties:
 *               userPrompt:
 *                 type: string
 *                 description: Prompt or topic for the article generation
 *                 example: "future opportunities in data science"
 *               platform:
 *                 type: array
 *                 description: List of social media platforms (comma-separated strings)
 *                 items:
 *                   type: string
 *                   example: ["x.com","linkedin"]
 *                   
 *               isImageRequired:
 *                 type: array
 *                 description: Platforms where images are required (comma-separated strings)
 *                 items:
 *                   type: string
 *                   example: "x.com"
 *               compile:
 *                 type: string
 *                 enum: [yes, no]
 *                 description: Whether to compile the results into a single output
 *                 example: "yes"
 *     responses:
 *       200:
 *         description: Article generated successfully
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 status:
 *                   type: boolean
 *                   example: true
 *                 message:
 *                   type: string
 *                   example: Article Generated Successfully
 *                 credits:
 *                   type: integer
 *                   example: 40
 *                 jsonFileContents:
 *                   type: array
 *                   items:
 *                     type: object
 *                     properties:
 *                       filename:
 *                         type: string
 *                         example: article_x_com.json
 *                       content:
 *                         type: object
 *                         description: Parsed JSON content
 *                 textFiles:
 *                   type: array
 *                   items:
 *                     type: object
 *                     properties:
 *                       filename:
 *                         type: string
 *                         example: article_x_com.txt
 *                       content:
 *                         type: string
 *                         description: Trimmed article text content
 *       400:
 *         description: Missing or invalid input parameters
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 status:
 *                   type: boolean
 *                   example: false
 *                 message:
 *                   type: string
 *                   example: Please Enter User Prompt
 *       500:
 *         description: Internal server error during generation
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 status:
 *                   type: boolean
 *                   example: false
 *                 message:
 *                   type: string
 *                   example: Internal Server Error
 */

router.post('/generate-article',authenticateUser, articleController.generateArticle);

router.post('/generate-image',upload.single('image'), articleController.generateContentImage);



export default router