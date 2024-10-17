import { select, Separator } from "@inquirer/prompts";
import inquirer from "inquirer";

const entered = await inquirer.prompt([
    {
        type: "input",
        name: "name",
        message: "what's your name?",
    },
]);
console.log("hi", entered);

const answer = await select({
    message: "select a package manager",
    choices: [
        {
            name: "npm",
            value: "npm",
            description: "npm is the most popular package manager",
        },
        {
            name: "yarn",
            value: "yarn",
            description: "yarn is an awesome package manager",
        },
        new Separator(),
        { name: "jspm", value: "jspm", disabled: true },
        { name: "pnpm", value: "pnpm", disabled: "(pnpm is not available)" },
    ],
});

console.log(answer);
