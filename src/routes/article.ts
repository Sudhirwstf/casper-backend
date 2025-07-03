import express from "express"
import controllers from "../controllers";
import validators from "../validators";
import { authenticateUser, validateRequest } from "../middleware";
import articleController from "../controllers/article";
import { auth } from "../controllers/auth";


import multer from 'multer';
import { articleValidator } from "../validators/articleValidator";
import { multerHandler, uploadAudio, uploadImage, uploadVideo } from "../helper/multer";







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
 *       - Article
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
router.post('/generate-image',multerHandler(uploadImage.single('image')),authenticateUser,validateRequest(articleValidator.generateImageValidator),articleController.generateContentImage);
/**
 * @swagger
 * /article/generate-audio:
 *   post:
 *     summary: Upload an audio file and generate enhanced podcast/audio content.
 *     tags:
 *       - Article
 *     consumes:
 *       - multipart/form-data
 *     requestBody:
 *       required: true
 *       content:
 *         multipart/form-data:
 *           schema:
 *             type: object
 *             required:
 *               - audio
 *             properties:
 *               audio:
 *                 type: string
 *                 format: binary
 *                 description: >
 *                   Audio file to be processed. Supported formats:
 *                   mpeg, wav, ogg, mp3, wave.
 *     responses:
 *       200:
 *         description: Audio generated successfully.
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 status:
 *                   type: boolean
 *                   example: true
 *                 sessionId:
 *                   type: string
 *                   example: "90d8de96-5d8a-4b86-a39e-9d71cf05fec4"
 *                 audio:
 *                   type: object
 *                   properties:
 *                     enhanced_8ea5849d-4f2f-4ff9-91c6-b42a692dcfaf:
 *                       type: object
 *                       properties:
 *                         uuid:
 *                           type: string
 *                           example: "2c3390f7-0461-4992-927f-d6f730e2a518"
 *                         url:
 *                           type: string
 *                           format: uri
 *                           example: "https://res.cloudinary.com/dmz4lknv4/video/upload/v1751031498/enhanced_audio/fasyfdusycwasfbqcvwd.wav"
 *                         transcript_uuid:
 *                           type: string
 *                           example: "34723a8d-83ef-424a-b907-849e2bb7bdbc"
 *                         apple_podcast_title:
 *                           type: string
 *                           example: "Midwest Heart Connection Chat"
 *                         apple_podcast_desc:
 *                           type: string
 *                           example: "Join us as we check in midway with the boys from the Midwest Heart Connection. We discuss their current state, the weather in Nebraska, and their love for rain over sunshine."
 *                         spotify_title:
 *                           type: string
 *                           example: "Midwest Heart Connection: A Journey Through Nebraska"
 *                         spotify_desc:
 *                           type: string
 *                           example: "Join us as we traverse the great state of Nebraska on 'Midwest Heart Connection'. We're midway through our journey, the weather's wild, but our spirits are high. Rain or shine, we're taking on the Midwest with smiles on our faces. Tune in to our podcast for heartwarming stories, thrilling adventures, and a genuine exploration of America's heartland. Click here to journey with us: https://spoti.fi/MidwestHeartConnection"
 *                 message:
 *                   type: string
 *                   example: "Audio generated successfully"
 *       400:
 *         description: Invalid request. Audio file missing or unsupported format.
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 error:
 *                   type: string
 *                   example: "Invalid file type. Only audio files are allowed (mpeg, wav, ogg, mp3, wave)."
 *       500:
 *         description: Server error during audio generation.
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
 *                   example: "Failed to generate audio"
 */



// Audio generation 
router.post('/generate-audio',multerHandler(uploadAudio.single('audio')),authenticateUser,validateRequest(articleValidator.audioValidator),articleController.generateContentAudio);



/**
 * @swagger
 * /article/generate-video:
 *   post:
 *     summary: Generate platform videos and download as ZIP
 *     tags:
 *       - Article
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               video:
 *                 type: string
 *                 example: "aaa1.mp4"
 *               platforms:
 *                 type: array
 *                 items:
 *                   type: string
 *                 example: ["instagram", "youtube"]
 *     responses:
 *       200:
 *         description: ZIP file containing platform videos
 *         content:
 *           application/zip:
 *             schema:
 *               type: string
 *               format: binary
 *       400:
 *         description: Video generation failed
 *       500:
 *         description: Internal server error
 */


// video generation
router.post('/generate-video',multerHandler(uploadVideo.single('video')),authenticateUser,validateRequest(articleValidator.videoContentValidator),articleController.generateContentVideo);

export default router