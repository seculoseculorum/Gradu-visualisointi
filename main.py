import pandas as pd
import os
import matplotlib.pyplot as plt
import mplfinance as mpf
from dotenv import load_dotenv
from openai import OpenAI
import re
from IPython.display import SVG, display
import sys
from io import StringIO

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

def create_svg(df):
    # Set fixed Y-axis range
    y_axis_min = 75
    y_axis_max = 125
    y_axis_range = y_axis_max - y_axis_min

    svg_height = 300
    svg_width = 800
    chart_height = 200  # Actual height of the price chart
    chart_bottom = 250  # Y position where the lowest price will be

    # Calculate scaling factor based on the fixed Y-axis range
    scale = chart_height / y_axis_range

    # SVG header
    svg_content = f'<svg width="{svg_width}" height="{svg_height}" xmlns="http://www.w3.org/2000/svg">\n'

    # Draw the y-axis line
    svg_content += f'  <line x1="40" y1="{chart_bottom}" x2="40" y2="{chart_bottom - chart_height}" stroke="black" stroke-width="2" />\n'

    # Add y-axis ticks, labels, and support lines
    y_tick_step = 10
    for price in range(y_axis_min, y_axis_max + y_tick_step, y_tick_step):
        y_position = chart_bottom - (price - y_axis_min) * scale
        # Y-axis tick and label
        svg_content += f'  <line x1="35" y1="{y_position}" x2="40" y2="{y_position}" stroke="black" stroke-width="1" />\n'
        svg_content += f'  <text x="10" y="{y_position + 5}" font-size="10" fill="black">{price}</text>\n'
        # Support line across the chart
        svg_content += f'  <line x1="40" y1="{y_position}" x2="{svg_width - 20}" y2="{y_position}" stroke="lightgray" stroke-width="1" stroke-dasharray="5, 5" />\n'

    # Explicitly add the Y-tick and line at 100 (if not already included)
    if 100 not in range(y_axis_min, y_axis_max + y_tick_step, y_tick_step):
        y_position = chart_bottom - (100 - y_axis_min) * scale
        svg_content += f'  <line x1="35" y1="{y_position}" x2="40" y2="{y_position}" stroke="black" stroke-width="1" />\n'
        svg_content += f'  <text x="10" y="{y_position + 5}" font-size="10" fill="black">100</text>\n'
        svg_content += f'  <line x1="40" y1="{y_position}" x2="{svg_width - 20}" y2="{y_position}" stroke="lightgray" stroke-width="1" stroke-dasharray="5, 5" />\n'

    # Calculate the width available for each candlestick
    num_candles = len(df)
    candle_width = (svg_width - 280) / num_candles
    min_body_height = 1  # Minimum height for the candle body to ensure visibility

    # Loop over each row in the DataFrame to create candlesticks
    for i, (index, row) in enumerate(df.iterrows()):
        x_position = 40 + i * candle_width  # Space out each candlestick
        wick_x_position = x_position + candle_width / 2  # Wick is centered on the candle

        # Ensure all values are within the fixed Y-axis range
        high = max(y_axis_min, min(y_axis_max, row['High']))
        low = max(y_axis_min, min(y_axis_max, row['Low']))
        open_price = max(y_axis_min, min(y_axis_max, row['Open']))
        close_price = max(y_axis_min, min(y_axis_max, row['Close']))

        wick_y1 = chart_bottom - (high - y_axis_min) * scale
        wick_y2 = chart_bottom - (low - y_axis_min) * scale
        body_y = chart_bottom - (max(open_price, close_price) - y_axis_min) * scale
        body_height = max(abs(close_price - open_price) * scale, min_body_height)  # Ensure a minimum body height

        # Determine if the stock went up or down (green or red body)
        body_color = 'green' if close_price > open_price else 'red'

        # Draw the wick (line from high to low)
        svg_content += f'  <line x1="{wick_x_position}" y1="{wick_y1}" x2="{wick_x_position}" y2="{wick_y2}" stroke="black" stroke-width="1" />\n'

        # Draw the body (rectangle from open to close)
        body_x_position = x_position + candle_width * 0.05  # Make the body 90% of the candle width
        svg_content += f'  <rect x="{body_x_position}" y="{body_y}" width="{candle_width * 0.9}" height="{body_height}" fill="{body_color}" />\n'

    # SVG footer
    svg_content += '</svg>'

    return svg_content


