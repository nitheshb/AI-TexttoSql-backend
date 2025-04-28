from typing import Any, Dict, List, Optional
from pydantic import BaseModel

class DatabaseCredentials(BaseModel):
    host: Optional[str] = None
    port: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    database_name: Optional[str] = None
    database_url: Optional[str] = None
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None
    client_email: Optional[str] = None
    private_key: Optional[str] = None
    project_id: Optional[str] = None
    
class QueryRequest(BaseModel):
    query: str
    credentials: Optional[DatabaseCredentials] = None

class QueryResponse(BaseModel):
    response: str