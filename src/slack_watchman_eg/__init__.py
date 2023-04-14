import argparse
import multiprocessing
import os
import time
import calendar
from pathlib import Path
from typing import List

from . import __version__
from . import sw_logger
from . import slack_wrapper
from . import signature_updater
from .models import (
    signature,
    user,
    workspace,
    post,
    conversation
)

SIGNATURES_PATH = (Path(__file__).parents[2] / 'watchman-signatures').resolve()
OUTPUT_LOGGER: sw_logger.JSONLogger


def load_signatures() -> List[signature.Signature]:
    """ Load signatures from YAML files
    Returns:
        List containing loaded definitions as Signatures objects
    """

    loaded_signatures = []
    try:
        for root, dirs, files in os.walk(SIGNATURES_PATH):
            for sig_file in files:
                sig_path = (Path(root) / sig_file).resolve()
                if sig_path.name.endswith('.yaml'):
                    loaded_def = signature.load_from_yaml(sig_path)
                    for sig in loaded_def:
                        if sig.status == 'enabled' and 'slack_eg' in sig.watchman_apps:
                            loaded_signatures.append(sig)
        return loaded_signatures
    except Exception as e:
        raise e


def search(loaded_signature: signature,
           slack_connection: slack_wrapper.SlackAPI,
           user_list: List[user.User],
           message_list: List[post.Message],
           workspace_list: List[workspace.Workspace],
           files_list: List[post.File],
           scope: str,
           cores: int,
           verbose: bool) -> None:
    """ Uses the signature to call the relevant search functions to find data in messages
    files and drafts. Results are output to stdout logging.
    Args:
        slack_connection: Slack API object
        loaded_signature: Signature object
        user_list: List of User objects from the Enterprise
        message_list: List of Message objects to search through
        workspace_list: List of Workspace objects from the Enterprise
        files_list: List of File objects to search through
        scope: Scope of any results found for logging: e.g. Draft
        cores: Number of CPU cores to use
        verbose: Whether to use verbose logging or not
    """

    if scope == 'messages':
        OUTPUT_LOGGER.log('INFO', f'Searching for posts containing {loaded_signature.name}')
        messages = slack_wrapper.search_message_matches(
            loaded_signature,
            slack_connection,
            user_list,
            message_list,
            workspace_list,
            cores,
            OUTPUT_LOGGER,
            verbose
        )
        if messages:
            for message in messages:
                OUTPUT_LOGGER.log(
                    'NOTIFY',
                    message,
                    scope=scope,
                    severity=loaded_signature.severity,
                    detect_type=loaded_signature.name,
                    notify_type='result'
                )

    if scope == 'files':
        OUTPUT_LOGGER.log('INFO', f'Searching for {loaded_signature.name}')
        files = slack_wrapper.search_file_matches(
            loaded_signature,
            user_list,
            files_list,
            cores,
            OUTPUT_LOGGER
        )
        if files:
            for file in files:
                OUTPUT_LOGGER.log(
                    'NOTIFY',
                    file,
                    scope=scope,
                    severity=loaded_signature.severity,
                    detect_type=loaded_signature.name,
                    notify_type='result'
                )


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


def init_logger(logging_type: str, debug: bool) -> sw_logger.JSONLogger or sw_logger.StdoutLogger:
    """ Create a logger object
    Returns:
        Logging object for outputting results
    """

    if not logging_type or logging_type == 'terminal':
        return sw_logger.StdoutLogger(debug=debug)
    else:
        return sw_logger.JSONLogger(debug=debug)


