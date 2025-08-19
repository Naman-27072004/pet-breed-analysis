from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import engine, Base, get_db
import models, schemas
import crud
# main.py (only the endpoint; keep the rest as you already have)
import services

# Create all DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Pet Breed & Disease Analysis API")

# --- Endpoints placeholder ---

@app.post("/breeds", response_model=schemas.BreedResponseSchema, status_code=status.HTTP_201_CREATED)
def create_breed(breed: schemas.BreedCreateSchema, db: Session = Depends(get_db)):
    return crud.create_breed(db, breed)

# @app.post("/breeds", response_model=schemas.BreedResponseSchema, status_code=status.HTTP_201_CREATED)
# def create_breed(breed: schemas.BreedCreateSchema, db: Session = Depends(get_db)):
#     """
#     Create a new breed with diseases.
#     (Implementation will go in crud.py later)
#     """
#     raise HTTPException(status_code=501, detail="Not implemented yet")

@app.get("/breeds/risk_analysis", response_model=schemas.RiskAnalysisResponseSchema)
def risk_analysis(breed_name: str, db: Session = Depends(get_db)):
    return services.run_risk_analysis(db, breed_name)

# @app.get("/breeds/risk_analysis", response_model=schemas.RiskAnalysisResponseSchema)
# def risk_analysis(breed_name: str, db: Session = Depends(get_db)):
#     """
#     Analyze disease risks and similarities.
#     (Implementation will go in services.py later)
#     """
#     raise HTTPException(status_code=501, detail="Not implemented yet")
# uvicorn main:app --reload