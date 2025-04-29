import os
from dotenv import load_dotenv

# Loading environment variables from the .env file
load_dotenv()

# Getting the api key from the environment variable and using the API key in my code
the_api_key = os.getenv("DTK531_I2_GEMINI_AI_API_KEY")