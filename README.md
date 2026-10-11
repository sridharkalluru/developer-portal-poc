# Developer Portal POC (Docker Compose)

A local proof of concept for a developer portal and API documentation ecosystem:

- Drupal 11 Community: open-source portal/CMS (installation wizard at http://localhost:8080)
- PostgreSQL 16: persistent Drupal and Keycloak databases
- Swagger UI 5: interactive OpenAPI documentation at http://localhost:8083
- Spring Boot Claims API: sample service at http://localhost:8082
- Keycloak 26: local identity provider at http://localhost:8081
- Microcks: API mock server and contract-testing UI at http://localhost:8585 (optional profile)
- GitLab CI example: `.gitlab-ci.yml` validates the OpenAPI contract
- Optional GitLab Runner profile: for connecting to an existing GitLab instance

> Drupal and Microcks use their open-source community distributions; no paid or enterprise editions are required for this POC.
>
> Local-only POC. All credentials are development credentials. Do not expose this setup to the internet or reuse these secrets in production.

## Start

Requirements: Docker Desktop with Compose v2.

```bash
docker compose --profile microcks up --build -d
docker compose ps
```

Open:
- Drupal: http://localhost:8080
- Keycloak admin: http://localhost:8081 (admin / admin_dev_only)
- Swagger UI: http://localhost:8083
- Claims API health: http://localhost:8082/actuator/health
- Microcks: http://localhost:8585
- Claims API sample endpoint: http://localhost:8082/api/claims

## Test cases and verification

Run the offline structural tests from the project root:

```bash
python -m pip install pyyaml
python -m unittest discover -s tests -v
```

These checks validate Compose service declarations and port mappings, Community image configuration, the OpenAPI 3.1 Claims operations/schema references, and the Keycloak realm/client/user configuration. The GitLab pipeline runs these tests before OpenAPI linting.

The Spring Boot API also has MockMvc tests for `GET /api/claims` and `POST /api/claims`. Run them in an environment with Maven and JDK 21:

```bash
cd claims-api
mvn test
```

These tests have been added to the project but cannot be executed in environments without Maven/dependency resolution. Docker runtime tests must be run on a machine with Docker Compose; see the manual smoke-test checklist below.

### Manual runtime smoke-test checklist

1. `docker compose --profile microcks up --build -d`
2. Confirm `docker compose ps` shows services running/healthy where health checks exist.
3. Open Drupal at `http://localhost:8080` and complete its installer using the README database settings.
4. Open Swagger UI at `http://localhost:8083`; confirm Claims endpoints render.
5. Call `GET http://localhost:8082/api/claims` and expect HTTP 200 with the seed claim.
6. Call `POST http://localhost:8082/api/claims` with `Content-Type: application/json` and body `{"description":"manual smoke test"}`; expect HTTP 201.
7. Open Keycloak at `http://localhost:8081`; confirm the `developer-poc` realm appears.
8. Open Microcks at `http://localhost:8585`, import `specs/openapi.yaml`, then call the mock URL displayed by Microcks.

## Finish Drupal setup

1. Open http://localhost:8080 and choose the standard installation.
2. Database type: PostgreSQL.
3. Database name: `drupal`
4. Database username: `drupal`
5. Database password: `drupal_dev_only`
6. Database host: `drupal-db`
7. Database port: `5432`

Create an `API` content type or a content type named `API Product`, with fields such as:
- API name and description
- Business domain
- API version
- OpenAPI specification URL
- Base URL
- Authentication method
- Owner/team
- Lifecycle status

Use Drupal Views to create `/developer/apis` as a searchable catalog. Add links from each API entry to the Swagger UI page. For this POC, Swagger UI loads the Claims API spec by default.

## Keycloak

A `developer-poc` realm is imported at startup. It includes:
- public client `developer-portal`
- confidential client `claims-api`
- demo user `developer` / `developer_dev_only`

The sample API is deliberately open for easy local testing. The realm and clients are starter configuration, not production-hardened. The next step is to validate bearer tokens in Spring Security and configure Swagger UI's OAuth authorization-code + PKCE flow. Never put a confidential client secret in browser-side code.

## API spec and sample API

- Contract: `specs/openapi.yaml`
- Service source: `claims-api/`
- The OpenAPI server URL is `http://localhost:8082`, so Swagger's “Try it out” calls the host-published API.

## CI

`.gitlab-ci.yml` runs Redocly lint against the OpenAPI spec. Add it to a GitLab repository and push it to trigger validation.

To run a local lint check without GitLab:

```bash
docker run --rm -v "$PWD/specs:/specs:ro" node:22-alpine \
  sh -lc "npm install -g @redocly/cli && redocly lint /specs/openapi.yaml"
```

Optional runner profile (requires an existing GitLab URL and registration token):

```bash
docker compose --profile ci up -d gitlab-runner
docker compose exec gitlab-runner gitlab-runner register
```


## Use Microcks for API mocks and contract tests

Microcks Community Edition is started by the `microcks` Compose profile using the official open-source all-in-one native image, pinned to `1.15.0-native` for reproducibility.

1. Start the stack with `docker compose --profile microcks up --build -d`.
2. Open http://localhost:8585.
3. In Microcks, use **Importers** / **Direct import** (wording may vary by version) and upload `specs/openapi.yaml`.
4. Open the imported `Claims API` service in Microcks and inspect the generated mock endpoint URLs.
5. Call the mock URL shown by Microcks. Do not assume the mock path is the same as the Spring Boot endpoint; copy the URL shown in the UI.
6. To test the real API, use Microcks' test action and target `http://host.docker.internal:8082` when the test runner runs inside a container and needs to reach the host-published service. If the runner is configured to reach services on the same Compose network, use `http://claims-api:8080` instead.

Microcks mock generation uses examples and request/response data in the API artifact. Add realistic `examples` to the OpenAPI spec for useful mock payloads.

The all-in-one image is intended for local evaluation. For a team/shared or production installation, use the deployment instructions in the official Microcks documentation. This Community Edition POC does not automatically import the spec into Microcks on startup; import it through the UI or add a secured Microcks CLI import job to your CI pipeline.

Official docs:
- Getting started: https://microcks.io/documentation/tutorials/getting-started/
- GitLab CI integration: https://microcks.io/documentation/guides/automation/gitlab/

## Where Gloo fits

Gloo Gateway is Kubernetes-native; it is not included as a fake Docker Compose service. For the next stage, deploy Gloo in a local Kubernetes cluster (Docker Desktop Kubernetes or kind), route `/api/*` through Gloo, and configure Keycloak/OIDC policies there. Swagger's `servers` URL can then be changed to the gateway address.

Microcks is included as an optional Compose profile (`--profile microcks`) to keep the default stack lighter. The OpenAPI contract in `specs/` can be imported into Microcks for mock generation and contract tests.

## Stop and reset

```bash
docker compose down
# Destructive: remove persistent databases too
docker compose down -v
```

## Suggested next milestones

1. Create Drupal API Product content type and catalog view.
2. Add Keycloak OIDC login to Drupal.
3. Add Spring Security JWT validation to Claims API.
4. Put Gloo in front of APIs in local Kubernetes.
5. Add Microcks contract/mock tests.
6. Publish versioned specs and update the Drupal catalog from GitLab CI.
