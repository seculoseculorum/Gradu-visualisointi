import pandas as pd
import os
import matplotlib.pyplot as plt
import mplfinance as mpf
from dotenv import load_dotenv
from openai import OpenAI
import re

def get_apikey():
    """
    Load the API key from the .env file.
    """
    load_dotenv("keys.env")
    api_key = os.getenv("api_key")
    if not api_key:
        raise ValueError("API key not found. Please check your keys.env file.")
    return api_key

import re
import matplotlib.pyplot as plt

def process_text(text):
    """
    Extract and clean the code generated from the GPT model.
    """
    # Step 1: Extract the code between ```python and ```
    code_blocks = re.findall(r"```python(.*?)```", text, re.DOTALL)
    
    if not code_blocks:
        return "No code block found."

    # Extracted code (assuming there's one primary code block)
    extracted_code = code_blocks[0]

    # Step 2: Remove data description and creation
    cleaned_code = re.sub(r"#.*\n.*data\s*=\s*\[.*?\]", "", extracted_code, flags=re.DOTALL)

    # Remove the output file line
    cleaned_code = re.sub(r"# Define the output file variable\noutput_file\s*=\s*.*", "", cleaned_code)

    return cleaned_code


def get_code(client, prompt):
    """
    Call OpenAI's GPT model to generate code based on the provided prompt.
    """
    try:
        response = client.chat.completions.create(
            model='gpt-4o',  # Use the correct model for chat completion
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.1
        )

        # Extract the generated code from the response
        code = response.choices[0].message.content.strip()
        return code
    except Exception as e:
        print(f"Error while generating code: {e}")
        return ""

def execute_chart_code(df, generated_code, output_file):
    """
    Safely execute the generated code to produce the output image.
    """
    local_vars = {"data": df, "mpf": mpf, "plt": plt, "output_file": output_file}  # Setup the required libraries and variables
    try:
        print(generated_code)
        exec(generated_code
            ,
            {},
            local_vars
        )

        return False
    except Exception as e:
        print(f"Error while executing generated code: {e}")
        return ""


def main():
    """
    Main function to read stock data from CSV files, generate code using GPT, and save visualizations.
    """
    key = get_apikey()
    client = OpenAI(api_key=key)  # Instantiate the OpenAI client with the new interface

    path = f"{os.getcwd()}/Data/"
    out_path = f"{path}Outputs/"
    
    # Create the output directory if it doesn't exist
    os.makedirs(out_path, exist_ok=True)
    
    for file in os.listdir(path):
        if file.endswith('.csv'):
            # Load the CSV file into a DataFrame
            df = pd.read_csv(f"{path}{file}")

            # Define the output filename for the visualization
            output_file = f"{out_path}{file.replace('.csv', '.png')}"

            # Check if the output file already exists
            while not os.path.exists(output_file):
                print(f"Generating code for {output_file}...")

                # Generate a descriptive prompt based on the stock data
                prompt = f"""
                Read in the following stock data provided as a dictionary:
                {df.to_dict(orient='records')}.

                Use mplfinance library to generate a candlestick chart.
                The data contains open, high, low, close, and volume columns for stock prices in a dataframe named data. The data also includes Simple momentum data. 
                Your task is to generate a Python script that will plot this data using a candlestick chart style. Ensure that the file is saved using the variable output_file that will be defined elsewhere. 
                Ensure to set up the matplotlib plot with appropriate axis labels. The title should include the stock name {file} and a prediction of 
                short-term performance. Base the prediction on the Simple momentum data. 
                """

                # Get the generated code from the GPT model
                generated_code = get_code(client, prompt)

                if generated_code:
                    # Process the generated code if necessary
                    generated_code = process_text(generated_code)
                    # Execute the generated code and create the chart
                    execute_chart_code(df, generated_code, output_file)
            else:
                print(f"File {output_file} already exists. Skipping...")



#    for file in os.listdir(path):
 #       if file.endswith('.csv'):
  #          # Load the CSV file into a DataFrame
   #         df = pd.read_csv(f"{path}{file}")
#
 #           # Define the output filename for the visualization
  #          output_file = f"{out_path}{file.replace('.csv', '.png')}"
   #         print(output_file)
    #        # Generate a descriptive prompt based on the stock data
     #       prompt = f"""
      #      Read in the following stock data provided as a dictionary:
       #     {df.to_dict(orient='records')}.
#
 #           Use matplotlib and mplfinance libraries to generate a candlestick chart.
  #          The data contains open, high, low, close, and volume columns for stock prices in a dataframe. The data also includes Simple momentum data. 
   #         Your task is to generate a Python script that will plot this data using a candlestick chart style. Ensure that the file is saved using the variable output_file that will be defined elsewhere. 
    #        Ensure to set up the matplotlib plot with an appropriate axis labels. The title should include the stock name {file} and a prediction of 
     #       short-term performance. Base the prediction on the Simple momentum data. 
      #      """
       #             
            # Get the generated code from the GPT model
        #    generated_code = get_code(client, prompt)
#
 #           if generated_code:
                #print(f"Generated code:\n{generated_code}")
  #              generated_code = process_text(generated_code)
   #             print(generated_code)
#
                # Execute the generated code and create the chart
 #               execute_chart_code(df, generated_code, output_file)
            
            

if __name__ == "__main__":
    main()
