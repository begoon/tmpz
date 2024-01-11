import { Spinner } from "https://deno.land/std@0.211.0/cli/spinner.ts";
const spinner = new Spinner({ message: "connecting..." });
spinner.start();
setTimeout(() => {
    spinner.stop();
    console.log("finished");
}, 3000);
