# syntax=docker/dockerfile:1
ARG UBUNTU_IMAGE=ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852
FROM ${UBUNTU_IMAGE} AS builder
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential ca-certificates clang cmake curl git libopenmpi-dev openmpi-bin python3 unzip \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /tutorial
ENV CC=clang CXX=clang++
COPY lab/setup.sh lab/prepare.py lab/versions.env ./lab/
COPY lab/data ./lab/data
COPY container/build.sh ./container/build.sh
ARG BUILD_JOBS=2
RUN bash container/build.sh "$BUILD_JOBS"

FROM ${UBUNTU_IMAGE} AS runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl gosu libopenmpi-dev openmpi-bin python3 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=builder /opt/hypre-tutorial /opt/hypre-tutorial
WORKDIR /tutorial
COPY lab ./lab
COPY container/entrypoint.sh ./container/entrypoint.sh
RUN printf '/opt/hypre-tutorial\n' > lab/.build-path \
    && chmod +x container/entrypoint.sh
ENV PATH="/opt/hypre-tutorial/bin:${PATH}" \
    OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
    HYPRE_TUTORIAL_BUILD_INFO=/opt/hypre-tutorial/build-info.json \
    OMPI_MCA_rmaps_base_oversubscribe=1
LABEL org.opencontainers.image.title="Exploring Scalable Linear Solvers with hypre and hypredrive" \
    org.opencontainers.image.description="CPU tutorial with pinned hypre/hypredrive, MPI and all required exercises"
ENTRYPOINT ["/tutorial/container/entrypoint.sh"]
CMD ["--help"]
