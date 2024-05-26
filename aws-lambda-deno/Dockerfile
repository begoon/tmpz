FROM denoland/deno-lambda:1.43.6

COPY main.ts .
RUN deno cache main.ts

CMD ["main.handler"]
