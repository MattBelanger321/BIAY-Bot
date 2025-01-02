import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import json
import datetime
import asyncio
import logging
from pathlib import Path
import pytz
import os

class BibleBot:
    def __init__(self, config_path: str = "config.json"):
        # Load configuration
        self.config = self.load_config(config_path)
        self.token = self.config['token']
        self.channel_id = self.config['channel_id']
        self.json_path = Path(self.config['json_file_path'])
        self.timezone = pytz.timezone(self.config['timezone'])
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize Discord client
        intents = discord.Intents.default()
        self.client = discord.Client(intents=intents)
        self.scheduler = AsyncIOScheduler()
        
        # Set up client events
        self.client.event(self.on_ready)

    @staticmethod
    def load_config(config_path: str) -> dict:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                config = json.load(file)
                
            # Validate required fields
            required_fields = ['token', 'channel_id', 'timezone', 'json_file_path']
            for field in required_fields:
                if field not in config:
                    raise KeyError(f"Missing required field in config: {field}")
                
            return config
        except FileNotFoundError:
            raise FileNotFoundError(f"Config file not found at {config_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON format in config file: {config_path}")
        
    def load_bible_data(self) -> dict:
        """Load and validate Bible reading data from JSON file."""
        try:
            with open(self.json_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            self.logger.info(f"Successfully loaded Bible data from {self.json_path}")
            return data
        except FileNotFoundError:
            self.logger.error(f"Bible readings file not found at {self.json_path}")
            raise
        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON format in {self.json_path}")
            raise

    def format_daily_message(self, entry: dict, date: datetime.datetime) -> str:
        """Format the daily Bible reading message."""
        message = [
            f"# Bible in a Year Day {entry['day']} ({date.strftime('%B %d')}) {entry['period']}",
            "",
            "## Readings",
            "",
            f"### First Reading",
            f"{entry['first_reading']['book']} Chapter(s) {entry['first_reading']['chapters']}"
        ]
        
        if entry['second_reading'] != "none":
            message.extend([
                "",
                "### Second Reading",
                entry['second_reading']
            ])
            
        message.extend([
            "",
            "### Poem",
            f"{entry['poem']['book']} {entry['poem']['chapters']}"
        ])
        
        return "\n".join(message)

    async def send_bible_message(self):
        """Send the daily Bible reading message to Discord."""
        try:
            bible_data = self.load_bible_data()
            today = datetime.datetime.now(self.timezone)
            day_of_year = today.timetuple().tm_yday
            
            for entry in bible_data:
                if entry['day'] == day_of_year:
                    message = self.format_daily_message(entry, today)
                    channel = self.client.get_channel(self.channel_id)
                    
                    if channel is None:
                        self.logger.error(f"Could not find channel with ID {self.channel_id}")
                        return
                        
                    await channel.send(message)
                    self.logger.info(f"Successfully sent Bible reading for day {day_of_year}")
                    break
            else:
                self.logger.warning(f"No reading found for day {day_of_year}")
                
        except Exception as e:
            self.logger.error(f"Error sending Bible message: {str(e)}")

    async def on_ready(self):
        """Handler for when the bot connects to Discord."""
        self.logger.info(f'Logged in as {self.client.user}')
        
        # Schedule daily messages
        self.scheduler.add_job(
            self.send_bible_message,
            CronTrigger(
                hour=0, 
                minute=0, 
                second=0, 
                timezone=self.timezone
            )
        )
        self.scheduler.start()
        
        # Keep the bot alive
        while True:
            await asyncio.sleep(60)

    def run(self):
        """Start the bot."""
        try:
            self.client.run(self.token)
        except discord.LoginFailure:
            self.logger.error("Failed to login to Discord. Please check your token.")
        except Exception as e:
            self.logger.error(f"An error occurred while running the bot: {str(e)}")

if __name__ == "__main__":
    # Initialize and run the bot
    bot = BibleBot()
    bot.run()