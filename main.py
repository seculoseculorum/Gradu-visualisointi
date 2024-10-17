import pandas as pd
import os
import matplotlib.pyplot as plt
import mplfinance as mpf
from dotenv import load_dotenv
from openai import OpenAI
import re
from IPython.display import SVG, display
import sys

def create_svgs(df):
    # Calculate scaling factors
    price_min = df[['Low']].min().min()
    price_max = df[['High']].max().max()
    price_range = price_max - price_min

    svg_height = 300
    svg_width = 400
    chart_height = 200  # Actual height of the price chart
    chart_bottom = 250  # Y position where the lowest price will be
    scale_factor = chart_height / price_range
    
    # SVG header
    svg_content = f'<svg width="{svg_width}" height="{svg_height}" xmlns="http://www.w3.org/2000/svg">\n'
    
    # Draw the x-axis line
    svg_content += f'  <line x1="40" y1="{chart_bottom}" x2="{svg_width - 40}" y2="{chart_bottom}" stroke="black" stroke-width="2" />\n'
    
    # Calculate the width available for each candlestick
    num_candles = len(df)
    candle_width = (svg_width - 80) / num_candles
    min_body_height = 1  # Minimum height for the candle body to ensure visibility
    
    # Loop over each row in the DataFrame to create candlesticks and ticks
    for i, (index, row) in enumerate(df.iterrows()):
        x_position = 40 + i * candle_width  # Space out each candlestick
        wick_x_position = x_position + candle_width / 2  # Wick is centered on the candle
        
        wick_y1 = chart_bottom - (row['High'] - price_min) * scale_factor
        wick_y2 = chart_bottom - (row['Low'] - price_min) * scale_factor
        body_y = chart_bottom - (max(row['Open'], row['Close']) - price_min) * scale_factor
        body_height = max(abs(row['Close'] - row['Open']) * scale_factor, min_body_height)  # Ensure a minimum body height
        
        # Determine if the stock went up or down (green or red body)
        body_color = 'green' if row['Close'] > row['Open'] else 'red'
        
        # Draw the wick (line from high to low)
        svg_content += f'  <line x1="{wick_x_position}" y1="{wick_y1}" x2="{wick_x_position}" y2="{wick_y2}" stroke="black" stroke-width="1" />\n'
        
        # Draw the body (rectangle from open to close)
        body_x_position = x_position + candle_width * 0.05  # Make the body 90% of the candle width
        svg_content += f'  <rect x="{body_x_position}" y="{body_y}" width="{candle_width * 0.9}" height="{body_height}" fill="{body_color}" />\n'
        
        # Add the tick marks and the date as text below the candlestick
        svg_content += f'  <line x1="{wick_x_position}" y1="{chart_bottom}" x2="{wick_x_position}" y2="{chart_bottom + 5}" stroke="black" stroke-width="1" />\n'
        date_str = index.strftime('%Y-%m-%d')
        svg_content += f'  <text x="{x_position}" y="275" font-size="12" fill="black">{date_str}</text>\n'
    ###
    #Use this for creating SVG with SMI-line
    #SMI lines scaling
    #smi_min = df['SMI 10'].min()
    #smi_max = df['SMI 10'].max()
    #smi_range = smi_max - smi_min
    #smi_scale_factor = chart_height / smi_range

    # Add SMI 10 line
    #smi_values = df['SMI 10']
    #scaled_smi = [(chart_bottom - (value - smi_min) * smi_scale_factor) for value in smi_values]
    #svg_content += f'  <polyline fill="none" stroke="blue" stroke-width="2" points="'
    
    #for i, y in enumerate(scaled_smi):
    #    x_position = 40 + i * candle_width
    #    svg_content += f'{x_position + candle_width / 2},{y} '
    
    #svg_content += f'" />\n'
    
    # Add label for SMI 10 line
    #svg_content += f'  <text x="10" y="{chart_bottom - (df["SMI 10"].iloc[0] - smi_min) * smi_scale_factor}" font-size="12" fill="blue">SMI 10</text>\n'
    
    ###
    
    # Add SVG footer

    svg_content += '</svg>'
    
    return svg_content



def get_apikey():
    """
    Load the API key from the .env file.
    """
    load_dotenv("keys.env")
    api_key = os.getenv("api_key")
    if not api_key:
        raise ValueError("API key not found. Please check your keys.env file.")
    return api_key

def save_svg(svg_content,path, filename):
    with open(f"{path}{filename}", 'w') as file:
        file.write(svg_content)

def get_svg(code, svg):
    
    pattern = r"```xml\s*(.*?)\s*```"
    match = re.search(pattern,code, re.DOTALL)
    if match:
        xml_lines = match.group(1).strip()
    else:
        print("No XML code block found.")
        return
    closing_svg_index = svg.rfind('</svg>')
    if closing_svg_index == -1:
        print("Invalid SVG content: No closing </svg> tag found.")
        return
    # Insert the xml_lines before the closing </svg> tag
    new_svg = (svg[:closing_svg_index]
                       + '\n' + xml_lines + '\n'
                       + svg[closing_svg_index:])
    print(new_svg)
    # Step 3: Show the visualization generated
    display(SVG(new_svg))
    return new_svg


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

def main():
    path = f"{os.getcwd()}/Data/"
    in_path = f"{path}Inputs/"
    mid_path = f"{path}First_SVG/"
    out_path = f"{path}Outputs/"
   
    for file in os.listdir(in_path): 
        filename = file.replace(".csv", ".svg")

        df = pd.read_csv(f"{in_path}{file}")
        df = df.dropna()
        df['Date'] = pd.to_datetime(df['Date'], origin='1900-01-01', unit='D')

        df.set_index('Date', inplace=True)
        df = df.tail(30)
        svg = create_svgs(df)
        save_svg(svg,mid_path,filename)

    sys.exit()

    key = get_apikey()
    client = OpenAI(api_key=key)  # Instantiate the OpenAI client with the new interface

    
    # Create the output directory if it doesn't exist
    os.makedirs(out_path, exist_ok=True)

    file = f"{path}test_no_SMI.svg"
    print(file)    
    with open(file, 'r') as file:
        svg = file.read()
    # Define the output filename for the visualization
    prompt = f"""
                Read in the following candlechart:
                {svg}.
                Add technical analysis lines to the chart showing the stock have a bearish (downward) breakout. Please output only the lines that should be added to the revised svg.
                ensure that the resistance level (This is a price level where a stock has historically had difficulty moving above. When the price breaks above this level, it indicates a bullish breakout)
                  and support levels (This is a price level where a stock has had difficulty falling below. A break below this level indicates a bearish breakout.) are added. 
                  You can also add a trendline. Use the levels and the trendline to imply a breakout in accordance with the instruction. Please label the lines.
                """
    generated_code = get_code(client, prompt)
    svg = get_svg(generated_code, svg) 
    print(svg)
    save_svg(svg, out_path , filename)
if __name__ == "__main__":
    main()
