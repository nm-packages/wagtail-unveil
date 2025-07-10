from django.core.management.base import BaseCommand
import requests
import json


class Command(BaseCommand):
    help = (
        "Fetches all API endpoints from the index and outputs their results as a dict."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--api-root",
            type=str,
            default="http://localhost:8000/unveil/api/",
            help="Base URL for the API index.",
        )
        parser.add_argument(
            "--token",
            type=str,
            required=True,
            help="Bearer token for API authentication.",
        )

    def handle(self, *args, **options):
        api_root = options["api_root"]
        token = options["token"]
        headers = {"Authorization": f"Bearer {token}"}
        try:
            index_response = requests.get(api_root, headers=headers)
            index_response.raise_for_status()
            endpoints = index_response.json().get("endpoints", {})
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Failed to fetch API index: {e}"))
            return

        results = {}
        for name, url in endpoints.items():
            try:
                resp = requests.get(url, headers=headers)
                resp.raise_for_status()
                results[name] = resp.json()
            except Exception as e:
                results[name] = {"error": str(e)}

        self.stdout.write(json.dumps(results, indent=2))
