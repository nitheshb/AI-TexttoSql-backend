import openai
import json
import config

openai.api_key = config.OPENAI_API_KEY

def transform_to_system_response(original_query: str, query_text: str, results: list, query_type: str = "SQL"):
    """
    Transforms database query results into a human-readable response using OpenAI's chat models.
    
    Args:
        original_query: The original natural language query from the user
        query_text: The generated query that was executed (SQL, Firestore code, etc.)
        results: The query results (list of dictionaries)
        query_type: Type of query ("SQL" or "Firestore")
        
    Returns:
        String with a human-readable explanation of the results
    """
    results_json = json.dumps(results, default=str)
    
    if query_type.upper() == "FIRESTORE":
        query_description = "Firestore query code"
    else:
        query_description = "SQL query"
    
    prompt = f"""
You are an assistant that explains database query results in a natural, conversational way.

Original question: {original_query}

{query_description} that was executed:
{query_text}

Query results:
{results_json}

Please provide a clear, concise explanation of these results in natural language.
Respond as if you're directly answering the original question.
Focus on the key information and insights from the data.
If there are no results, explain that no data was found that matches the query.
DO NOT mention the query code or SQL in your response.
DO NOT include any technical terms like "database", "query", or "results" in your explanation.

FORMATTING INSTRUCTIONS:
1. If the results contain a list of items or multiple records, use bullet points or numbered lists when appropriate.
2. For bullet points, use the format:
   • Item 1
   • Item 2
   • Item 3
3. For numbered lists, use the format:
   1. First item
   2. Second item
   3. Third item
4. Ensure each bullet point or numbered item is on a new line.
5. Use proper line breaks to make the response readable.
"""

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You convert database results into natural human language responses with proper formatting."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=800
    )

    return response['choices'][0]['message']['content'].strip() 