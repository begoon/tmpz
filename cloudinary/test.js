import { v2 as cloudinary } from "cloudinary";
import fs from "node:fs";

import dotenv from "dotenv";

dotenv.config();

cloudinary.config({
    cloud_name: process.env.CLOUDINARY_CLOUD_NAME,
    api_key: process.env.CLOUDINARY_API_KEY,
    api_secret: process.env.CLOUDINARY_API_SECRET,
});
console.log(process.env);

const filename = "avatar.png";
const [name, ext] = filename.split(".");
const content = Buffer.from(fs.readFileSync(filename, "base64")).toString();
console.log(content.slice(0, 100) + "...");

try {
    await cloudinary.uploader.upload("data:image/png;base64," + content, {
        public_id: name,
        format: ext,
        folder: "dashok/media/ru",
        overwrite: true,
        unique_filename: false,
    });
} catch (error) {
    console.error(error);
}
