from datetime import date
from unittest.mock import patch

from django.test import SimpleTestCase
from django.urls import NoReverseMatch, reverse

from wagtail_unveil.api_contract import (
    API_VERSION_REGISTRY,
    APIVersionContract,
    get_api_contract,
    get_latest_stable_api_contract,
    get_latest_stable_api_version,
    get_supported_api_versions,
    validate_api_version_registry,
)


def _contract(
    *,
    version,
    status,
    backend_path,
    frontend_path,
    platform_path=None,
    backend_name,
    frontend_name,
    platform_name=None,
    deprecated_on=None,
    sunset_on=None,
):
    return APIVersionContract(
        version=version,
        status=status,
        deprecated_on=deprecated_on,
        sunset_on=sunset_on,
        backend_url_path=backend_path,
        frontend_url_path=frontend_path,
        platform_url_path=platform_path or f"api/{version}/platform/",
        backend_url_name=backend_name,
        frontend_url_name=frontend_name,
        platform_url_name=platform_name or f"api_{version}_platform",
    )


class TestAPIContractRegistry(SimpleTestCase):
    def test_registry_has_at_least_one_stable_version(self):
        self.assertTrue(any(contract.status == "stable" for contract in API_VERSION_REGISTRY.values()))

    def test_latest_stable_helpers_resolve_consistently(self):
        latest_version = get_latest_stable_api_version()
        latest_contract = get_latest_stable_api_contract()
        self.assertEqual(latest_contract.version, latest_version)
        self.assertEqual(latest_contract.status, "stable")

    def test_supported_api_versions_are_sorted(self):
        versions = get_supported_api_versions()
        self.assertEqual(tuple(sorted(versions, key=lambda version: int(version[1:]))), versions)

    def test_validate_registry_rejects_duplicate_paths(self):
        registry = {
            "v1": _contract(
                version="v1",
                status="stable",
                backend_path="api/v1/backend-urls/",
                frontend_path="api/v1/frontend-urls/",
                backend_name="api_v1_backend_urls",
                frontend_name="api_v1_frontend_urls",
            ),
            "v2": _contract(
                version="v2",
                status="deprecated",
                backend_path="api/v1/backend-urls/",
                frontend_path="api/v2/frontend-urls/",
                backend_name="api_v2_backend_urls",
                frontend_name="api_v2_frontend_urls",
            ),
        }

        with self.assertRaises(ValueError):
            validate_api_version_registry(registry)

    def test_validate_registry_rejects_duplicate_platform_paths(self):
        registry = {
            "v1": _contract(
                version="v1",
                status="stable",
                backend_path="api/v1/backend-urls/",
                frontend_path="api/v1/frontend-urls/",
                platform_path="api/v1/platform/",
                backend_name="api_v1_backend_urls",
                frontend_name="api_v1_frontend_urls",
                platform_name="api_v1_platform",
            ),
            "v2": _contract(
                version="v2",
                status="deprecated",
                backend_path="api/v2/backend-urls/",
                frontend_path="api/v2/frontend-urls/",
                platform_path="api/v1/platform/",
                backend_name="api_v2_backend_urls",
                frontend_name="api_v2_frontend_urls",
                platform_name="api_v2_platform",
            ),
        }

        with self.assertRaises(ValueError):
            validate_api_version_registry(registry)

    def test_validate_registry_rejects_duplicate_names(self):
        registry = {
            "v1": _contract(
                version="v1",
                status="stable",
                backend_path="api/v1/backend-urls/",
                frontend_path="api/v1/frontend-urls/",
                backend_name="api_v1_backend_urls",
                frontend_name="api_v1_frontend_urls",
            ),
            "v2": _contract(
                version="v2",
                status="deprecated",
                backend_path="api/v2/backend-urls/",
                frontend_path="api/v2/frontend-urls/",
                backend_name="api_v2_backend_urls",
                frontend_name="api_v1_frontend_urls",
            ),
        }

        with self.assertRaises(ValueError):
            validate_api_version_registry(registry)

    def test_validate_registry_rejects_duplicate_platform_names(self):
        registry = {
            "v1": _contract(
                version="v1",
                status="stable",
                backend_path="api/v1/backend-urls/",
                frontend_path="api/v1/frontend-urls/",
                platform_path="api/v1/platform/",
                backend_name="api_v1_backend_urls",
                frontend_name="api_v1_frontend_urls",
                platform_name="api_v1_platform",
            ),
            "v2": _contract(
                version="v2",
                status="deprecated",
                backend_path="api/v2/backend-urls/",
                frontend_path="api/v2/frontend-urls/",
                platform_path="api/v2/platform/",
                backend_name="api_v2_backend_urls",
                frontend_name="api_v2_frontend_urls",
                platform_name="api_v1_platform",
            ),
        }

        with self.assertRaises(ValueError):
            validate_api_version_registry(registry)

    def test_validate_registry_rejects_invalid_lifecycle_dates(self):
        registry = {
            "v1": _contract(
                version="v1",
                status="stable",
                backend_path="api/v1/backend-urls/",
                frontend_path="api/v1/frontend-urls/",
                backend_name="api_v1_backend_urls",
                frontend_name="api_v1_frontend_urls",
            ),
            "v2": _contract(
                version="v2",
                status="deprecated",
                backend_path="api/v2/backend-urls/",
                frontend_path="api/v2/frontend-urls/",
                backend_name="api_v2_backend_urls",
                frontend_name="api_v2_frontend_urls",
                deprecated_on=date(2026, 8, 1),
                sunset_on=date(2026, 7, 1),
            ),
        }

        with self.assertRaises(ValueError):
            validate_api_version_registry(registry)

    def test_validate_registry_rejects_stable_version_with_deprecated_on(self):
        registry = {
            "v1": _contract(
                version="v1",
                status="stable",
                backend_path="api/v1/backend-urls/",
                frontend_path="api/v1/frontend-urls/",
                backend_name="api_v1_backend_urls",
                frontend_name="api_v1_frontend_urls",
                deprecated_on=date(2026, 1, 1),
            ),
        }

        with self.assertRaises(ValueError):
            validate_api_version_registry(registry)

    def test_validate_registry_rejects_stable_version_with_sunset_on(self):
        registry = {
            "v1": _contract(
                version="v1",
                status="stable",
                backend_path="api/v1/backend-urls/",
                frontend_path="api/v1/frontend-urls/",
                backend_name="api_v1_backend_urls",
                frontend_name="api_v1_frontend_urls",
                sunset_on=date(2026, 12, 31),
            ),
        }

        with self.assertRaises(ValueError):
            validate_api_version_registry(registry)

    def test_validate_registry_rejects_empty_registry(self):
        with self.assertRaises(ValueError):
            validate_api_version_registry({})

    def test_validate_registry_rejects_mismatched_key_and_contract_version(self):
        registry = {
            "v1": _contract(
                version="v2",
                status="stable",
                backend_path="api/v1/backend-urls/",
                frontend_path="api/v1/frontend-urls/",
                backend_name="api_v1_backend_urls",
                frontend_name="api_v1_frontend_urls",
            ),
        }

        with self.assertRaises(ValueError):
            validate_api_version_registry(registry)

    def test_validate_registry_rejects_invalid_version_key_format(self):
        registry = {
            "one": _contract(
                version="one",
                status="stable",
                backend_path="api/one/backend-urls/",
                frontend_path="api/one/frontend-urls/",
                backend_name="api_one_backend_urls",
                frontend_name="api_one_frontend_urls",
            ),
        }

        with self.assertRaises(ValueError):
            validate_api_version_registry(registry)

    def test_validate_registry_rejects_invalid_status(self):
        registry = {
            "v1": _contract(
                version="v1",
                status="sunset",  # type: ignore[arg-type]
                backend_path="api/v1/backend-urls/",
                frontend_path="api/v1/frontend-urls/",
                backend_name="api_v1_backend_urls",
                frontend_name="api_v1_frontend_urls",
            ),
        }

        with self.assertRaises(ValueError):
            validate_api_version_registry(registry)

    def test_validate_registry_requires_stable_version(self):
        registry = {
            "v1": _contract(
                version="v1",
                status="deprecated",
                backend_path="api/v1/backend-urls/",
                frontend_path="api/v1/frontend-urls/",
                backend_name="api_v1_backend_urls",
                frontend_name="api_v1_frontend_urls",
            ),
        }

        with self.assertRaises(ValueError):
            validate_api_version_registry(registry)

    def test_validate_registry_rejects_deprecated_version_without_deprecated_on(self):
        registry = {
            "v1": _contract(
                version="v1",
                status="stable",
                backend_path="api/v1/backend-urls/",
                frontend_path="api/v1/frontend-urls/",
                backend_name="api_v1_backend_urls",
                frontend_name="api_v1_frontend_urls",
            ),
            "v2": _contract(
                version="v2",
                status="deprecated",
                backend_path="api/v2/backend-urls/",
                frontend_path="api/v2/frontend-urls/",
                backend_name="api_v2_backend_urls",
                frontend_name="api_v2_frontend_urls",
            ),
        }

        with self.assertRaises(ValueError):
            validate_api_version_registry(registry)

    def test_validate_registry_rejects_sunset_without_deprecated_on(self):
        registry = {
            "v1": _contract(
                version="v1",
                status="stable",
                backend_path="api/v1/backend-urls/",
                frontend_path="api/v1/frontend-urls/",
                backend_name="api_v1_backend_urls",
                frontend_name="api_v1_frontend_urls",
            ),
            "v2": _contract(
                version="v2",
                status="deprecated",
                backend_path="api/v2/backend-urls/",
                frontend_path="api/v2/frontend-urls/",
                backend_name="api_v2_backend_urls",
                frontend_name="api_v2_frontend_urls",
                sunset_on=date(2026, 12, 31),
            ),
        }

        with self.assertRaises(ValueError):
            validate_api_version_registry(registry)


