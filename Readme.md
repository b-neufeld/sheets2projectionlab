
# Overview 
This Docker container contains a cron job that calls a Python script that runs evert five minutes*, grabbing a bunch of data from a Google Sheet that you own, and dumping it into ProjectionLab. 

*Five minutes is somewhat arbitrary but allows for some easy visibility of if the container is working or not (e.g. you don't have to wait 24 hours to see a value update).

The script authenticates with Google Drive, grabs values from your Sheet, spins up an instance of Selenium web browser, mimics the clicks to log into ProjectionLab with your credentials, and posts updated balances to the Selenium browser console via the ProjectionLab API. 

# Limitations: 
- Only tested on a self-hosted ProjectionLab install with email/password login (not Google credentials)
- Not sure how to handle Google authentication (only works if you sign in with an email & password)

## Disclaimer 
I am not a professional programmer. I'm more of a cobbler-together-of-Stackoverflow answers. It is certain thisis not the most efficient or sustainable solution - but it'll work for me! I don't have a ton of time to spend on this, however, I do like learning and hacking away on things, so constructive feedback is welcome. 

# TODO:
- Better documentation / screenshots 
- Figure out how to test with non-self-hosted users and/or using Google authentication, if there is interest. 

# Instructions
## Set up Service User on Google Account (one-time)
1. Log into [Google Cloud Console](https://console.cloud.google.com/apis/dashboard) with your Google account
2. Create a new Project, you can call it "Expose Sheets to ProjectionLab"
3. Navigate to Enable APIs and Services 
4. Enable Google Sheets API and Google Drive API 
5. Create a new set of credentials with Owner permissions (can call it something like yourname+sheets2projectionlab). Make a note of the full email account associated with it. 
6. Navigate to the Keys tab, Create a new set of Keys, and download as JSON. Keep these credentials secure as they can access your account! 

## Grab Account ID's from ProjectionLab (one-time, or whenever new account(s) are added)
1. Log into ProjectionLab
2. User icon in top-right, Account Settings, Plugins
3. Enable Plugins and copy your API Key. 
4. Press F12 to open the developer console in your browser (while on the ProjectionLab page), and run the following script that gives you the `id` and name of your accounts ([script credit](https://github.com/georgeck/projectionlab-monarchmoney-import?tab=readme-ov-file#step-2-get-the-accountid-of-projectionlab-accounts-that-you-want-to-import)]): 

```javascript
const exportData = await window.projectionlabPluginAPI.exportData({ key: 'YOUR_PL_API_KEY' });

// Merge the list of savings accounts, investment accounts, assets and debts
const plAccounts = [...exportData.today.savingsAccounts, ...exportData.today.investmentAccounts,
                    ...exportData.today.assets, ...exportData.today.debts];

plAccounts.forEach(account => {
    console.log(account.id, account.name)
});
```
Copy the information returned to extract your account IDs. 

## Prepare your Google spreadsheet
1. Share your Google spreadsheet (that you want to sync to PL) with the service account you just created. 
2. Create a new tab for syncing to ProjectionLab. 
3. Create the following four columns:

- A: Account Name (friendly name, just for your reference, helps if this matches PL account name)
- B: Current Amount (doing whatever spreadsheet magic required to get numeric dollar values in this column)
- C: ProjectionLab Account ID
- D: The formula (below) which creates a javascript projectionlab API update command for each account. These will be read by the script and pushed to a browser console to update account balances based on your Google Sheet. 

`=CONCATENATE("window.projectionlabPluginAPI.updateAccount('",C2,"', { balance: ",B2," }, { key: 'YOUR_PROJECTIONLAB_API_KEY' })")`

## Setting up the Docker Image 
Docker Compose Template:
```yaml
services:
  sheets2projectionlab:
    container_name: sheets2projectionlab
    image: ghcr.io/b-neufeld/sheets2projectionlab:latest 
    volumes:
      # Map the folder where you have saved the Google .json key file. 
      # If running on windows this could look like this:
      # - C:\Users\Brahm\Desktop\sheets2projectionlab\private:/keys
      # If running on on linux this could look like this: 
      - /mnt/external/folder/with/authfile:/keys
      # ^ For clarity, only one volume mapping to the /keys folder in the container is required. 
    environment:
      - GOOGLE_JSON_KEY_FILENAME=googlejsonkeyfilename.json
      - PL_EMAIL=your_email@domain
      - PL_PASSWORD=your_pl_password
      - PL_URL=http://172.16.1.98:8099/register
      - SHEETS_FILENAME=My Financial Plan
      - SHEETS_WORKSHEET=PLsync
      - TIME_DELAY=10
    restart: unless-stopped
```
Notes:
- The ProjectionLab URL must be the /register login page, as the Selenium script is looking for specific buttons to click to log in. 
- `SHEETS_FILENAME` and `SHEETS_WORKSHEET` should be self-explanatory. Spaces are OK here, e.g. `SHEETS_FILENAME=Financial Plan`
- `TIME_DELAY` is the number of seconds between opening the PL_URL and attempting to enter the username/password. This should not be too small (10 seconds is default) or the script will try and log in or publish values before the content renders in the browser.
- If you use Docker Run instead of Docker Compose, see https://www.decomposerize.com/ or a similar site.