def createinputs():
    out = "C:\\Users\\jussi\\Seculo Seculorum Oy\\Jussi Personal - Documents\\Jussin gradu\\Visualisointi\\Data\\SVG\\"
    inputs = "C:\\Users\\jussi\\Seculo Seculorum Oy\\Jussi Personal - Documents\\Jussin gradu\\Visualisointi\\Data\\Inputs\\"
    files =os.listdir(inputs)
    
    for file in files: 
        name = str(file)
        name = name[:-4]
        df = pd.read_csv(f"{inputs}{file}")
        df = df.dropna()
        df['Date'] = pd.to_datetime(df['Date'])  # Removed origin and unit parameters
        df = df.tail(30)
        # Scale data by setting the first Open value as the base (100)
        base_open = df['Open'].iloc[0]
        df[['Close', 'Open', 'High', 'Low']] = df[['Close', 'Open', 'High', 'Low']].apply(lambda x: x / base_open * 100)

        # Set 'Date' as the index
        df.set_index('Date', inplace=True)


        # Generate the SVG
        svg_code = create_svg(df)

        #Save to a file
        with open(f'{out}{name}.svg', 'w') as file:
            file.write(svg_code)


    
def main():
    createinputs()
    prompts = {
    "positive": f"""
                    In the end I will give you a svg-file with candlestick stock data.
                    Add technical analysis lines to the chart showing the stock has a bullish (upward) breakout. Please output only the lines that should be added to the revised svg.
                    Ensure that the resistance level (This is a price level where a stock has historically had difficulty moving above. When the price breaks above this level, it indicates a bullish breakout)
                    and support levels (This is a price level where a stock has had difficulty falling below. A break below this level indicates a bearish breakout.) are added. 
                    You can also add a trendline. Use the levels and the trendline to imply a breakout in accordance with the instruction. Please label the lines.
                    End any lines you make at the last candle which is located at x=600 and add a name for the line to the right of this. 
                    Read in the following candlechart:
                   
                    """,
    "neutral": f"""
                    In the end I will give you a svg-file with candlestick stock data.
                    Based on the data available add technical analysis lines to the chart. Depending on the data the lines can be bullish (upward), bearish (downward), or neutral. 
                    Please output only the lines that should be added to the revised svg.
                    Ensure that the resistance level (This is a price level where a stock has historically had difficulty moving above)
                    and support levels (This is a price level where a stock has had difficulty falling below) are added. 
                    You can also add a trendline. Use the levels and the trendline to illustrate potential breakout scenarios without favoring any specific direction. Please label the lines.
                    End any lines you make at the last candle which is located at x=600 and add a name for the line to the right of this. 

                    Read in the following candlechart:
                    
                    """,
    "negative": f"""
                    In the end I will give you a svg-file with candlestick stock data.
                    Add technical analysis lines to the chart showing the stock has a bearish (downward) breakout. Please output only the lines that should be added to the revised svg.
                    Ensure that the resistance level (This is a price level where a stock has historically had difficulty moving above. When the price breaks above this level, it indicates a bullish breakout)
                    and support levels (This is a price level where a stock has had difficulty falling below. A break below this level indicates a bearish breakout.) are added. 
                    You can also add a trendline. Use the levels and the trendline to imply a breakout in accordance with the instruction. Please label the lines.
                    End any lines you make at the last candle which is located at x=600 and add a name for the line to the right of this. 
                    Read in the following candlechart:
                
                    """
}


    key = get_apikey()
    client = OpenAI(api_key=key)  # Instantiate the OpenAI client with the new interface

    in_path = "C:\\Users\\jussi\\Seculo Seculorum Oy\\Jussi Personal - Documents\\Jussin gradu\\Visualisointi\\Data\\SVG\\"
    out_path = "C:\\Users\\jussi\\Seculo Seculorum Oy\\Jussi Personal - Documents\\Jussin gradu\\Visualisointi\\Data\\Outputs\\"
    # Create the output directory if it doesn't exist
    os.makedirs(out_path, exist_ok=True)
    
    files = os.listdir(in_path)
    for file in files: 
        filebase = file[:4]
        path = f"{in_path}{file}"
        
        with open(path, 'r') as file:
 
            in_svg = file.read()
        # Loop through the dictionary
        for key, prompt in prompts.items():
            while True:
                try:
                    # Format the file name
                  
                    filename = f"{filebase}_{key}.svg"
                    file_path = os.path.join(out_path, filename)
            
            # Skip if the file already exists
                    if os.path.exists(file_path):
                        print(f"File '{filename}' already exists. Skipping.")
                        break

                    # Generate the updated prompt
                    curprompt = f"{prompt}{in_svg}"
                    
                    # Generate code based on the prompt
                    generated_code = get_code(client, curprompt)
                    
                    # Generate SVG using the generated code
                    svg = get_svg(generated_code, in_svg)
                    
                    # Print the SVG for verification
                    print(svg)
                    
                    
                    # Save the SVG file
                    save_svg(svg, out_path, filename)
                    
                    # If everything succeeds, break the loop
                    break
                except Exception as e:
                    print(f"The following error occurred.\n {e} \nRetrying...")
                    
if __name__ == "__main__":
    main()
