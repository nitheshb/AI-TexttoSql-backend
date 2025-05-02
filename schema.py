from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel

class MySQLCredentials(BaseModel):
    host: str
    port: str
    username: str
    password: str
    database_name: str

class PostgreSQLCredentials(BaseModel):
    database_url: str

class NeonDBCredentials(BaseModel):
    database_url: str

class SupabaseCredentials(BaseModel):
    supabase_url: str
    supabase_key: str
    database_url: str

class FirestoreCredentials(BaseModel):
    client_email: str
    private_key: str
    project_id: str

class MySQLQueryRequest(BaseModel):
    query: str
    credentials: MySQLCredentials

class PostgreSQLQueryRequest(BaseModel):
    query: str
    credentials: PostgreSQLCredentials

class NeonDBQueryRequest(BaseModel):
    query: str
    credentials: NeonDBCredentials

class SupabaseQueryRequest(BaseModel):
    query: str
    credentials: SupabaseCredentials

class FirestoreQueryRequest(BaseModel):
    query: str
    credentials: FirestoreCredentials

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    response: Any