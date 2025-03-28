# malmo-lunch
Malmö daily special 

# Malmö Lunch Deals - Technical Overview

## Core Components

### 1. Web Scraping (`restaurant_scraper.py`)
- Uses `BeautifulSoup4` for HTML parsing
- Implements custom scrapers for each restaurant
- Handles retries and error cases
- Saves data in JSON format

### 2. Email System (`lunch_deal_sender.py`)
- Uses SMTP for email delivery
- Gmail integration with app-specific passwords
- HTML-formatted emails with emojis
- Error handling and logging

### 3. Scheduling (`scheduler.py`)
- Uses `schedule` library for task management
- Runs daily at 6:00 AM
- Handles both scraping and email sending
- Continuous monitoring with 60-second intervals

### 4. Web Interface (`app.py` & `index.html`)
- Flask-based web server
- Bootstrap for responsive design
- Auto-refreshing content
- Mobile-friendly interface

## Data Flow
1. Scraper collects daily lunch deals
2. Data saved to `lunch_data.json`
3. Email sent to subscribers
4. Web interface displays current deals

## Automation
- GitHub Actions for automated updates
- Scheduled daily runs
- Automatic error reporting
- Version control integration


