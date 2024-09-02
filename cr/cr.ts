import { $ } from "bun";

import consola, { LogLevels } from "consola";
import fs from "node:fs";

consola.options.formatOptions.columns = 0;

function flag(name: string) {
    const i = process.argv.findIndex((v) => v === name);
    if (i === -1) return undefined;
    process.argv.splice(i, 1);
    return true;
}

function option(name: string, default_: string | undefined = undefined) {
    const i = process.argv.findIndex((v) => v === name);
    if (i === -1) return default_;
    const value = process.argv[i + 1];
    if (!value) return default_;
    process.argv.splice(i, 2);
    return value;
}

const verbose = flag("--verbose");
if (verbose) consola.level = LogLevels.debug;

const MakefileName = option("-f", "Makefile");
if (!MakefileName || !fs.existsSync(MakefileName)) {
    consola.error("not found", MakefileName);
    process.exit(1);
}
consola.info(MakefileName);

const Makefile = fs.readFileSync(MakefileName, "utf-8");

function parseMakefile(content: string) {
    const lines = content.split("\n");
    const variables = {};
    for (const line of lines) {
        if (line.startsWith("#")) continue;
        const [name, value] = line.split("=");
        if (value && name.toUpperCase().trim() === name)
            variables[name] = value;
    }
    consola.debug("variables", { variables });
    return {
        variables,
        get: (name: string, echo = false) => {
            const v = variables[name];
            if (!v) {
                consola.error(`variable ${name} not found`);
                process.exit(1);
            }
            if (echo) consola.info(name, "=", v);
            return v;
        },
    };
}

const makefile = parseMakefile(Makefile);

const NAME = makefile.get("NAME");
const REPO = makefile.get("REPO");

const REGION = makefile.get("REGION");
const PROJECT = makefile.get("PROJECT");
const SERVICE_NAME = makefile.get("SERVICE_NAME");

const cmd = process.argv[2];

async function info() {
    consola.info("query", { NAME, REPO, REGION, PROJECT, SERVICE_NAME });
    const data =
        await $`gcloud run services describe ${SERVICE_NAME} --region ${REGION} --project ${PROJECT} --format json`.json();
    consola.debug("info", JSON.stringify(data, null, 2));
    return {
        url: data.status.url,
        image: data.spec.template.spec.containers[0].image,
    };
}

async function tags() {
    const data =
        await $`gcloud artifacts docker images list ${REPO}/${NAME} --include-tags --sort-by "~UPDATE_TIME" --limit 10 --format json`.json();
    consola.debug("tags", JSON.stringify(data, null, 2));
    return data
        .map((image: { tags: string[] }) => image.tags)
        .reduce((a: string[], v: string) => a.concat(v), [])
        .filter((tag: string) => tag !== "latest");
}

const { url, image } = await info();

consola.info("image", image);

consola.info("dial", url + "/health");

const health = async () => await (await fetch(`${url}/health`)).json();

consola.info("health", await health());

const options = await tags();

if (flag("--last")) {
    consola.box(options[0]);
    process.exit(0);
}

const update = await consola.prompt("deploy?", {
    type: "select",
    initial: options[0],
    options,
});

if (typeof update === "symbol") {
    consola.info("cancelled");
    process.exit(0);
}

console.log("deploying", update);

for await (let line of $`gcloud run deploy ${SERVICE_NAME} --region ${REGION} --project ${PROJECT} --image=${REPO}/${NAME}:${update} 2>&1`.lines()) {
    console.log(line);
}
consola.info("OK");

consola.info(await health());
