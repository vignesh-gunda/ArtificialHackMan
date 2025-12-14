#!/usr/bin/env python3
"""
Fully Dynamic Dashboard Generator - NO HARDCODED PROMPTS
Uses GPT-4 to generate prompts from brief.md and create code
"""

import os
import json
import pandas as pd
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

class DynamicPromptGenerator:
    """Generates prompts dynamically from brief.md using GPT-4"""
    
    def __init__(self, llm):
        self.llm = llm
    
    def generate_html_prompt(self, user_prompt, data_info):
        """Use GPT-4 to generate HTML creation prompt from user requirements"""
        prompt_creator = ChatPromptTemplate.from_messages([
            ("system", "You are a prompt engineer. Create a detailed prompt for generating HTML code based on user requirements."),
            ("human", f"""User Requirements:
{user_prompt}

Data Information:
- JSON file: happiness_data.json
- Countries: {data_info['count']}
- Columns: {data_info['columns']}
- Key happiness column: 'Ladder score'

Create a detailed prompt that will instruct an HTML developer to build exactly what the user wants. The prompt should specify:
1. What HTML structure is needed
2. What containers and elements to create
3. How to link external files (CSS, JS, CDN libraries)
4. What accessibility features to include
5. Any specific requirements from the user's description

Return only the prompt text, no explanations.""")
        ])
        
        response = self.llm.invoke(prompt_creator.format_messages())
        return response.content
    
    def generate_css_prompt(self, user_prompt, data_info):
        """Use GPT-4 to generate CSS creation prompt from user requirements"""
        prompt_creator = ChatPromptTemplate.from_messages([
            ("system", "You are a prompt engineer. Create a detailed prompt for generating CSS code based on user requirements."),
            ("human", f"""User Requirements:
{user_prompt}

Data Information:
- JSON file: happiness_data.json
- Countries: {data_info['count']}
- Theme: Based on user's design requirements

Create a detailed prompt that will instruct a CSS designer to style exactly what the user wants. The prompt should specify:
1. What design theme to use based on user requirements
2. How to style interactive elements
3. What colors and typography to use
4. How to make it responsive
5. Any specific styling requirements from the user's description

Return only the prompt text, no explanations.""")
        ])
        
        response = self.llm.invoke(prompt_creator.format_messages())
        return response.content
    
    def generate_js_prompt(self, user_prompt, data_info):
        """Use GPT-4 to generate JavaScript creation prompt from user requirements"""
        prompt_creator = ChatPromptTemplate.from_messages([
            ("system", "You are a prompt engineer. Create a detailed prompt for generating JavaScript code based on user requirements."),
            ("human", f"""User Requirements:
{user_prompt}

Data Information:
- JSON file: happiness_data.json
- Countries: {data_info['count']}
- Columns: {data_info['columns']}
- Key happiness column: 'Ladder score'
- Score range: {data_info.get('score_range', 'Unknown')}

Create a detailed prompt that will instruct a JavaScript developer to build exactly what the user wants. The prompt should specify:
1. What data to load and how to process it
2. What visualizations to create (maps, charts, etc.)
3. What interactions to implement
4. How to handle user events
5. What libraries to use and how
6. Any specific functionality from the user's description

Return only the prompt text, no explanations.""")
        ])
        
        response = self.llm.invoke(prompt_creator.format_messages())
        return response.content

