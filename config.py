from dotenv import load_dotenv
from os import getenv

# Load the environment from the .env file to the current environment.
load_dotenv()


# Get the variable environment 'TOKEN' and 'ADMIN_IDs'
BOT_TOKEN = getenv('BOT_TOKEN')
ADMIN_IDs = getenv('ADMIN_ID').split(',')
print(ADMIN_IDs)
MODEL = getenv('MODEL')

# Set the values for the local API
temperature = 0.7  # Default value is 0.7
repeat_penalty = 1.0  # Default value is 1.0
presence_penalty = 0.5  # Default value is 0.5
frequency_penalty = 0.5  # Default value is 0.5
top_p = 0.9  # Default value is 0.9

