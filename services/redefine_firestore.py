from fastapi import HTTPException
from typing import Dict, List, Any
import openai
from google.cloud import firestore
import json
from config import get_firestore_client
import config


openai.api_key = config.OPENAI_API_KEY

db = get_firestore_client() 

COLLECTION_SCHEMA = {
    "users": ["id", "empId", "uid", "offPh", "projAccessA", "userStatus", "orgName", "roles", "department", 
        "perPh", "email", "orgStatus", "orgId", "name"],
    "spark_units": ["id", "Katha_no", "blockId", "PID_no", "facing", "sqft_rate", "north_d", "north_sch_by", 
        "west_sch_by", "south_d", "intype", "pId", "area", "east_d", "phaseId", "north_south_d", 
        "south_sch_by", "size", "mode", "status", "east_sch_by", "survey_no", "west_d", "unit_type", 
        "release_status", "unit_no", "by", "mortgage_type", "east_west_d", "area_sqm", "unit_d", 
        "Date", "plc_per_sqft"], 
    "spark_projects": ["id", "bmrdaEndDate", "uid", "areaDropDownPrimary", "hdmaEndDate", "soldArea", "status", 
        "hdmaStartDate", "editMode", "area", "city", "areaDropdownSecondary", "t_bal", "projectName", 
        "areaTextPrimary", "created", "builderGSTno", "bookUnitCount", "s_agreeCount", "builder_bank_details", 
        "landlord_bank_details", "blockedUnitCount", "builderShare", "t_collect", "updated", "address", 
        "state", "s_regisCount", "landlordShare", "bmrdaNo", "mangBlockCount", "builderBankDocId", "hdmaNo", 
        "custBlockValue", "custBlockCount", "bmrdaStartDate", "blockedArea", "mangBlockValue", "bankAccounts", 
        "soldValue", "areaTextSecondary", "blockedValue", "location", "landlordName", "bmrdaApproval", 
        "builderName", "landlordBankDocId", "hdmaApproval", "totalUnitCount", "PlanningApprovalAuthority", 
        "pincode", "mangBlockArea", "projectType", "atsCount", "soldUnitCount", "developmentType", 
        "custBlockArea", "availableCount"],
    "spark_leads": ["id", "assignedTo", "ProjectId", "schTime", "assignedToObj", "Note", "by", "Status", 
        "Project", "leadUpT", "Source", "intype", "Name", "Email", "Mobile", "coveredA", "stsUpT", 
        "Date"]    
}

def generate_redefine_firebase_query(query_text: str) -> str:
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

***Return ONLY executable Python code. Do not include any additional explanations, comments, or paragraphs. No text other than the python firetsore query code.***

Example of what the response should look like: (for reference only):
results = []
order_docs = db.collection('orders').where('total_price', '<', 100).stream()
for order in order_docs:
    product_doc = db.collection('products').document(order.to_dict()['product_id']).get()
    if product_doc.exists:
        data = product_doc.to_dict()
        data['id'] = product_doc.id
        results.append(data)
return results

"""

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a code generator that outputs only pure Python code for Firestore queries, returning only the final referenced collection's data."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
        max_tokens=800
    )
    
    code = response['choices'][0]['message']['content'].strip()
    print("code:", code)

    return code

def execute_redefine_firebase_query(query_code: str) -> List[Dict[str, Any]]:
    """
    Execute the generated query code and return the results.
    """
    local_vars = {"db": db, "firestore": firestore}
    
    try:
        formatted_code = "\n".join("    " + line for line in query_code.split("\n"))
        exec_code = f"def execute_query():\n{formatted_code}"
        
        exec(exec_code, globals(), local_vars)
        results = local_vars["execute_query"]()
        
        if isinstance(results, list):
            processed_results = []
            for item in results:
                if hasattr(item, "to_dict"):
                    item_dict = item.to_dict()
                    item_dict["id"] = item.id
                    processed_results.append(item_dict)
                else:
                    processed_results.append(item)
            return processed_results
        elif hasattr(results, "to_dict"):
            result_dict = results.to_dict()
            result_dict["id"] = results.id
            return [result_dict]
        else:
            return results if isinstance(results, list) else [results]
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing query: {str(e)}")
