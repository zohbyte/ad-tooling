FROM timescale/timescaledb:latest-pg15

RUN apk add --no-cache build-base make git
COPY tulip /tulip
RUN cd /tulip && make USE_PGXS=1 with_llvm=no install && cd / && \
	git clone --depth 1 https://github.com/ossc-db/pg_hint_plan --branch PG15 && \
	cd pg_hint_plan && make USE_PGXS=1 with_llvm=no install
