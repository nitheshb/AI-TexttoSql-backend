from typing import Dict, List, Any
import openai
from sqlalchemy import text, create_engine
import config
from schema import PostgreSQLCredentials
from fastapi import HTTPException

openai.api_key = config.OPENAI_API_KEY

def generate_postgresql_query(query: str) -> str:
    """
    Generate PostgreSQL query from a natural language query using OpenAI's chat models.
    """
    prompt = """
You are a helpful assistant that generates optimized PostgreSQL queries based on natural language queries.
Below are the table schemas and relationships that should be used to generate the PostgreSQL queries:

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
- Translate the user's natural language query into **only a valid PostgreSQL query** that can be directly executed in PostgreSQL.
- Do not include explanatory text, only return the PostgreSQL query.

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
        raise HTTPException(status_code=500, detail=f"Error generating PostgreSQL query: {str(e)}")

def execute_postgresql_query(sql_query: str, credentials: PostgreSQLCredentials) -> List[Dict[str, Any]]:
    """
    Execute the generated postgreSQL query and return the results.
    Requires credentials from frontend.
    """
    if not credentials:
        raise HTTPException(status_code=400, detail="Credentials are required")
        
    if not credentials.database_url:
        raise HTTPException(status_code=400, detail="Database URL is required in credentials")
    
    connection = None
    try:
        engine = create_engine(credentials.database_url)
        with engine.connect() as connection:
            result = connection.execute(text(sql_query))        
            columns = result.keys()
            rows = result.fetchall()
            return [dict(zip(columns, row)) for row in rows] if rows else []
    except Exception as e:
        print(f"PostgreSQL error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error executing PostgreSQL query: {str(e)}")
    finally:
        if connection is not None:
            connection.close()
