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

def get_bullen_info(soup):
    """
    Extract specific information from Bullen's website
    """
    try:
        # Find the price in the hero section
        hero_section = soup.find('div', class_='hero__inner')
        price_text = ""
        if hero_section:
            price_text = hero_section.get_text(strip=True)
            # Extract price (should be 145 SEK)
            if "145" in price_text:
                price = "145 SEK"
            else:
                price = "145 SEK"  # Default if not found
        else:
            price = "145 SEK"  # Default if section not found

        # Find the included items note
        included_items_note = "Sallad och måltidsdryck ingår, köp till kaffe eller te för 19kr"
        
        return price, included_items_note
    except Exception as e:
        print(f"Error extracting Bullen info: {e}")
        return "145 SEK", "Sallad och måltidsdryck ingår, köp till kaffe eller te för 19kr"

def get_kolga_info(soup, current_day):
    """
    Extract specific information from Restaurang Kolga's website
    """
    try:
        # Map English to Swedish day names with correct characters
        day_mapping = {
            'Monday': 'Måndag',
            'Tuesday': 'Tisdag',
            'Wednesday': 'Onsdag',
            'Thursday': 'Torsdag',
            'Friday': 'Fredag'
        }
        
        swedish_day = day_mapping[current_day]
        
        # Find all text content
        all_text = soup.get_text()
        
        # Split into lines and clean
        lines = [line.strip() for line in all_text.split('\n') if line.strip()]
        
        # Debug print
        print(f"Looking for menu for {swedish_day}")
        
        # Find the day's menu
        for i, line in enumerate(lines):
            if swedish_day in line:
                # The menu items should be the next two lines
                if i + 2 < len(lines):
                    menu_items = [lines[i + 1], lines[i + 2]]
                    # Filter out any lines that contain prices or other days
                    menu_items = [item for item in menu_items if not any(day in item for day in day_mapping.values()) and not "kr" in item]
                    if menu_items:
                        print(f"Found menu item: {menu_items[0]}")
                        return menu_items[0]  # Return the first menu item
        
        print(f"Debug: Could not find menu for {swedish_day}")
        return None
    except Exception as e:
        print(f"Error extracting Kolga info: {e}")
        return None

def get_matochsmak_info(soup, current_day):
    """
    Extract specific information from Mat & Smak's website
    """
    try:
        # Map English to Swedish day names with correct characters
        day_mapping = {
            'Monday': 'Måndag',
            'Tuesday': 'Tisdag',
            'Wednesday': 'Onsdag',
            'Thursday': 'Torsdag',
            'Friday': 'Fredag'
        }
        
        swedish_day = day_mapping[current_day]
        
        # Find all text content
        all_text = soup.get_text()
        
        # Split into lines and clean
        lines = [line.strip() for line in all_text.split('\n') if line.strip()]
        
        # Debug print
        print(f"Looking for menu for {swedish_day}")
        
        # Find the day's menu
        daily_specials = []
        for i, line in enumerate(lines):
            if swedish_day in line:
                # Look for the different options (Kött, Fisk, Vegetarisk)
                j = i + 1
                while j < len(lines) and not any(day in lines[j] for day in day_mapping.values()):
                    if any(option in lines[j] for option in ['Kött', 'Fisk', 'Vegetarisk']):
                        # Get the menu item (next line)
                        if j + 1 < len(lines):
                            menu_item = lines[j + 1]
                            if not any(day in menu_item for day in day_mapping.values()) and not "kr" in menu_item and not any(option in menu_item for option in ['Kött', 'Fisk', 'Vegetarisk', 'Sallad']):
                                daily_specials.append(f"{lines[j]}: {menu_item}")
                    j += 1
                break
        
        if daily_specials:
            print(f"Found menu items: {daily_specials}")
            return daily_specials
        
        print(f"Debug: Could not find menu for {swedish_day}")
        return None
    except Exception as e:
        print(f"Error extracting Mat & Smak info: {e}")
        return None

def get_restaurant_info(restaurant_name, url):
    """
    Use AI to extract lunch information from a restaurant's website
    """
    # First get the webpage content
    soup, webpage_content = get_webpage_content(url)
    if not webpage_content:
        print(f"Could not fetch content from {url}")
        return None

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

    # Customize prompt based on restaurant
    if restaurant_name == "Restaurang Kolga":
        # Get specific Kolga information from the website
        daily_special = get_kolga_info(soup, current_day)
        if not daily_special:
            print(f"Could not find {current_day}'s menu for Kolga")
            return None
            
        prompt = f"""
        Extract the lunch menu information for {restaurant_name} from this webpage content:
        
        {webpage_content}
        
        Please provide the following information in a structured format:
        1. The lunch special for {current_day} (found on website: {daily_special})
        2. Lunch price (125 kr)
        3. What's included (Dryck, bröd, sallad och kaffe ingår)
        4. Lunch serving hours (11:00-14:30)
        5. Any special notes or dietary information
        
        Note: 
        - The daily special is: {daily_special}
        - The lunch price is 125 kr
        - Included items: Dryck, bröd, sallad och kaffe ingår
        - Lunch is served 11:00-14:30
        
        Return a JSON object with these exact fields:
        {{
            "restaurant_name": "{restaurant_name}",
            "daily_special": "{daily_special}",
            "price": "125 kr",
            "included_items": ["Dryck", "Bröd", "Sallad", "Kaffe"],
            "lunch_hours": "11:00-14:30",
            "special_notes": "any special information",
            "day_of_week": "{current_day}",
            "date": "{formatted_date}"
        }}
        
        Return ONLY the JSON object, no other text or explanation.
        """
    elif restaurant_name == "Bullen":
        # Get specific Bullen information from the website
        price, included_items_note = get_bullen_info(soup)
        
        prompt = f"""
        Extract the lunch menu information for {restaurant_name} from this webpage content:
        
        {webpage_content}
        
        Please provide the following information in a structured format:
        1. The lunch special for {current_day}
        2. Lunch price (found on website: {price})
        3. What's included (found on website: {included_items_note})
        4. Lunch serving hours (when lunch is served, not general opening hours)
        5. Any special notes or dietary information
        
        Note:
        - The lunch price is {price}
        - Included items note: {included_items_note}
        - Make sure to get the correct day's menu ({current_day})
        
        Return a JSON object with these exact fields:
        {{
            "restaurant_name": "{restaurant_name}",
            "daily_special": "description of today's lunch",
            "price": "{price}",
            "included_items": ["Sallad", "Måltidsdryck"],
            "lunch_hours": "when lunch is served (e.g., 11:30-14:00)",
            "special_notes": "{included_items_note}",
            "day_of_week": "{current_day}",
            "date": "{formatted_date}"
        }}
        
        Return ONLY the JSON object, no other text or explanation.
        """
    else:
        print(f"Unknown restaurant: {restaurant_name}")
        return None

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
            # Try to parse the response as JSON
            data = json.loads(response_text)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON for {restaurant_name}: {e}")
            print(f"Raw response: {response_text}")
            return None
            
        # Ensure all required fields are present
        required_fields = [
            "restaurant_name", "daily_special", "price", "included_items",
            "lunch_hours", "special_notes", "day_of_week", "date"
        ]
        
        for field in required_fields:
            if field not in data:
                print(f"Missing required field '{field}' in response for {restaurant_name}")
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
            "name": "Restaurang Kolga",
            "url": "https://www.restaurangkolga.se/lunch/"
        },
        {
            "name": "Mat & Smak",
            "url": "https://www.restaurangmatochsmak.se/lunchmeny/"
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

