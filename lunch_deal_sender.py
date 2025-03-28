import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LunchDealSender:
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER')
        self.smtp_port = int(os.getenv('SMTP_PORT'))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.sender_email = os.getenv('SENDER_EMAIL')
        self.recipient_email = os.getenv('RECIPIENT_EMAIL')

    def send_lunch_deals(self, deals):
        """Send lunch deals via email"""
        # Create message
        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = self.recipient_email
        msg['Subject'] = f"Today's Lunch Deals - {datetime.now().strftime('%Y-%m-%d')}"

        # Create email body
        body = "🍽️ Today's Lunch Deals 🍽️\n\n"
        
        for restaurant, deal in deals.items():
            body += f"📍 {restaurant}\n"
            body += f"🍴 {deal['description']}\n"
            body += f"💰 {deal['price']}\n\n"
            body += "-" * 40 + "\n\n"

        msg.attach(MIMEText(body, 'plain'))

        try:
            # Create SMTP session
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            print("Email sent successfully!")
            return True
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return False

# Example usage
if __name__ == "__main__":
    sender = LunchDealSender()
    
    # Example deals
    deals = {
        "The Tasty Corner": {
            "description": "Special Lunch Menu: Grilled Salmon with Seasonal Vegetables",
            "price": "15.99€"
        },
        "Pizza Place": {
            "description": "Lunch Special: Margherita Pizza + Drink",
            "price": "12.99€"
        }
    }
    
    sender.send_lunch_deals(deals) 