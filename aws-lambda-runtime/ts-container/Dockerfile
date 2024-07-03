FROM denoland/deno-lambda:1.44.4

ENV DENO_DIR=/tmp

COPY lambda.ts /var/task/

ENTRYPOINT [ "/usr/bin/deno" ]
CMD [ "run", "-A", "--no-lock", "/var/task/lambda.ts"]
