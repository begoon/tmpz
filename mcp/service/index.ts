import process from "node:process";

const port = parseInt(process.env.PORT || "9000");

Bun.serve({
    port,
    fetch(req) {
        const url = new URL(req.url);

        if (url.pathname === "/getweather") {
            const location = url.searchParams.get("location");
            console.log(`/getweather called with location=${location}`);

            let temp, conditions;

            if (location == "Boston") {
                temp = 99;
                conditions = "hot and humid";
            } else if (location == "Seattle") {
                temp = 40;
                conditions = "rainy and overcast";
            } else {
                return new Response("there is no data for the requested location", {
                    status: 400,
                });
            }

            console.log(`returning weather for ${location}: ${temp}F and ${conditions}`);
            return Response.json({
                weather: temp,
                location: location,
                conditions: conditions,
            });
        }

        if (url.pathname === "/") {
            return new Response("welcome to hard-coded weather!");
        }

        return new Response("Not Found", { status: 404 });
    },
});

console.log(`backend listening on port ${port}`);
