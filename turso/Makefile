DBNAME=first

all: run

info:
	turso db show $(DBNAME)

create-token:
	turso db tokens create $(DBNAME)

shell:
	turso db shell $(DBNAME)

run:
	deno run -A main.ts

insert:
	deno run -A main.ts create
