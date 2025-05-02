from typing import Dict, List, Any
import openai
from sqlalchemy import text, create_engine
import config
from schema import MySQLCredentials
from fastapi import HTTPException

openai.api_key = config.OPENAI_API_KEY

def generate_mysql_query(query: str, prompt_helper: str = None) -> str:
    """Generates SQL query from a natural language query using OpenAI's chat models."""

    prompt = """
You are a helpful assistant that generates optimized SQL queries based on natural language queries.
Below are the table schemas and relationships that should be used to generate the SQL queries:

1. **Products Table**: 
    - **id** (INTEGER): Unique product identifier.
    - **name** (STRING): Name of the product.
    - **price** (DECIMAL): Price of the product.
    - **description** (TEXT): Description of the product.
    - **stock_quantity** (INTEGER): Quantity of the product in stock.
    - **weight** (DECIMAL): Weight of the product.
    - **manufacturer** (STRING): Manufacturer of the product.
    - **created_at** (TIMESTAMP): Date and time when the product was added.

2. **Customers Table**:
    - **id** (INTEGER): Unique customer identifier.
    - **name** (STRING): Name of the customer.
    - **email** (STRING): Unique email address of the customer.
    - **address** (TEXT): Address of the customer.
    - **phone** (STRING): Phone number of the customer.
    - **date_of_birth** (DATE): Birth date of the customer.
    - **loyalty_points** (INTEGER): Loyalty points accumulated by the customer.

3. **Orders Table**:
    - **id** (INTEGER): Unique order identifier.
    - **customer_id** (INTEGER): Foreign key referencing `customers(id)`.
    - **product_id** (INTEGER): Foreign key referencing `products(id)`.
    - **quantity** (INTEGER): Quantity of the product ordered.
    - **total_price** (DECIMAL): Total price of the order.
    - **order_date** (TIMESTAMP): Date and time when the order was placed.
    - **shipping_address** (TEXT): Shipping address for the order.
    - **order_status** (STRING): Status of the order (e.g., 'Pending', 'Shipped', 'Delivered').

4. **Shipping Addresses Table**:
    - **id** (INTEGER): Unique shipping address identifier.
    - **customer_id** (INTEGER): Foreign key referencing `customers(id)`.
    - **address** (TEXT): Shipping address.
    - **city** (STRING): City of the shipping address.
    - **state** (STRING): State of the shipping address.
    - **zip_code** (STRING): Zip code of the shipping address.
    - **country** (STRING): Country of the shipping address.

5. **Payment Methods Table**:
    - **id** (INTEGER): Unique payment method identifier.
    - **customer_id** (INTEGER): Foreign key referencing `customers(id)`.
    - **card_type** (STRING): Type of the card (e.g., 'Visa', 'MasterCard').
    - **card_number** (STRING): Card number.

6. **Employees Table**:
    - **id** (INTEGER): Unique employee identifier.
    - **name** (STRING): Name of the employee.
    - **position** (STRING): Position of the employee.
    - **department** (STRING): Department the employee belongs to.
    - **hire_date** (DATE): Date when the employee was hired.
    - **manager_id** (INTEGER): Foreign key referencing `employees(id)` (self-referencing for manager).

7. **Salaries Table**:
    - **id** (INTEGER): Unique salary identifier.
    - **employee_id** (INTEGER): Foreign key referencing `employees(id)`.
    - **salary** (DECIMAL): Salary of the employee.

### Rules:
- If the query involves `product`, `name`, `price`, or related details, refer to the **products** table.
- If the query involves `customer`, `address`, `loyalty points`, or related details, refer to the **customers** table.
- If the query involves `order`, `quantity`, `total price`, or related details, refer to the **orders** table.
- If the query involves `shipping address`, `zip code`, or `city`, refer to the **shipping_addresses** table.
- If the query involves `payment`, `card type`, `card number`, or `payment details`, refer to the **payment_methods** table.
- If the query involves `employee`, `position`, `department`, or related details, refer to the **employees** table.
- If the query involves `salary` or `employee pay`, refer to the **salaries** table. **ALWAYS JOIN** the `employees` table to **salary** to include employee details such as `name`, `position`, `department`, etc.
- Always ensure to use `employee_id` for joins between **employees** and **salaries** tables.
- For salary-related queries, make sure to display the relevant employee details (e.g., `name`, `position`, `department`), by joining the **employees** table with the **salaries** table.
- Translate the user's natural language query into **only a valid SQL query** that can be directly executed.
- Do not include explanatory text, only return the SQL query.

Please generate a MySQL query based on the user's request, utilizing the relevant table and field names. 
Return ONLY MySQL query, no additional explanations, comments, or paragraphs. No text other than the  SQL query.

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

        sql_query = response['choices'][0]['message']['content'].strip()
        return sql_query
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating MySQL query: {str(e)}")

def execute_mysql_query(sql_query: str, credentials: MySQLCredentials) -> List[Dict[str, Any]]:
    """
    Execute the generated MySQL query and return the results.
    Requires credentials from frontend.
    """
    if not credentials:
        raise HTTPException(status_code=400, detail="Credentials are required")
        
    if not credentials.host or not credentials.port or not credentials.username or not credentials.password or not credentials.database_name:
        raise HTTPException(status_code=400, detail="Missing required MySQL credentials")
    
    connection = None
    try:
        connection_url = f"mysql+pymysql://{credentials.username}:{credentials.password}@{credentials.host}"
        if credentials.port:
            connection_url += f":{credentials.port}"
        connection_url += f"/{credentials.database_name}"
        
        engine = create_engine(connection_url)
        with engine.connect() as connection:
            result = connection.execute(text(sql_query))        
            columns = result.keys()
            rows = result.fetchall()
            return [dict(zip(columns, row)) for row in rows] if rows else []
    except Exception as e:
        print(f"MySQL error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error executing MySQL query: {str(e)}")
    finally:
        if connection is not None:
            connection.close()
