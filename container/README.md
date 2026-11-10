# Container setup

The tutorial provides Linux CPU images for `amd64` and `arm64`, with
hypredrive v0.4.0 and hypre v3.2.1. On macOS and
Windows, Docker Desktop, Colima, or WSL2 runs these images in a Linux VM. This
project does not build native macOS or Windows containers.

## 1. Install a container runtime

- **Linux:** install and start [Docker Engine](https://docs.docker.com/engine/install/).
- **macOS:** start [Docker Desktop](https://docs.docker.com/desktop/setup/install/mac-install/),
  or install Colima with `brew install docker colima` and start it with
  `colima start --cpu 4 --memory 4`.
- **Windows:** install [Docker Desktop](https://docs.docker.com/desktop/setup/install/windows-install/)
  and [WSL2](https://learn.microsoft.com/windows/wsl/install). Enable Docker Desktop
  integration for Ubuntu, then use the Ubuntu terminal for the commands below.

On Linux and macOS, verify the runtime is running with `docker info`.

## 2. Get the repository and run a lab

Clone the public repository, or open its downloaded folder in a terminal:

```bash
git clone https://github.com/victorapm/hypre-tutorial-2026.git
cd hypre-tutorial-2026
bash container/run.sh 1
```

The first run pulls the published image automatically, including the SPE10
input for Lab 3. The repository and GHCR image must be public for anonymous
access. Run Lab 3 with `bash container/run.sh 3`
or Lab 4 with `bash container/run.sh 4`; replace `1` with `2` for Lab 2. Use
`bash container/run.sh all` for Labs 1–4. The runner also accepts `darcy` as an alias
for Lab 3. Use `bash container/run.sh --help` for MPI, shell and SuiteSparse commands.

Results stay on your computer in `results/container/`; optional SuiteSparse
inputs are cached in `.cache/suitesparse/`. For a ZIP download without a Git
remote, set the published image explicitly:

```bash
export HYPRE_TUTORIAL_IMAGE=ghcr.io/victorapm/hypre-tutorial-2026:2026
```

If optional matrix downloads need a network's trusted CA, set
`HYPRE_TUTORIAL_CA_BUNDLE` to an absolute path to its PEM bundle. TLS
verification stays enabled.

## 3. Image publishing and local builds

A push to `master` builds and tests both architectures on native GitHub runners.
After both pass, the workflow publishes the multi-architecture `:2026` image
to GHCR. Set the GHCR package visibility to **Public** so students can pull
without signing in.

Maintainers can build and test locally with Docker Buildx:

```bash
docker buildx build --load --tag hypre-tutorial-2026:local .
bash container/test.sh hypre-tutorial-2026:local
```

Saved container results are available for [arm64](../lab/reference/linux-arm64-container-m5/README.md)
and [amd64](../lab/reference/linux-amd64-container-m5/README.md).
