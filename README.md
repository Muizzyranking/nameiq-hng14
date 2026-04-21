# Insighta Labs Profile API

A Flask-based REST API for demographic intelligence, supporting advanced filtering, sorting, pagination, natural language search, and SQLite persistence. Built for **HNG Internship 14 — Backend Stage 1(and 2)**.

---

## Tech Stack

- **Python 3.11+** / **Flask** / **Pydantic**
- **SQLite** — lightweight, zero-config persistence
- **uuid6** — UUID v7 generation
- **requests** — external API calls

---

## Project Structure

```
app/
├── app.py              # Flask app entry point — mounts API blueprint
├── api.py              # All routes (POST, GET list, GET single, DELETE, NL search)
├── models.py           # SQLite layer — schema, CRUD, advanced filtering, pagination
├── services.py         # External API calls (Genderize, Agify, Nationalize) + country mapping
├── schemas.py          # Pydantic models for request validation & response serialization
├── exceptions.py       # Global exception class + Flask error handlers
├── parser.py        # Rule-based natural language parser (190+ countries mapped)
├── seed.py             # Idempotent database seeder with age_group validation
├── data/
│   └── profiles.json   # Seed data (2026 profiles)
├── profiles.db         # Auto-created SQLite database
└── README.md
```

---

## Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/muizzyranking/nameiq-hng14.git
cd nameiq-hng14
```

### 2. Install dependencies (using uv)

```bash
uv sync
```

### 3. Seed the database

Place the provided `profiles.json` (2026 records) in `data/profiles.json`, then run:

```bash
uv run python app/seed.py
```

Re-running the seed will not create duplicates.

### 4. Run the server

```bash
uv run python app/app.py
```

The server starts at `http://127.0.0.1:5000`.

---

## API Reference

### Base URL

```
http://127.0.0.1:5000/api
```

---

### `POST /api/profiles`

Creates a new profile by calling the Genderize, Agify, and Nationalize APIs. If a profile with the same name already exists, the existing record is returned (case-insensitive match).

**Request body:**

```json
{ "name": "emmanuel" }
```

**Response `201 Created`:**

```json
{
  "status": "success",
  "data": {
    "id": "b3f9c1e2-7d4a-4c91-9c2a-1f0a8e5b6d12",
    "name": "emmanuel",
    "gender": "male",
    "gender_probability": 0.99,
    "age": 34,
    "age_group": "adult",
    "country_id": "NG",
    "country_name": "Nigeria",
    "country_probability": 0.85,
    "created_at": "2026-04-01T12:00:00Z"
  }
}
```

**Response `200 OK` (name already exists):**

```json
{
  "status": "success",
  "data": { "...existing profile..." }
}
```

---

### `GET /api/profiles`

Returns all profiles with advanced filtering, sorting, and pagination.

**Query parameters:**

| Parameter | Type | Example | Description |
|-----------|------|---------|-------------|
| `gender` | string | `?gender=male` | Filter by gender (`male` or `female`) |
| `country_id` | string | `?country_id=NG` | Filter by ISO country code |
| `age_group` | string | `?age_group=adult` | Filter by age group (`child`, `teenager`, `adult`, `senior`) |
| `min_age` | integer | `?min_age=25` | Minimum age (inclusive) |
| `max_age` | integer | `?max_age=40` | Maximum age (inclusive) |
| `min_gender_probability` | float | `?min_gender_probability=0.8` | Minimum gender confidence (0.0–1.0) |
| `min_country_probability` | float | `?min_country_probability=0.5` | Minimum country confidence (0.0–1.0) |
| `sort_by` | string | `?sort_by=age` | Sort field: `age`, `created_at`, `gender_probability` |
| `order` | string | `?order=desc` | Sort order: `asc` or `desc` |
| `page` | integer | `?page=1` | Page number (default: 1) |
| `limit` | integer | `?limit=10` | Items per page (default: 10, max: 50) |

All filters are combinable (AND logic).

**Example:**

```
GET /api/profiles?gender=male&country_id=NG&min_age=25&sort_by=age&order=desc&page=1&limit=10
```

**Response `200 OK`:**

```json
{
  "status": "success",
  "page": 1,
  "limit": 10,
  "total": 2026,
  "data": [
    {
      "id": "b3f9c1e2-7d4a-4c91-9c2a-1f0a8e5b6d12",
      "name": "emmanuel",
      "gender": "male",
      "gender_probability": 0.99,
      "age": 34,
      "age_group": "adult",
      "country_id": "NG",
      "country_name": "Nigeria",
      "country_probability": 0.85,
      "created_at": "2026-04-01T12:00:00Z"
    }
  ]
}
```

---

### `GET /api/profiles/:id`

Returns a single profile by its UUID v7.

**Response `200 OK`:**

```json
{
  "status": "success",
  "data": {
    "id": "b3f9c1e2-7d4a-4c91-9c2a-1f0a8e5b6d12",
    "name": "emmanuel",
    "gender": "male",
    "gender_probability": 0.99,
    "age": 34,
    "age_group": "adult",
    "country_id": "NG",
    "country_name": "Nigeria",
    "country_probability": 0.85,
    "created_at": "2026-04-01T12:00:00Z"
  }
}
```

---

### `DELETE /api/profiles/:id`

Deletes a profile by its UUID. Returns `204 No Content` on success.

---

### `GET /api/profiles/search`

Natural language search endpoint. Parses plain English queries into structured filters using a rule-based parser (no AI/LLMs).

**Query parameters:**

| Parameter | Type | Example | Description |
|-----------|------|---------|-------------|
| `q` | string | `?q=young males from nigeria` | Natural language query (required) |
| `page` | integer | `?page=1` | Page number (default: 1) |
| `limit` | integer | `?limit=10` | Items per page (default: 10, max: 50) |

