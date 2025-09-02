from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from .database import Base

# Tabla de asociación para la relación muchos a muchos
task_tag_association = Table('task_tags', Base.metadata,
    Column('task_id', String, primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)

class Tag(Base):
    __tablename__ = 'tags'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)

    # La relación se define usando 'secondary' para apuntar a la tabla de asociación.
    # SQLAlchemy manejará la lógica de la relación muchos a muchos a través de esta tabla.
    # Aunque no tenemos un modelo 'Task', la relación se puede gestionar del lado de 'Tag'.
