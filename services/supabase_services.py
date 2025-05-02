from fastapi import HTTPException
from typing import Dict, List, Any
import openai
from supabase import create_client
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import config
from schema import SupabaseCredentials

openai.api_key = config.OPENAI_API_KEY

def create_execute_sql_function(credentials: SupabaseCredentials):
    """
    Uses SQLAlchemy to create the execute_sql function directly in Supabase.
    Requires credentials parameter to create the function in the client's database.
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

    session = None
    try:
        if not credentials or not credentials.database_url:
            raise ValueError("Database URL is required in credentials")
            
        engine = create_engine(credentials.database_url)
        Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = Session()
        
        session.execute(text(create_function_query))
        session.commit()
        session.close()
    except Exception as e:
        if session:
            session.rollback()
            session.close()
        if isinstance(e, HTTPException):
            raise
        else:
            raise HTTPException(status_code=500, detail=f"Error creating function: {str(e)}")

def generate_supabase_query(query: str) -> str:
    """
    Generate PostgreSQL query from a natural language query using OpenAI's chat models.
    """
    prompt = """
You are a helpful assistant that generates optimized SQL queries based on natural language queries.
Below are the table schemas and relationships that should be used to generate the SQL queries:

1. **Products Table**: 
    - **id** (UUID): Unique product identifier (UUID type).
    - **name** (STRING): Name of the product.
    - **price** (DECIMAL): Price of the product.
    - **description** (TEXT): Description of the product.
    - **stock_quantity** (INTEGER): Quantity of the product in stock.
    - **weight** (DECIMAL): Weight of the product.
    - **manufacturer** (STRING): Manufacturer of the product.
    - **created_at** (TIMESTAMP): Date and time when the product was added.

2. **Customers Table**:
    - **id** (UUID): Unique customer identifier (UUID type).
    - **name** (STRING): Name of the customer.
    - **email** (STRING): Unique email address of the customer.
    - **address** (TEXT): Address of the customer.
    - **phone** (STRING): Phone number of the customer.
    - **date_of_birth** (DATE): Birth date of the customer.
    - **loyalty_points** (INTEGER): Loyalty points accumulated by the customer.

3. **Orders Table**:
    - **id** (UUID): Unique order identifier (UUID type).
    - **customer_id** (UUID): Foreign key referencing `customers(id)`.
    - **product_id** (UUID): Foreign key referencing `products(id)`.
    - **quantity** (INTEGER): Quantity of the product ordered.
    - **total_price** (DECIMAL): Total price of the order.
    - **order_date** (TIMESTAMP): Date and time when the order was placed.
    - **shipping_address** (TEXT): Shipping address for the order.
    - **order_status** (STRING): Status of the order (e.g., 'Pending', 'Shipped', 'Delivered').

4. **Shipping Addresses Table**:
    - **id** (UUID): Unique shipping address identifier (UUID type).
    - **customer_id** (UUID): Foreign key referencing `customers(id)`.
    - **address** (TEXT): Shipping address.
    - **city** (STRING): City of the shipping address.
    - **state** (STRING): State of the shipping address.
    - **zip_code** (STRING): Zip code of the shipping address.
    - **country** (STRING): Country of the shipping address.

5. **Payment Methods Table**:
    - **id** (UUID): Unique payment method identifier (UUID type).
    - **customer_id** (UUID): Foreign key referencing `customers(id)`.
    - **card_type** (STRING): Type of the card (e.g., 'Visa', 'MasterCard').
    - **card_number** (STRING): Card number.

### Rules:
- If the query involves `product`, `name`, `price`, or related details, refer to the **products** table.
- If the query involves `customer`, `address`, `loyalty points`, or related details, refer to the **customers** table.
- If the query involves `order`, `quantity`, `total price`, or related details, refer to the **orders** table.
- If the query involves `shipping address`, `zip code`, or `city`, refer to the **shipping_addresses** table.
- If the query involves `payment`, `card type`, `card number`, or `payment details`, refer to the **payment_methods** table.
- Translate the user's natural language query into **only a valid SQL query** that can be directly executed in PostgreSQL.
- Do not include explanatory text, only return the SQL query.

Please generate a PostgreSQL query based on the user's request, utilizing the relevant table and field names.
Return ONLY PostgreSQL query, no additional explanations, comments, or paragraphs. No text other than the PostgreSQL query.
"""
    try:
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
        return query_sql
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating Supabase query: {str(e)}")

def execute_supabase_query(sql_query: str, credentials: SupabaseCredentials) -> List[Dict[str, Any]]:
    """
    Execute the generated SQL query and return the results as a list of dictionaries.
    Requires credentials from frontend.
    """
    try:
        if sql_query.endswith(";"):
            sql_query = sql_query[:-1]

        if not credentials:
            raise HTTPException(status_code=400, detail="Credentials are required")

        if not credentials.supabase_url or not credentials.supabase_key:
            raise HTTPException(status_code=400, detail="Missing Supabase URL or API key in credentials")
            
        if not credentials.database_url:
            raise HTTPException(status_code=400, detail="Database URL is required in credentials")
            
        client = create_client(credentials.supabase_url, credentials.supabase_key)
        
        try:
            create_execute_sql_function(credentials)
        except Exception as e:
            print(f"Warning: Could not create execute_sql function: {str(e)}")
        
        response = client.rpc('execute_sql', {"query": sql_query}).execute()
        
        if isinstance(response.data, dict) and 'error' in response.data:
            print(f"Supabase SQL error: {response.data['error']}")
            raise HTTPException(status_code=400, detail=f"SQL Error: {response.data['error']}")
            
        return response.data
        
    except Exception as e:
        print(f"Supabase error: {str(e)}")
        
        if isinstance(e, HTTPException):
            raise
        else:
            raise HTTPException(status_code=500, detail=f"Error executing Supabase query: {str(e)}")
