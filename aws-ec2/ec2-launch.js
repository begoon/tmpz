import { EC2 } from "@aws-sdk/client-ec2";

const cmd = process.argv[2];

const client = new EC2({ region: "eu-west-2" });

const now = new Date().toISOString();

async function start(tags) {
    const instance = await client.runInstances({
        ImageId: "ami-01f10c2d6bce70d90",
        InstanceType: "t2.micro",
        MinCount: 1,
        MaxCount: 1,
        UserData: Buffer.from(
            [
                "#!/bin/bash",
                "sudo yum update -y",
                "sudo yum install docker -y",
                "sudo systemctl start docker",
                `sudo echo "webserver started at ${now}" >index.html`,
                "sudo docker run -d -v $PWD/index.html:/usr/share/caddy/index.html -p :80:80 caddy",
            ].join("\n")
        ).toString("base64"),
        SecurityGroupIds: ["sg-046938788a0c5da74"],
    });
    var instanceId = instance.Instances[0].InstanceId;
    console.log("created instance", instanceId);

    await client.createTags({ Resources: [instanceId], Tags: tags });
    console.log(`instance ${instanceId} tagged`);
    return instanceId;
}

async function terminate(instanceId) {
    await client.terminateInstances({ InstanceIds: [instanceId] });
    console.log(`instance ${instanceId} terminated`);
}

async function state(instanceId) {
    const instance = await client.describeInstances({
        InstanceIds: [instanceId],
    });
    return {
        state: instance.Reservations[0].Instances[0].State.Name,
        ip: instance.Reservations[0].Instances[0].PublicIpAddress,
    };
}

async function awaitState(instanceId, desiredState) {
    let seconds = 0;
    while (true) {
        const { state: current, ip } = await state(instanceId);
        process.stdout.write(
            `\rwaiting ${instanceId} ${
                ip || "-"
            } (${current}) to be ${desiredState} / ${seconds}s`
        );
        seconds += 1;
        if (current === desiredState) break;
        await new Promise((resolve) => setTimeout(resolve, 1000));
    }
    console.log();
}

if (cmd === "start") {
    const started = performance.now();
    const tags = [
        { Key: "Name", Value: "instance-name-" + new Date().toISOString() },
        { Key: "Owner", Value: process.env.USER },
    ];
    const instanceId = await start(tags);
    await awaitState(instanceId, "running");
    console.log(`instance ${instanceId} is running`);

    const ended = performance.now();
    console.log(`time taken: ${ended - started}ms`);
}

if (cmd === "terminate") {
    const started = performance.now();
    const instanceId = process.argv[3];
    await terminate(instanceId);
    await awaitState(instanceId, "terminated").then(() => {
        console.log(`instance ${instanceId} is terminated`);
    });
    const ended = performance.now();
    console.log(`time taken: ${ended - started}s`);
}
