import { $ } from "bun";

import * as toml from "@std/toml";

import { spinner } from "@clack/prompts";
import consola, { LogLevels } from "consola";
import fs from "node:fs";

type VM = {
    name: string;
    status: string;
    networkInterfaces: { accessConfigs: { natIP: string }[] }[];
};

consola.options.formatOptions.columns = 0;
consola.options.formatOptions.compact = false;

const verbose = flag("--verbose");
consola.level = verbose ? LogLevels.debug : LogLevels.info;

const MakefileName = option("-f", "Makefile");
consola.info(MakefileName);

const Makefiles = [MakefileName, MakefileName + ".local", ".env"];

const Makefile = Makefiles.map((v) => fs.existsSync(v!) && fs.readFileSync(v!, "utf-8")).join("\n");

const makefile = await parseVariables(Makefile);

const NAME = makefile.get("NAME");
const REPO = makefile.get("REPO");

const REGION = makefile.get("REGION");
const PROJECT = makefile.get("PROJECT");

const SERVICE_NAME = makefile.get("SERVICE_NAME");

let service: Awaited<ReturnType<typeof info>> | undefined;

if (SERVICE_NAME != "-") {
    service = await info();
    consola.info("image", imageHref(service.image));
}

function imageHref(image: string) {
    const [repo, _tag] = image.split(":");
    const [host, project, prefix, name] = repo.split("/");
    const [location, _] = host.split("-");
    const gar = "https://console.cloud.google.com/artifacts/docker";
    const link = `${gar}/${project}/${location}/${prefix}/${name}?project=${project}`;
    consola.debug(link);
    return href(link, image);
}
const commands = process.argv.slice(2).filter((v) => !v.startsWith("-"));

if (commands.length > 0) {
    consola.debug("commands", commands);
    for (const command of commands) {
        consola.debug("command", command);
        switch (command) {
            case "info":
            case "i":
                consola.info(service);
                break;
            case "tags":
            case "t":
                consola.info(await tags());
                break;
            case "tag":
            case "l":
                const wait = flag("--wait") || flag("-w");
                const first = (await tags())[0];
                let tag = first;
                if (wait) {
                    const v = spinner();
                    v.start(`${first}...`);
                    do {
                        await new Promise((r) => setTimeout(r, 1000));
                        tag = (await tags())[0] as string;
                    } while (tag === first);
                    v.stop(tag);
                    await notify(`new tag is pushed`);
                }
                consola.info(tag);
                break;
            case "health":
            case "h":
                consola.info(await health());
                break;
            default:
                consola.error("ha?", command);
                process.exit(1);
        }
    }
    process.exit(0);
}

if (!service) consola.error("undefined service"), process.exit(1);

consola.info("dial", service.url + "/health");
consola.info("health", await health());

const options = await tags();

const now = new Date()
    .toISOString()
    .replace(/[^0-9]/g, "")
    .slice(0, 14);

const BRANCH = await $`git rev-parse --abbrev-ref HEAD`.text();
const COMMIT = await $`git rev-parse --short HEAD`.text();
const VERSION = version();

const TAG_ = [VERSION, "X", BRANCH, COMMIT, now].map((v) => v.trim()).join("-");

const TAG = await consola.prompt("version/tag", { type: "text", initial: TAG_ });
cancelled(TAG);

const update = await consola.prompt("deploy?", { type: "select", initial: options[0], options });
cancelled(update);

console.log("deploying", update);

for await (let line of $`gcloud run deploy ${SERVICE_NAME} --region ${REGION} --project ${PROJECT} --image=${REPO}/${NAME}:${update} --update-env-vars TAG=${TAG} 2>&1`.lines()) {
    console.log(line);
}
consola.info("OK");

consola.info(await health());

await notify("deployed");

// ---

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

function href(href: string, text: string) {
    return `\u001b]8;;${href}\u001b\\${text}\u001b]8;;\u001b\\`;
}

async function parseVariables(content: string) {
    const lines = content.split("\n");
    const values = {};
    for (const line of lines) {
        const first = line.charAt(0);
        if ("# \t".includes(first)) continue;
        const [name, value] = line.split("=").map((v) => v.trim());
        if (!name || !value) continue;
        consola.debug("variable", { name, value });
        const multiSuffix = "_NAMES";
        if (name.endsWith(multiSuffix)) {
            const singular = name.slice(0, -1);
            const names = value.split(",").map((v) => v.trim());
            const selected = await consola.prompt(`which ${singular}?`, { type: "select", options: names });
            cancelled(selected);
            consola.debug("selected", singular, "=", selected);
            values[singular] = selected;
        } else {
            if (value) values[name] = value;
        }
    }
    consola.debug("variables", { values });
    return {
        get: (name: string) => {
            const v = values[name];
            if (!v) {
                consola.error("variable not found", name);
                process.exit(1);
            } else consola.debug(name, "=", v);
            return v;
        },
    };
}

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

async function health() {
    if (!service) consola.error("undefined service"), process.exit(1);
    const url = service.url + "/health";
    consola.info("health", url);
    return await (await fetch(url)).json();
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

async function notify(msg: string) {
    await $`osascript -e 'display notification "${msg}" with title "OK"'`;
    await $`say "${msg}"`;
}

function cancelled(answer: any) {
    if (typeof answer === "symbol") {
        consola.info("cancelled");
        process.exit(0);
    }
}

function version() {
    try {
        const pyprojectTOML = toml.parse(fs.readFileSync("pyproject.toml", "utf-8")) as {
            tool: { poetry: { version: string } };
            project: { version: string };
        };
        const { version: poetryVersion } = pyprojectTOML.tool?.poetry || {};
        const { version: projectVersion } = pyprojectTOML.project || {};

        if (poetryVersion) return poetryVersion;
        if (projectVersion) return projectVersion;
    } catch {}

    try {
        const packageJSON = JSON.parse(fs.readFileSync("package.json", "utf-8")) as { version: string };
        const { version: packageVersion } = packageJSON;
        if (packageVersion) return packageVersion;
    } catch {}

    try {
        const versionTXT = fs.readFileSync("VERSION.txt", "utf-8").trim();
        if (versionTXT) return versionTXT;
    } catch {}

    return "0.0.0";
}
