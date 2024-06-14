import { $ } from "bun";

// ---

const ingressIP = await $`
kubectl get ingress \
--output=jsonpath='{.items[0].status.loadBalancer.ingress[0].ip}'
`.text();

const ingress = `http://${ingressIP}`;

const InfoURL = `${ingress}/info`;
const { HOSTNAME, VERSION, GENERATION } = await $`curl ${InfoURL}`.json();
console.log(InfoURL, HOSTNAME, "/", VERSION, "/", GENERATION);

const CaddyURL = `${ingress}/web`;
const headers = (await fetch(CaddyURL)).headers;
console.log("caddy", CaddyURL, headers.get("via"), headers.get("server"));

// ---
