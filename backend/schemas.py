"""
Pydantic models (schemas) for data validation and serialization.

This module defines the structure of the data that is received and sent by the API.
It ensures that the data conforms to the expected types and constraints.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# --- Tag Schemas ---

class TagBase(BaseModel):
    """Base schema for a tag, containing the essential data."""
    name: str

class TagCreate(TagBase):
    """Schema used for creating a new tag. Inherits from TagBase."""
    pass

class Tag(TagBase):
    """Schema for a tag as it is stored in the database, including its ID."""
    id: int

    class Config:
        """Pydantic configuration to allow creating the model from ORM objects."""
        from_attributes = True

# --- Auth Schemas ---

class TokenData(BaseModel):
    """Schema for receiving the access token from the client."""
    access_token: str

class UserInfo(BaseModel):
    """Schema for representing user information obtained from Google."""
    email: str
    name: str
    picture: Optional[str] = None

# --- Task Schemas ---

class GoogleTask(BaseModel):
    """
    Represents the structure of a task as returned by the Google Tasks API.
    Includes only the fields relevant to this application.
    """
    id: str
    title: str
    status: str
    due: Optional[datetime] = None
    notes: Optional[str] = None

class Task(GoogleTask):
    """
    Represents a task enriched with local application data (tags).
    This is the schema that will be returned by our API.
    """
    tags: List[Tag] = []
