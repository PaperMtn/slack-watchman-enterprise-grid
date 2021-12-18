<img src="https://i.imgur.com/86TiciX.png" width="550">

# Slack Watchman for Enterprise Grid

Slack Watchman for Enterprise Grid uses Slack’s API to search a Slack Enterprise for:

- API Keys, Tokens & Service Accounts
  - AWS, Azure, GCP, Google API, Slack (keys & webhooks), Twitter, Facebook, GitHub
  - Generic Private keys
  - Access Tokens, Bearer Tokens, Client Secrets, Private Tokens
- Files
  - Certificate files
  - Potentially interesting/malicious/sensitive files (.docm, .xlsm, .zip etc.)
  - Executable files
  - Keychain files
  - Config files for popular services (Terraform, Jenkins, OpenVPN and more)
- Personal Data
  - Leaked passwords
  - Passport numbers, Dates of birth, Social security numbers, National insurance numbers, Drivers licence numbers (UK), Individual Taxpayer Identification Number
  - CVs, salary information
- Financial data
  - Paypal Braintree tokens, Bank card details, IBAN numbers, CUSIP numbers
  - Budget files
  
Slack Watchman looks for this exposed data across all workspaces in the Enterprise, in the following locations:
- Public channels
- Private channels
- Draft messages
- Slack connect channels


## Usage
```
usage: slack-watchman-eg [-h] [--hours HOURS] [--minutes MINUTES] [--version] [--users] [--workspaces] [--tombstone]

Monitoring your Slack Enterprise Grid for sensitive information

optional arguments:
  -h, --help         show this help message and exit
  --hours HOURS      How far back to search in whole hours between 1-24. Defaults to 1 if no acceptable value given
  --minutes MINUTES  How far back to search in whole minutes between 1-60
  --cores CORES      Number of cores to use between 1-12
  --version          show program's version number and exit
  --users            Find all users
  --workspaces       Find all workspaces
  --tombstone        Tombstone messages
```