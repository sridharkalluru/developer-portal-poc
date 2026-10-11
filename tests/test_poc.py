"""Offline structural tests for the Developer Portal POC. Run: python -m unittest discover -s tests -v"""
import json
import pathlib
import unittest
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]

class ComposeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.compose = yaml.safe_load((ROOT / "docker-compose.yml").read_text())
        cls.services = cls.compose["services"]

    def test_expected_services_exist(self):
        for name in ("drupal", "drupal-db", "keycloak", "keycloak-db", "swagger-ui", "claims-api", "microcks"):
            with self.subTest(service=name):
                self.assertIn(name, self.services)

    def test_open_source_community_images_configured(self):
        self.assertEqual(self.services["drupal"]["image"], "drupal:11-apache")
        self.assertTrue(self.services["microcks"]["image"].startswith("quay.io/microcks/microcks-uber:"))
        self.assertIn("microcks", self.services["microcks"].get("profiles", []))

    def test_expected_host_ports_are_unique(self):
        expected = {"drupal": "8080:80", "keycloak": "8081:8080", "claims-api": "8082:8080", "swagger-ui": "8083:8080", "microcks": "8585:8080"}
        seen = set()
        for service, port in expected.items():
            with self.subTest(service=service):
                ports = self.services[service].get("ports", [])
                self.assertIn(port, ports)
                host_port = port.split(":", 1)[0]
                self.assertNotIn(host_port, seen)
                seen.add(host_port)

    def test_microcks_is_optional_profile(self):
        self.assertIn("microcks", self.services["microcks"].get("profiles", []))
        self.assertNotIn("microcks", self.services["drupal"].get("profiles", []))

class OpenApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = yaml.safe_load((ROOT / "specs/openapi.yaml").read_text())

    def test_openapi_31_and_claims_operations(self):
        self.assertEqual(self.spec["openapi"], "3.1.0")
        self.assertIn("/api/claims", self.spec["paths"])
        self.assertIn("get", self.spec["paths"]["/api/claims"])
        self.assertIn("post", self.spec["paths"]["/api/claims"])

    def test_request_and_response_schema_references_resolve(self):
        schemas = self.spec["components"]["schemas"]
        self.assertIn("Claim", schemas)
        self.assertIn("NewClaim", schemas)
        post = self.spec["paths"]["/api/claims"]["post"]
        request_schema = post["requestBody"]["content"]["application/json"]["schema"]["$ref"]
        response_schema = post["responses"]["201"]["content"]["application/json"]["schema"]["$ref"]
        self.assertEqual(request_schema, "#/components/schemas/NewClaim")
        self.assertEqual(response_schema, "#/components/schemas/Claim")

    def test_swagger_server_points_to_host_api(self):
        self.assertEqual(self.spec["servers"][0]["url"], "http://localhost:8082")

class KeycloakTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.realm = json.loads((ROOT / "keycloak/realm-import/developer-poc-realm.json").read_text())

    def test_realm_and_clients_exist(self):
        self.assertEqual(self.realm["realm"], "developer-poc")
        client_ids = {c["clientId"] for c in self.realm["clients"]}
        self.assertTrue({"developer-portal", "claims-api"}.issubset(client_ids))

    def test_demo_user_is_enabled(self):
        user = next(u for u in self.realm["users"] if u["username"] == "developer")
        self.assertTrue(user["enabled"])
        self.assertTrue(user["credentials"])

if __name__ == "__main__":
    unittest.main(verbosity=2)
