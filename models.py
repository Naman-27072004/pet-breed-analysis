from sqlalchemy import Column, Integer, String, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base

class Breed(Base):
    __tablename__ = "breeds"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    species = Column(String, nullable=False)

    diseases = relationship("BreedDiseaseLink", back_populates="breed")

class Disease(Base):
    __tablename__ = "diseases"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)

    breeds = relationship("BreedDiseaseLink", back_populates="disease")

class BreedDiseaseLink(Base):
    __tablename__ = "breed_disease_links"
    breed_id = Column(Integer, ForeignKey("breeds.id"), primary_key=True)
    disease_id = Column(Integer, ForeignKey("diseases.id"), primary_key=True)
    prevalence = Column(Float, nullable=False)

    breed = relationship("Breed", back_populates="diseases")
    disease = relationship("Disease", back_populates="breeds")

    __table_args__ = (UniqueConstraint("breed_id", "disease_id"),)
