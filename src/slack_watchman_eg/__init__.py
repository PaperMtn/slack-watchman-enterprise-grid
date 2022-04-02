import argparse
import multiprocessing
import os
import time
import calendar
from pathlib import Path

from . import __version__
from . import logger as logger
from . import slack_wrapper
from . import signature

SIGNATURES_PATH = (Path(__file__).parents[1] / 'signatures').resolve()
OUTPUT_LOGGER: logger.StdoutLogger
TOMBSTONE_CONTENT = None


def load_signatures(sandbox: bool) -> [signature.Signature]:
    """
    Load signatures from YAML files

    Args:
        sandbox: Whether to load sandbox signatures
    Returns:
        List containing loaded definitions as signatures objects

    """

    loaded_signatures = []
    if sandbox:
        signature_path = (SIGNATURES_PATH / 'sandbox').resolve()
        OUTPUT_LOGGER.log_info('Importing sandbox signatures')
    else:
        signature_path = SIGNATURES_PATH

    try:
        for root, dirs, files in os.walk(signature_path):
            for sig_file in files:
                sig_path = (Path(root) / sig_file).resolve()
                if sig_path.name.endswith('.yaml'):
                    loaded_sig = signature.load_from_yaml(sig_path)
                    if loaded_sig.enabled:
                        loaded_signatures.append(loaded_sig)
        return loaded_signatures
    except Exception as e:
        raise e


def search(sig: signature,
           slack_connection: slack_wrapper.SlackAPI,
           user_list: list,
           message_list: list,
           workspace_list: list,
           files_list: list,
           scope: str,
           cores: int,
           tombstone: bool):
    """ Uses the signature to call the relevant search functions to find data in messages
    files and drafts. Results are output to stdout logging.

    Args:
        slack_connection: Slack API object
        sig: Signature object
        user_list: List of User objects from the Enterprise
        message_list: List of Message objects to search through
        workspace_list: List of Workspace objects from the Enterprise
        files_list: List of File objects to search through
        scope: Scope of any results found for logging: e.g Draft
        cores: Number of CPU cores to use
        tombstone: Whether to tombstone the file or not
    """

    if scope == 'messages':
        OUTPUT_LOGGER.log_info(f'Searching for posts containing {sig.meta.name}')
        messages = slack_wrapper.search_message_matches(
            sig,
            slack_connection,
            user_list,
            message_list,
            workspace_list,
            cores,
            OUTPUT_LOGGER
        )
        if messages:
            for message in messages:
                OUTPUT_LOGGER.log_notification(
                    message,
                    scope=scope,
                    severity=sig.meta.severity,
                    detect_type=sig.meta.name
                )
            if tombstone:
                OUTPUT_LOGGER.log_info(f'Tombstoning messages containing {sig.meta.name}')
                for message in messages:
                    slack_wrapper.tombstone_message(slack_connection, message.get('message'), content=TOMBSTONE_CONTENT)
                OUTPUT_LOGGER.log_info(f'{len(messages)} messages tombstoned')

    if scope == 'files':
        OUTPUT_LOGGER.log_info(f'Searching for {sig.meta.name}')
        files = slack_wrapper.search_file_matches(
            sig,
            user_list,
            files_list,
            cores,
            OUTPUT_LOGGER
        )
        if files:
            for file in files:
                OUTPUT_LOGGER.log_notification(
                    file,
                    scope=scope,
                    severity=sig.meta.severity,
                    detect_type=sig.meta.name
                )
            if tombstone:
                OUTPUT_LOGGER.log_info(f'Tombstoning {sig.meta.name}')
                for file in files:
                    slack_wrapper.tombstone_file(slack_connection, file.get('file'), content=TOMBSTONE_CONTENT)
                OUTPUT_LOGGER.log_info(f'{len(files)} files tombstoned')


def core_validation(cores: int) -> int:
    """ Validate the number of cores entered

    Args:
        cores: Number of cores passed to CLI
    Returns:
        Number of cores to use

    """

    if not cores or cores > multiprocessing.cpu_count() or cores > 12:
        if multiprocessing.cpu_count() >= 8:
            return 8
        else:
            return multiprocessing.cpu_count()
    else:
        return cores


def init_logger() -> logger.StdoutLogger:
    """ Create a logger object

    Returns:
        Logging object for outputting results
    """

    return logger.StdoutLogger()


def parse_tombstone_text(filepath: str) -> str or None:
    """ Use a custom tombstone notification from a txt file

    Args:
        filepath: Path to txt file containing custom tombstone text
    Returns:
        String containing contents of the txt file, or None to use the default
    """

    try:
        with open(filepath, encoding='utf8') as f:
            contents = f.read()
            return contents
    except:
        return None


