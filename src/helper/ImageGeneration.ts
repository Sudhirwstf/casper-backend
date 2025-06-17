

import dotenv from "dotenv";
dotenv.config();


import { spawn } from "child_process";
import path from "path";

function ImageGenerationHelper(
  
): Promise<{uuid: string } | null> {
  console.log("__dirname:", __dirname);

  return new Promise((resolve, reject) => {
    const python = spawn("python", [
      "./Casper_Ai_Pipeline-image-optimization/Casper_Ai_Pipeline-image-optimization/main.py",
  
    ]);


   

    python.stdout.on("data", (data) => {
      console.log(`stdout: ${data}`);
    });

    python.stderr.on("data", (data) => {
      const text = data.toString();
      console.error(`stderr: ${text}`);

     
    });

    python.on("close", (code) => {
      console.log(`child process exited with code ${code}`);
     
      }
   
    );
  });
}

export default ImageGenerationHelper;

