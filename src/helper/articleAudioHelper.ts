import { spawn } from "child_process";

export async function runPythonScriptAudio(scriptPath: string): Promise<string> {
    return new Promise((resolve, reject) => {
        const python = spawn("python", ["./Ai_audio_optimization/main.py", scriptPath]);

        let sessionId: string | null = null;

        python.stdout.on("data", (data) => {
            const text = data.toString();
            console.log("[PYTHON]", text.trim());

            // ✅ Match UUID line: [PYTHON] session started for UUID: <uuid>
            const uuidMatch = text.match(/UUID:\s*([a-f0-9-]{36})/i);
            if (uuidMatch && !sessionId) {
                sessionId = uuidMatch[1];
                console.log("📌 Session ID captured:", sessionId);
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
            if (code === 0 && sessionId) {
                resolve(sessionId); // ✅ Resolve only after process ends successfully
            } else if (!sessionId) {
                reject(new Error("UUID not captured from Python output."));
            } else {
                reject(new Error(`Python process exited with code ${code}`));
            }
        });
    });
}
