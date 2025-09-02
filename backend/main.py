"""
Main application file for the FastAPI backend.

This file initializes the FastAPI application, creates the database tables,
and defines the API endpoints.
"""
import httpx
from fastapi import FastAPI, Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List

from . import crud, models, schemas
from .database import SessionLocal, engine

# Create all database tables on startup
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Domino Tasks API",
    description="Backend services for the Domino Tasks application.",
    version="0.1.0"
)

# --- Security Scheme ---
bearer_scheme = HTTPBearer()

# --- Dependencies ---

def get_db():
    """
    Dependency that provides a database session for each request.

    Yields:
        Session: The SQLAlchemy database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- API Endpoints ---

@app.post("/auth/google", response_model=schemas.UserInfo)
async def authenticate_google(token_data: schemas.TokenData):
    """
    Authenticates a user by validating a Google access token.

    This endpoint acts as a proxy to Google's userinfo endpoint. It takes an
    access token, sends it to Google for validation, and returns the user's
    information if the token is valid.

    Args:
        token_data: A Pydantic model containing the Google access_token.

    Raises:
        HTTPException: 401 Unauthorized if the token is invalid or expired.
        HTTPException: 400 Bad Request if the request to Google fails.

    Returns:
        The user's information (email, name, picture).
    """
    google_userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
    headers = {"Authorization": f"Bearer {token_data.access_token}"}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(google_userinfo_url, headers=headers)
            response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
            user_data = response.json()
            return schemas.UserInfo(**user_data)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired Google token.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to fetch user info from Google: {e.response.text}"
                )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"An error occurred while requesting user info from Google: {e}"
            )

@app.get("/tasks", response_model=List[schemas.Task])
async def get_tasks(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
    db: Session = Depends(get_db)
):
    """
    Retrieves tasks from the user's default Google Tasks list and enriches
    them with locally stored tags.

    Args:
        credentials: The bearer token credentials handled by FastAPI's security scheme.
        db: The database session dependency.

    Raises:
        HTTPException: 401 if the token is invalid or missing.
        HTTPException: 400 if the request to Google fails.

    Returns:
        A list of tasks, each enriched with its associated tags.
    """
    token = credentials.token
    google_tasks_url = "https://www.googleapis.com/tasks/v1/lists/@default/tasks"
    headers = {"Authorization": f"Bearer {token}"}
    
    enriched_tasks = []

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(google_tasks_url, headers=headers)
            response.raise_for_status()
            google_tasks_data = response.json().get("items", [])
            
            for task_data in google_tasks_data:
                # Validate and parse Google Task data
                google_task = schemas.GoogleTask.model_validate(task_data)
                
                # Get local tags for the task
                local_tags = crud.get_tags_for_task(db, task_id=google_task.id)
                
                # Create the enriched task object
                enriched_task = schemas.Task(**google_task.model_dump(), tags=local_tags)
                enriched_tasks.append(enriched_task)
                
            return enriched_tasks

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired Google token.",
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to fetch tasks from Google: {e.response.text}"
                )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"An error occurred while requesting tasks from Google: {e}"
            )


@app.post("/tags/", response_model=schemas.Tag)
def create_tag(tag: schemas.TagCreate, db: Session = Depends(get_db)):
    """
    Creates a new tag in the database.

    Checks if a tag with the same name already exists before creating.

    Args:
        tag: The tag data for creation.
        db: The database session dependency.

    Raises:
        HTTPException: 400 Bad Request if the tag name already exists.

    Returns:
        The newly created tag.
    """
    db_tag = crud.get_tag_by_name(db, name=tag.name)
    if db_tag:
        raise HTTPException(status_code=400, detail="Tag already registered")
    return crud.create_tag(db=db, tag=tag)

@app.get("/tags/", response_model=List[schemas.Tag])
def read_tags(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieves a list of tags from the database.

    Args:
        skip: The number of records to skip (for pagination).
        limit: The maximum number of records to return.
        db: The database session dependency.

    Returns:
        A list of tags.
    """
    tags = crud.get_tags(db, skip=skip, limit=limit)
    return tags