def main():
    global OUTPUT_LOGGER, TOMBSTONE_CONTENT
    try:
        OUTPUT_LOGGER = init_logger()
        parser = argparse.ArgumentParser(description=__version__.__summary__)

        parser.add_argument('--hours', dest='hours', type=int,
                            help='How far back to search in whole hours between 1-24. Defaults to 1 if no acceptable '
                                 'value given', required=False)
        parser.add_argument('--minutes', dest='minutes', type=int,
                            help='How far back to search in whole minutes between 1-60', required=False)
        parser.add_argument('--cores', dest='cores', type=int,
                            help='Number of cores to use between 1-12', required=False)
        parser.add_argument('--version', action='version',
                            version=f'Slack Watchman for Enterprise Grid: {__version__.__version__}')
        parser.add_argument('--users', dest='users', action='store_true', help='Find all users')
        parser.add_argument('--workspaces', dest='workspaces', action='store_true', help='Find all workspaces')
        parser.add_argument('--sandbox', dest='sandbox', action='store_true', help='Search using only sandbox '
                                                                                   'signatures')
        parser.add_argument('--tombstone', dest='tombstone', action='store_true', help='Tombstone (REMOVE) all '
                                                                                       'matching messages')
        parser.add_argument('--tombstone-text-file', dest='tombstone_filepath', type=str,
                            help='Path to file containing custom tombstone notification text (Optional)',
                            required=False)

        args = parser.parse_args()
        hours = args.hours
        minutes = args.minutes
        tombstone = args.tombstone
        tombstone_filepath = args.tombstone_filepath
        cores = args.cores
        users = args.users
        workspaces = args.workspaces
        sandbox = args.sandbox

        span = 0

        if minutes:
            if isinstance(minutes, int) and 1 <= int(minutes) <= 60:
                span = (int(minutes) * 60)
            else:
                minutes = None

        if hours:
            if isinstance(hours, int) and 1 <= int(hours) <= 24:
                span = (span + (hours * 3600))
            else:
                hours = None

        if not minutes and not hours:
            tf = calendar.timegm(time.gmtime()) - 3600
            hours = 1
            minutes = 0
        else:
            tf = calendar.timegm(time.gmtime()) - span

        if not minutes:
            minutes = 0
        if not hours:
            hours = 0

        cores = core_validation(cores)

        slack_con = slack_wrapper.initiate_slack_connection()
        OUTPUT_LOGGER.log_info('Slack Watchman Enterprise Grid started execution')
        OUTPUT_LOGGER.log_info(f'Version: {__version__.__version__}')
        OUTPUT_LOGGER.log_info(f'Created by: {__version__.__author__} - {__version__.__email__}')
        OUTPUT_LOGGER.log_info(f'{cores} cores in use')
        OUTPUT_LOGGER.log_info('Importing signatures...')
        signature_list = load_signatures(sandbox)
        OUTPUT_LOGGER.log_info(f'{len(signature_list)} signatures loaded')

        if tombstone:
            OUTPUT_LOGGER.log_info('Tombstone option selected. All files and messages that match signatures will be '
                                   'removed and replaced with a notification')
            if tombstone_filepath:
                TOMBSTONE_CONTENT = parse_tombstone_text(tombstone_filepath)

        OUTPUT_LOGGER.log_info(f'Searching previous {hours} hour(s), {minutes} minutes')
        OUTPUT_LOGGER.log_info('Enumerating Enterprise information')
        OUTPUT_LOGGER.log_notification(slack_wrapper.get_enterprise(slack_con), detect_type='Enterprise')
        OUTPUT_LOGGER.log_info('Enumerating Enterprise workspaces')
        workspace_list = slack_wrapper.get_workspaces(slack_con)
        OUTPUT_LOGGER.log_info(f'{len(workspace_list)} workspaces discovered')
        OUTPUT_LOGGER.log_info('Enumerating Enterprise users')
        user_list = slack_wrapper.get_users(slack_con, workspace_list)
        OUTPUT_LOGGER.log_info(f'{len(user_list)} users discovered')

        if users:
            OUTPUT_LOGGER.log_info('Outputting Enterprise users')
            for user in user_list:
                OUTPUT_LOGGER.log_notification(user, detect_type='User')

        if workspaces:
            OUTPUT_LOGGER.log_info('Outputting Enterprise workspaces')
            for workspace in workspace_list:
                OUTPUT_LOGGER.log_notification(workspace, detect_type='Workspace')

        OUTPUT_LOGGER.log_info('Enumerating files')
        file_list = slack_wrapper.get_all_files(slack_con, cores=cores, timeframe=tf)
        OUTPUT_LOGGER.log_info(f'{len(file_list)} files discovered')

        OUTPUT_LOGGER.log_info('Enumerating messages')
        message_list = slack_wrapper.get_all_messages(slack_con, cores=cores, timeframe=tf)
        OUTPUT_LOGGER.log_info(f'{len(message_list)} messages discovered')

        for sig in signature_list:
            for scope in sig.scope:
                search(
                    sig,
                    slack_con,
                    user_list,
                    message_list,
                    workspace_list,
                    file_list,
                    scope,
                    cores,
                    tombstone
                )

        OUTPUT_LOGGER.log_info('Enumerating draft messages')
        draft_list = slack_wrapper.get_all_drafts(
            slack_con,
            workspace_list,
            cores=cores,
            timeframe=tf
        )
        OUTPUT_LOGGER.log_info(f'{len(draft_list)} drafts discovered')
        for sig in signature_list:
            if 'drafts' in sig.scope:
                OUTPUT_LOGGER.log_info(f'Searching for drafts containing {sig.meta.name}')
                drafts = slack_wrapper.search_draft_matches(
                    slack_con,
                    sig,
                    draft_list,
                    user_list,
                    OUTPUT_LOGGER,
                    tf
                )
                if drafts:
                    for draft in drafts:
                        OUTPUT_LOGGER.log_notification(
                            draft,
                            scope='Draft',
                            severity=sig.meta.severity,
                            detect_type=sig.meta.name
                        )

        OUTPUT_LOGGER.log_info('Slack Watchman Enterprise Grid finished execution')

    except Exception as e:
        OUTPUT_LOGGER.log_critical(e)


if __name__ == '__main__':
    main()
