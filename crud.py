from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import models, schemas

# -------------------------
# Create / Get Diseases
# -------------------------
def get_disease_by_name(db: Session, name: str):
    return db.query(models.Disease).filter(models.Disease.name == name).first()

def create_disease(db: Session, name: str):
    disease = models.Disease(name=name)
    db.add(disease)
    db.commit()
    db.refresh(disease)
    return disease

# -------------------------
# Create / Get Breeds
# -------------------------
def get_breed_by_name(db: Session, name: str):
    return db.query(models.Breed).filter(models.Breed.name == name).first()

def create_breed(db: Session, breed_data: schemas.BreedCreateSchema):
    # ✅ Check species
    if breed_data.species not in ["dog", "cat"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Species must be 'dog' or 'cat'.")

    # ✅ Check duplicate
    existing_breed = get_breed_by_name(db, breed_data.name)
    if existing_breed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Breed already exists.")

    # ✅ Create breed
    breed = models.Breed(name=breed_data.name, species=breed_data.species)
    db.add(breed)
    db.commit()
    db.refresh(breed)

    # ✅ Handle diseases
    for d in breed_data.diseases:
        if not (0 <= d.prevalence <= 1):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Prevalence must be between 0 and 1.")

        disease = get_disease_by_name(db, d.disease_name)
        if not disease:
            disease = create_disease(db, d.disease_name)

        link = models.BreedDiseaseLink(breed_id=breed.id, disease_id=disease.id, prevalence=d.prevalence)
        db.add(link)

    db.commit()
    db.refresh(breed)

    # ✅ Build response
    return schemas.BreedResponseSchema(
        name=breed.name,
        species=breed.species,
        diseases=[
            schemas.DiseaseResponseSchema(disease_name=d.disease.name, prevalence=d.prevalence)
            for d in breed.diseases
        ]
    )
