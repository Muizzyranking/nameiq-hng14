from typing import Any

from pydantic import BaseModel, Field, field_validator


class ProfileCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, description="Person's full name")

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        return v.strip()


class ProfileListQuery(BaseModel):
    gender: str | None = None
    country_id: str | None = None
    age_group: str | None = None
    min_age: int | None = Field(None, ge=0)
    max_age: int | None = Field(None, ge=0)
    min_gender_probability: float | None = Field(None, ge=0.0, le=1.0)
    min_country_probability: float | None = Field(None, ge=0.0, le=1.0)
    sort_by: str = "created_at"
    order: str = "desc"
    page: int = Field(1, ge=1)
    limit: int = Field(10, ge=1, le=50)

    @field_validator("gender", "country_id", "age_group")
    @classmethod
    def lowercase_strings(cls, v: str | None) -> str | None:
        if isinstance(v, str):
            return v.strip().lower()
        return v


class NaturalLanguageQuery(BaseModel):
    q: str = Field(..., min_length=1)
    page: int = Field(1, ge=1)
    limit: int = Field(10, ge=1, le=50)

    @field_validator("q")
    @classmethod
    def strip_query(cls, v: str) -> str:
        return v.strip()


class ProfileFullView(BaseModel):
    id: str
    name: str
    gender: str
    gender_probability: float
    age: int
    age_group: str
    country_id: str
    country_name: str
    country_probability: float
    created_at: str

    @field_validator("gender_probability", "country_probability")
    @classmethod
    def round_probabilities(cls, v: float) -> float:
        return round(v, 2)

    @classmethod
    def from_db_row(cls, row: dict[str, Any]) -> "ProfileFullView":
        return cls(**row)


class ProfileListView(BaseModel):
    id: str
    name: str
    gender: str
    age: int
    age_group: str
    country_id: str
    country_name: str

    @classmethod
    def from_db_row(cls, row: dict[str, Any]) -> "ProfileListView":
        return cls(**{k: v for k, v in row.items() if k in cls.model_fields})


class ProfileListResponse(BaseModel):
    status: str = "success"
    page: int
    limit: int
    total: int
    data: list[ProfileFullView]


class ProfileCreateResponse(BaseModel):
    status: str = "success"
    message: str | None = None
    data: ProfileFullView


class ProfileSingleResponse(BaseModel):
    status: str = "success"
    data: ProfileFullView


class ErrorResponse(BaseModel):
    status: str = "error"
    message: str
    errors: dict[str, Any] | None = None
