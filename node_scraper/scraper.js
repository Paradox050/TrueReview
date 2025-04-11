import puppeteer from "puppeteer-extra";
import StealthPlugin from "puppeteer-extra-plugin-stealth";
import fs from "fs/promises";
import path from "path";
import { fileURLToPath } from "url";

puppeteer.use(StealthPlugin());

// 🛠️ Fix __dirname for ES modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function scrapeAmazonReviews(baseUrl) {
    const browser = await puppeteer.launch({
        headless: true,
        args: ["--start-maximized", "--no-sandbox", "--disable-setuid-sandbox"],
        defaultViewport: null
    });

    const page = await browser.newPage();

    // ✅ Set a realistic User-Agent
    await page.setUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36");

    try {
        const cookiesPath = path.join(__dirname, "amazon_cookies.json");
        const cookies = JSON.parse(await fs.readFile(cookiesPath));
        await page.setCookie(...cookies);
        console.log("✅ Cookies loaded!");
    } catch (error) {
        console.warn("⚠️ No cookies found. Continuing without login...");
    }

    if (!baseUrl.includes("/product-reviews/")) {
        const match = baseUrl.match(/\/dp\/([A-Z0-9]+)/);
        if (match) {
            const productId = match[1];
            baseUrl = `https://www.amazon.in/product-reviews/${productId}/?reviewerType=all_reviews&pageNumber=1`;
        } else {
            console.error("❌ Invalid product URL");
            await browser.close();
            return;
        }
    }

    const productPage = baseUrl.replace("/product-reviews", "/dp").split("?")[0];
    await page.goto(productPage, { waitUntil: "domcontentloaded" });

    try {
        const productTitle = await page.$eval("#productTitle", el => el.innerText.trim());
        console.log("🛍️ Product Title (scraped):", productTitle);
    
        const titlePath = path.join(__dirname, "..","product_title.txt");
        await fs.writeFile(titlePath, productTitle, "utf-8");
        console.log("✅ Title saved to:", titlePath);
    } catch (err) {
        console.warn("⚠️ Could not extract product title:", err.message);
    }
      
    const allReviews = [];
    const maxPages = 10;

    for (let pageNum = 1; pageNum <= maxPages; pageNum++) {
        const url = baseUrl.replace(/pageNumber=\d+/, `pageNumber=${pageNum}`);
        await page.goto(url, { waitUntil: "networkidle2", timeout: 30000 });

        await page.waitForSelector('[data-hook="review"]', { timeout: 20000 });
        await page.evaluate(() => window.scrollBy(0, window.innerHeight));
        await new Promise(res => setTimeout(res, 1000));

        const reviews = await page.evaluate(() => {
            const parseDate = (dateText) => {
                const match = dateText.match(/on\s(\d+\s\w+\s\d{4})/);
                return match ? match[1] : null;
            };

            return Array.from(document.querySelectorAll('[data-hook="review"]')).map(review => {
                const text = review.querySelector('[data-hook="review-body"] span')?.innerText.trim() || "";
                const titleRaw = review.querySelector('[data-hook="review-title"] span')?.innerText.trim() || "";
                const title = titleRaw.replace(/^.*?stars\s/, '').trim();

                const ratingMatch = review.querySelector('[data-hook="review-star-rating"]')?.innerText.match(/(\d[\d.]*) out of 5 stars/);
                const rating = ratingMatch ? parseFloat(ratingMatch[1]) : null;

                const dateText = review.querySelector('.review-date')?.innerText.trim() || "";
                const reviewDate = parseDate(dateText);

                const verified = !!review.querySelector('[data-hook="avp-badge"]');

                return {
                    text,
                    title,
                    rating,
                    date: reviewDate,
                    verifiedPurchase: verified,
                    length: text.length
                };
            });
        });

        if (!reviews.length) break;
        allReviews.push(...reviews);
    }

    await fs.writeFile(path.join(__dirname, "amazon_reviews.json"), JSON.stringify(allReviews, null, 2), "utf-8");
    console.log(`✅ Scraped ${allReviews.length} reviews with metadata.`);
    await browser.close();
}

if (process.argv[2]) {
    scrapeAmazonReviews(process.argv[2]);
} else {
    console.log("❗ Please pass a product or reviews URL to scrape.");
}