import httpx
from fastapi import FastAPI, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import List, Annotated

from . import crud, models, schemas
from .database import SessionLocal, engine

# Create all database tables on startup
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Domino Tasks API",
    description="Backend services for the Domino Tasks application.",
    version="0.1.0"
)

# --- Dependencies ---

def get_db():
    """
    Dependency that provides a database session for each request.

    Yields:
        Session: The SQLAlchemy database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- API Endpoints ---

@app.post("/auth/google", response_model=schemas.UserInfo)
async def authenticate_google(token_data: schemas.TokenData):
    """
    Authenticates a user by validating a Google access token.

    This endpoint acts as a proxy to Google's userinfo endpoint. It takes an
    access token, sends it to Google for validation, and returns the user's
    information if the token is valid.

    Args:
        token_data: A Pydantic model containing the Google access_token.

    Raises:
        HTTPException: 401 Unauthorized if the token is invalid or expired.
        HTTPException: 400 Bad Request if the request to Google fails.

    Returns:
        The user's information (email, name, picture).
    """
    google_userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
    headers = {"Authorization": f"Bearer {token_data.access_token}"}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(google_userinfo_url, headers=headers)
            response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
            user_data = response.json()
            return schemas.UserInfo(**user_data)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired Google token.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to fetch user info from Google: {e.response.text}"
                )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"An error occurred while requesting user info from Google: {e}"
            )

@app.get("/tasks", response_model=List[schemas.Task])
async def get_tasks(
    authorization: Annotated[str, Header()],
    db: Session = Depends(get_db)
):
    """
    Retrieves tasks from the user's default Google Tasks list and enriches
    them with locally stored tags.

    Args:
        authorization: The 'Bearer <token>' authorization header.
        db: The database session dependency.

    Raises:
        HTTPException: 401 if the token is invalid or missing.
        HTTPException: 400 if the request to Google fails.

    Returns:
        A list of tasks, each enriched with its associated tags.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization scheme."
        )
    token = authorization.split(" ")[1]
    
    google_tasks_url = "https://www.googleapis.com/tasks/v1/lists/@default/tasks"
    headers = {"Authorization": f"Bearer {token}"}
    
    enriched_tasks = []

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(google_tasks_url, headers=headers)
            response.raise_for_status()
            google_tasks_data = response.json().get("items", [])
            
            for task_data in google_tasks_data:
                # Validate and parse Google Task data
                google_task = schemas.GoogleTask.model_validate(task_data)
                
                # Get local tags for the task
                local_tags = crud.get_tags_for_task(db, task_id=google_task.id)
                
                # Create the enriched task object
                enriched_task = schemas.Task(**google_task.model_dump(), tags=local_tags)
                enriched_tasks.append(enriched_task)
                
            return enriched_tasks

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired Google token.",
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to fetch tasks from Google: {e.response.text}"
                )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"An error occurred while requesting tasks from Google: {e}"
            )


@app.post("/tags/", response_model=schemas.Tag)
def create_tag(tag: schemas.TagCreate, db: Session = Depends(get_db)):
    """
    Creates a new tag in the database.

    Checks if a tag with the same name already exists before creating.

    Args:
        tag: The tag data for creation.
        db: The database session dependency.

    Raises:
        HTTPException: 400 Bad Request if the tag name already exists.

    Returns:
        The newly created tag.
    """
    db_tag = crud.get_tag_by_name(db, name=tag.name)
    if db_tag:
        raise HTTPException(status_code=400, detail="Tag already registered")
    return crud.create_tag(db=db, tag=tag)

@app.get("/tags/", response_model=List[schemas.Tag])
def read_tags(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieves a list of tags from the database.

    Args:
        skip: The number of records to skip (for pagination).
        limit: The maximum number of records to return.
        db: The database session dependency.

    Returns:
        A list of tags.
    """
    tags = crud.get_tags(db, skip=skip, limit=limit)
    return tags