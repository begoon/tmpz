# https://hub.docker.com/r/denoland/deno

FROM denoland/deno:1.10.3

WORKDIR /app

USER deno

ADD ws.ts .
RUN deno cache ws.ts

CMD ["run", "--allow-net", "ws.ts"]

