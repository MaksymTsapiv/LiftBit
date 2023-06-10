# Leveraging the pre-built Docker images with 
# cargo-chef and the Rust toolchain
FROM lukemathwalker/cargo-chef:latest-rust-1 AS chef
WORKDIR /storage-ms

FROM chef AS planner
COPY . .
RUN cargo chef prepare --recipe-path recipe.json

FROM chef AS builder 
COPY --from=planner /storage-ms/recipe.json recipe.json
# Build dependencies - this is the caching Docker layer!
RUN cargo chef cook --release --recipe-path recipe.json
# Build application
COPY . .
RUN cargo build --release --bin storage-ms

# We do not need the Rust toolchain to run the binary!
FROM debian:bullseye-slim AS runtime

RUN apt-get update
RUN apt-get install -y --no-install-recommends ca-certificates
RUN update-ca-certificates


WORKDIR /storage-ms
COPY --from=builder /storage-ms/target/release/storage-ms /usr/local/bin
ENTRYPOINT ["/usr/local/bin/storage-ms"]