def main():
    global OUTPUT_LOGGER
    try:
        OUTPUT_LOGGER = ''
        parser = argparse.ArgumentParser(description=__version__.__summary__)

        parser.add_argument('--hours', '-hr', dest='hours', type=int,
                            help='How far back to search in whole hours between 1-24. Defaults to 1 if no acceptable '
                                 'value given', required=False)
        parser.add_argument('--minutes', '-m', dest='minutes', type=int,
                            help='How far back to search in whole minutes between 1-60', required=False)
        parser.add_argument('--output', '-o', choices=['json', 'terminal'], dest='logging_type',
                            help='What logging output to use - JSON formatted output, or textual output'
                                 'for reading via terminal. Default is terminal')
        parser.add_argument('--cores', '-c', dest='cores', type=int,
                            help='Number of cores to use between 1-12', required=False)
        parser.add_argument('--version', '-v', action='version',
                            version=f'Slack Watchman for Enterprise Grid: {__version__.__version__}')
        parser.add_argument('--users', '-u', dest='users', action='store_true', help='Return all users')
        parser.add_argument('--workspaces', '-w', dest='workspaces', action='store_true', help='Return all workspaces')
        parser.add_argument('--debug', '-d', dest='debug', action='store_true', help='Turn on debug level logging')
        parser.add_argument('--verbose', '-V', dest='verbose', action='store_true',
                            help='Turn on more verbose output for JSON logging. '
                                 'This includes more fields, but is larger')

        args = parser.parse_args()
        hours = args.hours
        minutes = args.minutes
        cores = args.cores
        users = args.users
        workspaces = args.workspaces
        logging_type = args.logging_type
        debug = args.debug
        verbose = args.verbose

        span = 0
        OUTPUT_LOGGER = init_logger(logging_type, debug)
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

        slack_con = slack_wrapper.initiate_slack_connection(os.environ.get('SLACK_WATCHMAN_EG_TOKEN'))
        OUTPUT_LOGGER.log('SUCCESS', 'Slack Watchman Enterprise Grid started execution')
        OUTPUT_LOGGER.log('INFO', f'Version: {__version__.__version__}')
        OUTPUT_LOGGER.log('INFO', f'Created by: {__version__.__author__} - {__version__.__email__}')
        OUTPUT_LOGGER.log('INFO', f'{cores} cores in use')
        OUTPUT_LOGGER.log('INFO', 'Downloading signature file updates')
        signature_updater.SignatureUpdater(OUTPUT_LOGGER).update_signatures()
        OUTPUT_LOGGER.log('INFO', 'Importing signatures...')
        signature_list = load_signatures()
        OUTPUT_LOGGER.log('SUCCESS', f'{len(signature_list)} signatures loaded')
        OUTPUT_LOGGER.log('INFO', f'Searching previous {hours} hour(s), {minutes} minutes')
        OUTPUT_LOGGER.log('INFO', 'Enumerating Enterprise information')
        OUTPUT_LOGGER.log('NOTIFY', slack_wrapper.get_enterprise(slack_con), scope='Enterprise',
                          notify_type='enterprise')
        OUTPUT_LOGGER.log('INFO', 'Enumerating Enterprise workspaces')
        workspace_list = slack_wrapper.get_workspaces(slack_con, verbose)
        OUTPUT_LOGGER.log('INFO', f'{len(workspace_list)} workspaces discovered')
        OUTPUT_LOGGER.log('INFO', 'Enumerating Enterprise users')
        user_list = slack_wrapper.get_users(slack_con, workspace_list, verbose)
        OUTPUT_LOGGER.log('INFO', f'{len(user_list)} users discovered')

        if users:
            OUTPUT_LOGGER.log('INFO', 'Outputting Enterprise users')
            for user in user_list:
                OUTPUT_LOGGER.log('NOTIFY', user, detect_type='User', notify_type='user')

        if workspaces:
            OUTPUT_LOGGER.log('INFO', 'Outputting Enterprise workspaces')
            for workspace in workspace_list:
                OUTPUT_LOGGER.log('NOTIFY', workspace, detect_type='Workspace', notify_type='workspace')

        OUTPUT_LOGGER.log('INFO', 'Enumerating files')
        file_list = slack_wrapper.get_all_files(slack_con, cores=cores, verbose=verbose, timeframe=tf)
        OUTPUT_LOGGER.log('INFO', f'{len(file_list)} files discovered')

        OUTPUT_LOGGER.log('INFO', 'Enumerating messages')
        message_list = slack_wrapper.get_all_messages(slack_con, cores=cores, timeframe=tf)
        OUTPUT_LOGGER.log('INFO', f'{len(message_list)} messages discovered')

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
                    verbose
                )

        OUTPUT_LOGGER.log('INFO', 'Enumerating draft messages')
        draft_list = slack_wrapper.get_all_drafts(
            slack_con,
            workspace_list,
            cores=cores,
            verbose=verbose,
            timeframe=tf
        )
        OUTPUT_LOGGER.log('INFO', f'{len(draft_list)} drafts discovered')
        for sig in signature_list:
            if 'drafts' in sig.scope:
                OUTPUT_LOGGER.log('INFO', f'Searching for drafts containing {sig.name}')
                drafts = slack_wrapper.search_draft_matches(
                    slack_con,
                    sig,
                    draft_list,
                    user_list,
                    OUTPUT_LOGGER,
                    verbose,
                    tf
                )
                if drafts:
                    for draft in drafts:
                        OUTPUT_LOGGER.log(
                            'NOTIFY',
                            draft,
                            scope='Draft',
                            severity=sig.severity,
                            detect_type=sig.name,
                            notify_type='result'
                        )

        OUTPUT_LOGGER.log('SUCCESS', 'Slack Watchman Enterprise Grid finished execution')

    except Exception as e:
        OUTPUT_LOGGER.log('CRITICAL', e)


if __name__ == '__main__':
    main()