class TestAPIVersionRouting(SimpleTestCase):
    def test_all_supported_versions_have_backend_frontend_and_platform_routes(self):
        for api_version in get_supported_api_versions():
            contract = get_api_contract(api_version)
            self.assertEqual(
                reverse(f"wagtail_unveil:{contract.backend_url_name}"),
                f"/unveil/{contract.backend_url_path}",
            )
            self.assertEqual(
                reverse(f"wagtail_unveil:{contract.frontend_url_name}"),
                f"/unveil/{contract.frontend_url_path}",
            )
            self.assertEqual(
                reverse(f"wagtail_unveil:{contract.platform_url_name}"),
                f"/unveil/{contract.platform_url_path}",
            )

    def test_v1_url_names_remain_resolvable(self):
        contract = get_api_contract("v1")
        self.assertEqual(
            reverse(f"wagtail_unveil:{contract.backend_url_name}"),
            "/unveil/api/v1/backend-urls/",
        )
        self.assertEqual(
            reverse(f"wagtail_unveil:{contract.frontend_url_name}"),
            "/unveil/api/v1/frontend-urls/",
        )
        self.assertEqual(
            reverse(f"wagtail_unveil:{contract.platform_url_name}"),
            "/unveil/api/v1/platform/",
        )

    def test_unversioned_alias_names_are_not_exposed(self):
        with self.assertRaises(NoReverseMatch):
            reverse("wagtail_unveil:api_backend_urls")

        with self.assertRaises(NoReverseMatch):
            reverse("wagtail_unveil:api_frontend_urls")

        with self.assertRaises(NoReverseMatch):
            reverse("wagtail_unveil:api_platform")


class TestAPIContractAccessors(SimpleTestCase):
    def test_get_api_contract_rejects_unknown_version(self):
        with self.assertRaises(KeyError):
            get_api_contract("v999")

    def test_get_latest_stable_version_raises_when_none_stable(self):
        deprecated_registry = {
            "v1": _contract(
                version="v1",
                status="deprecated",
                backend_path="api/v1/backend-urls/",
                frontend_path="api/v1/frontend-urls/",
                backend_name="api_v1_backend_urls",
                frontend_name="api_v1_frontend_urls",
            ),
        }

        with patch("wagtail_unveil.api_contract.API_VERSION_REGISTRY", deprecated_registry):
            with self.assertRaises(ValueError):
                get_latest_stable_api_version()