**Example mappings:**

| Query | Parsed Filters |
|-------|----------------|
| `young males` | `gender=male`, `min_age=16`, `max_age=24` |
| `females above 30` | `gender=female`, `min_age=30` |
| `people from angola` | `country_id=AO` |
| `adult males from kenya` | `gender=male`, `age_group=adult`, `country_id=KE` |
| `male and female teenagers above 17` | `age_group=teenager`, `min_age=17` |

**Response `200 OK`:**

```json
{
  "status": "success",
  "page": 1,
  "limit": 10,
  "total": 42,
  "data": [ "...profiles..." ]
}
```

**Response `400` (uninterpretable query):**

```json
{ "status": "error", "message": "Unable to interpret query" }
```

---

## Natural Language Parsing Approach

The natural language search endpoint (`GET /api/profiles/search?q=...`) uses a **rule-based parser** with no AI or LLMs.

### Supported Keywords

| Concept | Keywords | Mapping |
|---------|----------|---------|
| **Gender** | `male`, `female`, `man`, `woman`, `men`, `women`, `boy`, `girl` | `gender=male\|female` |
| **Age Group** | `child`, `children`, `teenager`, `teen`, `teens`, `adult`, `adults`, `senior`, `seniors`, `elderly` | `age_group=child\|teenager\|adult\|senior` |
| **Young** | `young`, `youth` | `min_age=16`, `max_age=24` (parsing-only, not a stored group) |
| **Age Thresholds** | `above X`, `over X`, `older than X` | `min_age=X` |
| | `below X`, `under X`, `younger than X` | `max_age=X` |
| **Countries** | Full country names (e.g., `nigeria`, `kenya`, `united states`) | `country_id=NG\|KE\|US` |

### How the Logic Works

1. **Tokenization**: The query is lowercased and split into alphanumeric tokens.
2. **Gender Detection**: Scans for gender keywords; picks the first match.
3. **Age Group Detection**: Scans for age group keywords; picks the first match.
4. **"Young" Detection**: If `young` or `youth` appears, sets `min_age=16` and `max_age=24`. This does **not** set `age_group`.
5. **Numeric Thresholds**: Uses regex to find patterns like `above 30`, `under 25`, `older than 40`.
6. **Country Matching**: Matches against a comprehensive mapping of 190+ country names to ISO codes. Multi-word countries (e.g., `south africa`, `united kingdom`) are checked before single-word ones to avoid partial matches.
7. **Return**: Returns structured filter parameters. If **no** interpretable filters are found, returns `400 Unable to interpret query`.

### Limitations & Edge Cases

1. **No Compound Age Ranges**: `"between 20 and 30"` is **not** supported. Only single thresholds (`above`, `below`).
2. **No Negation**: `"not from Nigeria"` or `"excluding males"` are **not** supported.
3. **Single Country Only**: Queries with multiple countries (e.g., `"from Nigeria or Kenya"`) will only match the first found.
4. **No Ordinal Ages**: `"in their twenties"`, `"teenagers"` (as an ordinal concept) are not parsed numerically beyond the keyword mapping.
5. **"Young" Conflicts**: If a query says `"young adults"`, both `young` (16-24) and `adult` (age_group) are applied. This may return empty results since `adult` starts at 20. The parser does not resolve such conflicts.
6. **No Boolean Logic**: `"and"` and `"or"` are treated as noise words, not logical operators. `"male and female"` will only match the first gender found.
7. **Case Sensitivity**: All matching is case-insensitive, but country names must match the dictionary exactly (e.g., `"united states of america"` won't match `"united states"`).
8. **No Fuzzy Matching**: Typos in country names or keywords will cause the parser to miss them.

---

## Classification Rules

### Age Group

| Age Range | Group |
|-----------|-------|
| 0 – 12 | `child` |
| 13 – 19 | `teenager` |
| 20 – 59 | `adult` |
| 60+ | `senior` |

### Country Name Resolution

Country names are resolved via a static mapping of 190+ ISO codes. For API-created profiles, the top country from Nationalize.io is used. For seeded profiles, the provided `country_name` is used (with validation against the mapping).

---

## Error Responses

All errors follow this structure:

```json
{ "status": "error", "message": "<error message>" }
```

| Status | Meaning |
|--------|---------|
| `400` | Missing or empty parameter |
| `404` | Profile not found |
| `409` | Profile with this name already exists |
| `422` | Invalid parameter type or value |
| `500` | Internal server error |
| `502` | External API returned an invalid response |

**502 error example:**

```json
{ "status": "error", "message": "Genderize returned an invalid response" }
```

Possible API names in the message: `Genderize`, `Agify`, `Nationalize`.

> Profiles are **never stored** if any external API returns an invalid or empty response.

---

## External APIs Used

| API | URL | Data provided |
|-----|-----|---------------|
| Genderize.io | `https://api.genderize.io` | `gender`, `probability` |
| Agify.io | `https://api.agify.io` | `age` |
| Nationalize.io | `https://api.nationalize.io` | `country` array with probabilities |

All three are free and require no API key.

---

## Notes

- All IDs are **UUID v7** (time-sortable).
- All timestamps are **UTC ISO 8601** (`YYYY-MM-DDTHH:MM:SSZ`).
- CORS is enabled (`Access-Control-Allow-Origin: *`) on all routes.
- Name matching for idempotency is **case-insensitive** (`emmanuel` == `Emmanuel` == `EMMANUEL`).
- Database indexes are created on `gender`, `age_group`, `country_id`, `age`, and `created_at` to avoid full-table scans.
- The seed script validates `age_group` against computed values and skips duplicates on re-runs.
