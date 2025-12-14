# World Happiness Dashboard Generator

A dynamic LangGraph agent that uses OpenAI GPT-4o mini to create an interactive dashboard from the World Happiness Report data without any hardcoded prompts.

## Features

- **Dynamic Agent**: Uses OpenAI GPT-4o mini with zero hardcoded prompts
- **Interactive Dashboard**: World map with happiness score gradients
- **Data-Driven**: Uses only data from `DataForFigure2.1WHR2021C2.xls`
- **Complete Package**: Generates HTML, CSS, JavaScript, and data files

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set OpenAI API key** in `.env` file:
   ```
   OPENAI_API_KEY=your-api-key-here
   ```

## Usage

Run the main script to generate the dashboard:

```bash
python main.py
```

This will create a complete dashboard in the `outputs/` folder:
- `index.html` - Main dashboard page
- `styles.css` - Happiness-themed styling  
- `script.js` - Interactive functionality
- `happiness_data.json` - Processed data from Excel file

## Dashboard Features

- **Interactive World Map**: Color-coded by happiness scores
- **Hover Tooltips**: Show country names and exact happiness values
- **Click Selection**: Select countries to view detailed components
- **Linked Bar Chart**: Shows happiness factors for selected countries
- **Responsive Design**: Works on desktop and mobile
- **Happiness Theme**: Warm, positive colors and design

## Data Source

Uses data from `inputs/DataForFigure2.1WHR2021C2.xls` containing:
- 149 countries
- 20 data columns including happiness scores and components
- Regional indicators and detailed metrics

## Project Structure

```
task_9/
├── inputs/
│   ├── brief.md                        # Project requirements
│   └── DataForFigure2.1WHR2021C2.xls   # Happiness data
├── outputs/                            # Generated dashboard files
│   ├── index.html                      # Main dashboard
│   ├── styles.css                      # Styling
│   ├── script.js                       # Interactivity
│   └── happiness_data.json             # Processed data
├── main.py                             # Dashboard generator
├── requirements.txt                    # Dependencies
└── .env                               # Configuration
```

## How It Works

The agent follows a dynamic workflow:

1. **Reads Data**: Loads and analyzes the Excel file
2. **Generates HTML**: Creates interactive dashboard structure
3. **Creates CSS**: Applies happiness-themed styling
4. **Builds JavaScript**: Implements map and chart interactions
5. **Processes Data**: Converts Excel to JSON format

All decisions are made by the LLM - no hardcoded templates or prompts!

## View Dashboard

After running `main.py`, open `outputs/index.html` in your browser to explore the interactive World Happiness Dashboard.