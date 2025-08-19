from pydantic import BaseModel, Field
from typing import List

# Disease schema inside a breed request
class DiseaseCreateSchema(BaseModel):
    disease_name: str
    prevalence: float = Field(..., ge=0, le=1)  # must be between 0 and 1

class BreedCreateSchema(BaseModel):
    name: str
    species: str  # "dog" or "cat"
    diseases: List[DiseaseCreateSchema]

class DiseaseResponseSchema(BaseModel):
    disease_name: str
    prevalence: float

class BreedResponseSchema(BaseModel):
    name: str
    species: str
    diseases: List[DiseaseResponseSchema]

    class Config:
        orm_mode = True   # allows returning SQLAlchemy objects

# Risk analysis output
class SimilarBreedSchema(BaseModel):
    name: str
    species: str
    similarity: float

class RiskAnalysisResponseSchema(BaseModel):
    target_breed: str
    similar_breeds: List[SimilarBreedSchema]
    shared_diseases: List[str]
    care_plan: str
