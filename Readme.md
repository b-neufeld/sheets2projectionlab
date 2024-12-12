
# Overview 
This Docker container contains a cron job that calls a Python script that runs every five minutes*. The script grabs a bunch of data from your Google Sheet and dumps it into ProjectionLab. 

\*Five minutes is high-frequency for planning software with daily balance logs and yearly simulation horizons, but why not? I picked this frequency because it visibly demonstrates the script is working - no need to wait 24 hours to see. And if you're like me, you're always running PL scenarios based on your finances *right now*.

The script authenticates with Google Drive, grabs values from your Sheet, spins up an instance of Selenium web browser, mimics the clicks to log into ProjectionLab with your credentials, and posts updated balances to the Selenium browser console via the ProjectionLab API. 

# Limitations: 
- Only tested on a self-hosted ProjectionLab install with email/password login.
  - **Currently not working on ProjectionLab.com. I am tinkering with how to resolve this,**
- Doesn't handle Google authentication for login. If you sign in this way, go into your account settings and enable an email/password combination as well.
- If you have more than 200 accounts in ProjectionLab for some reason, there's a risk that the script will take longer to execute than the 5-minute cron job that triggers it (based on about 60 seconds of "prep" and 1 second per account update). Workarounds: Run 2 containers with <200 accounts each, or build your own image and change the duration of the cron job in the Dockerfile. 

## Disclaimer 
I am not a professional programmer. I'm a cobbler-together-of-Stackoverflow answers. Certainly there are more elegant solutions possible - but this is working for me, and I wanted to share! I may be time constrained in how far this develops, however, I do like learning and hacking away on things, so constructive feedback is welcome. 

# Instructions
## Set up Service User on Google Account (one-time)
1. Log into [Google Cloud Console](https://console.cloud.google.com/apis/dashboard) with your Google account.
2. Create a new Project, you can call it "Expose Sheets to ProjectionLab".
3. Navigate to Enable APIs and Services.
4. Enable Google Sheets API and Google Drive API.
5. Create a new set of credentials with Owner permissions (can call it something like yourname+sheets2projectionlab). Make a note of the full email account associated with it.
6. Navigate to the Keys tab, Create a new set of Keys, and download as JSON. Keep these credentials secure as they can access your account! 

## Grab Account ID's from ProjectionLab (one-time, or whenever new account(s) are added)
1. Log into ProjectionLab.
2. User icon in top-right, Account Settings, Export Data (just in case!!)
3. User icon in top-right, Account Settings, Plugins.
4. Enable Plugins and copy your API Key. 
5. Press F12 to open the developer console in your browser (while on the ProjectionLab page), and run the following script that gives you the `id` and name of your accounts ([script credit](https://github.com/georgeck/projectionlab-monarchmoney-import?tab=readme-ov-file#step-2-get-the-accountid-of-projectionlab-accounts-that-you-want-to-import)]): 

```javascript
const exportData = await window.projectionlabPluginAPI.exportData({ key: 'YOUR_PL_API_KEY' });

// Merge the list of savings accounts, investment accounts, assets and debts
const plAccounts = [...exportData.today.savingsAccounts, ...exportData.today.investmentAccounts,
                    ...exportData.today.assets, ...exportData.today.debts];

plAccounts.forEach(account => {
    console.log(account.id, account.name)
});
```
Copy the information returned by the console to extract your ProjectionLab account IDs. 

## Prepare your Google spreadsheet
1. Share your Google spreadsheet (that you want to sync to PL) with the Google service account you just created. **Important**: Share with Editor permissions. The script writes a temporary value to the Sheet (then reverts the change) which triggers a refresh of the Sheet. Otherwise, stale data could be queried. 
2. Create a new, dedicated tab to sync to ProjectionLab. 
3. Create the following four columns. Column headers are required as the script truncates the first row:

- A: Account Name (friendly name, just for your reference, helps if this matches PL account name).
- B: Balance (doing whatever spreadsheet magic is required to populate dollars in this column).
- C: ProjectionLab Account ID (from previous step).
- D: The formula (below) in cell D2 and applied to all rows. This creates a javascript ProjectionLab API update command for each account balance. 

`=CONCATENATE("window.projectionlabPluginAPI.updateAccount('",C2,"', { balance: ",B2," }, { key: 'YOUR_PROJECTIONLAB_API_KEY' })")`

Screenshot of example Google Sheet (with random balances and blanked-out ProjectionLab API key):
![image](https://github.com/user-attachments/assets/92e0259d-2b18-4504-91f9-f97da66d83a2)

#### If you have a ProjectionLab.com account and the Docker container doesn't work...
You COULD simply copy and paste the contents of Column D into your browser's development terminal for much-faster-than-manual updates. 

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
      # Should be https://app.projectionlab.com/login for non-self-hosted (not tested)
      - PL_URL=http://172.16.1.98:8099/register
      - SHEETS_FILENAME=My Financial Plan
      - SHEETS_WORKSHEET=PLsync
      - TZ=America/Regina
      - TIME_DELAY=10
    restart: unless-stopped
```
Notes:
- The ProjectionLab URL must point to the /register login page, as the Selenium script is looking for specific buttons to click to log in. 
- `SHEETS_FILENAME` and `SHEETS_WORKSHEET` should be self-explanatory. Spaces are OK here, e.g. `SHEETS_FILENAME=Financial Plan`
- `TIME_DELAY` is the number of seconds between opening the PL_URL and attempting to enter the username/password. This should not be too small (10 seconds is default) or the script will try and log in or publish values before the content renders in the browser.
- Time zone `TZ` is required to ensure the Docker container is running in the same time zone as your ProjectionLab instance. 
- If you use Docker Run instead of Docker Compose, see https://www.decomposerize.com/ or a similar site.

## How do I know it's working? 
Every 5 minutes, the log output of the container will show the steps the script has taken:
![image](https://github.com/user-attachments/assets/2fac639f-e465-41b3-bc32-028f300a4d47)
I've observed the script fail somewhat randomly and I believe this has to do with spinning up a Selenium browser and for some reason, it is slow to load my self-hosted ProjectionLab instance, and the script times out.  
