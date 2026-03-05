"""Internal API version registry and lifecycle metadata helpers."""

from dataclasses import dataclass
from datetime import date
from typing import Literal

APILifecycleStatus = Literal["stable", "deprecated"]


@dataclass(frozen=True)
class APIVersionContract:
    version: str
    status: APILifecycleStatus
    deprecated_on: date | None
    sunset_on: date | None
    backend_url_path: str
    frontend_url_path: str
    backend_url_name: str
    frontend_url_name: str


def _parse_version_number(version: str) -> int:
    if not version.startswith("v") or not version[1:].isdigit():
        raise ValueError(f"Unsupported API version key format: {version!r}")
    return int(version[1:])


def validate_api_version_registry(registry: dict[str, APIVersionContract]) -> None:
    if not registry:
        raise ValueError("API version registry must define at least one version.")

    seen_paths: set[str] = set()
    seen_names: set[str] = set()
    stable_versions: list[str] = []

    for key, contract in registry.items():
        if key != contract.version:
            raise ValueError(f"API registry key {key!r} must match contract.version {contract.version!r}.")

        _parse_version_number(contract.version)

        if contract.status not in {"stable", "deprecated"}:
            raise ValueError(
                f"API contract {contract.version!r} has invalid status {contract.status!r}.",
            )

        if contract.status == "stable" and (contract.deprecated_on is not None or contract.sunset_on is not None):
            raise ValueError(
                f"API contract {contract.version!r} is stable and must not set deprecated_on/sunset_on.",
            )

        if contract.status == "deprecated" and contract.deprecated_on is None:
            raise ValueError(
                f"API contract {contract.version!r} is deprecated and must set deprecated_on.",
            )

        if contract.deprecated_on and contract.sunset_on and contract.deprecated_on > contract.sunset_on:
            raise ValueError(f"API contract {contract.version!r} has deprecated_on after sunset_on.")

        for path in (contract.backend_url_path, contract.frontend_url_path):
            if path in seen_paths:
                raise ValueError(f"Duplicate API path in registry: {path!r}")
            seen_paths.add(path)

        for name in (contract.backend_url_name, contract.frontend_url_name):
            if name in seen_names:
                raise ValueError(f"Duplicate API URL name in registry: {name!r}")
            seen_names.add(name)

        if contract.status == "stable":
            stable_versions.append(contract.version)

    if not stable_versions:
        raise ValueError("API version registry must define at least one stable version.")


API_VERSION_REGISTRY: dict[str, APIVersionContract] = {
    "v1": APIVersionContract(
        version="v1",
        status="stable",
        deprecated_on=None,
        sunset_on=None,
        backend_url_path="api/v1/backend-urls/",
        frontend_url_path="api/v1/frontend-urls/",
        backend_url_name="api_v1_backend_urls",
        frontend_url_name="api_v1_frontend_urls",
    ),
}

validate_api_version_registry(API_VERSION_REGISTRY)


def get_api_contract(version: str) -> APIVersionContract:
    try:
        return API_VERSION_REGISTRY[version]
    except KeyError as error:
        raise KeyError(f"Unsupported API version {version!r}.") from error


def get_supported_api_versions() -> tuple[str, ...]:
    return tuple(
        sorted(
            API_VERSION_REGISTRY.keys(),
            key=_parse_version_number,
        ),
    )


def get_latest_stable_api_version() -> str:
    stable_versions = [contract.version for contract in API_VERSION_REGISTRY.values() if contract.status == "stable"]
    if not stable_versions:
        raise ValueError("No stable API versions are available.")

    return max(stable_versions, key=_parse_version_number)


def get_latest_stable_api_contract() -> APIVersionContract:
    return get_api_contract(get_latest_stable_api_version())
