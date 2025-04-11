import puppeteer from "puppeteer-extra";
import StealthPlugin from "puppeteer-extra-plugin-stealth";
import fs from "fs/promises";

puppeteer.use(StealthPlugin());

async function saveAmazonCookies() {
    const browser = await puppeteer.launch({ headless: false, defaultViewport: null });
    const page = await browser.newPage();

    // Set a real user agent
    await page.setUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36");

    // Open Amazon India homepage
    await page.goto("https://www.amazon.in", { waitUntil: "networkidle2" });

    console.log("🕐 Please manually log in. You have 3 minutes...");
    await new Promise(res => setTimeout(res, 180000)); // 3 minutes

    // Optional: visit a product page to make sure session is active
    await page.goto("https://www.amazon.in/dp/B08FTQXWC7", { waitUntil: "domcontentloaded" });

    const cookies = await page.cookies();
    await fs.writeFile("amazon_cookies.json", JSON.stringify(cookies, null, 2));
    console.log("✅ Amazon login cookies saved to amazon_cookies.json");

    await browser.close();
}

saveAmazonCookies();
