import google.generativeai as genai


# Configure Gemini
genai.configure(api_key="")

# Gemini 1.5 Flash model
model = genai.GenerativeModel("gemini-1.5-flash")

# Company to analyze
company_name = input("Enter the company name to benchmark: ")

# Create prompt
prompt = f"""
You are a competitive benchmarking expert.

Create a detailed benchmarking table that includes the company **{company_name}** and its top 10 global or regional competitors.

For each company, include these columns:

1. Company Symbol
2. Company Name
3. Industry Type
4. Revenue (in USD billions, latest year)
5. Market Capitalization (USD billions)
6. Net Profit (USD billions, if available)
7. Employee Count
8. Headquarters Location
9. Growth Rate (% if available)
10. Global Rank or Notable Position (if available)

Format the response as a **clean markdown table** or **CSV-style text** so it can be parsed easily in a program. Include the input company ({company_name}) in the list.
"""

# Generate response
response = model.generate_content(prompt)

# Output result
print(response.text)
