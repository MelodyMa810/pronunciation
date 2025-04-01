import os
import json
from google import genai

# Configure the API
client = genai.Client(api_key="")

prompt = """Assess the English pronunciation based on this ToBI label TextGrid. Give scores on accuracy, fluency, and prosody on a scale from 1 to 5, 5 being the best.

For each dimension, provide both a numeric score (integer 1-5) and a brief explanation. Then provide detailed reasoning that references specific ToBI patterns and markers from the TextGrid.

Return results in this exact JSON format:
{
  "Accuracy": {"score": 1-5, "comment": "brief explanation"},
  "Fluency": {"score": 1-5, "comment": "brief explanation"},
  "Prosody": {"score": 1-5, "comment": "brief explanation"},
  "Reasoning": "detailed analysis referencing specific ToBI markers"
}
"""

def get_file_list(rootdir, endswith="_result.TextGrid"):
    file_list = []
    for subdir, dirs, files in os.walk(rootdir):
        for file in files:
            filepath = subdir + os.sep + file
            if filepath.endswith(endswith):
                file_list.append(filepath)
    return file_list

def read_textgrid(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        textgrid_content = f.read()
    return textgrid_content

def call_gemini(textgrid_content):
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[
            prompt,
            textgrid_content,
        ],
    )
    return response

file_list = get_file_list("/Users/melodyma/Desktop/Speech/MultiPA/ToBI")
output_dir = "/Users/melodyma/Desktop/Speech/MultiPA/Gemini_ToBI"

# Create output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

output_list = get_file_list(output_dir, endswith=".json")

file_bases = {os.path.basename(f).replace("_result.TextGrid","") for f in file_list}
output_bases = {os.path.splitext(os.path.basename(f))[0] for f in output_list}

# Filter the file list to exclude files that already have a corresponding .json file
filtered_files = [
    f for f in file_list if os.path.basename(f).replace("_result.TextGrid","") not in output_bases
]

print("File list:", len(file_list))
print("Output list:", len(output_list))
print("Unprocessed files:", len(filtered_files))

for filepath in filtered_files:
    try:
        # Read the TextGrid file
        textgrid_content = read_textgrid(filepath)
        
        # Call Gemini with the TextGrid content
        response = call_gemini(textgrid_content)

        # Save response to output file as JSON
        output_path = os.path.join(
            output_dir, 
            os.path.basename(filepath).replace("_result.TextGrid", ".json")
        )
        
        # Extract the text content from the response
        response_text = response.text
        
        # Try to parse the response as JSON
        try:
            # Check if the response is already a JSON string
            json_data = json.loads(response_text)
        except json.JSONDecodeError:
            # If not, create a JSON object with the full response
            json_data = {"response": response_text}
            
        # Write to JSON file
        with open(output_path, "w", encoding="utf-8") as json_file:
            json.dump(json_data, json_file, indent=2)
            
        print(f"Processed: {filepath}")
    except Exception as e:
        print(f"Error processing {filepath}: {e}")