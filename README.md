<img src="https://i.imgur.com/VPgx6ra.png" width="550">

# Slack Watchman for Enterprise Grid
![Python 2.7 and 3 compatible](https://img.shields.io/pypi/pyversions/slack-watchman-eg)
![PyPI version](https://img.shields.io/pypi/v/slack-watchman-eg.svg)
![License: MIT](https://img.shields.io/pypi/l/slack-watchman-eg.svg)


## About Slack Watchman for Enterprise Grid

Slack Watchman for Enterprise Grid uses the Slack Enterprise Grid DLP API to look for potentially exposed secrets and sensitive data in Slack Enterprise Grid.

**Note**: Slack Watchman for Enterprise Grid is designed for Enterprise Grid subscribers of Slack only. If you use Slack without an Enterprise subscription, you can use the standard version of [Slack Watchman](https://github.com/PaperMtn/slack-watchman)

### Features
Slack Watchman for Enterprise Grid looks for:

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
  - PayPal Braintree tokens, Bank card details, IBAN numbers, CUSIP numbers
  - Budget files
  
It looks for this exposed data across all workspaces in the Enterprise, in the following locations:
- Public channels
- Private channels
- Draft messages
- Slack connect channels
- Direct messages
- Multi-person direct messages

#### Time based searching
Slack Watchman for Enterprise Grid can search through all messages sent in your Enterprise in the previous 24 hours. Limitations in the API, and data processing bottlenecks, don't allow for any further than 24 hours to be queried. 

You can provide time periods to search for using the `--hours` and `--minutes` options at runtime. This means you can schedule running regularly, and in general little and often is the best approach.

#### Multiprocessing
Multiprocessing is used to search the potentially huge amount of data retrieved when getting all messages sent in an Enterprise. You can specify how many cores to use at runtime, and the more cores you use, the faster processing is generally done. That being said, you are still constrained by the API.

I have found the most efficient approach is to use between 8-12 cores.

You can specify cores using the optional flag `--cores` at runtime. If this flag is not set, Slack Watchman will automatically use all available cores up to a maximum of 8.
### Signatures
Slack Watchman uses custom YAML signatures to detect matches in Slack. These signatures are pulled from the central [Watchman Signatures repository](https://github.com/PaperMtn/watchman-signatures). Slack Watchman for Enterprise Grid automatically updates its signature base at runtime to ensure its using the latest signatures to detect secrets. 

## Requirements
### Slack API token
To run Slack Watchman for Enterprise Grid, you will need a Slack API access token that is authorised to use the Enterprise DLP API.

To do this, you need to create a [Slack App](https://api.slack.com/apps) and install it at the organisation level.

The app needs to have the following **User Token Scopes** added:
```
discovery:read
discovery:write
team:read
users:read
```
**Note**: `discovery:read` and `discovery:write` can only be added to an app by Slack themselves, you will need to contact your Slack CSM. They will also provide you with instructions on how to install the app at organisation level and retrieve the access token.

#### Providing token
Provide the token in the environment variable `SLACK_WATCHMAN_EG_TOKEN`

## Installation
You can install the latest stable version via pip:

`python3 -m pip install slack-watchman-eg`

Or build from source yourself:

Download the release source files, then from the top level repository run:
```shell
python3 -m pip build
python3 -m pip install --force-reinstall dist/*.whl
```

## Docker Image

Slack Watchman for Enterprise Grid is also available from the Docker hub as a Docker image:

`docker pull papermountain/slack-watchman-eg:latest`

You can then run Slack Watchman for Enterprise Grid in a container, making sure you pass the required environment variables:

```
// help
docker run --rm papermountain/slack-watchman-eg -h

// scan all
docker run --rm -e SLACK_WATCHMAN_EG_TOKENN=xoxp... papermountain/slack-watchman-eg --hours 1 --cores 8
docker run --rm --env-file .env papermountain/slack-watchman-eg --hours 1 --cores 8
```

## Usage
```
usage: slack-watchman-eg [-h] [--hours HOURS] [--minutes MINUTES] [--output {json,terminal}] [--cores CORES] [--version] [--users] [--workspaces] [--debug] [--verbose]

Monitoring your Slack Enterprise Grid for sensitive information

options:
  -h, --help            show this help message and exit
  --hours HOURS, -hr HOURS
                        How far back to search in whole hours between 1-24. Defaults to 1 if no acceptable value given
  --minutes MINUTES, -m MINUTES
                        How far back to search in whole minutes between 1-60
  --output {json,terminal}, -o {json,terminal}
                        What logging output to use - JSON formatted output, or textual outputfor reading via terminal. Default is terminal
  --cores CORES, -c CORES
                        Number of cores to use between 1-12
  --version, -v         show program's version number and exit
  --users, -u           Return all users
  --workspaces, -w      Return all workspaces
  --debug, -d           Turn on debug level logging
  --verbose, -V         Turn on more verbose output for JSON logging. This includes more fields, but is larger
```

## Other Watchman apps
You may be interested in the other apps in the Watchman family:
- [Slack Watchman](https://github.com/PaperMtn/slack-watchman)
- [GitLab Watchman](https://github.com/PaperMtn/gitlab-watchman)
- [GitHub Watchman](https://github.com/PaperMtn/github-watchman)

## License
The source code for this project is released under the [GNU General Public Licence](https://www.gnu.org/licenses/licenses.html#GPL). This project is not associated with Slack Technologies or Salesforce.