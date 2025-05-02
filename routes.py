from fastapi import APIRouter, HTTPException
from schema import QueryRequest, QueryResponse
from services.firestore_services import execute_firebase_query, generate_firebase_query
from services.mysql_services import execute_mysql_query, generate_mysql_query
from services.postgresql_services import execute_postgresql_query, generate_postgresql_query
from services.redefine_firestore import execute_redefine_firebase_query, generate_redefine_firebase_query
from services.redefine_supabase import execute_redefine_supabase_query, generate_redefine_supabase_query
from services.supabase_services import execute_supabase_query, generate_supabase_query
from services.neondb_services import execute_neon_query, generate_neon_query
from services.utilities import transform_to_system_response

router = APIRouter()

@router.post("/mysql_query", response_model=QueryResponse)
async def mysql_query(request: QueryRequest):
    """
    Process a natural language query, convert it to SQL query,
    execute it, and return the results in human-readable format.
    """
    if not request.credentials:
        raise HTTPException(status_code=400, detail="Credentials are required")
            
    try:
        generated_query = generate_mysql_query(request.query)
        results = execute_mysql_query(generated_query, request.credentials)
        system_response = transform_to_system_response(request.query, generated_query, results)
                
        return {
            "response": system_response
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/postgresql_query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process a natural language query, convert it to Postgresql query,
    execute it, and return the results in human-readable format.
    """
    if not request.credentials:
        raise HTTPException(status_code=400, detail="Credentials are required")
            
    try:
        generated_query = generate_postgresql_query(request.query)
        results = execute_postgresql_query(generated_query, request.credentials)
        system_response = transform_to_system_response(request.query, generated_query, results)
                
        return {
            "response": system_response
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/neon_query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process a natural language query, convert it to Postgresql query,
    execute it, and return the results in human-readable format.
    """
    if not request.credentials:
        raise HTTPException(status_code=400, detail="Credentials are required")
            
    try:
        generated_query = generate_neon_query(request.query)
        results = execute_neon_query(generated_query, request.credentials)
        system_response = transform_to_system_response(request.query, generated_query, results)
                
        return {
            "response": system_response
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
 
@router.post("/supabase_query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process a natural language query, convert it to Postgresql query,
    execute it, and return the results in human-readable format.
    """
    if not request.credentials:
        raise HTTPException(status_code=400, detail="Credentials are required")
            
    try:
        generated_query = generate_supabase_query(request.query)
        results = execute_supabase_query(generated_query, request.credentials)
        system_response = transform_to_system_response(request.query, generated_query, results)
                
        return {
            "response": system_response
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/firestore_query", response_model=QueryResponse)
async def firestore_query(request: QueryRequest):
    """
    Process a natural language query, convert it to Firestore query code,
    execute it, and return the results in human-readable format.
    """
    if not request.credentials:
        raise HTTPException(status_code=400, detail="Credentials are required")
            
    try:
        generated_query = generate_firebase_query(request.query)
        results = execute_firebase_query(generated_query, request.credentials)
        system_response = transform_to_system_response(request.query, generated_query, results, query_type="FIRESTORE")
                
        return {
            "response": system_response
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/redefine_firestore", response_model=QueryResponse)
async def firestore_query(request: QueryRequest):
    """
    Process a natural language query, convert it to Firestore query code,
    execute it, and return the results in human-readable format.
    """
    
    try:
        generated_query = generate_redefine_firebase_query(request.query)
        results = execute_redefine_firebase_query(generated_query)
        # human_readable = transform_to_system_response(request.query, generated_query, results, query_type="FIRESTORE")
                
        return {
            "response": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/redefine_supabase", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process a natural language query, convert it to Postgresql query,
    execute it, and return the results in human-readable format.
    """
    try:
        generated_query = generate_redefine_supabase_query(request.query)
        results = execute_redefine_supabase_query(generated_query)
        human_readable = transform_to_system_response(request.query, generated_query, results)
                
        return {
            "response": human_readable
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
