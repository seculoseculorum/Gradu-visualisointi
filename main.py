import pandas as pd
import os
from dotenv import load_dotenv
from openai import OpenAI

def get_apikey():
    load_dotenv("keys.env")
    api_key = os.getenv("api_key")
    if not api_key:
        raise ValueError("API key not found. Please check your keys.env file.")
    return api_key

def get_svg(client, df, prompt):
    try:
        response = client.chat.completions.create(
            #model='gpt-4o',  # Use the correct model name here
            model = 'gpt-4',
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=2000,
            temperature=0.1
        )
        
        # Get the chart content
        chart = response.choices[0].message.content.strip()
        
        # Remove all symbols before the first '<'
        first_angle_bracket_index = chart.find('<')
        if first_angle_bracket_index != -1:
            chart = chart[first_angle_bracket_index:]  # Keep only the part from the first '<' onward

        return chart
    except Exception as e:
        print(f"Error while generating SVG: {e}")
        return ""

def main():
    key = get_apikey()
    client = OpenAI(api_key=key)  # Initialize the client with the API key
    path = f"{os.getcwd()}\\Data\\"
    out_path = f"{path}Outputs\\"
    # Create the output directory if it doesn't exist
    os.makedirs(out_path, exist_ok=True)
    for file in os.listdir(path):
        df = pd.read_csv(f"{path}{file}")
        print(df)

        prompt = f"""
        Read in the following stock data: 
        {df.to_dict(orient='records')}  # Convert DataFrame to a list of records for clarity
        Based on the data create a basic SVG candle chart. 
        Focus on representing the stock price trends effectively. Please output only the .svg-file data.
        Please loop through the stock data and create a candlestick for each day.
        """
        chart = get_svg(client, df, prompt)


        if chart:  # Only save if chart generation was successful
            output_file = f"{out_path}{file}.svg"
            with open(output_file, 'w') as f:
                f.write(chart)

            print(f"SVG visualization has been saved to {output_file}.")
        break  # Remove this break to process all files

if __name__ == "__main__":
    main()
