"""
CRUD (Create, Read, Update, Delete) operations for the database.

This module contains functions for interacting with the database models,
separating the database logic from the API endpoint logic.
"""
from sqlalchemy.orm import Session
from typing import List
from . import models, schemas

# --- Tag CRUD Operations ---

def get_tag_by_name(db: Session, name: str) -> models.Tag | None:
    """
    Retrieves a tag from the database by its name.

    Args:
        db: The database session.
        name: The name of the tag to retrieve.

    Returns:
        The Tag object if found, otherwise None.
    """
    return db.query(models.Tag).filter(models.Tag.name == name).first()

def get_tags(db: Session, skip: int = 0, limit: int = 100) -> List[models.Tag]:
    """
    Retrieves a list of tags from the database with pagination.

    Args:
        db: The database session.
        skip: The number of records to skip.
        limit: The maximum number of records to return.

    Returns:
        A list of Tag objects.
    """
    return db.query(models.Tag).offset(skip).limit(limit).all()

def create_tag(db: Session, tag: schemas.TagCreate) -> models.Tag:
    """
    Creates a new tag in the database.

    Args:
        db: The database session.
        tag: The Pydantic schema for the tag to create.

    Returns:
        The newly created Tag object.
    """
    db_tag = models.Tag(name=tag.name)
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    return db_tag

def get_tags_for_task(db: Session, task_id: str) -> List[models.Tag]:
    """
    Retrieves all tags associated with a specific task ID.

    Args:
        db: The database session.
        task_id: The ID of the task.

    Returns:
        A list of Tag objects associated with the task.
    """
    return (
        db.query(models.Tag)
        .join(models.task_tag_association)
        .filter(models.task_tag_association.c.task_id == task_id)
        .all()
    )
