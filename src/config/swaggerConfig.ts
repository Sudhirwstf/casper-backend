// swagger.ts
import swaggerJSDoc from 'swagger-jsdoc';
import { Options } from 'swagger-jsdoc';

const options: Options = {
  definition: {
    openapi: '3.0.0',
    info: {
      title: 'CASPER -AI',
      version: '1.0.0',
   description: `
**Casper AI** is an intelligent content generation platform designed to boost social media engagement through advanced AI-driven APIs.

### ✨ Available APIs:

1. **Text Generation for Social Media**
   - Automatically generates engaging captions, posts, and hashtags.
   - Supports multiple platforms (e.g., Instagram, Twitter, LinkedIn).
   - Returns platform-optimized text, metadata, posting time suggestions, and image recommendations.

2. **Image Generation for Maximum Reach**
   - AI-powered and manual image generation options.
   - Style and color theme customization.
   - Tailored for each platform's format and engagement patterns.

3. **Audio Enhancement**
   - Accepts uploaded audio (e.g., voice recordings, podcasts).
   - Uses AI models to remove noise and enhance speech clarity.
   - Returns high-quality audio ready for social distribution.

4. **Video Enhancement for Social Media**
   - Accepts raw video uploads.
   - Automatically detects and fills gaps (e.g., silent pauses, dead frames).
   - Outputs refined videos for short-form and long-form platforms.

---

All APIs are secured using **Bearer Token Authentication**. For testing in Swagger UI, click on "Authorize" and enter your token.

Casper AI is built to serve creators, brands, and marketing teams aiming to scale content quality and output with minimal effort.
`
,
    },
    components: {
      securitySchemes: {
        bearerAuth: {
          type: 'http',
          scheme: 'bearer',
        },
      },
    },
    servers: [
      
      {
        url: 'http://localhost:8000'
      }
    ],
  },
  apis: ['./src/routes/*.ts'],
};

const swaggerSpec = swaggerJSDoc(options);
export default swaggerSpec;
