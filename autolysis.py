# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests",
#   "openai",
#   "pandas",
#   "seaborn",
#   "matplotlib",
# ]
# ///

import os
import sys
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import requests
import json

# Define the AI Proxy URL and Token
API_URL = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
# AIPROXY_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjIxZjIwMDA3NTNAZHMuc3R1ZHkuaWl0bS5hYy5pbiJ9.ElOtWhp7TzvKysUJpm76R5M7DD3z0PvuifmrpORDa50"  # Replace with the actual token
AIPROXY_TOKEN = os.getenv('AIPROXY_TOKEN')  # Use environment variable to store the token

if not AIPROXY_TOKEN:
    print("Error: AIPROXY_TOKEN environment variable not set.")
    sys.exit(1)
# Set the headers with the proxy token
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {AIPROXY_TOKEN}"
}

def load_data(filename):
    """Load the dataset from a CSV file."""
    try:
        data = pd.read_csv(filename, encoding='latin1')  # Use 'latin1' for non-UTF-8 encoding
        print(f"Dataset '{filename}' loaded successfully.")
        return data
    except Exception as e:
        print(f"Error loading dataset: {e}")
        sys.exit(1)

def analyze_data(data):
    """Perform a general analysis of the dataset."""
    analysis = {}
    try:
        analysis["shape"] = data.shape
        analysis["columns"] = data.dtypes.to_dict()
        analysis["missing_values"] = data.isnull().sum().to_dict()
        analysis["summary_stats"] = data.describe(include="all").to_dict()
    except Exception as e:
        print(f"Error analyzing data: {e}")
    return analysis

def visualize_data(data, output_dir):
    """Create visualizations for the dataset."""
    os.makedirs(output_dir, exist_ok=True)
    chart_paths = []
    try:
        for column in data.select_dtypes(include=["number"]).columns:
            plt.figure(figsize=(8, 6))
            sns.histplot(data[column], kde=True, color="blue")
            plt.title(f"Distribution of {column}")
            plt.xlabel(column)
            plt.ylabel("Frequency")
            chart_path = os.path.join(output_dir, f"{column}_distribution.png")
            plt.savefig(chart_path)
            plt.close()
            chart_paths.append(chart_path)
    except Exception as e:
        print(f"Error creating visualizations: {e}")
    return chart_paths

def generate_story(analysis, chart_paths):
    """Generate a story summarizing the analysis using the LLM via AI Proxy."""
    try:
        prompt = (
            f"I have a dataset with the following structure:\n"
            f"Shape: {analysis['shape']}\n"
            f"Columns: {analysis['columns']}\n"
            f"Missing Values: {analysis['missing_values']}\n"
            f"Summary Statistics: {analysis['summary_stats']}\n\n"
            f"Using the above analysis and the following visualizations:\n"
            f"{', '.join(chart_paths)}\n"
            f"Generate a story summarizing the dataset, highlighting key insights, "
            f"and explaining their implications."
        )
        
        # Send the prompt to AI Proxy for generation
        data = {
            "model": "gpt-4o-mini",  # Model supported by AI Proxy
            "messages": [{"role": "user", "content": prompt}],
        }

        # Make the POST request to the AI Proxy
        response = requests.post(API_URL, headers=headers, data=json.dumps(data))

        if response.status_code == 200:
            response_data = response.json()
            return response_data['choices'][0]['message']['content'].strip()
        else:
            print(f"API call failed: {response.status_code} - {response.text}")
            sys.exit(1)
    
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

def save_readme(story, chart_paths, output_dir):
    """Save the story and visualizations to a README.md file."""
    try:
        readme_path = os.path.join(output_dir, "README.md")
        with open(readme_path, "w") as f:
            f.write("# Analysis Report\n\n")
            f.write(story + "\n\n")
            for chart_path in chart_paths:
                relative_path = os.path.relpath(chart_path, output_dir)
                f.write(f"![Chart]({relative_path})\n\n")
        print(f"README.md generated at {readme_path}")
    except Exception as e:
        print(f"Error saving README.md: {e}")

def main():
    """Main function to orchestrate the script."""
    if len(sys.argv) != 2:
        print("Usage: python autolysis.py <dataset.csv>")
        sys.exit(1)

    filename = sys.argv[1]
    output_dir = os.path.splitext(os.path.basename(filename))[0]

    # Load data
    data = load_data(filename)

    # Analyze data
    analysis = analyze_data(data)

    # Visualize data
    chart_paths = visualize_data(data, output_dir)

    # Generate story with LLM via AI Proxy
    story = generate_story(analysis, chart_paths)

    # Save README
    save_readme(story, chart_paths, output_dir)

if __name__ == "__main__":
    main()
