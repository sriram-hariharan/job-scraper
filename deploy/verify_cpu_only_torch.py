"""Fail the production image build if the CPU-only PyTorch contract regressed.

Production runs on a CPU-only Hetzner host with no CUDA/GPU workload. The
default PyPI ``torch`` wheel declares ``nvidia-cudnn-cu13``,
``nvidia-cusparselt-cu13``, ``nvidia-nccl-cu13``, ``nvidia-nvshmem-cu13`` and
``triton`` under ``platform_system == "Linux"``. Resolving those added several
gigabytes to the image and exhausted the disk while unpacking
``libcusparseLt.so.0``.

The Dockerfile installs an exact ``+cpu`` build from PyTorch's official CPU
index before the general requirements resolution. This module proves that the
result actually is CPU-only, so a future dependency bump that silently pulls a
CUDA build fails the build instead of the production host.
"""

from __future__ import annotations

import sys
from importlib import metadata

# Distribution name prefixes published by the CUDA/GPU PyTorch stack.
GPU_DISTRIBUTION_PREFIXES = ("nvidia-", "nvidia_", "triton", "pytorch-triton")


def installed_gpu_distributions(distributions=None) -> list[str]:
    """Return installed distribution names belonging to the CUDA/GPU stack."""
    found = set()
    for distribution in metadata.distributions() if distributions is None else distributions:
        name = (distribution.metadata["Name"] or "").strip()
        if name.lower().replace("_", "-").startswith(GPU_DISTRIBUTION_PREFIXES):
            found.add(name)
    return sorted(found)


def verify_cpu_only_torch(torch_version: str, gpu_distributions: list[str]) -> None:
    """Raise SystemExit unless torch is a CPU build and no GPU packages exist."""
    if not torch_version.endswith("+cpu"):
        raise SystemExit(
            f"Expected a CPU-only torch build, found torch=={torch_version}. "
            "The production image must install torch from "
            "https://download.pytorch.org/whl/cpu."
        )
    if gpu_distributions:
        raise SystemExit(
            "CUDA/GPU packages leaked into the production image: "
            f"{', '.join(gpu_distributions)}."
        )


def main() -> None:
    torch_version = metadata.version("torch")
    verify_cpu_only_torch(torch_version, installed_gpu_distributions())
    print(f"Verified CPU-only torch=={torch_version}; no CUDA/GPU packages present.")


if __name__ == "__main__":
    main()
