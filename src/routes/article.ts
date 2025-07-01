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
import { articleValidator } from "../validators/articleValidator";




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
 *     security:
 *       - bearerAuth: []  # Requires Bearer token via Authorize button
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
 *                 description: List of social media platforms
 *                 items:
 *                   type: string
 *                 example:
 *                   - x.com
 *                   - linkedin
 *               isImageRequired:
 *                 type: array
 *                 description: Platforms where images are required
 *                 items:
 *                   type: string
 *                 example:
 *                   - x.com
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


router.post('/generate-article',authenticateUser,validateRequest(articleValidator.textGenerationValidator), articleController.generateArticle);




/**
 * @swagger
 * /article/generate-image:
 *   post:
 *     summary: Generate content image and captions for selected social media platforms
 *     tags:
 *       - Image
 *     security:
 *       - bearerAuth: []  # Requires Bearer token via Authorize button
 *     requestBody:
 *       required: true
 *       content:
 *         multipart/form-data:
 *           schema:
 *             type: object
 *             required:
 *               - image
 *               - platforms
 *               - description
 *               - useAI
 *               - styleChoice
 *             properties:
 *               image:
 *                 type: string
 *                 format: binary
 *                 description: Image file to upload (only image/* types are accepted)
 *               platforms:
 *                 type: string
 *                 description: Comma-separated list of target platforms
 *                 example: instagram,twitter
 *               description:
 *                 type: string
 *                 description: Description for the image
 *                 example: "Promotional banner for our AI tool"
 *               useAI:
 *                 type: string
 *                 enum: [true, false]
 *                 description: Whether to use AI for content generation
 *                 example: "true"
 *               styleChoice:
 *                 type: integer
 *                 minimum: 1
 *                 maximum: 7
 *                 description: Style preset number (1 to 7)
 *                 example: 3
 *               colorChoice:
 *                 type: integer
 *                 minimum: 1
 *                 maximum: 15
 *                 description: Required only when styleChoice is 7
 *                 example: 4
 *     responses:
 *       200:
 *         description: Content image and captions generated successfully
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 success:
 *                   type: boolean
 *                   example: true
 *                 sessionId:
 *                   type: string
 *                   example: "abc123-session"
 *                 captions:
 *                   type: object
 *                   additionalProperties:
 *                     type: string
 *                   example:
 *                     abc123_instagram.txt: "Generated caption for Instagram"
 *                 json:
 *                   type: object
 *                   description: Final combined JSON output
 *       400:
 *         description: Missing or invalid input parameters
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 error:
 *                   type: string
 *                   example: Platforms are required.
 *       401:
 *         description: Unauthorized - User not logged in
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 error:
 *                   type: string
 *                   example: Unauthorized user.
 *       500:
 *         description: Internal server error during image generation
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 error:
 *                   type: string
 *                   example: Failed to generate content image.
 */

// Image generation with text
router.post('/generate-image',upload.single('image'),authenticateUser,validateRequest(articleValidator.generateImageValidator),articleController.generateContentImage);

// Audio generation 
router.post('/generate-audio',upload.single('audio'),articleController.generateContentAudio);



export default router