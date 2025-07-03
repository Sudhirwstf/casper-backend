import multer from "multer";
import path from "path";
import fs from "fs";
import { v4 as uuidv4 } from "uuid";
import { Request, Response, NextFunction } from "express";

// Create the uploads folder if it doesn't exist
const uploadDir = "uploads";
if (!fs.existsSync(uploadDir)) {
  fs.mkdirSync(uploadDir);
}

 //---------------------multer disk storage-----------
const storage = multer.diskStorage({
  destination: function (req, file, cb) {
    cb(null, uploadDir);
  },
  filename: function (req, file, cb) {
    const uniqueName = `${uuidv4()}${path.extname(file.originalname)}`;
    cb(null, uniqueName);
  },
});

// ----------------Filter to allow only images
const imageFileFilter = (req: any, file: any, cb: any) => {
  if (!file.mimetype.startsWith("image/")) {
    const error: any = new Error("Only image files are allowed");
    error.statusCode = 400;
    return cb(error, false);
  }
  cb(null, true);
};

// only saves valid images to disk
export const uploadImage = multer({
  storage,
  fileFilter: imageFileFilter,
  limits: { fileSize: 10 * 1024 * 1024 }, 
});



//--------------------------audio file filter
export const audioFileFilter = (req: any, file: any, cb: any) => {
  if (!file.mimetype.startsWith("audio/")) {
    const error: any = new Error("Only audio files are allowed");
    error.statusCode = 400;
    return cb(error, false);
  }
  cb(null, true);
}

export const uploadAudio = multer({
  storage,
  fileFilter: audioFileFilter,
 
});

const videoFileFilter = (req: any, file: any, cb: any) => {
  if (!file.mimetype.startsWith("video/")) {
    const error: any = new Error("Only video files are allowed");
    error.statusCode = 400;
    return cb(error, false);
  }
  cb(null, true);
}

export const uploadVideo = multer({
  storage,
  fileFilter: videoFileFilter,
})

// error handler

export function multerHandler(middleware: any) {
  return (req: Request, res: Response, next: NextFunction) => {
    middleware(req, res, function (err: any) {
      if (err instanceof multer.MulterError || err?.statusCode) {
        return res.status(err.statusCode || 400).json({
          status: false,
          error: err.message || "File upload error",
        });
      }

      if (err) {
        return res.status(400).json({
          status: false,
          error: err.message || "Unknown error",
        });
      }

      next();
    });
  };
}
