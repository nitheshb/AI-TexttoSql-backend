from fastapi import HTTPException
from typing import Dict, List, Any
import openai
from google.cloud import firestore
import json
from config import get_firestore_client
import config
from datetime import datetime

openai.api_key = config.OPENAI_API_KEY

db = get_firestore_client() 

COLLECTION_SCHEMA = {
    "users": ["id", "empId", "uid", "offPh", "projAccessA", "userStatus", "orgName", "roles", "department", 
        "perPh", "email", "orgStatus", "orgId", "name"],
    "spark_units": ["id", "Katha_no", "blockId", "PID_no", "facing", "sqft_rate", "north_d", "north_sch_by", 
        "west_sch_by", "south_d", "intype", "pId", "area", "east_d", "phaseId", "north_south_d", 
        "south_sch_by", "size", "mode", "status", "east_sch_by", "survey_no", "west_d", "unit_type", 
        "release_status", "unit_no", "by", "mortgage_type", "east_west_d", "area_sqm", "unit_d", 
        "Date", "plc_per_sqft","T_balance","T_total","T_elgible","T_elgible_balance","booked_on"], 
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

1. **spark_units Collection**:  
    - **Katha_no** (STRING): The Katha number, typically a legal property identification number (can be blank).  
    - **blockId** (INTEGER): Identifier for the block in which the unit is located.  
    - **PID_no** (STRING): Property Identification Number, used for official property records (can be blank).  
    - **facing** (STRING): Direction the plot/unit is facing (e.g., SOUTH-WEST).  
    - **sqft_rate** (STRING): Rate per square foot for the unit, typically in currency (e.g., 3750).  
    - **north_d** (STRING): Distance (in meters or feet) of the northern boundary.  
    - **north_sch_by** (STRING): Description of the boundary on the northern side (e.g., adjacent plot number).  
    - **west_sch_by** (STRING): Description of the boundary on the western side.  
    - **south_d** (STRING): Distance of the southern boundary.  
    - **intype** (STRING): Input type or categorization of the unit, such as 'bulk'.  
    - **pId** (STRING): Unique identifier for the project or parent entity the unit belongs to (UUID format).  
    - **area** (STRING): Total area of the unit in square feet (may contain comma formatting).  
    - **east_d** (STRING): Distance of the eastern boundary.  
    - **phaseId** (INTEGER): Identifier for the phase within the block/project.  
    - **north_south_d** (INTEGER): Combined distance or differential measurement from north to south (0 if not applicable).  
    - **south_sch_by** (STRING): Description of the boundary on the southern side.  
    - **size** (STRING): Description of the size or layout type (e.g., 'UNIQUE').  
    - **mode** (STRING): Mode of entry or validation status (e.g., 'valid').  
    - **status** (STRING): Current availability status of the unit (e.g., 'available').  
    - **east_sch_by** (STRING): Description of the boundary on the eastern side.  
    - **survey_no** (STRING): Survey number associated with the property (can be blank).  
    - **west_d** (STRING): Distance of the western boundary.  
    - **unit_type** (STRING): Type of unit, such as 'plot'.  
    - **release_status** (STRING): Indicates whether the unit is released for sale (e.g., 'Un Released').  
    - **unit_no** (STRING): Unit number within the block/phase (e.g., '46').  
    - **by** (STRING): Email ID of the person who added or last modified the unit. It cannot be used as doc id. Containing relationship with user collection email field  
    - **mortgage_type** (STRING): Type of mortgage, if applicable (e.g., 'NA' for not applicable).  
    - **east_west_d** (INTEGER): Combined distance or differential measurement from east to west (0 if not applicable).  
    - **area_sqm** (STRING): Area of the unit in square meters.  
    - **unit_d** (STRING): Total calculated unit distance (likely perimeter or another derived metric).  
    - **Date** (TIMESTAMP): Timestamp (epoch milliseconds) indicating creation or update time.  
    - **plc_per_sqft** (STRING): Preferential Location Charges per square foot, if applicable.  
    - **id** (STRING): Unique document ID in the database (custom or auto-generated).  

2. **users Collection**:  
    - **empId** (STRING): Employee identifier or username assigned to the user (e.g., 'revati').  
    - **uid** (STRING): Unique user ID used for authentication (e.g., Firebase UID).  
    - **offPh** (STRING): Official phone number of the user.  
    - **projAccessA** (ARRAY of STRING): List of project IDs the user has access to.  
    - **userStatus** (STRING): Current status of the user (e.g., 'active', 'inactive').  
    - **orgName** (STRING): Name of the organization the user belongs to.  
    - **roles** (ARRAY of STRING): Roles assigned to the user (e.g., 'sales-manager').  
    - **department** (ARRAY of STRING): Departments the user is associated with (e.g., 'sales').  
    - **perPh** (STRING): Personal phone number of the user.  
    - **email** (STRING): Email address of the user.  
    - **orgStatus** (STRING): Status of the organization the user belongs to (e.g., 'active').  
    - **orgId** (STRING): Unique identifier for the organization (e.g., 'testEnv').  
    - **name** (STRING): Display name or employee code (e.g., '101').  
    - **id** (STRING): Document ID in the database, usually same as `uid`.  

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


***Return ONLY executable Python code. Do not include any additional explanations, comments or paragraphs. No code other than the python firetsore query code.***

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
    if code.startswith("```python"):
        code = code[len("```python"):].strip()
    if code.startswith("```"):
        code = code[3:].strip()
    if code.endswith("```"):
        code = code[:-3].strip()
    if code.startswith("#"):
        code = code[3:].strip()

    code = "\n".join(
    line for line in code.splitlines() if not line.lstrip().startswith("#"))

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
