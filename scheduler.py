import schedule
import time
from restaurant_scraper import main as update_lunch_menu
from lunch_deal_sender import LunchDealSender
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def scheduled_update():
    """Function to run the lunch menu update and send email"""
    try:
        # Update the lunch menu
        update_lunch_menu()
        
        # Send the email
        sender = LunchDealSender()
        sender.send_lunch_deals()
        
    except Exception as e:
        print(f"Error in scheduled update: {e}")

def main():
    # Schedule the daily update at 6:00 AM
    schedule.every().day.at("06:00").do(scheduled_update)
    
    # Run the initial update
    scheduled_update()
    
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main() 