from openai import OpenAI
from datetime import datetime
from pathlib import Path
import json
import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Initialize OpenAI client with API key from environment variable
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def get_webpage_content(url):
    """
    Fetch webpage content with error handling and retries
    """
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser'), response.text
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                print(f"Error fetching webpage: {e}")
                return None, None
            print(f"Attempt {attempt + 1} failed, retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)

def clean_webpage_content(soup):
    """
    Clean and reduce webpage content to focus on relevant lunch information
    """
    # Remove script and style elements
    for script in soup(["script", "style", "nav", "footer", "header"]):
        script.decompose()
    
    # Get text content
    text = soup.get_text()
    
    # Split into lines and clean
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Look for lunch-related sections
    lunch_keywords = ['lunch', 'lunchmeny', 'dagens lunch', 'veckans lunch', 'lunchmeny']
    relevant_lines = []
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        # If we find a lunch-related keyword, include the next few lines
        if any(keyword in line_lower for keyword in lunch_keywords):
            relevant_lines.append(line)
            # Include next 5 lines if they exist
            for j in range(1, 6):
                if i + j < len(lines):
                    relevant_lines.append(lines[i + j])
    
    # If we found lunch-related content, return it
    if relevant_lines:
        return '\n'.join(relevant_lines)
    
    # If no lunch content found, return first 1000 characters of text
    return text[:1000]

def get_bullen_menu(soup, current_day):
    """
    Extract specific menu information from Bullen's website
    """
    try:
        # Get all text content
        text = soup.get_text()
        
        # Split into lines and clean
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Debug print
        print(f"Looking for {current_day}'s menu in Bullen")
        print("Available lines:", lines)
        
        # Find the current day's menu
        for i, line in enumerate(lines):
            if current_day in line:
                print(f"Found {current_day} at line {i}")
                # The menu item should be the next line
                if i + 1 < len(lines):
                    menu_item = lines[i + 1]
                    print(f"Found menu item: {menu_item}")
                    # Make sure it's not another day or a price
                    if not any(day in menu_item for day in ['Måndag', 'Tisdag', 'Onsdag', 'Torsdag', 'Fredag', 'Lördag', 'Söndag']) and not 'kr' in menu_item:
                        included_items = ["Sallad", "måltidsdryck"]  # Known included items for Bullen
                        return menu_item, included_items
        return None, []
    except Exception as e:
        print(f"Error extracting Bullen menu: {e}")
        return None, []

def get_friis_menu(soup, current_day):
    """
    Extract specific menu information from Friis 14's website, including vegetarian options and included items
    """
    try:
        # Get all text content
        text = soup.get_text()
        
        # Split into lines and clean
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Debug print
        print(f"Looking for {current_day}'s menu in Friis 14")
        print("Available lines:", lines)
        
        # Find the current day's menu and vegetarian option
        regular_menu = None
        vegetarian_menu = None
        included_items = ["Salladsbuffet", "surdegsbröd", "kaffe"]  # Known included items for Friis 14
        
        # First find the regular menu
        for i, line in enumerate(lines):
            if current_day in line:
                print(f"Found {current_day} at line {i}")
                # The menu item should be the next line
                if i + 1 < len(lines):
                    regular_menu = lines[i + 1]
                    print(f"Found regular menu: {regular_menu}")
                    break
        
        # Then find the vegetarian menu
        for i, line in enumerate(lines):
            if "Veckans vegetariska" in line:
                print(f"Found vegetarian section at line {i}")
                # The vegetarian menu should be the next line
                if i + 1 < len(lines):
                    vegetarian_menu = lines[i + 1]
                    print(f"Found vegetarian menu: {vegetarian_menu}")
                    break
        
        # Combine the menus if we found both
        if regular_menu and vegetarian_menu:
            return f"{regular_menu} | Vegetarisk: {vegetarian_menu}", included_items
        elif regular_menu:
            return regular_menu, included_items
        elif vegetarian_menu:
            return f"Vegetarisk: {vegetarian_menu}", included_items
        return None, included_items
    except Exception as e:
        print(f"Error extracting Friis 14 menu: {e}")
        return None, []

def get_restaurant_info(restaurant_name, url):
    """
    Use AI to extract lunch information from a restaurant's website
    """
    # First get the webpage content
    soup, webpage_content = get_webpage_content(url)
    if not webpage_content:
        print(f"Could not fetch content from {url}")
        return None

    # Clean and reduce webpage content
    cleaned_content = clean_webpage_content(soup)
    
    # Get current weekday (0 = Monday, 6 = Sunday)
    current_weekday = datetime.now().weekday()
    weekday_names = ['Måndag', 'Tisdag', 'Onsdag', 'Torsdag', 'Fredag', 'Lördag', 'Söndag']
    current_day = weekday_names[current_weekday]
    
    # Format date in Swedish style
    day_suffix = {1: 'a', 2: 'a', 3: 'e', 21: 'a', 22: 'a', 23: 'e', 31: 'a'}
    day = datetime.now().day
    suffix = day_suffix.get(day, 'e')
    
    # Swedish month names
    month_names = {
        1: 'januari', 2: 'februari', 3: 'mars', 4: 'april',
        5: 'maj', 6: 'juni', 7: 'juli', 8: 'augusti',
        9: 'september', 10: 'oktober', 11: 'november', 12: 'december'
    }
    month = month_names[datetime.now().month]
    year = datetime.now().year
    
    formatted_date = f"{current_day} den {day}{suffix} {month} {year}"

    # Try to extract price using BeautifulSoup
    price = None
    try:
        # Set known prices for specific restaurants
        known_prices = {
            "Bullen": "145 kr",
            "Saltimporten": "135 kr"
        }
        
        if restaurant_name in known_prices:
            price = known_prices[restaurant_name]
        else:
            # Look for common price patterns in Swedish
            price_patterns = [
                r'(\d+)\s*(?:kr|:-|SEK)',
                r'pris:\s*(\d+)\s*(?:kr|:-|SEK)',
                r'lunch:\s*(\d+)\s*(?:kr|:-|SEK)',
                r'(\d+)\s*(?:kr|:-|SEK)\s*inkl',
                r'(\d+)\s*(?:kr|:-|SEK)\s*per\s*person',
                r'\n\s*(\d+)\s*\n'  # Match numbers that are on their own line
            ]
            
            # Get all text content
            text_content = soup.get_text()
            
            # Look for price in text
            for pattern in price_patterns:
                import re
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    price_value = int(match.group(1))
                    # Validate price is within reasonable range for Malmö daily specials (99-180 kr)
                    if 99 <= price_value <= 180:
                        price = f"{price_value} kr"
                        break
                    else:
                        print(f"Found price {price_value} kr for {restaurant_name} but it's outside the reasonable range (99-180 kr)")
                    
    except Exception as e:
        print(f"Error extracting price: {e}")

    # Get specific menu for restaurants with custom handling
    daily_special = None
    included_items = None
    if restaurant_name == "Bullen":
        daily_special, included_items = get_bullen_menu(soup, current_day)
        if daily_special:
            cleaned_content = f"{current_day}\n{daily_special}"  # Override cleaned content with just the relevant menu
            print(f"Found Bullen menu for {current_day}: {daily_special}")
            print(f"Found Bullen included items: {included_items}")
    elif restaurant_name == "Friis 14":
        daily_special, included_items = get_friis_menu(soup, current_day)
        if daily_special:
            cleaned_content = f"{current_day}\n{daily_special}"  # Override cleaned content with just the relevant menu
            print(f"Found Friis 14 menu for {current_day}: {daily_special}")
            print(f"Found Friis 14 included items: {included_items}")

    # Prepare the daily_special value
    daily_special_value = daily_special if daily_special else f"description of today's lunch (or array of options if multiple) - MUST be for {current_day}"
    
    # General prompt for any restaurant
    prompt = f"""
    Analyze this restaurant website content and extract the lunch menu information for {restaurant_name}:
    
    {cleaned_content}
    
    Please provide the following information in a structured format:
    1. The lunch special(s) for {current_day} - IMPORTANT: Make sure to get the menu for {current_day}, not any other day
    2. Lunch price (look for prices in SEK/kr/:-)
    3. What's included in the lunch (e.g., drinks, bread, salad, coffee)
    4. Lunch serving hours (when lunch is served, not general opening hours)
    5. Any special notes or dietary information
    
    Important:
    - You MUST find the menu specifically for {current_day}
    - Look for the exact day name "{current_day}" in the menu
    - If you can't find the menu for {current_day}, return null or an empty string for daily_special
    - If multiple options are available, include all of them
    - Look for prices in SEK/kr/:- (common Swedish price formats)
    - Look for what's included in the lunch price
    - Look for lunch serving hours
    - Common Swedish price indicators: "kr", ":-", "SEK", "pris:", "lunch:"
    - Look for vegetarian options and mark them with "Vegetarisk:" prefix
    - Common vegetarian indicators: "vegetarisk", "veg", "vegetarian", "vegansk", "vegan"
    
    For included_items, ONLY include items that are explicitly mentioned as included using Swedish words like:
    - "ingår" (is included)
    - "inkluderad" (included)
    - "medföljer" (comes with)
    - "följer med" (comes with)
    
    Common included items to look for when these words are used:
    - Coffee (kaffe)
    - Bread (bröd)
    - Drinks (dryck)
    - Salad (sallad)
    - Dessert (dessert)
    - Soup (soppa)
    - Other sides that come with the lunch
    
    Do NOT include items in included_items unless they are explicitly mentioned as included using the Swedish words above.
    Do NOT include the main dish in included_items - that goes in daily_special.
    
    Return a JSON object with these exact fields:
    {{
        "restaurant_name": "{restaurant_name}",
        "url": "{url}",
        "daily_special": "{daily_special_value}",
        "price": "{price if price else 'price in SEK/kr'}",
        "included_items": {json.dumps(included_items) if included_items else "[]"},
        "lunch_hours": "lunch serving hours",
        "special_notes": "any special information or notes",
        "day_of_week": "{current_day}",
        "date": "{formatted_date}"
    }}
    
    Return ONLY the JSON object, no other text or explanation.
    """

    try:
        # Create the chat completion with a shorter context window
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts lunch menu information from restaurant websites. Return only the requested JSON object, no other text."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000  # Limit the response length
        )
        
        # Get the response text
        response_text = response.choices[0].message.content.strip()
        
        # Debug print
        print(f"API Response for {restaurant_name}: {response_text}")
        
        try:
            # Clean the response text by removing markdown code block markers
            cleaned_response = response_text.replace('```json', '').replace('```', '').strip()
            
            # Try to parse the response as JSON
            data = json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON for {restaurant_name}: {e}")
            print(f"Raw response: {response_text}")
            # Try to create a basic JSON object with the information we have
            data = {
                "restaurant_name": restaurant_name,
                "url": url,
                "daily_special": daily_special_value,
                "price": price if price else "price in SEK/kr",
                "included_items": included_items if included_items else [],
                "lunch_hours": "11:30-14:00",  # Default lunch hours
                "special_notes": "",
                "day_of_week": current_day,
                "date": formatted_date
            }
            
        # Ensure all required fields are present
        required_fields = [
            "restaurant_name", "url", "daily_special", "price", "included_items",
            "lunch_hours", "special_notes", "day_of_week", "date"
        ]
        
        for field in required_fields:
            if field not in data:
                print(f"Missing required field '{field}' in response for {restaurant_name}")
                if field == "included_items":
                    data[field] = included_items if included_items else []
                elif field == "lunch_hours":
                    data[field] = "11:30-14:00"
                elif field == "special_notes":
                    data[field] = ""
                else:
                    return None
        
        # Ensure date is correct
        data['date'] = formatted_date
        return json.dumps(data)
        
    except Exception as e:
        print(f"Error getting restaurant info for {restaurant_name}: {e}")
        return None

def save_lunch_data(data, filename="lunch_data.json"):
    """
    Save the lunch data to a JSON file
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Data saved to {filename}")
    except Exception as e:
        print(f"Error saving data: {e}")

def main():
    # List of restaurants to check
    restaurants = [
        {
            "name": "Bullen",
            "url": "https://www.bullen.nu/sv/lunch/"
        },
         {
            "name": "Saltimporten",
            "url": "https://www.saltimporten.com/"
        },
        {
            "name": "Välfärden",
            "url": "https://valfarden.nu/dagens-lunch/"
        },
        {
            "name": "Friis 14",
            "url": "https://www.friis14.com/lunch"
        }
    ]
    
    print(f"Starting lunch menu update for {datetime.now().strftime('%Y-%m-%d')}")
    all_lunch_data = []
    
    for restaurant in restaurants:
        print(f"Getting lunch info for {restaurant['name']}...")
        restaurant_data = get_restaurant_info(restaurant['name'], restaurant['url'])
        if restaurant_data:
            all_lunch_data.append(json.loads(restaurant_data))
    
    # Save all lunch data to a JSON file
    save_lunch_data(all_lunch_data)
    print("Lunch menu update completed!")

if __name__ == "__main__":
    main()

