import puppeteer from "puppeteer";

const browser = await puppeteer.launch();
const page = await browser.newPage();
await page.goto("http://localhost:8000");
await page.pdf({ path: "example.pdf", format: "A4" });

await browser.close();
