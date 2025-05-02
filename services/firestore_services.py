from fastapi import HTTPException
from typing import Dict, List, Any
import openai
from google.cloud import firestore
from google.oauth2 import service_account
import json
import config
from schema import FirestoreCredentials
import textwrap

openai.api_key = config.OPENAI_API_KEY

COLLECTION_SCHEMA = {
    "products": ["name", "price", "stock_quantity", "description", "manufacturer", "weight"],
    "customers": ["name", "email", "phone", "address", "loyalty_points", "date_of_birth"],
    "orders": ["product_id", "customer_id", "quantity", "total_price", "order_status", "shipping_address", "order_date"]
}

def get_firestore_client_from_credentials(credentials: FirestoreCredentials) -> firestore.Client:
    """
    Create a Firestore client using provided credentials.
    """
    if not credentials or not credentials.client_email or not credentials.private_key or not credentials.project_id:
        raise HTTPException(status_code=400, detail="Missing required Firestore credentials")
    
    try:
        credentials_info = {
            "type": "service_account",
            "project_id": credentials.project_id,
            "private_key_id": credentials.client_email.split("@")[0],
            "private_key": credentials.private_key.replace("\\n", "\n"),
            "client_email": credentials.client_email,
            "client_id": "",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{credentials.client_email}"
        }
        
        service_credentials = service_account.Credentials.from_service_account_info(credentials_info)
        return firestore.Client(credentials=service_credentials, project=credentials.project_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating Firestore client: {str(e)}")

def generate_firebase_query(query_text: str) -> str:
    """
    Generate Python code for Firestore query based on natural language input
    using OpenAI's chat model.
    """
    prompt = f"""You are a Python code generator for Firestore queries. Given this request: "{query_text}"

Using this schema:
{json.dumps(COLLECTION_SCHEMA, indent=2)}

Generate Python code that queries Firestore collections. If the query involves references to other collections:
1. Identify the collections referenced in the query based on the schema provided
2. First query the initial collection
3. Use the reference IDs to query the final target collection
4. Return ONLY the results from the final target collection

The code must:
1. Use the 'db' Firestore client that's already initialized
2. Return results as a list of dictionaries from the final collection only
3. Include document IDs in the results using doc.id
4. Use proper Firestore methods (.where(), .order_by(), .limit(), etc.)
5. CONTAIN NO COMMENTS, DOCSTRINGS, EXPLANATIONS OR ANY TEXT THAT IS NOT EXECUTABLE CODE
6. Be optimized and clean without any print statements or debugging code

Example format (for reference only):
results = []
order_docs = db.collection('orders').where('total_price', '<', 100).stream()
for order in order_docs:
    product_doc = db.collection('products').document(order.to_dict()['product_id']).get()
    if product_doc.exists:
        data = product_doc.to_dict()
        data['id'] = product_doc.id
        results.append(data)
return results

Return ONLY executable Python code, no additional explanations, comments, or paragraphs. No text other than the code.
"""
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a code generator that outputs only pure Python code for Firestore queries with no comments, quotation marks, docstrings or explanations."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
        max_tokens=800
    )
    
    code = response['choices'][0]['message']['content'].strip()
    
    if code.startswith("```python"):
        code = code[len("```python"):].strip()
    if code.startswith("```"):
        code = code[3:].strip()
    if code.endswith("```"):
        code = code[:-3].strip()
        
    print("code:", code)
    return code

def execute_firebase_query(query_code: str, credentials: FirestoreCredentials) -> List[Dict[str, Any]]:
    """
    Execute the generated query code and return the results.
    """
    if not credentials:
        raise HTTPException(status_code=400, detail="Credentials are required")
        
    if not credentials.client_email or not credentials.private_key or not credentials.project_id:
        raise HTTPException(status_code=400, detail="Valid Firestore credentials are required")

    try:
        client = get_firestore_client_from_credentials(credentials)
        
        if len(query_code.strip()) < 10 or "collections()" in query_code:
            results = []
            collections = client.collections()
            for collection in collections:
                docs = collection.stream()
                for doc in docs:
                    data = doc.to_dict()
                    data['id'] = doc.id
                    data['collection'] = collection.id
                    results.append(data)
            return results
        
        if "results = []" not in query_code:
            query_code = "results = []\n" + query_code
        if "return results" not in query_code:
            query_code += "\nreturn results"
            
        global_vars = {'firestore': firestore, 'db': client}
        
        function_code = f"""
def execute_query():
{textwrap.indent(query_code, '    ')}
"""
        print("Executing code:", function_code)
        
        try:
            exec(function_code, global_vars)
            results = global_vars['execute_query']()
            
            if results is None:
                return []
            if not isinstance(results, list):
                results = [results]
                
            processed_results = []
            for item in results:
                if hasattr(item, "to_dict"):
                    item_dict = item.to_dict()
                    item_dict["id"] = item.id
                    processed_results.append(item_dict)
                elif isinstance(item, dict):
                    processed_results.append(item)
                else:
                    processed_results.append({"value": str(item)})
                    
            return processed_results
                
        except Exception as e:
            import traceback
            error_detail = f"Error in query execution: {str(e)}\n{traceback.format_exc()}"
            print(error_detail)
            
            collections = client.collections()
            results = []
            for collection in collections:
                docs = collection.stream()
                for doc in docs:
                    data = doc.to_dict()
                    data['id'] = doc.id
                    data['collection'] = collection.id
                    results.append(data)
            return results
            
    except Exception as e:
        import traceback
        error_detail = f"Error executing query: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        raise HTTPException(status_code=500, detail=f"Error executing query: {str(e)}")
