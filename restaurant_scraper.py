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

print("Starting scraper...")
print(f"OpenAI API Key present: {'Yes' if os.getenv('OPENAI_API_KEY') else 'No'}")

def get_webpage_content(url):
    """
    Fetch webpage content with error handling and retries
    """
    print(f"Fetching content from: {url}")
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            print(f"Successfully fetched content from {url}")
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
                    if not any(day in menu_item for day in ['Måndagen', 'Tisdagen', 'Onsdagen', 'Torsdagen', 'Fredagen', 'Lördagen', 'Söndagen']) and not 'kr' in menu_item:
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

def get_valfarden_menu(soup, current_day):
    """
    Extract specific menu information from Välfärden's website
    """
    try:
        # Get all text content
        text = soup.get_text()
        
        # Split into lines and clean
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Debug print
        print(f"Looking for {current_day}'s menu in Välfärden")
        print("Available lines:", lines)
        
        # Look for the current day's menu
        for i, line in enumerate(lines):
            if current_day in line:
                print(f"Found {current_day} at line {i}")
                # The menu items should be in the next two lines
                if i + 2 < len(lines):
                    menu1 = lines[i + 1]
                    menu2 = lines[i + 2]
                    # Skip if the lines contain contact info or other non-menu text
                    if not any(x in menu1.lower() for x in ['tel:', 'email:', 'kontakt', 'intolerant']):
                        print(f"Found menus: {menu1} | {menu2}")
                        included_items = ["vatten", "salladsbuffé", "bröd", "smör", "hummus", "kaffe / te"]
                        return f"{menu1}\n\n{menu2}", included_items
        return None, []
    except Exception as e:
        print(f"Error extracting Välfärden menu: {e}")
        return None, []

def get_saltimporten_menu(soup, current_day):
    """
    Extract specific menu information from Saltimporten's website
    """
    try:
        # Get all text content
        text = soup.get_text()
        
        # Split into lines and clean
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Debug print
        print(f"Looking for {current_day}'s menu in Saltimporten")
        print("Available lines:", lines)
        
        # Find the current day's menu and vegetarian option
        regular_menu = None
        vegetarian_menu = None
        
        # Look for the current day's menu
        for i, line in enumerate(lines):
            if current_day in line:
                print(f"Found {current_day} at line {i}")
                # The menu item should be the next line
                if i + 1 < len(lines):
                    menu_text = lines[i + 1]
                    # Skip if the line contains contact info or other non-menu text
                    if not any(x in menu_text.lower() for x in ['tel:', 'email:', 'kontakt', 'öppet', 'hullkajen']):
                        regular_menu = menu_text
                        print(f"Found regular menu: {regular_menu}")
                        break
        
        # Look for vegetarian menu
        for i, line in enumerate(lines):
            if "VEGETARISKT" in line:
                print(f"Found vegetarian section at line {i}")
                # The vegetarian menu should be the next line
                if i + 1 < len(lines):
                    menu_text = lines[i + 1]
                    # Skip if the line contains contact info or other non-menu text
                    if not any(x in menu_text.lower() for x in ['tel:', 'email:', 'kontakt', 'öppet', 'hullkajen']):
                        vegetarian_menu = menu_text
                        print(f"Found vegetarian menu: {vegetarian_menu}")
                        break
        
        # Combine the menus if we found both
        if regular_menu and vegetarian_menu:
            return f"{regular_menu}\nVegetarisk: {vegetarian_menu}", []
        elif regular_menu:
            return regular_menu, []
        elif vegetarian_menu:
            return f"Vegetarisk: {vegetarian_menu}", []
        return None, []
    except Exception as e:
        print(f"Error extracting Saltimporten menu: {e}")
        return None, []

def get_clemens_menu(soup, current_day):
    """
    Extract specific menu information from Clemens Kött's website
    """
    try:
        # Get all text content
        text = soup.get_text()
        
        # Split into lines and clean
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Debug print
        print(f"Looking for {current_day}'s menu in Clemens Kött")
        print("Available lines:", lines)
        
        # Look for the current day's menu
        for i, line in enumerate(lines):
            if current_day in line:
                print(f"Found {current_day} at line {i}")
                # The menu item should be the next line
                if i + 1 < len(lines):
                    menu_text = lines[i + 1]
                    # Skip if the line contains contact info or other non-menu text
                    if not any(x in menu_text.lower() for x in ['tel:', 'email:', 'kontakt', 'öppet', 'gibraltargatan']):
                        print(f"Found menu: {menu_text}")
                        return menu_text, []
        return None, []
    except Exception as e:
        print(f"Error extracting Clemens Kött menu: {e}")
        return None, []

