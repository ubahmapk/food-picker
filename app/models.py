from pydantic import BaseModel, field_validator


class Place(BaseModel):
    name: str
    categories: list[str]

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name cannot be empty")
        return v

    @field_validator("categories")
    @classmethod
    def at_least_one_category(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("place must have at least one category")
        return v


class PlacesData(BaseModel):
    categories: list[str]
    places: list[Place]
