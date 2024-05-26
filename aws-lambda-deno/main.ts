import {
    APIGatewayProxyEventV2,
    APIGatewayProxyResultV2,
    Context,
} from "https://deno.land/x/lambda/mod.ts";

// deno-lint-ignore require-await
export async function handler(
    event: APIGatewayProxyEventV2,
    context: Context
): Promise<APIGatewayProxyResultV2> {
    return {
        statusCode: 200,
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
            message: `welcome to deno ${Deno.version.deno} 🦕`,
            event,
            context,
            env: Deno.env.toObject(),
        }),
    };
}
