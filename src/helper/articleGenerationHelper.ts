import dotenv from "dotenv";
dotenv.config();


import { spawn } from "child_process";
import path from "path";

function articleHelper(
  filepath: string,
  platform: string,
  isImageRequired: string,
  compile: string
): Promise<{uuid: string } | null> {
  console.log("__dirname:", __dirname);

  return new Promise((resolve, reject) => {
    const python = spawn("python", [
      "./Article_optimizer-main/main.py",
      filepath,          // ./UserFiles/article.txt
      platform.toString(),          //["linkedin","facebook"]
      isImageRequired,   // ["none"] or  ['all]
      compile,            //"yes"
    ]);

    let jsonFile: string | null = null;
    let uuid: string | null = null;

    const jsonRegex = /Saved .* optimization to:\s*([a-f0-9-]+.*optimization.*\.json)/i;

    python.stdout.on("data", (data) => {
      console.log(`stdout: ${data}`);
    });

    python.stderr.on("data", (data) => {
      const text = data.toString();
      console.error(`stderr: ${text}`);

      const lines = text.split("\n");
      for (const line of lines) {
        const match = line.match(jsonRegex);
        if (match) {
          jsonFile = match[1].trim();
          uuid = jsonFile.split("_")[0];
          
          // Once found, resolve immediately
          resolve({uuid:uuid});
          return;
        }
      }
    });

    python.on("close", (code) => {
      console.log(`child process exited with code ${code}`);
      if(code==1){
        resolve(null);
      }
      // If process ends but no file found, return null
      if (!uuid) {
        resolve(null);
      }
    });

    python.on("error", (err) => {
      reject(err);
    });
  });
}

export default articleHelper;

