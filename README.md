# nameiq-hng14

A Flask REST API that accepts a name, enriches it with data from three external APIs (gender, age, nationality), classifies the result, and persists it in SQLite. Built for **HNG Internship 14 — Backend Stage 1**.

---

## Tech Stack

- **Python 3.11+** / **Flask**
- **SQLite** — lightweight, zero-config persistence
- **uuid6** — UUID v7 generation
- **requests** — external API calls

---

## Project Structure

```
nameiq-hng14/
├── app/
│   ├── app.py        # Flask app, routes, CORS
│   ├── models.py     # SQLite schema & DB helpers
│   └── services.py   # External API calls & classification logic
├── profiles.db       # auto-created on first run
└── README.md
```

---

## Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/muizzyranking/nameiq-hng14.git
cd nameiq-hng14
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the server

```bash
cd app
python app.py
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
{ "name": "ella" }
```

**Response `201 Created`:**

```json
{
  "status": "success",
  "data": {
    "id": "019d8fd0-5db1-744d-8391-d9f9dbb10b07",
    "name": "ella",
    "gender": "female",
    "gender_probability": 0.98,
    "sample_size": 9321,
    "age": 34,
    "age_group": "adult",
    "country_id": "DK",
    "country_probability": 0.12,
    "created_at": "2026-04-15T10:00:00Z"
  }
}
```

**Response `200 OK` (name already exists):**

```json
{
  "status": "success",
  "message": "Profile already exists",
  "data": { "...existing profile..." }
}
```

---

### `GET /api/profiles/:id`

Returns a single profile by its UUID.

**Response `200 OK`:**

```json
{
  "status": "success",
  "data": {
    "id": "019d8fd0-5db1-744d-8391-d9f9dbb10b07",
    "name": "ella",
    "gender": "female",
    "gender_probability": 0.98,
    "sample_size": 9321,
    "age": 34,
    "age_group": "adult",
    "country_id": "DK",
    "country_probability": 0.12,
    "created_at": "2026-04-15T10:00:00Z"
  }
}
```

---

### `GET /api/profiles`

Returns all profiles. Supports optional query parameters for filtering. All filter values are case-insensitive.

**Query parameters:**

| Parameter  | Example           | Description              |
|------------|-------------------|--------------------------|
| `gender`   | `?gender=female`  | Filter by gender         |
| `country_id` | `?country_id=NG` | Filter by country code  |
| `age_group` | `?age_group=adult` | Filter by age group    |

Parameters can be combined: `?gender=male&country_id=NG`

**Response `200 OK`:**

```json
{
  "status": "success",
  "count": 2,
  "data": [
    {
      "id": "019d8fd0-5db1-744d-8391-d9f9dbb10b07",
      "name": "ella",
      "gender": "female",
      "age": 34,
      "age_group": "adult",
      "country_id": "DK"
    }
  ]
}
```

---

### `DELETE /api/profiles/:id`

Deletes a profile by its UUID. Returns `204 No Content` on success.

---

## Classification Rules

### Age Group (from Agify)

| Age Range | Group        |
|-----------|--------------|
| 0 – 12    | `child`      |
| 13 – 19   | `teenager`   |
| 20 – 59   | `adult`      |
| 60+       | `senior`     |

### Nationality (from Nationalize)

The country with the highest probability in the response is selected as `country_id`.

---

## Error Responses

All errors follow this structure:

```json
{ "status": "error", "message": "<error message>" }
```

| Status | Meaning                                      |
|--------|----------------------------------------------|
| `400`  | Missing or empty `name` field                |
| `404`  | Profile not found                            |
| `422`  | Invalid type (e.g. `name` is not a string)   |
| `500`  | Internal server error                        |
| `502`  | External API returned an invalid response    |

**502 error format:**

```json
{ "status": "error", "message": "Genderize returned an invalid response" }
```

Possible API names in the message: `Genderize`, `Agify`, `Nationalize`.

> Profiles are **never stored** if any external API returns an invalid or empty response.

---

## External APIs Used

| API           | URL                              | Data provided                     |
|---------------|----------------------------------|-----------------------------------|
| Genderize.io  | `https://api.genderize.io`       | `gender`, `probability`, `count`  |
| Agify.io      | `https://api.agify.io`           | `age`                             |
| Nationalize.io| `https://api.nationalize.io`     | `country` array with probabilities|

All three are free and require no API key.

---

## Notes

- All IDs are **UUID v7** (time-sortable).
- All timestamps are **UTC ISO 8601** (`YYYY-MM-DDTHH:MM:SSZ`).
- CORS is enabled (`Access-Control-Allow-Origin: *`) on all routes.
- Name matching for idempotency is **case-insensitive** (`ella` == `Ella` == `ELLA`).
