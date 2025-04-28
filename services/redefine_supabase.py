import os
from fastapi import HTTPException
from typing import Dict, List, Any
import openai
from supabase import create_client, Client
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import config

openai.api_key = config.OPENAI_API_KEY

url = config.SUPABASE_URL
key = config.SUPABASE_KEY

supabase: Client = create_client(url, key)

DATABASE_URL = config.DATABASE_URL

engine = create_engine(DATABASE_URL)
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = Session()

def create_execute_sql_function():
    """
    Uses SQLAlchemy to create the execute_sql function directly in Supabase.
    """
    create_function_query = """
    CREATE OR REPLACE FUNCTION public.execute_sql(query text)
    RETURNS JSONB
    LANGUAGE plpgsql
    SECURITY DEFINER
    SET search_path = public
    AS $$
    DECLARE
        result JSONB;
    BEGIN
        EXECUTE format('SELECT json_agg(t) FROM (%s) t', query) INTO result;
        RETURN COALESCE(result, '[]'::jsonb);
    EXCEPTION WHEN OTHERS THEN
        RETURN jsonb_build_object(
            'error', SQLERRM,
            'detail', SQLSTATE
        );
    END;
    $$;

    GRANT EXECUTE ON FUNCTION public.execute_sql(text) TO authenticated;
    GRANT EXECUTE ON FUNCTION public.execute_sql(text) TO anon;
    """

    try:
        session.execute(text(create_function_query))
        session.commit()
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating function: {str(e)}")
    finally:
        session.close()

def generate_redefine_supabase_query(query: str) -> str:
    """
    Generate PostgreSQL query from a natural language query using OpenAI's chat models.
    """
    prompt = """
You are a helpful assistant that generates optimized SQL queries based on natural language queries.
Below are the table schemas and relationships that should be used to generate the SQL queries:

1. **spark_lead_logs Table**:
   - **T** (TIMESTAMP): Timestamp of the log entry (in milliseconds).
   - **by** (STRING): Email address of the person who made the log entry.
   - **to** (STRING): Email address of the recipient (if applicable).
   - **uid** (UUID): Unique identifier for the log entry (UUID type).
   - **Luid** (UUID): Unique identifier for the log (UUID type).
   - **from** (STRING): Email address of the sender (if applicable).
   - **type** (STRING): Type of the log entry (e.g., "sts_change").
   - **payload** (OBJECT): Object containing additional information about the log entry:
     - **msg** (STRING): Message associated with the log entry (e.g., "lead update to new status").
   - **subtype** (STRING): Subtype of the log entry (e.g., "newStatus").
   - **projectId** (UUID): Unique identifier for the project associated with the log (if applicable).

2. **spark_unit_logs Table**:
   - **T** (TIMESTAMP): Timestamp of the log entry (in milliseconds).
   - **by** (STRING): Email address of the person who made the log entry.
   - **to** (STRING): Recipient of the log entry (e.g., "review").
   - **uid** (UUID): Unique identifier for the log entry (UUID type).
   - **Uuid** (UUID): Unique identifier for the log (UUID type).
   - **from** (STRING): Sender of the log entry (e.g., "review").
   - **type** (STRING): Type of the log entry (e.g., "accounts").
   - **payload** (OBJECT): Object containing additional information about the log entry:
     - **mode** (STRING): Mode of the transaction (e.g., "cheque").
     - **amount** (DECIMAL): Amount involved in the transaction.
     - **receivedBy** (STRING): Email address of the person who received the payment.
     - **bank_ref_no** (STRING): Bank reference number associated with the transaction.
   - **subtype** (STRING): Subtype of the log entry (e.g., "pay_capture").
   - **projectId** (UUID): Unique identifier for the project associated with the log (if applicable).

3. **spark_account_logs Table**:
   - **T** (TIMESTAMP): Timestamp of the log entry (in milliseconds).
   - **by** (STRING): Email address of the person who made the log entry.
   - **to** (STRING): Recipient of the log entry (if applicable).
   - **uid** (UUID): Unique identifier for the log entry (UUID type).
   - **from** (STRING): Sender of the log entry (if applicable).
   - **type** (STRING): Type of the log entry (e.g., "l_ctd").
   - **amount** (DECIMAL): Amount involved in the transaction.
   - **unitId** (STRING): Unique identifier for the unit associated with the log.
   - **payload** (OBJECT): Empty object for additional data (if applicable).
   - **subtype** (STRING): Subtype of the log entry (if applicable).
   - **description** (TEXT): Description of the log entry (if applicable).
   - **TransactionUid** (STRING): Unique identifier for the transaction.

### Rules:
- **For queries related to log entries with email addresses, status changes, or timestamps** (e.g., "Show logs where the status changed to new status", "Get the logs for a specific project"), refer to the **spark_lead_logs** table:
   - Use the **by** and **from** columns for filtering based on email addresses.
   - Use the **msg** column to get log messages related to status updates.
   - Use **T** for filtering logs based on time (timestamp in milliseconds).
   - Use **projectId** to filter logs for specific projects.

- **For queries related to transaction logs, bank references, and payment details** (e.g., "What payment mode was used for the transaction?", "Show all transactions for cheque payments"), refer to the **spark_unit_logs** table:
   - Use the **mode** column to filter logs based on transaction modes (e.g., "cheque", "cash").
   - Use the **amount** column to get the transaction amount.
   - Use the **receivedBy** column to get information about the person who received the payment.
   - Use the **bank_ref_no** column to filter by bank reference number.
   - Use **subtype** to specify the type of transaction (e.g., "pay_capture").
   - Use **T** for filtering based on the timestamp.

- **For queries related to account transactions, unit details, and descriptions of financial actions** (e.g., "Get all transactions for a specific unit", "Show logs for unit id 'abc123'"), refer to the **spark_account_logs** table:
   - Use **amount** to filter transactions based on the amount.
   - Use **unitId** to filter logs by unit.
   - Use **description** to find descriptions of the log (if provided).
   - Use **TransactionUid** to filter logs by transaction identifier.
   - Use **T** for filtering based on timestamp.

- **Translate the user's natural language query into only a valid SQL query** that can be directly executed in PostgreSQL.
- Do not include explanatory text, only return the SQL query.

Please generate a PostgreSQL query based on the user's request, utilizing the relevant table and field names.
Return ONLY PostgreSQL query, no additional explanations, comments, or paragraphs. No text other than the PostgreSQL query.
"""
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": query}
        ],
        temperature=0.1,
        max_tokens=800
    )
    
    query_sql = response['choices'][0]['message']['content'].strip()
    print("query_sql:", query_sql)
    return query_sql

def execute_redefine_supabase_query(sql_query: str) -> List[Dict[str, Any]]:
    """
    Execute the generated SQL query and return the results as a list of dictionaries.
    """
    try:
        if sql_query.endswith(";"):
            sql_query = sql_query[:-1]

        response = supabase.rpc('execute_sql', {"query": sql_query}).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing query: {str(e)}")
    
create_execute_sql_function()
