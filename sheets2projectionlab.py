# BNeufeld 2024-12-06

# Extra console output for debugging
debug=True

#importing the required libraries
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options #required to fix crashes?
from selenium.webdriver.chrome.service import Service #also required
from chromedriver_py import binary_path # this will get you the path variable https://pypi.org/project/chromedriver-py/
import time
import os

# Get Environment Variables (reference: https://www.tutorialspoint.com/how-to-pass-command-line-arguments-to-a-python-docker-container)
google_auth_json_filename = os.getenv("GOOGLE_JSON_KEY_FILENAME")
pl_email = os.getenv("PL_EMAIL")
pl_pass = os.getenv("PL_PASSWORD")
projectionlab_url = os.getenv("PL_URL")
sheets_filename = os.getenv("SHEETS_FILENAME")
sheets_worksheet = os.getenv("SHEETS_WORKSHEET")
time_delay = int(os.getenv("TIME_DELAY"))

####################################
### GRAB DATA FROM GOOGLE SHEETS ###
#################################### 

#Good chunk of this is borrwed from https://www.analyticsvidhya.com/blog/2020/07/read-and-update-google-spreadsheets-with-python/
# define the scope
scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']

# add credentials to the account
creds = ServiceAccountCredentials.from_json_keyfile_name(os.path.join("/keys",google_auth_json_filename), scope)

# authorize the clientsheet 
if debug: print("Authorizing Google creds...")
client = gspread.authorize(creds)

# get the instance of the Spreadsheet
if debug: print("Opening spreadsheet...")
sheet = client.open(sheets_filename)

# Specify the name of the sheet with financial numbers 
sheet_instance = sheet.worksheet(sheets_worksheet)

# List of accounts and balances to update
# Should be a list of values matching this string:window.projectionlabPluginAPI.updateAccount('xxxxxxxxx-accountid', { balance: 33019.78 }, { key: 'xxxxxxxxxxx-apikey' })
# Assumes Column 4 and that people are matching my template. 
if debug: print("Grabbing PL values from Google Sheet...")
update_list = sheet_instance.col_values(4)
# trim the header row element
update_list = update_list[1:]

# For debugging
#print(sheet_instance.cell(col=2,row=60))
print("Example output for debugging: "+update_list[1])

#########################################
### POPULATE PROJECTIONLAB W/ BROWSER ###
#########################################

# Here is a good reference on how Monarch Money updates PL. https://github.com/georgeck/projectionlab-monarchmoney-import
# Here is a site about using Selenium to open a browser and log in: https://medium.com/@kikigulab/how-to-automate-opening-and-login-to-websites-with-python-6aeaf1f6ae98

# create selenium browser. Options hopefully fix a crashing issue (https://stackoverflow.com/a/53073789)
if debug: print("Setting Chrome/Selenium options...")
chrome_options = Options()
chrome_options.add_argument('--headless=new')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
service = Service(executable_path=binary_path)

# Chromedriver is in this folder in my image, maybe need to specify it? 
if debug: print("Starting Chrome...")
# NOTE LATE ON DEC 7: IF I REMOVE THE OPTIONS, CHROME TRIES TO START...
driver = webdriver.Chrome(service=service, options=chrome_options)

# Navigate to ProjectionLab https://www.selenium.dev/documentation/webdriver/interactions/navigation/
if debug: print("Navigating to ProjectionLab URL...")
driver.get(projectionlab_url)

if debug: print("Sleeping "+time_delay+" seconds for page load...")
time.sleep(time_delay) # Sleep for a bit 

# Click Sign In With Email button based on XPATH
if debug: print("Clicking Sign In...")
driver.find_element(By.XPATH,'//*[@id="auth-container"]/button[2]').click()
#An alternative might be find element, but kludgier: driver.find_element(By.CLASS_NAME,'d-flex.align-center.ml-n2').click()

# Enter email address
if debug: print("Entering email & password...")
email_input = driver.find_element(By.XPATH, '//*[@id="input-6"]')
email_input.clear()  # Clear field
email_input.send_keys(pl_email)

# Enter password
email_input = driver.find_element(By.XPATH, '//*[@id="input-8"]')
email_input.clear()  # Clear field
email_input.send_keys(pl_pass)

# Click Sign In Button
if debug: print("Clicking Sign In button...")
driver.find_element(By.XPATH,'//*[@id="auth-container"]/form/button').click()

if debug: print("Sleeping "+time_delay+" seconds for page load...")
time.sleep(time_delay) # Sleep for a bit 

# Interate over update list
if debug: print("Iterating over list to update PL accounts....")
for command in update_list:
    # This should be a formatted ProjectionLab API account update
    driver.execute_script(command)

if debug: print("Sleeping "+time_delay+" seconds then stopping...")
time.sleep(time_delay) # Sleep for a bit 
