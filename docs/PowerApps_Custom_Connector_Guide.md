# Power Apps Custom Connector: USAspending.gov

This guide explains how to import and test the USAspending.gov OpenAPI 2.0 definition in Power Apps.

## Files

- YAML (recommended for import): `docs/usaspendingapi.yaml`
- JSON (alternate): `docs/usaspendingapi.json`

Both describe a minimal, Power Apps–compatible subset of the USAspending API v2.

## Import Steps (Power Apps)

1. Sign in to https://make.powerapps.com/
2. Go to Data > Custom connectors > New custom connector > Import an OpenAPI file
3. Name the connector (e.g., "USAspending")
4. Upload `usaspendingapi.yaml` and Continue
5. On General, verify:
   - Host: `api.usaspending.gov`
   - Base URL: `/api/v2`
6. Create connector

## Test

- Create a new connection (no auth required)
- Test operations:
  - Get Award Details: use a real Award ID. Example pattern: `CONT_AWD_89233218CNA000001_8900_-NONE-_-NONE-` (replace with a known ID)
  - Count Federal Accounts: same `award_id`
  - Funding Rollup: body `{ "award_id": "<AWARD_ID>" }`
  - Transactions: body `{ "award_id": "<AWARD_ID>", "page": 1, "limit": 10 }`

## Troubleshooting

- Generic YAML parsing error on import:
  - Ensure file size < 1 MB (this spec is small)
  - Try the JSON version `usaspendingapi.json`
  - Remove cached connector attempts and retry
- 404 calling Get Award Details:
  - Some USAspending endpoints require a trailing slash. If needed, edit the path to `/awards/{award_id}/` in the connector UI and save.
- Encoding issues for path parameters:
  - The spec sets `x-ms-url-encoding: single`. If the award ID contains characters that cause 404, try removing or setting to `double` and retest.

## Notes

- The endpoints used are documented at https://api.usaspending.gov/docs/endpoints
- No API key is required
- Number formats use `float` for compatibility with Power Apps
