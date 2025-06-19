

import dotenv from "dotenv";
dotenv.config();


import { ChildProcess, spawn } from "child_process";
import path from "path";
import { child } from "winston";

function ImageGenerationHelper( args: string[]): Promise<{uuid: string } | null> {
  console.log("__dirname:", __dirname);

 

const pythonProcess = spawn('python', args);
  return new Promise((resolve, reject) => {
    const python = spawn("python", args);


   

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

