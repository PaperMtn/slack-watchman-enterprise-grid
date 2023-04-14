## [2.0.0] - 2023-04-14
This major version release brings multiple updates to Slack Watchman for Enterprise Grid, both in usability, functionality and behind the scenes improvements.
### Added
- Support for centralised signatures from the Watchman Signatures repository. This makes it much easier to keep the signature base for all Watchman applications up to date, and to add functionality to Slack Watchman with new signatures. New signatures are downloaded, and updates to existing signatures are applied, at runtime, meaning Slack Watchman for Enterprise Grid will always be using the most up to date signatures. 
- Option for terminal optimised logging instead of JSON formatting. This is now the default when running with no output option selected, and is a lot easier for humans to read. Also, colours! 
- Option choose between verbose or succinct logging when using JSON output. Default is succinct.
- Debug logging option
### Removed
- Support for tombstoning posts that match signatures removed
- Local signatures - Centralised signatures mean that user-created custom signatures can't be used with Slack Watchman for Enterprise Grid anymore. If you have made a signature you think would be good for sharing with the community, feel free to add it to the Watchman Signatures repository, so it can be used in all Watchman applications 
- For the reason above, the functionality to have sandbox signatures has been removed as well
### Fixed
- Draft searches were giving an error due to not being able to populate some workspace information. This has now been fixed

## [1.1.1] - 2022-05-16
### Added
- Signature to find Atlassian tokens

## [1.1.0] - 2022-04-02
### Added
- Docker image now available from the Docker hub, or by building from source.
- Support for Python 3.7
- New logo to play nicely with dark mode
### Fixed
- More errors when importing packages

## [1.0.2] - 2021-12-30
### Fixed
- Error when importing packages
- Signatures not being included in the distribution package

## [1.0.1] - 2021-12-30
### Added
- Refactor and update distribution files

## [1.0.0] - 2021-12-30
- Initial release

