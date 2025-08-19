# seed.py
from sqlalchemy.orm import Session
from database import Base, engine, SessionLocal
import models

# Drop & recreate tables
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

# Sample data
breeds = [
    {"name": "Labrador Retriever", "species": "dog"},
    {"name": "German Shepherd", "species": "dog"},
    {"name": "Golden Retriever", "species": "dog"},
    {"name": "Bulldog", "species": "dog"},
    {"name": "Beagle", "species": "dog"},
    {"name": "Persian", "species": "cat"},
    {"name": "Siamese", "species": "cat"},
    {"name": "Maine Coon", "species": "cat"},
    {"name": "Ragdoll", "species": "cat"},
    {"name": "British Shorthair", "species": "cat"},
]

diseases = [
    "Hip Dysplasia",
    "Diabetes",
    "Kidney Disease",
    "Arthritis",
    "Heart Disease"
]

# (breed_name, disease_name, prevalence)
links = [
    ("Labrador Retriever", "Hip Dysplasia", 0.8),
    ("Labrador Retriever", "Arthritis", 0.4),
    ("German Shepherd", "Hip Dysplasia", 0.7),
    ("German Shepherd", "Heart Disease", 0.3),
    ("Golden Retriever", "Hip Dysplasia", 0.6),
    ("Golden Retriever", "Arthritis", 0.5),
    ("Bulldog", "Heart Disease", 0.6),
    ("Beagle", "Diabetes", 0.4),
    ("Persian", "Kidney Disease", 0.7),
    ("Siamese", "Diabetes", 0.5),
    ("Maine Coon", "Heart Disease", 0.4),
    ("Ragdoll", "Kidney Disease", 0.6),
    ("British Shorthair", "Arthritis", 0.3),
    ("British Shorthair", "Diabetes", 0.4),
]

def seed():
    db: Session = SessionLocal()

    # Add diseases
    disease_objs = {}
    for d in diseases:
        obj = models.Disease(name=d)
        db.add(obj)
        disease_objs[d] = obj
    db.commit()

    # Add breeds
    breed_objs = {}
    for b in breeds:
        obj = models.Breed(name=b["name"], species=b["species"])
        db.add(obj)
        breed_objs[b["name"]] = obj
    db.commit()

    # Add links
    for breed_name, disease_name, prevalence in links:
        link = models.BreedDiseaseLink(
            breed_id=breed_objs[breed_name].id,
            disease_id=disease_objs[disease_name].id,
            prevalence=prevalence
        )
        db.add(link)

    db.commit()
    db.close()
    print("✅ Database seeded successfully!")

if __name__ == "__main__":
    seed()