def get_restaurant_info(restaurant_name, url):
    """
    Use AI to extract lunch information from a restaurant's website
    """
    # Get current weekday (0 = Monday, 6 = Sunday)
    current_weekday = datetime.now().weekday()
    weekday_names = ['Måndagen', 'Tisdagen', 'Onsdagen', 'Torsdagen', 'Fredagen', 'Lördagen', 'Söndagen']
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
    
    formatted_date = f"{current_day} den {day}:e {month} {year}"

    # If it's a weekend, return "Lunch serveras ej" message
    if current_weekday > 4:  # Saturday (5) or Sunday (6)
        data = {
            "restaurant_name": restaurant_name,
            "url": url,
            "daily_special": f"Lunch serveras ej på {current_day}",
            "price": "0 kr",
            "included_items": [],
            "lunch_hours": "Ej servering",
            "special_notes": "",
            "day_of_week": current_day,
            "date": formatted_date
        }
        return json.dumps(data)

    # First get the webpage content
    soup, webpage_content = get_webpage_content(url)
    if not webpage_content:
        print(f"Could not fetch content from {url}")
        return None

    # Clean and reduce webpage content
    cleaned_content = clean_webpage_content(soup)
    
    # Try to extract price using BeautifulSoup
    price = None
    try:
        # Set known prices for specific restaurants
        known_prices = {
            "Bullen": "145 kr",
            "Saltimporten": "135 kr",
            "Friis 14": "159 kr",
            "Välfärden": "115 kr"
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
    elif restaurant_name == "Välfärden":
        daily_special, included_items = get_valfarden_menu(soup, current_day)
        if daily_special:
            cleaned_content = f"{current_day}\n{daily_special}"  # Override cleaned content with just the relevant menu
            print(f"Found Välfärden menu for {current_day}: {daily_special}")
            print(f"Found Välfärden included items: {included_items}")
    elif restaurant_name == "Saltimporten":
        daily_special, included_items = get_saltimporten_menu(soup, current_day)
        if daily_special:
            cleaned_content = f"{current_day}\n{daily_special}"  # Override cleaned content with just the relevant menu
            print(f"Found Saltimporten menu for {current_day}: {daily_special}")
            print(f"Found Saltimporten included items: {included_items}")

    # Prepare the daily_special value
    daily_special_value = daily_special if daily_special else f"description of today's lunch (or array of options if multiple) - MUST be for {current_day}"
    
    # If we have the menu data from custom handlers, create a basic JSON object
    if daily_special and included_items:
        data = {
            "restaurant_name": restaurant_name,
            "url": url,
            "daily_special": daily_special_value,
            "price": price if price else "159 kr",  # Default to known price for Friis 14
            "included_items": included_items,
            "lunch_hours": "11:30-14:00",
            "special_notes": "",
            "day_of_week": current_day,
            "date": formatted_date
        }
        return json.dumps(data)

    # If we don't have custom handler data, try the API
    max_retries = 3
    retry_delay = 2  # seconds
    
    # Define the prompt for the OpenAI API
    prompt = f"""Extract lunch menu information from this restaurant website content for {current_day}:

{cleaned_content}

Return a JSON object with this structure:
{{
    "restaurant_name": "{restaurant_name}",
    "url": "{url}",
    "daily_special": "description of today's lunch (or array of options if multiple)",
    "price": "price in kr",
    "included_items": ["item1", "item2"],
    "lunch_hours": "11:30-14:00",
    "special_notes": "",
    "day_of_week": "{current_day}",
    "date": "{formatted_date}"
}}

Return only the JSON object, no other text."""
    
    for attempt in range(max_retries):
        try:
            print(f"Attempting OpenAI API call for {restaurant_name} (attempt {attempt + 1}/{max_retries})...")
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts lunch menu information from restaurant websites. Return only the requested JSON object, no other text."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000
            )
            
            response_text = response.choices[0].message.content.strip()
            print(f"API Response for {restaurant_name}: {response_text}")
            
            try:
                cleaned_response = response_text.replace('```json', '').replace('```', '').strip()
                data = json.loads(cleaned_response)
                return json.dumps(data)
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON for {restaurant_name}: {e}")
                print(f"Raw response: {response_text}")
                # Create a basic JSON object with the information we have
                data = {
                    "restaurant_name": restaurant_name,
                    "url": url,
                    "daily_special": daily_special_value,
                    "price": price if price else "159 kr",
                    "included_items": included_items if included_items else [],
                    "lunch_hours": "11:30-14:00",
                    "special_notes": "",
                    "day_of_week": current_day,
                    "date": formatted_date
                }
                return json.dumps(data)
                
        except Exception as e:
            print(f"Attempt {attempt + 1} failed for {restaurant_name}:")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            if hasattr(e, 'response'):
                print(f"Response status: {e.response.status_code}")
                print(f"Response body: {e.response.text}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                # If all retries failed, create a basic JSON object with what we have
                data = {
                    "restaurant_name": restaurant_name,
                    "url": url,
                    "daily_special": daily_special_value,
                    "price": price if price else "159 kr",
                    "included_items": included_items if included_items else [],
                    "lunch_hours": "11:30-14:00",
                    "special_notes": "",
                    "day_of_week": current_day,
                    "date": formatted_date
                }
                return json.dumps(data)

def save_to_json(data):
    """
    Save data to JSON file with error handling
    """
    try:
        # First try to read existing data
        existing_data = []
        if os.path.exists('lunch_data.json'):
            with open('lunch_data.json', 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        
        # Only save if we have new data
        if data:
            with open('lunch_data.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("Data saved to lunch_data.json")
        else:
            print("No new data to save, keeping existing data")
            # Restore existing data if we have no new data
            with open('lunch_data.json', 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving to JSON: {e}")
        # If we have existing data, restore it
        if existing_data:
            with open('lunch_data.json', 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)
            print("Restored existing data due to error")
        else:
            # If no existing data, save empty array
            with open('lunch_data.json', 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
            print("Created empty JSON file due to error")

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
    save_to_json(all_lunch_data)
    print("Lunch menu update completed!")

if __name__ == "__main__":
    main()

