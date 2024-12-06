# ⚠ Work in Progress ⚠
I am working on making a Docker container to sync a Google Sheet to ProjectionLab. 

Stay tuned for updates! 

# Overview 
This Docker container contains a Python script that runs on a daily schedule, grabbing a bunch of data from a Google Sheet that you own, and dumping it into ProjectionLab. 

It does this by authenticating with Google, grabbing values from your spreadsheet, spinning up an instance of Selenium web browser, logging into ProjectionLab with your credentials, and posting updated information to the Selenium browser console via the PL API. 

# Limitations: 
- Only tested on a self-hosted install with email/password login (not Google credentials)
- Not sure how to handle Google authentication 

# Instructions
## Set up Service User on Google Account
1. Log into [Google Cloud Console](https://console.cloud.google.com/apis/dashboard) with your Google account
2. Create a new Project, you can call it "Expose Sheets to ProjectionLab"
3. Navigate to Enable APIs and Services 
4. Enable Google Sheets API and Google Drive API 
5. Create a new set of credentials with Owner permissions (can call it something like yourname+sheets2projectionlab). Make a note of the full email account associated with it. 
6. Navigate to the Keys tab, Create a new set of Keys, and download as JSON. Keep these credentials secure as they can access your account! 

## Grab Account ID's from ProjectionLab
1. Log into ProjectionLab
2. User icon in top-right, Account Settings, Plugins
3. Enable Plugins and copy your API Key. 
4. Press F12 to open the developer console in your browser (while on the ProjectionLab page), and run the following script that gives you the `id` and name of your accounts: 

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
⚠ Work in Progress ⚠
Docker Compose Template:
```yaml
version: "3.8"
services:
  sheets2projectionlab:
    container_name: sheets2projectionlab
    image: ### TBD
    environment:
      - GOOGLE_JSON_KEY=/path/to/googlejsonkey.json
      - PL_EMAIL=your_email@domain
      - PL_PASSWORD=your_pl_password
      - PL_URL=
      - SHEETS_FILENAME=
      - SHEETS_WORKSHEET=
      - TIME_DELAY=10
    restart: unless-stopped
```