
import archiver from "archiver";
import path from "path";
import fs from "fs";

export async function createVideoZip(sessionId: string, files: string[], videoData: any): Promise<string> {
  const outputDir = './Ai_video_optimizer/output/formatted';
  const zipPath = `./temp/${sessionId}.zip`;
  const metadataPath = `./temp/${sessionId}_meta.json`;

  await fs.promises.mkdir('./temp', { recursive: true });

  // Write metadata JSON temporarily
  await fs.promises.writeFile(metadataPath, JSON.stringify(videoData, null, 2), 'utf-8');

  return new Promise((resolve, reject) => {
    const output = fs.createWriteStream(zipPath);
    const archive = archiver("zip", { zlib: { level: 9 } });

    output.on("close", async () => {
      // Cleanup metadata file after zipping
      await fs.promises.unlink(metadataPath);
      resolve(zipPath);
    });

    archive.on("error", reject);
    archive.pipe(output);

    // Add all matched videos
    for (const file of files) {
      archive.file(path.join(outputDir, file), { name: file });
    }

    // Add the JSON metadata file
    archive.file(metadataPath, { name: "metadata.json" });

    archive.finalize();
  });
}
