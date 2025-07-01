
import { Request, Response } from "express";
import articleHelper from "../helper/articleGenerationHelper";
import { promises as fs } from "fs";
import path from "path";
import dbservices from "../services/dbservices";
import { runPythonScript } from "../helper/articleImageHelper";
import { runPythonScriptAudio } from "../helper/articleAudioHelper";

// platform must be array of social media
type Platform =
  | "facebook"
  | "blogger"
  | "linkedin"
  | "medium"
  | "instagram_threads"
  | "x.com";

interface articleBody {
  userPrompt: string;
  platform: Platform[];
  isImageRequired: string[];
  compile: string;
}

interface AuthenticateRequest extends Request {
  user?: { userId: number | string };
  body: any;
  file?: any;
}

export default class articleController {
  static generateArticle = async (req: AuthenticateRequest, res: Response): Promise<void> => {
    try {
      const userId = req.user?.userId;
      

      console.log('userId',userId)
      if (!userId) {
        res.status(401).send({ status: false, message: "UNAUTHORIZED USER" });
        return;
      }

      const { userPrompt, platform, isImageRequired, compile }: articleBody = req.body;
      if (!userPrompt) {
        res.status(400).send({ status: false, message: "Please Enter User Prompt" });
        return;
      }

      if (!Array.isArray(platform) || platform.length === 0) {
        res.status(400).send({ status: false, message: "Please enter at least one platform" });
        return;
      }

      try {
        await fs.access("./UserFiles");
      } catch {
        await fs.mkdir("./UserFiles");
      }

   

      const uniqueFileName = Math.random().toString(36).substr(2, 8).toUpperCase();
      const filePath = `./UserFiles/${uniqueFileName}.txt`;
      await fs.writeFile(filePath, userPrompt);

         console.log(filePath,
        platform.toString(),
        isImageRequired.toString(),
        compile.toLocaleLowerCase())
      
     

      const generatedArticle = await articleHelper(
        filePath,
        platform.toString(),
        isImageRequired.toString(),
        compile.toLocaleLowerCase()
      );

      if(!generatedArticle){
        res.status(400).send({ status: false, message: "Article generation failed" });
        return;
      }

      if (generatedArticle?.uuid) {
        const { jsonFiles, txtFiles } = await articleController.getFilesByUuid(generatedArticle.uuid);

        const jsonFileContents = await Promise.all(
          jsonFiles.map(async (filePath) => {
            try {
              const content = await fs.readFile(filePath, "utf-8");
              return { filename: path.basename(filePath), content };
            } catch (err) {
              return { filename: path.basename(filePath), content: null };
            }
          })
        );

        const trimTxtContent = async (filePath: string): Promise<{ filename: string; content: string | null }> => {
          try {
            const raw = await fs.readFile(filePath, "utf-8");
            const lines = raw.split("\n");
            const firstDividerIndex = lines.findIndex(line => line.trim() === "==================================================");
            const secondDividerIndex = lines.findIndex((line, i) => i > firstDividerIndex && line.trim() === "==================================================");

            let content = null;
            if (firstDividerIndex !== -1 && secondDividerIndex !== -1) {
              content = lines.slice(firstDividerIndex + 1, secondDividerIndex).join("\n").trim();
            }

            return { filename: path.basename(filePath), content };
          } catch (err) {
            return { filename: path.basename(filePath), content: null };
          }
        };

        const textFiles = await Promise.all(txtFiles.map(trimTxtContent));

        await fs.unlink(filePath);

        const optimizationDir = path.resolve("shared_optimization_results");
        try {
          await fs.access(optimizationDir);
          const allFiles = await fs.readdir(optimizationDir);
          await Promise.all(
            allFiles
              .filter(file => file.startsWith(generatedArticle.uuid))
              .map(file => fs.unlink(path.join(optimizationDir, file)))
          );
        } catch {}

        const { success, remainingCredits } = await dbservices.ArticleServices.saveArticles(textFiles, +userId);

        if (success) {
          res.status(200).json({
            status: true,
            message: "Article Generated Successfully",
            credits: remainingCredits,
            jsonFileContents,
            textFiles,
          });
        } else {
          res.status(500).json({ status: false, message: "Failed to save article" });
        }
      }
    } catch (error: any) {
      res.status(500).json({ status: false, message: error.message || "Internal Server Error" });
    }
  };

  static getFilesByUuid = async (uuid: string): Promise<{ jsonFiles: string[]; txtFiles: string[] }> => {
    const optimizationDir = path.resolve("shared_optimization_results");
    const jsonFiles: string[] = [];
    const txtFiles: string[] = [];

    try {
      await fs.access(optimizationDir);
      const allFiles = await fs.readdir(optimizationDir);

      for (const file of allFiles) {
        const fullPath = path.join(optimizationDir, file);
        if (file.startsWith(uuid) && file.includes("optimization") && file.endsWith(".json")) {
          jsonFiles.push(fullPath);
        } else if (file.startsWith(uuid) && file.endsWith(".txt") && file.includes("readable")) {
          txtFiles.push(fullPath);
        }
      }
    } catch {}

    return { jsonFiles, txtFiles };
  };


  //------------------------------Generate Content Image------------------------------//

