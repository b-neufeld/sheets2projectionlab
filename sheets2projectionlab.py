# BNeufeld

#importing required libraries
import logging
import os
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# Set up logging configuration
logging.basicConfig(
    level=logging.DEBUG,  # Set level to DEBUG for verbose output
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Get Environment Variables (reference: https://www.tutorialspoint.com/how-to-pass-command-line-arguments-to-a-python-docker-container)
def get_env_variable(var_name, default=None):
    value = os.getenv(var_name, default)
    if not value:
        logging.error(f"Environment variable {var_name} is missing or invalid.")
        exit()
    return value

# Validate data pulled from Google Sheets
def validate_update_commands(commands):
    for command in commands:
        if not command.startswith("window.projectionlabPluginAPI.updateAccount"):
            logging.warning(f"Invalid command detected: {command}")
            commands.remove(command)
    return commands

google_auth_json_filename = get_env_variable("GOOGLE_JSON_KEY_FILENAME")
pl_email = get_env_variable("PL_EMAIL")
pl_pass = get_env_variable("PL_PASSWORD")
projectionlab_url = get_env_variable("PL_URL")
sheets_filename = get_env_variable("SHEETS_FILENAME")
sheets_worksheet = get_env_variable("SHEETS_WORKSHEET")
time_delay = int(get_env_variable("SHEETS_WORKSHEET",10))

####################################
### GRAB DATA FROM GOOGLE SHEETS ###
#################################### 

logging.info("Starting data retrieval from Google Sheets.")

#Good chunk of this is borrwed from https://www.analyticsvidhya.com/blog/2020/07/read-and-update-google-spreadsheets-with-python/
# define the scope
scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']

# Check that key file exists and if not, exit the script. 
keyfile_path = os.path.join("/keys", google_auth_json_filename)
try:
    with open(keyfile_path, 'r') as file:
        logging.info("Google key file exists. Proceeding...")
except FileNotFoundError:
    logging.error("The expected key file JSON was not found. Exiting...")
    exit()

# add credentials to the account
creds = ServiceAccountCredentials.from_json_keyfile_name(keyfile_path, scope)

# authorize the clientsheet 
logging.debug("Authorizing Google credentials...")
client = gspread.authorize(creds)

# get the instance of the Spreadsheet
logging.debug("Opening Google Sheets spreadsheet...")
sheet = client.open(sheets_filename)

logging.debug("Accessing specified worksheet...")
sheet_instance = sheet.worksheet(sheets_worksheet)

# List of accounts and balances to update
# Should be a list of values matching this string:window.projectionlabPluginAPI.updateAccount('xxxxxxxxx-accountid', { balance: 33019.78 }, { key: 'xxxxxxxxxxx-apikey' })
# Assumes Column 4 and that people are matching my template. 
logging.debug("Fetching update list from Google Sheets...")
update_list = sheet_instance.col_values(4)
update_list = validate_update_commands(update_list[1:])  # Trim the header row and validate
logging.info(f"Retrieved {len(update_list)} entries from the update list.")

# For debugging: be cautious uncommenting this line for debugging as someone eventually using it may 
# accidentally share their PL private keys in a screenshot or something. 
# print("Example Google Sheets output for debugging: "+update_list[1])

#########################################
### POPULATE PROJECTIONLAB W/ BROWSER ###
#########################################

# Here is a good reference on how Monarch Money updates PL. https://github.com/georgeck/projectionlab-monarchmoney-import
# Here is a site about using Selenium to open a browser and log in: https://medium.com/@kikigulab/how-to-automate-opening-and-login-to-websites-with-python-6aeaf1f6ae98

# create selenium browser. Options hopefully fix a crashing issue (https://stackoverflow.com/a/53073789)
logging.info("Initializing Selenium WebDriver...")
chrome_options = Options()
chrome_options.add_argument('--headless=new')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')

try:
    logging.debug("Starting Chrome WebDriver...")
    driver = webdriver.Chrome(options=chrome_options)

    logging.debug(f"Navigating to ProjectionLab URL: {projectionlab_url}")
    driver.get(projectionlab_url)

    logging.info(f"Waiting {time_delay} seconds for the page to load.")
    time.sleep(time_delay)

    logging.debug("Clicking Sign In with Email button...")
    driver.find_element(By.XPATH, '//*[@id="auth-container"]/button[2]').click()
    time.sleep(1)

    logging.debug("Entering email address...")
    email_input = driver.find_element(By.XPATH, '//*[@id="input-6"]')
    email_input.clear()
    email_input.send_keys(pl_email)
    time.sleep(1)

    logging.debug("Entering password...")
    password_input = driver.find_element(By.XPATH, '//*[@id="input-8"]')
    password_input.clear()
    password_input.send_keys(pl_pass)
    time.sleep(1)

    logging.debug("Clicking Sign In button...")
    driver.find_element(By.XPATH, '//*[@id="auth-container"]/form/button').click()
    logging.info(f"Waiting {time_delay} seconds for login to complete.")
    time.sleep(time_delay)

    logging.info("Updating accounts in ProjectionLab...")
    for command in update_list:
        logging.debug(f"Executing command: {command}")
        driver.execute_script(command)
        logging.info(f"Successfully executed command, sleeping {time_delay} seconds.")
        time.sleep(time_delay)
    
    logging.info("All updates completed successfully.")

finally:
    logging.info("Closing WebDriver.")
    driver.quit()