import { Request, Response } from "express";
import articleHelper from "../helper/articleGenerationHelper";
import { array } from "zod";
import fs from "fs";
import path from "path";
import dbservices from "../services/dbservices";
import { ArticleServices } from "../services/dbservices/articles";
import ImageGenerationHelper from "../helper/ImageGeneration";

// platform must be array of social media
type Platform =
  | "facebook"
  | "twitter"
  | "linkedin"
  | "Threads"
  | "Instagram"
  | "x.com";

interface articleBody {
  userPrompt: string;
  platform: Platform[];
  isImageRequired: string[];
  compile: string;
}
export default class articleController {
  static generateArticle = async (
    req: Request,
    res: Response
  ): Promise<void> => {
    const { userPrompt, platform, isImageRequired, compile }: articleBody =
      req.body;
      console.log(userPrompt, platform, isImageRequired, compile)

   try {

     if (!userPrompt) {
      res
        .status(400)
        .send({ status: false, message: "Please Enter User Prompt" });
      return;
    }

    //if platform is not array

    if (!Array.isArray(platform) || platform.length === 0) {
      res
        .status(400)
        .send({ status: false, message: "Please enter at least one platform" });
      return;
    }

    const isFolderExist = fs.existsSync("./UserFiles");
    if (!isFolderExist) {
      fs.mkdirSync("./UserFiles");
    }
    const uiqueFileName = Math.random().toString(36).substr(2, 8).toUpperCase();

    fs.writeFileSync(`./UserFiles/${uiqueFileName}.txt`, userPrompt);

    const filepath = `./UserFiles/${uiqueFileName}.txt`;

    console.log(filepath, platform, isImageRequired, compile);

    const generatedArticle = await articleHelper(
      filepath,
      platform.toString(),
      isImageRequired.toString(),
      compile
    );

    if (generatedArticle && generatedArticle.uuid) {
      const { jsonFiles, txtFiles } = articleController.getFilesByUuid(
        generatedArticle.uuid
      );
      console.log("JSON Files:", jsonFiles);
      console.log("TXT Files:", txtFiles);

      // read the json

      const jsonFileContents = jsonFiles.map((filePath) => {
        try {
          const content = fs.readFileSync(filePath, "utf-8");
          return {
            filename: path.basename(filePath),
            content: JSON.parse(content),
          };
        } catch (err) {
          console.error("Failed to read or parse JSON file:", filePath, err);
          return { filename: path.basename(filePath), content: null };
        }
      });

      const trimTxtContent = (
        filePath: string
      ): { filename: string; content: string | null } => {
        try {
          const raw = fs.readFileSync(filePath, "utf-8");
          const lines = raw.split("\n");

          const firstDividerIndex = lines.findIndex(
            (line) =>
              line.trim() ===
              "=================================================="
          );
          const secondDividerIndex = lines.findIndex(
            (line, i) =>
              i > firstDividerIndex &&
              line.trim() ===
                "=================================================="
          );

          let content = null;
          if (firstDividerIndex !== -1 && secondDividerIndex !== -1) {
            const sliced = lines.slice(
              firstDividerIndex + 1,
              secondDividerIndex
            );
            content = sliced.join("\n").trim(); // final trimmed content
          }

          return {
            filename: path.basename(filePath),
            content,
          };
        } catch (err) {
          console.error("Error reading or trimming file:", filePath, err);
          return {
            filename: path.basename(filePath),
            content: null,
          };
        }
      };

      const textFiles = txtFiles.map(trimTxtContent);

      console.log("textFiles", textFiles);

      // remove file uiqueFileName

      fs.unlinkSync(`./UserFiles/${uiqueFileName}.txt`);

      //remove all files which starts with uuid in shared_optimization_results

      const optimizationDir = path.resolve("shared_optimization_results");
      if (fs.existsSync(optimizationDir)) {
        const allFiles = fs.readdirSync(optimizationDir);
        for (const file of allFiles) {
          if (file.startsWith(generatedArticle.uuid)) {
            fs.unlinkSync(path.join(optimizationDir, file));
          }
        }
      }


      console.log("text file before", textFiles);
      const {success,remainingCredits} = await dbservices.ArticleServices.saveArticles(
        textFiles,
       3
      );

      console.log("saveArticles", success, remainingCredits);

      if (success) {
        res.json({
          status: true,
          message: "Article Generated Successfully",
          credits: remainingCredits,
          jsonFileContents,
          textFiles,
        });
      }
    }
    
   } catch (error) {
    res.status(500).json({ status: false, message: error });
    console.error("Error:", error);
    
   }
  };

  static getFilesByUuid(uuid: string) {
    const optimizationDir = path.resolve("shared_optimization_results");

    const jsonFiles: string[] = [];
    const txtFiles: string[] = [];

    // Check for JSON optimization files
    if (fs.existsSync(optimizationDir)) {
      const allFiles = fs.readdirSync(optimizationDir);
      for (const file of allFiles) {
        if (
          file.startsWith(uuid) &&
          file.includes("optimization") &&
          file.endsWith(".json")
        ) {
          jsonFiles.push(path.join(optimizationDir, file));
        }
      }
    }

    // Check for TXT files
    if (fs.existsSync(optimizationDir)) {
      const allFiles = fs.readdirSync(optimizationDir);
      for (const file of allFiles) {
        if (
          file.startsWith(uuid) &&
          file.endsWith(".txt") &&
          file.includes("readable")
        ) {
          txtFiles.push(path.join(optimizationDir, file));
        }
      }
    }

    return { jsonFiles, txtFiles };
  }

  static generateImage = async (req: Request, res: Response): Promise<void> => {
    try {
      const {userPrompt,platforms,isImageRequired}=req.body.userPrompt
      const generatedImage=await ImageGenerationHelper(userPrompt,platforms,isImageRequired)
     
    } catch (error) {
      res.status(500).json({ status: false, message: error });
    }
  };
}