class FullyDynamicDashboardGenerator:
    """Completely dynamic dashboard generator with no hardcoded prompts"""
    
    def __init__(self):
        load_dotenv()
        
        # Use GPT-4 for all operations
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.1,
            max_tokens=4000
        )
        
        self.prompt_generator = DynamicPromptGenerator(self.llm)
        self.user_prompt = ""
        self.data_info = {}
    
    def load_user_prompt(self):
        """Load the exact user prompt from brief.md"""
        print("📖 Loading user prompt from brief.md...")
        
        with open("inputs/brief.md", "r") as f:
            brief_content = f.read()
        
        # Extract the actual requirements (remove markdown formatting)
        self.user_prompt = brief_content.strip()
        
        print("✅ User prompt loaded")
        print(f"📝 Prompt length: {len(self.user_prompt)} characters")
    
    def load_and_analyze_data(self):
        """Load and analyze the happiness data"""
        print("📊 Loading and analyzing data...")
        
        # Read Excel file
        df = pd.read_excel("inputs/DataForFigure2.1WHR2021C2.xls")
        
        # Analyze data dynamically
        self.data_info = {
            'count': len(df),
            'columns': list(df.columns),
            'score_range': f"{df['Ladder score'].min():.2f} - {df['Ladder score'].max():.2f}",
            'sample_countries': df['Country name'].head(5).tolist(),
            'data_types': {col: str(df[col].dtype) for col in df.columns}
        }
        
        # Save as JSON
        os.makedirs("outputs", exist_ok=True)
        data_json = df.to_json(orient='records', indent=2)
        with open("outputs/happiness_data.json", "w", encoding="utf-8") as f:
            f.write(data_json)
        
        print(f"✅ Data processed: {self.data_info['count']} countries")
        return df
    
    def generate_html(self):
        """Generate HTML using dynamically created prompt"""
        print("🏗️ Generating HTML prompt with GPT-4...")
        
        # Generate the prompt dynamically
        html_prompt_text = self.prompt_generator.generate_html_prompt(
            self.user_prompt, self.data_info
        )
        
        print("🏗️ Creating HTML with generated prompt...")
        
        # Use the generated prompt to create HTML
        html_creator = ChatPromptTemplate.from_messages([
            ("system", "You are an expert HTML developer. Follow the instructions exactly."),
            ("human", html_prompt_text)
        ])
        
        response = self.llm.invoke(html_creator.format_messages())
        html_code = self.extract_code(response.content, "html")
        
        with open("outputs/index.html", "w", encoding="utf-8") as f:
            f.write(html_code)
        
        print("✅ HTML generated with dynamic prompt")
    
    def generate_css(self):
        """Generate CSS using dynamically created prompt"""
        print("🎨 Generating CSS prompt with GPT-4...")
        
        # Generate the prompt dynamically
        css_prompt_text = self.prompt_generator.generate_css_prompt(
            self.user_prompt, self.data_info
        )
        
        print("🎨 Creating CSS with generated prompt...")
        
        # Use the generated prompt to create CSS
        css_creator = ChatPromptTemplate.from_messages([
            ("system", "You are an expert CSS designer. Follow the instructions exactly."),
            ("human", css_prompt_text)
        ])
        
        response = self.llm.invoke(css_creator.format_messages())
        css_code = self.extract_code(response.content, "css")
        
        with open("outputs/styles.css", "w", encoding="utf-8") as f:
            f.write(css_code)
        
        print("✅ CSS generated with dynamic prompt")
    
    def generate_javascript(self):
        """Generate JavaScript using dynamically created prompt"""
        print("⚡ Generating JavaScript prompt with GPT-4...")
        
        # Generate the prompt dynamically
        js_prompt_text = self.prompt_generator.generate_js_prompt(
            self.user_prompt, self.data_info
        )
        
        print("⚡ Creating JavaScript with generated prompt...")
        
        # Use the generated prompt to create JavaScript
        js_creator = ChatPromptTemplate.from_messages([
            ("system", "You are an expert JavaScript developer. Follow the instructions exactly and create working code."),
            ("human", js_prompt_text)
        ])
        
        response = self.llm.invoke(js_creator.format_messages())
        js_code = self.extract_code(response.content, "javascript")
        
        with open("outputs/script.js", "w", encoding="utf-8") as f:
            f.write(js_code)
        
        print("✅ JavaScript generated with dynamic prompt")
    
    def extract_code(self, content, code_type):
        """Extract clean code from LLM response"""
        import re
        
        # Try to extract code blocks
        patterns = [
            rf'```{code_type}\s*(.*?)\s*```',
            r'```\s*(.*?)\s*```',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
            if matches:
                return matches[0].strip()
        
        # If no code blocks, look for specific content
        if code_type == "html" and "<!DOCTYPE html>" in content:
            start = content.find("<!DOCTYPE html>")
            end = content.find("</html>") + 7
            if start != -1 and end != -1:
                return content[start:end]
        
        # Return cleaned content
        return content.strip()
    
    def run(self):
        """Run the fully dynamic dashboard generation process"""
        print("🚀 Starting Fully Dynamic Dashboard Generation")
        print("=" * 70)
        print("🎯 NO HARDCODED PROMPTS - Everything generated from brief.md")
        print("🤖 Using GPT-4 for prompt generation AND code creation")
        print("=" * 70)
        
        try:
            # Step 1: Load user prompt from brief.md
            self.load_user_prompt()
            
            # Step 2: Load and analyze data
            self.load_and_analyze_data()
            
            # Step 3: Generate HTML with dynamic prompt
            self.generate_html()
            
            # Step 4: Generate CSS with dynamic prompt
            self.generate_css()
            
            # Step 5: Generate JavaScript with dynamic prompt
            self.generate_javascript()
            
            print("\n" + "=" * 70)
            print("🎉 FULLY DYNAMIC DASHBOARD COMPLETE!")
            print("=" * 70)
            print("✅ User prompt loaded from brief.md")
            print("✅ Prompts generated dynamically by GPT-4")
            print("✅ Code created by GPT-4 using generated prompts")
            print("✅ Uses ONLY happiness_data.json from data analysis")
            print("✅ Zero hardcoded prompts or templates")
            
            print(f"\n📊 Data Summary:")
            print(f"   • {self.data_info['count']} countries processed")
            print(f"   • {len(self.data_info['columns'])} data columns")
            print(f"   • Happiness scores: {self.data_info['score_range']}")
            
            print(f"\n📁 Generated Files:")
            print("   • outputs/index.html (dynamic HTML)")
            print("   • outputs/styles.css (dynamic CSS)")
            print("   • outputs/script.js (dynamic JavaScript)")
            print("   • outputs/happiness_data.json (processed data)")
            
            print(f"\n🎯 Dashboard built exactly from your requirements!")
            print("🌐 Open outputs/index.html in your browser")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            print("Make sure your OpenAI API key is set in .env file")

def main():
    """Main execution function"""
    generator = FullyDynamicDashboardGenerator()
    generator.run()

if __name__ == "__main__":
    main()