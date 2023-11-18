import Logger from "https://deno.land/x/logger@v1.1.3/logger.ts";

const logger = new Logger();

logger.getWarn = () => new Date().toISOString() + " WARN";

logger.info("i am from console logger", { name: "abc" });
logger.warn("i am from console logger", 1, ["a", 2], "any");
logger.error("i am from console logger", new Error("test"));

await Deno.cron("ticker", "* * * * *", () => {
    console.log("*");
});
