import { $ } from "bun";
import consola from "consola";
import { colors } from "consola/utils";
import fs from "node:fs/promises";
import unidiff from "unidiff";

consola.options.formatOptions.columns = 0;
consola.options.formatOptions.compact = false;

const { yellowBright: yellow, whiteBright: white, underline } = colors;

// ---

const HOME = process.env.HOME;
if (!HOME) {
    consola.error("HOME not set");
    process.exit(1);
}

// ---

const VM = await fs.readFile(HOME + "/me/vm.json", "utf8");
consola.info("vm:", VM.trim());

const { name, project, zone, configuration } = JSON.parse(VM);
const force = flag("-f");

// ---

type Instance = {
    name: string;
    status: "RUNNING" | "TERMINATED";
    networkInterfaces: { accessConfigs: { natIP: string }[] }[];
};

// ---

const START = process.argv.find((v) => v === "up" || v === "start");
const STOP = process.argv.find((v) => v === "down" || v === "stop");
const SSH = process.argv.find((v) => v === "ssh");
const CHECK = process.argv.find((v) => v === "check" || v === "ping");

// ---

if (STOP) {
    const existing = await status();
    if (existing.status !== "RUNNING") {
        consola.warn("already stopped");
        process.exit(0);
    }
    await stop();
    process.exit(0);
}

if (START) {
    const existing = await status();
    if (existing.status === "RUNNING") {
        consola.warn("already running");
        process.exit(0);
    }
    await start();
    await updateSSH();
    await list();
    process.exit(0);
}

if (SSH) {
    await updateSSH();
    process.exit(0);
}

if (CHECK) {
    await check();
    process.exit(0);
}

await list();
process.exit(0);

// ---

async function updateSSH() {
    const sshConfigFile = HOME + "/.ssh/config";
    consola.info("ssh config file:", sshConfigFile);

    const sshConfig = await fs.readFile(sshConfigFile, "utf8");

    const sshConfigLines = sshConfig.split("\n");
    const n = sshConfigLines.findIndex((line) => line.includes("Host " + name)) + 1;
    const configuredIP = sshConfigLines[n].trim().split(" ")[1];
    consola.info("configured IP:", configuredIP);

    // ---

    // --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
    const info =
        await $`gcloud compute instances describe ${name} --project ${project} --configuration ${configuration} --zone ${zone} --format json'`
            .quiet()
            .json();

    const vmIP = info.networkInterfaces[0].accessConfigs[0].natIP;
    consola.info("vm IP:", underline(white(vmIP)));

    if (configuredIP === vmIP) {
        consola.warn("same IP");
        !force && process.exit(0);
    }

    // ---

    const backupFile = `${HOME}/Downloads/ssh-config.vm-${configuredIP}-${new Date()
        .toISOString()
        .replace(/[^0-9]/g, "")}.txt`;

    consola.info("backup file:", backupFile);

    const now = new Date().toISOString().replace(/(T|\.\d+Z)/g, " ");

    sshConfigLines[n] = `  HostName ${vmIP} # previous ${configuredIP} // ${now}`;

    const updated = sshConfigLines.join("\n") + "\n";
    if (updated === sshConfig) {
        consola.error("no changes found");
        process.exit(1);
    }

    const diff = unidiff.diffLines(sshConfig, updated);
    consola.box(unidiff.formatLines(diff));

    const yes = await consola.prompt(`replace ${yellow(configuredIP)} => ${white(vmIP)} ?`, { type: "confirm" });

    if (!yes || typeof yes === "symbol") {
        consola.warn("cancelled");
        process.exit(0);
    }

    await fs.writeFile(backupFile, sshConfig);
    consola.success("backup created", backupFile);

    await fs.writeFile(sshConfigFile, updated);
    consola.success("configuration updated", sshConfigFile);

    await new Promise((resolve) => setTimeout(resolve, 1000));
    await check();
}

// ---

async function check() {
    async function exec(cmd: string, color = white) {
        consola.success(color((await $`ssh ${name} ${cmd}`.quiet().text()).trim()));
    }
    await exec("hostname");
    await exec("uptime");
    await exec("curl https://api.ipify.org", yellow);
}

async function list() {
    await $`gcloud compute instances list --project ${project} --configuration ${configuration}`;
}

async function stop() {
    await $`gcloud compute instances stop ${name} --project ${project} --zone ${zone} --configuration ${configuration}`;
    consola.success("stopped");
}

async function status() {
    const running: Instance[] =
        await $`gcloud compute instances list --project ${project} --configuration ${configuration} --format json`.json();

    for (const instance of running) {
        const { name: name$, status, networkInterfaces } = instance;
        consola.info(name$, status, networkInterfaces[0].accessConfigs[0].natIP || "");
        if (name === name$) return instance;
    }

    consola.error("not found", name);
    process.exit(1);
}

async function start() {
    const start = await consola.prompt(`start ${white(name)} ?`, { type: "confirm" });
    if (!start || typeof start === "symbol") {
        consola.warn("cancelled");
        process.exit(0);
    }
    await $`gcloud compute instances start ${name} --project ${project} --configuration ${configuration} --zone ${zone}`;
    consola.success("started");
}

// ---

function flag(name: string) {
    const i = process.argv.findIndex((v) => v === name);
    if (i === -1) return undefined;
    process.argv.splice(i, 1);
    return true;
}
