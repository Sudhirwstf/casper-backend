import { spawn } from "child_process";

export async function runPythonScriptAudio(scriptPath: string): Promise<string> {
    return new Promise((resolve, reject) => {
        const python = spawn("python", ["./audio_optimization/scripts/main.py", scriptPath]);

        let sessionId: string | null = null;
        let outputPath: string | null = null;

        python.stdout.on("data", (data) => {
            const text = data.toString();
            console.log("[PYTHON]", text.trim());

            // Match UUID line
            const uuidMatch = text.match(/Run UUID:\s*([a-f0-9-]+)/i);
            if (uuidMatch) {
                sessionId = uuidMatch[1];
                console.log("📌 Session ID captured:", sessionId);
            }

            // Match "All done" output line
            const doneMatch = text.match(/All done! Output saved to:\s*(.*\.json)/i);
            if (doneMatch && sessionId) {
                outputPath = doneMatch[1].trim();
                console.log("Final output path:", outputPath);
                resolve(sessionId);
               
            }
        });

        python.stderr.on("data", (data) => {
            console.error("[PYTHON ERR]", data.toString());
        });

        python.on("error", (err) => {
            reject(new Error("Failed to start Python process: " + err.message));
        });

        python.on("close", (code) => {
             console.log(`child process exited with code ${code}`);
            if (code !== 0) {
                reject(new Error(`Python process exited with code ${code}`));
            }
        });
    });
}
