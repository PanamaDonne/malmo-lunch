from restaurant_scraper import get_restaurant_info, save_lunch_data
from lunch_deal_sender import LunchDealSender
from datetime import datetime
import json

def format_deals_for_email(lunch_data):
    """Convert lunch data into the format expected by the email sender"""
    deals = {}
    for restaurant in lunch_data:
        deals[restaurant['restaurant_name']] = {
            'description': restaurant['daily_special'],
            'price': restaurant['price']
        }
    return deals

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
        }
    ]
    
    print(f"Starting lunch menu update for {datetime.now().strftime('%Y-%m-%d')}")
    all_lunch_data = []
    
    # Get lunch data for each restaurant
    for restaurant in restaurants:
        print(f"Getting lunch info for {restaurant['name']}...")
        restaurant_data = get_restaurant_info(restaurant['name'], restaurant['url'])
        if restaurant_data:
            all_lunch_data.append(json.loads(restaurant_data))
    
    # Save all lunch data to a JSON file
    save_lunch_data(all_lunch_data)
    
    # Format deals for email
    deals = format_deals_for_email(all_lunch_data)
    
    # Send email with the deals
    sender = LunchDealSender()
    if sender.send_lunch_deals(deals):
        print("Email sent successfully!")
    else:
        print("Failed to send email.")
    
    print("Lunch menu update completed!")

if __name__ == "__main__":
    main() 