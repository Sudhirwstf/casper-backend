import { spawn } from "child_process";

export const runPythonScriptVideo = async (videoPath: string, platforms: string[]): Promise<string> => {
  return new Promise((resolve, reject) => {
    const args = ["./Ai_video_optimizer/main.py", videoPath, "--platforms", ...platforms];
    console.log("args", args);

    const python = spawn("python", args);

    let sessionId: string | null = null;
    let errorOutput = "";

    python.stdout.on("data", (data) => {
      const text = data.toString();
      console.log("[PYTHON STDOUT]", text);

      // Check for line containing session ID
      const match = text.match(/🆔 Starting new processing session:\s*([a-f0-9-]+)/i);
      if (match && match[1]) {
        sessionId = match[1];
      }
    });

    python.stderr.on("data", (data) => {
      const errText = data.toString();
      errorOutput += errText;
      console.error("[PYTHON STDERR]", errText);
    });

    python.on("close", (code) => {
      if (code === 0 && sessionId) {
        resolve(sessionId);
      } else {
        reject(new Error(`Python script exited with code ${code}. ${errorOutput || "Session ID not found."}`));
      }
    });
  });
};
