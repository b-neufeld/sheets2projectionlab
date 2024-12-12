# BNeufeld

#importing required libraries
import logging
import os
import time
import gspread
import re
from oauth2client.service_account import ServiceAccountCredentials
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_env_variable(var_name, default=None):
    # Get Environment Variables (reference: https://www.tutorialspoint.com/how-to-pass-command-line-arguments-to-a-python-docker-container)
    value = os.getenv(var_name, default)
    if not value:
        logging.error(f"Environment variable {var_name} is missing or invalid.")
        exit()
    return value

def validate_update_commands(commands):
    # Validate data pulled from Google Sheets
    for command in commands:
        if not command.startswith("window.projectionlabPluginAPI.updateAccount"):
            logging.warning(f"Invalid command detected: {command}")
            commands.remove(command)
    return commands

def redact_api_key(command):
    # Use a regular expression to find and replace the `key` field (remove sensitive information from logging)
    redacted_command = re.sub(r"(key: ')([^']+)(')", r"\1***REDACTED***\3", command)
    return redacted_command

def main(): 
    # Set up logging configuration
    logging.basicConfig(
        level=logging.DEBUG,  # Set level to INFO for verbose output (DEBUG could expose PL creds in logs)
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    google_auth_json_filename = get_env_variable("GOOGLE_JSON_KEY_FILENAME")
    pl_email = get_env_variable("PL_EMAIL")
    pl_pass = get_env_variable("PL_PASSWORD")
    projectionlab_url = get_env_variable("PL_URL")
    sheets_filename = get_env_variable("SHEETS_FILENAME")
    sheets_worksheet = get_env_variable("SHEETS_WORKSHEET")
    time_delay = int(get_env_variable("TIME_DELAY",10))

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
    logging.info("Authorizing Google credentials...")
    client = gspread.authorize(creds)

    # get the instance of the Spreadsheet
    logging.info("Opening Google Sheets spreadsheet...")
    sheet = client.open(sheets_filename)

    logging.info("Accessing specified worksheet...")
    sheet_instance = sheet.worksheet(sheets_worksheet)

    logging.info(f"Waiting {time_delay} seconds to (hopefully) ensure the sheet updates.")
    time.sleep(time_delay)

    logging.info(f"Writing dummy value to cell A1 to attempt to trigger a spreadsheet update")

    # Trigger refresh of functions like =GOOGLEFINANCE() by updating a dummy cell (per ChatGPT)
    dummy_cell = "A1" #A1 should be a header cell, OK to overwrite
    original_value = sheet_instance.acell(dummy_cell).value  # Backup original value
    sheet_instance.update_acell(dummy_cell, "Refresh Trigger")
    time.sleep(1)
    sheet_instance.update_acell(dummy_cell, original_value)  # Restore original value
    logging.info(f"Waiting {time_delay} after dummy value write (hopefully) ensure the sheet updates.")
    time.sleep(time_delay)

    # List of accounts and balances to update
    # Should be a list of values matching this string:window.projectionlabPluginAPI.updateAccount('xxxxxxxxx-accountid', { balance: 33019.78 }, { key: 'xxxxxxxxxxx-apikey' })
    # Assumes Column 4 and that people are matching my template. 
    logging.info("Fetching updated balances from Google Sheets...")
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
        logging.info("Starting Chrome WebDriver...")
        driver = webdriver.Chrome(options=chrome_options)

        logging.info(f"Navigating to ProjectionLab URL: {projectionlab_url}")
        driver.get(projectionlab_url)

        logging.info(f"Waiting {time_delay} seconds for the page to load.")
        time.sleep(time_delay)

        logging.info("Clicking Sign In with Email button...")
        button = driver.find_element(By.XPATH, '//*[@id="auth-container"]/button[2]')
        driver.execute_script("arguments[0].click();", button) #https://stackoverflow.com/a/58378714
        time.sleep(1)

        logging.info("Entering email address...")
        try:
            email_input = driver.find_element(By.XPATH, '//*[@id="input-7"]')  # input-7 on projectionlab.com
        except:
            try:
                email_input = driver.find_element(By.XPATH, '//*[@id="input-6"]')  # input-6 on self-hosted
            except:
                logging.info("Error finding email input...")
        email_input.clear()
        email_input.send_keys(pl_email)
        time.sleep(1)

        logging.info("Entering password...")
        try:
            password_input = driver.find_element(By.XPATH, '//*[@id="input-9"]') # input-9 on projectionlab.com
        except: 
            try:
                password_input = driver.find_element(By.XPATH, '//*[@id="input-8"]') # input-8 on self-hosted
            except:
                 logging.info("Error finding password input...")   
        password_input.clear()
        password_input.send_keys(pl_pass)
        time.sleep(1)

        logging.info("Clicking Sign In button...")
        button = driver.find_element(By.XPATH, '//*[@id="auth-container"]/form/button')
        driver.execute_script("arguments[0].click();", button) #https://stackoverflow.com/a/58378714
        logging.info(f"Selenium WebDriver Wait function until login is complete and page loads...")
        #time.sleep(time_delay)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body"))) # will this fix script execution?

        api_status = driver.execute_script("return typeof window.projectionlabPluginAPI;")
        logging.info(f"API Status: {api_status}")

        logging.info("Updating accounts in ProjectionLab...")
        for command in update_list:
            redacted_command = redact_api_key(command) # hide private info from logging
            logging.info(f"Executing command: {redacted_command}")
            driver.execute_script(command)
            logging.info("Successfully executed command. Sleeping 1 sec")
            time.sleep(1)

        
        logging.info("All updates completed successfully.")

    finally:
        logging.info("Closing WebDriver.")
        driver.quit()

if __name__ == "__main__":
    main()