  static generateContentImage = async (req: AuthenticateRequest, res: Response): Promise<any> => {
    try {
      const userId = req.user?.userId;

      if (!userId) {
        return res.status(401).json({ error: 'Unauthorized user.' });
      } 

      if (!req.file) {
        return res.status(400).json({ error: 'Photo is required.' });
      }

        const validImageTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/jpg' ];

    if (!validImageTypes.includes(req.file.mimetype)) {
      // Delete invalid file if needed
      await fs.unlink(req.file.path);
      return res.status(400).json({ error: 'Invalid file type. Only image files are allowed (jpeg, png, webp, gif).' });
    }

      const { platforms, description, useAI, styleChoice, colorChoice } = req.body;

      if (!platforms) {
        return res.status(400).json({ error: 'Platforms are required.' });
      }

      const styleNum = parseInt(styleChoice);
      const colorNum = parseInt(colorChoice);

      if (isNaN(styleNum) || styleNum < 1 || styleNum > 7) {
        return res.status(400).json({ error: 'Invalid style choice (1-7).' });
      }

      if (styleNum === 7 && (isNaN(colorNum) || colorNum < 1 || colorNum > 15)) {
        return res.status(400).json({ error: 'Invalid color choice (1-15).' });
      }


      console.log('platforms:', platforms);
     
      const photoPath = path.resolve(req.file.path);
      console.log({
        photoPath,
        platforms: platforms.split(',').map(platform => platform.trim()),
        description,
        useAI: useAI === 'true',
        styleChoice: styleNum,
        colorChoice: styleNum === 7 ? colorNum : undefined
      })

      
      

      const sessionId = await runPythonScript({
        photoPath,
        platforms: platforms.split(','),
        description,
        useAI: useAI === 'true',
        styleChoice: styleNum,
        colorChoice: styleNum === 7 ? colorNum : undefined,
      });

      if (!sessionId) {
        return res.status(500).json({ error: 'Failed to generate content image.' });
      }

      //delte photot from uplaods folder
      await fs.unlink(photoPath);

      const txtFolder = path.join(__dirname, '../../social_media_output/compiled_captions');
      const jsonFolder = path.join(__dirname, '../../social_media_output/json_results');

      const txtFiles = await fs.readdir(txtFolder);
      const matchedTxtFiles = txtFiles.filter(file => file.startsWith(sessionId) && file.endsWith('.txt'));

      const txtContents: Record<string, string> = {};
      for (const file of matchedTxtFiles) {
        const fullPath = path.join(txtFolder, file);
        const content = await fs.readFile(fullPath, 'utf-8');
        txtContents[file] = content;

        // delete txt file
        await fs.unlink(fullPath);
      }

      const jsonFiles = await fs.readdir(jsonFolder);
      const jsonMatch = jsonFiles.find(file => file.startsWith(`${sessionId}_combined_final_data_`) && file.endsWith('.json'));

      let jsonData: any = null;
      if (jsonMatch) {
        const jsonPath = path.join(jsonFolder, jsonMatch);
        const jsonContent = await fs.readFile(jsonPath, 'utf-8');
        jsonData = JSON.parse(jsonContent);

        // delete json file
        await fs.unlink(jsonPath);
      }

      return res.status(200).json({
        success: true,
        sessionId,
        captions: txtContents,
        json: jsonData,
      });

    } catch (err: any) {
      console.error('Controller error:', err);
      return res.status(500).json({ error: err.message || 'Unexpected error.' });
    }
  };


  //-------------------------------------Audio Generation controller------------------------------------//

  static generateContentAudio=async (req:AuthenticateRequest,res:Response):Promise<any>=>{
    
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'Audio is required.' });
    }
    console.log('audio',req.file);
    const audioFile=req.file.path;
    const audiopath=path.resolve(audioFile);
 
    console.log("audio",audiopath);

    
  

    const sessionId:string =await runPythonScriptAudio(audioFile);
    
    console.log('Id of session',sessionId);
    if(!sessionId){
      return res.status(400).json({ status: false, message: "Failed to generate audio" });
    }
   

    const audioFolder = path.join(process.cwd(), 'output');


   const audioFiles = await fs.readdir(audioFolder);
   const matchedAudioFiles:any= audioFiles.filter(file => file.startsWith(sessionId) && file.endsWith('final_output.json'));

    if(matchedAudioFiles.length===0){
      return res.status(400).json({ status: false, message: "Failed to generate audio" });
    }

    const jsonPath = path.join(audioFolder, matchedAudioFiles[0]);
    const audioContent = await fs.readFile(jsonPath, 'utf-8');
    const audioData = JSON.parse(audioContent);



     // delte audio from uploads and output folder
    await fs.unlink(audiopath);
  

    //delte all the files starting with session id
    const audioFilesToDelete = audioFiles.filter(file => file.startsWith(sessionId));
    for (const file of audioFilesToDelete) {
      const filePath = path.join(audioFolder, file);
      await fs.unlink(filePath);
    }

    return res.status(200).json({ status: true, sessionId, audio: audioData, message: "Audio generated successfully" });
   
   


    
  } catch (error) {
    console.error("Error occurred in generating Audio:", error);
    res.status(500).json({ status: false, message: "Failed to generate audio" });
    
  }
  }
}
