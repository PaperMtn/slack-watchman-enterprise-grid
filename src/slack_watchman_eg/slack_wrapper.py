import dataclasses
import json
import multiprocessing
import numpy
import os
import re
import requests
import time
import calendar
from requests.packages.urllib3.util import Retry
from requests.adapters import HTTPAdapter

from . import signature
from . import logger
from .slack_objects import workspace
from .slack_objects import user
from .slack_objects import enterprise
from .slack_objects import conversation
from .slack_objects import post

# Default timeframe of 1 hour
DEFAULT_TIMEFRAME = calendar.timegm(time.gmtime()) - 3600


class ScopeError(Exception):
    pass


class SlackAPIError(Exception):
    pass


class SlackAPI(object):

    def __init__(self, token):
        self.token = token
        self.base_url = 'https://slack.com/api'
        self.limit = '1000'
        self.session = session = requests.session()
        session.mount(self.base_url, HTTPAdapter(max_retries=Retry(connect=3, backoff_factor=1)))
        session.headers.update({
            'Connection': 'keep-alive, close',
            'Authorization': f'Bearer {self.token}',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Cafari/537.36 '
        })
        session.params['limit'] = self.limit

    def _pagination_loop(self,
                         response: requests.Response,
                         pagination: str,
                         method: str,
                         relative_url: str,
                         params: dict,
                         data: dict,
                         verify_ssl: bool) -> list:

        results = []

        if pagination == 'offset' and response.json().get('offset'):
            while response.json().get('offset'):
                response = self.session.request(
                    method,
                    relative_url,
                    params=params,
                    data=data,
                    verify=verify_ssl
                )

                params.update({
                    'offset': response.json().get('offset')
                })
                results.append(response.json())
        elif pagination == 'latest' and response.json().get('offset'):
            while response.json().get('offset'):
                response = self.session.request(
                    method,
                    relative_url,
                    params=params,
                    data=data,
                    verify=verify_ssl
                )

                params.update({
                    'latest': response.json().get('offset')
                })
                results.append(response.json())
        else:
            results.append(response.json())

        return results

    def _make_request(self,
                      url,
                      params=None,
                      data=None,
                      method='GET',
                      verify_ssl=True,
                      pagination=None):
        try:
            relative_url = '/'.join((self.base_url, url))
            response = self.session.request(
                method,
                relative_url,
                params=params,
                data=data,
                verify=verify_ssl
            )

            if not response.json().get('ok') and response.json().get('error') == 'missing_scope':
                raise ScopeError()
            elif not response.json().get('ok') and response.json().get('error') == 'channel_not_found':
                params['team'] = ''
                response = self.session.request(
                    method='GET',
                    url=relative_url,
                    params=params,
                    data=data,
                    verify=verify_ssl
                )
                return self._pagination_loop(
                    response,
                    pagination,
                    method,
                    relative_url,
                    params,
                    data,
                    verify_ssl
                )
            elif not response.json().get('ok') and response.json().get('error') == 'ratelimited':
                print('Slack API rate limit reached - cooling off')
                time.sleep(60)
                self._make_request(
                    url,
                    params,
                    data,
                    method,
                    verify_ssl,
                    pagination
                )
            elif not response.json().get('ok'):
                raise SlackAPIError()
            else:
                if not response.json().get('offset'):
                    return [response.json()]
                else:
                    return self._pagination_loop(
                        response,
                        pagination,
                        method,
                        relative_url,
                        params,
                        data,
                        verify_ssl
                    )
        except ScopeError:
            raise ScopeError(f"Missing required scope: {response.json().get('needed')}")
        except SlackAPIError:
            raise SlackAPIError(f"Slack API Error: {response.json().get('error')}")
        except Exception as e:
            raise Exception(e)

    def get_enterprise_info(self) -> dict:
        """ Return all information for the Enterprise Grid

        Returns:
            JSON object containing information on the Slack Enterprise Grid
        """

        return self._make_request('discovery.enterprise.info')[0].get('enterprise')

    def get_all_users(self, offset: str = None) -> [dict]:
        """ Get all users in a Grid

        Returns:
            All users in a Grid, plus Workspaces they are assigned to
        """

        params = {
            'offset': offset
        }

        users = self._make_request('discovery.users.list', params=params, pagination='offset')

        return _format_results(users, 'users')

    def get_user_info(self, user_id: str) -> dict:
        """ Get information from one user in the Grid

        Returns:
            User information for a single user
        """

        params = {
            'user': user_id
        }

        return self._make_request('discovery.user.info', params=params)[0].get('user')

    def get_user_conversations(self,
                               user_id: str,
                               public: bool = None,
                               private: bool = None,
                               im: bool = None,
                               mpim: bool = None,
                               historical: bool = None) -> [dict]:
        """ return all conversations a user is involved in

        Args:
            historical: Whether to search for
                channels that the user is not currently a member of, but has been in the past
            mpim: Whether to look at multi-person instant messages
            im: Whether to look at instant messages
            private: Whether only to look at private channels
            public: Whether to only look for public channels
            user_id: ID of the user to search for
        Returns:
            Dict containing user conversation data
        """

        params = {
            'only_public': public,
            'only_private': private,
            'only_mpim': mpim,
            'only_im': im,
            'include_historical': historical,
            'user': user_id
        }

        conversations = self._make_request('discovery.user.conversations', params=params, pagination='offset')

        return _format_results(conversations, 'channels')

    def get_all_conversations(self,
                              public: bool = None,
                              private: bool = None,
                              im: bool = None,
                              mpim: bool = None,
                              ext_shared: bool = None,
                              historical: bool = None) -> [dict]:
        """ return all conversations in a Grid

        Args:
            ext_shared: Whether to look for only external shared channels
            historical: Whether to search for
                channels that the user is not currently a member of, but has been in the past
            mpim: Whether to look at multi-person instant messages
            im: Whether to look at instant messages
            private: Whether only to look at private channels
            public: Whether to only look for public channels
        Returns:
            Dict containing user conversation data
        """

        params = {
            'only_public': public,
            'only_private': private,
            'only_mpim': mpim,
            'only_im': im,
            'only_ext_shared': ext_shared,
            'include_historical': historical
        }

        conversations = self._make_request('discovery.conversations.list', params=params, pagination='offset')

        return _format_results(conversations, 'channels')

    def get_recent_conversations(self, latest: float = None) -> [dict]:
        """
        Args:
            latest: Timestamp within the last 24 hours to shorten or lengthen the requested timespan.
                This method can return up to 7 days worth of data (prior to the current timestamp).
                If this parameter is not included, this endpoint will return data from the last 24 hours.
        Returns:
            JSON containing recent conversations created
        """

        params = {
            'latest': latest
        }

        conversations = self._make_request('discovery.conversations.recent', params=params, pagination='latest')

        return _format_results(conversations, 'channels')

    def get_conversation_history(self,
                                 channel_id: str,
                                 team_id: str = None,
                                 latest: float = None,
                                 oldest: float = None) -> [dict]:
        """ Retrieves the history of the channel-object. This can be thought of as
         the state of the conversation in the client: it’s what the users are seeing.

        Args:
            team_id: ID for the team the channel is in
            channel_id: ID for the channel to return
            latest: The newest date to retrieve messages from
            oldest: The oldest date to retrieve messages from
        Returns:
            JSON object containing channel information
        """

        params = {
            'channel': channel_id,
            'team': team_id,
            'latest': latest,
            'oldest': oldest
        }

        conversations = self._make_request('discovery.conversations.history', params=params, pagination='latest')

        return _format_results(conversations, 'messages')

    def get_conversation_edits(self,
                               channel_id: str,
                               team_id: str,
                               latest: float = None,
                               oldest: float = None) -> [dict]:
        """ Returns edit and delete records of messages

        Args:
            team_id: ID for the team to search in
            channel_id: ID for the channel to return
            latest: The newest date to retrieve messages from
            oldest: The oldest date to retrieve messages from
        Returns:
            JSON object containing channel edit and delete information

        """

        params = {
            'channel': channel_id,
            'team': team_id,
            'latest': latest,
            'oldest': oldest
        }

        conversations = self._make_request('discovery.conversations.edits', params=params, pagination='latest')

        return _format_results(conversations, 'edits')

    def get_conversation_info(self,
                              channel_id: str,
                              team_id: str = None) -> [dict]:
        """ Provides a comprehensive overview of a single channel outside of its message history

        Args:
            team_id: ID of the team the channel is in
            channel_id: ID of the channel to return
        Returns:
            JSON object with channel information
        """

        params = {
            'channel': channel_id,
            'team': team_id
        }

        return self._make_request('discovery.conversations.info', params=params)[0].get('info')

    def get_conversation_members(self,
                                 channel_id: str,
                                 team_id: str = None,
                                 include_member_left: bool = None) -> [dict]:
        """ Provides a list of everyone in a given channel, private channel, MDPM or DM

        Args:
            team_id: ID of the team the channel is in
            include_member_left: Whether to include members who have left the channel
            channel_id: ID of the channel to get members for
        Returns:
            JSON object with channel members
        """

        params = {
            'channel': channel_id,
            'team': team_id,
            'include_members_left': include_member_left
        }

        conversations = self._make_request('discovery.conversations.members', params=params, pagination='offset')

        return _format_results(conversations, 'members')

    def get_conversation_renames(self,
                                 latest: float = None,
                                 oldest: float = None,
                                 private: bool = None) -> [dict]:
        """ Get all channel renames that have occurred in an organisation

        Args:
            latest: Newest date (timestamp) of renames to include
            oldest: Oldest date (timestamp) of renames to include
            private: Setting this value to true will return only private channels.
             The default (or a false value) will include only public channels.
        Returns:
            JSON object with channel rename information
        """

        params = {
            'latest': latest,
            'oldest': oldest,
            'private': private
        }

        conversations = self._make_request('discovery.conversations.renames', params=params, pagination='latest')

        return _format_results(conversations, 'renames')

    def search_conversations(self,
                             query: str,
                             include_messages: bool = None,
                             latest: float = None,
                             oldest: float = None) -> [dict]:
        """ Find channels and messages within an instance that contain the provided search term.

        Args:
            query: Term or keyword to search conversation messages for.
            include_messages: By default, messages are not included in the response.
                To include both messages and channel information, pass include_messages with a true value.
            latest: Newest date (timestamp) of messages to include.
            oldest: Oldest date (timestamp) of message to include
        Returns:
            JSON object with message information that matches the search query
        """

        params = {
            'query': query,
            'include_messages': include_messages,
            'latest': latest,
            'oldest': oldest
        }

        conversations = self._make_request('discovery.conversations.search', params=params, pagination='offset')

        return _format_results(conversations, 'channels')

    def get_message_info(self,
                         timestamp: str,
                         channel_id: str,
                         team_id: str = None) -> dict:
        """ Returns a single message. If the message has been edited (or deleted),
        this method returns the current, edited (or deleted) message. If the enterprise has its retention set to keep
        edits and deletes, it will also return all of those edits or the deletion.

        Args:
            team_id: The ID of the team the message was posted in
            timestamp: The entire timestamp of the message as retrieved from one of the .history methods
            channel_id: The ID of the channel or DM where the message was posted
        Returns:
            JSON object with message details
        """

        params = {
            'ts': timestamp,
            'channel': channel_id,
            'team': team_id
        }

        return self._make_request('discovery.chat.info', params=params)[0].get('message')

    def update_message(self,
                       timestamp: str,
                       channel_id: str,
                       team_id: str,
                       text: str) -> dict:
        """ This method specifies text or attachments that should
        be included in place of the current message

        Args:
            team_id: The ID of the team the message was posted in
            channel_id: Can be a DM, MPDM, Group, or public channel
            timestamp: The timestamp of the message to update.
                If you are dealing with a message that has been edited, you must use the original_ts.
            text: Replacement text for the message.
        Returns:
            JSON confirmation the message has been updated
        """

        params = {
            'ts': timestamp,
            'channel': channel_id,
            'team': team_id,
            'text': text
        }

        return self._make_request('discovery.chat.update', method='POST', params=params)[0]

    def delete_message(self,
                       timestamp: str,
                       channel_id: str,
                       team_id: str) -> dict:
        """ Purges the history, edits, and message from Slack. Messages and any associated history or
        edits cannot be recovered after using this method, regardless of retention settings. This is different from
        the behavior of a user deleting a message through the UI. Messages deleted via the UI will be available,
        including their edits, and history.

        Args:
            team_id: The ID of the team the message was posted in
            channel_id: Can be a DM, MPDM, Group, or public channel
            timestamp: The timestamp of the message to update.
                If you are dealing with a message that has been edited, you must use the original_ts.
        Returns:
            JSON confirmation the message has been deleted
        """

        params = {
            'ts': timestamp,
            'channel': channel_id,
            'team': team_id
        }

        return self._make_request('discovery.chat.delete', method='POST', params=params)[0]

    def tombstone_message(self,
                          timestamp: str,
                          channel_id: str,
                          team_id: str,
                          content: str = None) -> dict:
        """ Update and or obscure a message in the event that the message violated policy.

        Args:
            team_id:
            channel_id: The ID of the channel or DM where the message was posted
            timestamp: The entire timestamp of the message
            content: Custom tombstone message content. If not provided, display default message
        Returns:
            JSON confirmation the message has been tombstoned
        """

        params = {
            'ts': timestamp,
            'channel': channel_id,
            'team': team_id,
            'content': content
        }

        return self._make_request('discovery.chat.tombstone', method='POST', params=params)[0]

    def restore_message(self,
                        channel_id: str,
                        timestamp: str,
                        team_id: str) -> dict:
        """ Restore a tombstoned message.

        Args:
            team_id: Team ID of the team the message was posted in
            timestamp: The entire timestamp of the message
            channel_id: The ID of the channel or DM where the message was posted
        Returns:
            JSON confirmation of the restore
        """

        params = {
            'ts': timestamp,
            'channel': channel_id,
            'team': team_id
        }

        return self._make_request('discovery.chat.restore', method='POST', params=params)[0]

    def list_drafts(self,
                    team_id: str,
                    oldest: int = None,
                    latest: int = None) -> [dict]:
        """

        Args:
            team_id: Team ID of the workspace the draft was created within.
            oldest: Start of time range of messages to include in results.
            latest: End of time range of messages to include in results.
        Returns:
            JSON object with drafts from specified team
        """

        params = {
            'team': team_id,
            'latest': latest,
            'oldest': oldest
        }

        drafts = self._make_request('discovery.drafts.list', params=params, pagination='offset')

        return _format_results(drafts, 'drafts')

    def get_draft_info(self,
                       team_id: str,
                       draft_id: str,
                       user_id: str,
                       oldest: float = None,
                       latest: float = None) -> dict:
        """ Provides information associated with a singular draft.

        Args:
            team_id: Team ID of the workspace the draft was created within.
            draft_id: Draft ID of the draft to collect.
            user_id: User ID of the author.
            oldest: Start of time range of messages to include in results.
            latest: End of time range of messages to include in results.
        Returns:
            JSON object containing information on the draft
        """

        params = {
            'team': team_id,
            'draft': draft_id,
            'user': user_id,
            'latest': latest,
            'oldest': oldest
        }

        return self._make_request('discovery.draft.info', params=params)[0].get('draft')

    def list_files(self,
                   oldest: int or str = None,
                   latest: int or str = None) -> [dict]:
        """ Returns files uploaded within a specified timeframe.

        Args:
            oldest: Start of time range of messages to include in results.
            latest: End of time range of messages to include in results.
        Returns:
            JSON object containing file data
        """

        params = {
            'latest': latest,
            'oldest': oldest
        }

        drafts = self._make_request('discovery.files.list', params=params, pagination='offset')

        return _format_results(drafts, 'files')

    def get_file_info(self, file_id: str) -> dict:
        """ Get all comments for a file

        Args:
            file_id: ID of the file to retrieve
        Returns:
            JSON object with file information
        """

        params = {
            'file': file_id
        }

        return self._make_request('discovery.file.info', params=params)[0].get('file')

    def tombstone_file(self,
                       file_id: str,
                       title: str = None,
                       content: str = None) -> dict:
        """ Tombstone a file, making it inaccessible.

        Args:
            file_id: The file to be tombstoned
            title: A custom title to display for the tombstone file
            content: A custom string to display in the content of the tombstone file in the client.
                Text only. Images and formatting not supported.
        Returns:
            JSON confirmation of the file being tombstoned
        """

        params = {
            'file': file_id,
            'title': title,
            'content': content
        }

        return self._make_request('discovery.file.tombstone', method='POST', params=params)[0].get('file')

    def restore_file(self, file_id: str) -> dict:
        """ Restore a tombstoned file

        Args:
            file_id: file to restore
        Returns:
            JSON object confirming the restoration
        """

        params = {
            'file': file_id
        }

        return self._make_request('discovery.file.restore', method='POST', params=params)[0].get('file')

    def delete_file(self, file_id: str) -> dict:
        """ Delete a file

        Args:
            file_id: ID of the file to delete
        Returns:
            JSON confirmation of deletion
        """

        params = {
            'file': file_id
        }

        return self._make_request('discovery.file.delete', method='POST', params=params)[0].get('file')

    def get_team_info(self, team_id: str) -> dict:
        """ Get information on a Slack Workspace
        Requires the User Scope team:read

        Args:
            team_id: ID of the team to return
        Returns:
            JSON object with team information
        """

        params = {
            'team': team_id
        }

        return self._make_request('team.info', params=params)[0].get('team')


def _format_results(results_list: list, identifier: str) -> [dict]:
    """ Format a JSON result from the Slack API. Results come in the format below:
    {
        "ok": true,
        "offset": "T2B5NCQZO",
        "info": [{
            "id": "...",
            "name": "...",
        }],
    }

    The data we want is under the 'info' key in this case. Identifiers may be different though,
    including 'files', 'drafts' etc.

    Args:
        results_list: list of results to format
        identifier: the identifier in JSON to use to get data.
            The key 'info' in the example above
    Returns:
         Formatted dict containing the required data
    """

    return _flatten_list([i.get(f'{identifier}') for i in results_list])


def _flatten_list(input_list) -> list:
    """ Flattens nested lists into one list of objects

    Args:
        input_list: list to be flattened
    Returns:
        Flattened list

    """

    return [item for sublist in input_list for item in sublist]


def _location_verification(conv: conversation.Conversation, sig: signature.Signature) -> bool:
    """ Verify post location against selected locations in the signature
        e.g: do not return direct messages if they have not been specified

    Args:
        conv: Conversation object
        sig: Signature to check against
    Returns:
        False if verification fails and the message should not be returned
            due to it being out of scope for the selected signature.
        True otherwise
    """

    if (conv.is_im and 'im' not in sig.locations) \
            or (conv.is_mpim and 'mpim' not in sig.locations) \
            or (conv.is_private and 'private' not in sig.locations):
        return False
    else:
        return True


def _convert_timestamp(timestamp: str or int) -> str:
    """ Converts epoch timestamp into human readable time

    Args:
        timestamp: epoch timestamp in seconds
    Returns:
        String time in the format YYYY-mm-dd hh:mm:ss
    """

    if isinstance(timestamp, str):
        timestamp = timestamp.split('.', 1)[0]

    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(timestamp)))


def _deduplicate(input_list: list) -> [dict]:
    """ Removes duplicates where results are returned by multiple queries
    Nested class handles JSON encoding for dataclass objects

    Args:
        input_list: List of dataclass objects
    Returns:
        List of JSON objects with duplicates removed
    """

    class EnhancedJSONEncoder(json.JSONEncoder):
        def default(self, o):
            if dataclasses.is_dataclass(o):
                return dataclasses.asdict(o)
            return super().default(o)

    json_set = {json.dumps(dictionary, sort_keys=True, cls=EnhancedJSONEncoder) for dictionary in input_list}

    return [json.loads(t) for t in json_set]


def initiate_slack_connection():
    """ Create a Slack API object to use for interacting with the Slack API
    First tries to get the API token from the environment variable:
        SLACK_WATCHMAN_EG_TOKEN
    Failing this, looks for it in the config file:
        watchman.conf

    Returns:
        Slack API object
    """

    try:
        token = os.environ['SLACK_WATCHMAN_EG_TOKEN']
    except Exception as e:
        raise e

    return SlackAPI(token)


def get_enterprise(slack_connection: SlackAPI) -> enterprise.Enterprise:
    """ Get information on the Slack Enterprise

    Args:
        slack_connection: Slack API connection object
    Returns:
        Enterprise object containing details about the Slack Enterprise
    """
    enterprise_info = slack_connection.get_enterprise_info()

    return enterprise.create_from_dict(slack_connection.get_team_info(enterprise_info.get('id')))


def get_workspaces(slack_connection: SlackAPI) -> [workspace.Workspace]:
    """ Get all workspaces in the Slack environment

    Args:
        slack_connection: Slack API connection object
    Returns:
        List containing Workspace objects for all Slack Workspaces
    """

    enterprise_info = slack_connection.get_enterprise_info()

    return [workspace.create_from_dict(wrk) for wrk in enterprise_info.get('teams')]


def get_users(slack_connection: SlackAPI,
              workspaces_list: [workspace.Workspace]) -> [user.User]:
    """ Find all users in the Enterprise

    Args:
        workspaces_list: List of Slack Workspaces
        slack_connection: Slack API object
    Returns:
        List of Slack User objects for all users in the enterprise
    """

    all_users = slack_connection.get_all_users()
    results = []

    for user_info in all_users:
        wk = []
        for w in workspaces_list:
            workspace = next((item for item in workspaces_list if item.id == w.id))
            wk.append(workspace)

        results.append(user.create_from_dict(user_info, workspaces_list))

    return results


def get_conversations(slack_connection: SlackAPI,
                      timeframe: int = DEFAULT_TIMEFRAME) -> [conversation.Conversation]:
    """ Gets all conversations created in a given timeframe, returns a list of
    Conversation objects

    Args:
        timeframe: timeframe to search in
        slack_connection: Slack API object
    Returns:
        List of Conversation objects that have been created in the given timeframe
    """

    all_conversations = slack_connection.get_all_conversations()
    results = []
    for conv in all_conversations:
        if conv.get('created') >= timeframe:
            shared = []
            conv_info = slack_connection.get_conversation_info(conv.get('id'))[0]
            if conv_info.get('shared'):
                for wrk in conv.get('shared').get('shared_team_ids'):
                    shared.append(workspace.create_from_dict(slack_connection.get_team_info(wrk)))
            conv_info['shared'] = shared
            results.append(conversation.create_from_dict(conv_info))

    return results


def tombstone_file(slack_connection: SlackAPI,
                   file: dict,
                   content: str = None):
    """ Tombstone the given file

    Args:
        slack_connection: Slack API object
        file: File to tombstone
        content: Tombstone text to display
    """

    try:
        slack_connection.tombstone_file(file.get('id'), 'File Removed', content)
    except Exception as e:
        raise e


def tombstone_message(slack_connection: SlackAPI,
                      message: dict,
                      content: str = None):
    """ Tombstone the given message

    Args:
        slack_connection: Slack API object
        message: Message to tombstone
        content: Tombstone text to display
    """

    try:
        slack_connection.tombstone_message(
            message.get('timestamp'),
            message.get('conversation').get('id'),
            message.get('team'),
            content
        )
    except Exception as e:
        raise e


def search_message_matches(sig: signature.Signature,
                           slack_connection: SlackAPI,
                           users_list: [user.User],
                           message_list: [post.Message],
                           workspaces_list: [workspace.Workspace],
                           cores: int,
                           log: logger.StdoutLogger) -> [dict]:
    """ Use the search API to find messages posted in a certain timeframe
    matching search terms in the signature file. These are then compared against a regex
    to assess whether they contain sensitive data matching the signature.

    Args:
        slack_connection: Slack API object
        message_list: List of Message objects to search through
        sig: Signature object defining what to search for
        users_list: List of User objects
        workspaces_list: List of Workspace objects
        cores: number of cores to use
        log: Logging object for output
    Returns:
        List of Message objects containing post data
    """

    try:
        results = multiprocessing.Manager().list()
        list_of_chunks = numpy.array_split(numpy.array(message_list), cores)

        processes = []

        for message_list in list_of_chunks:
            p = multiprocessing.Process(
                target=_mp_find_messages_worker,
                args=(
                    sig,
                    slack_connection,
                    users_list,
                    message_list,
                    workspaces_list,
                    results
                )
            )
            processes.append(p)
            p.start()

        for process in processes:
            process.join()

        if results:
            results = _deduplicate(results)
            log.log_info(f'{len(results)} total matches found after filtering')
            return results
        else:
            log.log_info('No matches found after filtering')
    except Exception as e:
        log.log_critical(e)


def search_file_matches(sig: signature.Signature,
                        users_list: [user.User],
                        files_list: [post.File],
                        cores: int,
                        log: logger.StdoutLogger) -> [dict]:
    """ Use the search API to find files posted in a certain timeframe
    matching search terms in the signature file.

    Args:
        files_list:
        sig: Signature object defining what to search for
        users_list: List of User objects
        cores: Number of cores to use
        log: Logging object for output
    Returns:
        List of Message objects containing post data
    """

    try:
        results = multiprocessing.Manager().list()
        list_of_chunks = numpy.array_split(numpy.array(files_list), cores)

        processes = []

        for message_list in list_of_chunks:
            p = multiprocessing.Process(
                target=_mp_find_files_worker,
                args=(
                    sig,
                    users_list,
                    message_list,
                    results
                )
            )
            processes.append(p)
            p.start()

        for process in processes:
            process.join()

        if results:
            results = _deduplicate(results)
            log.log_info(f'{len(results)} total matches found after filtering')
            return results
        else:
            log.log_info('No matches found after filtering')
    except Exception as e:
        log.log_critical(e)


def search_draft_matches(slack_connection: SlackAPI,
                         sig: signature.Signature,
                         drafts_list: [post.Draft],
                         users_list: [user.User],
                         log: logger.StdoutLogger,
                         timeframe: int = DEFAULT_TIMEFRAME) -> [dict]:
    """ Find drafts posted in a certain timeframe
    matching search terms in the signature file. These are then compared against a regex
    to assess whether they contain sensitive data matching the signature.

    Args:
        slack_connection: Slack API object
        sig: Signature object defining what to search for
        users_list: List of User objects
        drafts_list: List of Draft objects
        log: Logging object for output
        timeframe: How far back to search for drafts
    Returns:
        List of Drafts objects containing post data
    """

    results = []
    try:
        for draft in drafts_list:
            result_drafts = []

            # This nasty nested if is required to iterate through multiple
            # levels of blocks in the JSON data. This is where the
            # text that needs checking against regex is stored.
            if draft.blocks and draft.created >= timeframe:
                for block_list in draft.blocks:
                    if block_list.get('type') == 'rich_text':
                        for element in block_list.get('elements'):
                            element_sub_list = element.get('elements')
                            for esl in element_sub_list:
                                if esl.get('type') == 'text':
                                    r = re.compile(sig.pattern)
                                    if sig.search_strings:
                                        for search_string in sig.search_strings:
                                            if str(search_string.lower()) in esl.get('text').lower():
                                                if r.search(esl.get('text')):
                                                    draft_user = next((item for item in users_list if
                                                                       item.id == draft.user), None)
                                                    team_id = draft.team
                                                    team = slack_connection.get_team_info(team_id)
                                                    channel_id = draft.destinations[0]
                                                    if channel_id.startswith('D'):
                                                        team_id = get_enterprise(slack_connection).id

                                                    conv_info = slack_connection.get_conversation_info(
                                                        channel_id, team_id)[0]
                                                    shared = []
                                                    if conv_info.get('shared').get('shared_team_ids'):
                                                        for wksp in conv_info.get('shared').get('shared_team_ids'):
                                                            shared.append(workspace.create_from_dict(
                                                                slack_connection.get_team_info(wksp)))
                                                        conv_info['shared'] = shared
                                                    channel = conversation.create_from_dict(conv_info)

                                                    if _location_verification(channel, sig):
                                                        if draft_user:
                                                            draft_user.workspaces = []
                                                            user_dict = draft_user
                                                        else:
                                                            user_dict = None

                                                        if team:
                                                            team_dict = workspace.create_from_dict(team)
                                                        else:
                                                            team_dict = None

                                                        result_drafts.append({
                                                            'timestamp': _convert_timestamp(draft.created),
                                                            'match_string': r.search(esl.get('text')).group(0),
                                                            'draft': draft,
                                                            'user': user_dict,
                                                            'workspace': team_dict,
                                                            'conversation': channel
                                                        })
            if result_drafts:
                log.info(f'{len(result_drafts)} found containing {sig.meta.name} after filtering')
                for result in result_drafts:
                    results.append(result)
        if results:
            results = _deduplicate(results)
            log.log_info(f'{len(results)} total matches found after filtering')
            return results
        else:
            log.log_info('No matches found after filtering')
    except Exception as e:
        log.log_critical(e)


def find_shared_channels(slack_connection: SlackAPI) -> [conversation.Conversation]:
    """ Find all shared channels. These could be either shared between
    Workspaces in an Enterprise Grid, or Slack Connect external channels.

    Args:
        slack_connection: Slack API object
    Returns:
        List containing information on all external shared channels
    """

    channels = slack_connection.get_all_conversations(ext_shared=True)

    results = []

    for channel in channels:
        conversation_info = slack_connection.get_conversation_info(channel_id=channel.get('id'))[0]
        connected_teams = []
        for team in conversation_info.get('shared').get('connected_team_ids'):
            team_info = slack_connection.get_team_info(team)
            if team_info.get('id').startswith('E'):
                connected_teams.append(enterprise.create_from_dict(team_info))
            else:
                connected_teams.append(workspace.create_from_dict(team_info))

        results.append(conversation.create_from_dict(conversation_info))

    return results


def get_all_messages(slack_connection: SlackAPI,
                     cores: int,
                     timeframe: int = DEFAULT_TIMEFRAME) -> [post.Message]:
    """ Get all messages in the Enterprise for a given timeframe

    Args:
        timeframe: timeframe to search in
        slack_connection: Slack API object
        cores: number of cores to use
    Returns:
        list of Message objects containing all drafts
    """

    results = multiprocessing.Manager().list()
    updated_conversations = slack_connection.get_recent_conversations(latest=timeframe)
    list_of_chunks = numpy.array_split(numpy.array(updated_conversations), cores)
    processes = []

    for conv_list in list_of_chunks:
        p = multiprocessing.Process(
            target=_mp_message_search_worker,
            args=(
                conv_list,
                slack_connection,
                timeframe,
                results
            )
        )
        processes.append(p)
        p.start()

    for process in processes:
        process.join()

    return results


def get_all_files(slack_connection: SlackAPI,
                  cores: int,
                  timeframe: int = DEFAULT_TIMEFRAME) -> [post.File]:
    """ Get all files in the Enterprise for a given timeframe

    Args:
        timeframe: timeframe to search in
        slack_connection: Slack API object
        cores: Number of cores to use
    Returns:
        list of File objects containing all drafts
    """

    results = multiprocessing.Manager().list()
    updated_files = slack_connection.list_files(oldest=timeframe)
    list_of_chunks = numpy.array_split(numpy.array(updated_files), cores)
    processes = []

    for file_list in list_of_chunks:
        p = multiprocessing.Process(
            target=_mp_file_search_worker,
            args=(
                file_list,
                slack_connection,
                results
            )
        )
        processes.append(p)
        p.start()

    for process in processes:
        process.join()

    return results


def get_all_drafts(slack_connection: SlackAPI,
                   workspaces_list: [workspace.Workspace],
                   cores: int,
                   timeframe: int = DEFAULT_TIMEFRAME) -> [post.Draft]:
    """ Get all drafts in the Enterprise for a given timeframe

    Args:
        timeframe: timeframe to search in
        slack_connection: Slack API object
        workspaces_list: List of all workspaces in the Enterprise
        cores: Number of cores to use
    Returns:
        list of Draft objects containing all drafts
    """

    results = multiprocessing.Manager().list()
    list_of_chunks = numpy.array_split(numpy.array(workspaces_list), cores)
    processes = []

    for workspace in list_of_chunks:
        p = multiprocessing.Process(
            target=_mp_draft_search_worker,
            args=(
                workspace,
                slack_connection,
                timeframe,
                results
            )
        )
        processes.append(p)
        p.start()

    for process in processes:
        process.join()

    return results


def _message_block_search(message: dict, query: str) -> bool:
    """ Searches to see if a message contains blocks if it doesn't contain text.
    Also looks for blocks when the text string is:
        'This content can’t be displayed.'

    Then searches for the signature query string in the text that is found

    Args:
        message: Message to search for blocks in
        query: Query string to discover in text
    Returns:
        True if the query is in text, False if not
    """

    if message.get('client_msg_id'):
        if str(query.lower()) in message.get('text').lower():
            return True
        else:
            return False
    elif message.get('bot_id') and \
            (not message.get('text') or message.get('text') == 'This content can’t be displayed.'):
        if not message.get('blocks'):
            return False
        else:
            for block in message.get('blocks'):
                if block.get('text'):
                    if str(query.lower()) in block.get('text').get('text').lower():
                        return True


def _regex_search_message(message: dict, regex: re.Pattern) -> str:
    """ Search a post text for matches against the regex

    Args:
        message: Post to look for text in
        regex: Complied regex object
    Returns:
        Regex match string if found, nothing if not
    """

    if not message.get('text') or message.get('text') == 'This content can’t be displayed.':
        if message.get('blocks'):
            for block in message.get('blocks'):
                if block.get('text'):
                    if regex.search(str(block.get('text').get('text'))):
                        return regex.search(str(block.get('text').get('text'))).group(0)
    elif regex.search(str(message.get('text'))):
        return regex.search(str(message.get('text'))).group(0)


# Multiprocessing Worker Functions
def _mp_draft_search_worker(workspaces_list: [workspace.Workspace],
                            slack_connection: SlackAPI,
                            timeframe: int,
                            results: list):
    """ MULTIPROCESSING WORKER - Iterates through a workspace and returns all draft
    messages.

    Args:
        workspaces_list: List of workspace Objects
        slack_connection: Slack API connection
        timeframe: Furthest back time to get messages from
        results: MP results list to pass back to calling function
    Returns:
        List of draft objects
    """

    for workspace in workspaces_list:
        workspace_drafts = slack_connection.list_drafts(workspace.id, oldest=timeframe)
        for draft_info in workspace_drafts:
            if draft_info.get('date_created') >= timeframe:
                results.append(post.create_draft_from_dict(draft_info))

    return results


def _mp_message_search_worker(conv_list: list,
                              slack_connection: SlackAPI,
                              timeframe: int,
                              results: list):
    """ MULTIPROCESSING WORKER - Iterates through a list of conversation IDs
    and gets recent messages for each

    Args:
        conv_list: List of output from discovery.conversations.recent endpoint
        slack_connection: Slack API object
        timeframe: Furthest back time to get messages from
        results: MP results list to pass back to calling function
    Returns:
        List of messages from each recently updated conversation
    """

    for conv in conv_list:
        message_list = slack_connection.get_conversation_history(conv.get('id'), conv.get('team'), oldest=timeframe)
        for message in message_list:
            if not message.get('files') and not message.get('subtype'):
                message['conv_id'] = conv.get('id')
                message['conv_team'] = conv.get('team')
                results.append(message)
    return results


def _mp_file_search_worker(file_list: list,
                           slack_connection: SlackAPI,
                           results: list) -> list:
    """ MULTIPROCESSING WORKER - Iterates through a list of conversation IDs
    and gets recent messages for each

    Args:
        file_list: List of file information in dict format from the discovery.files.list endpoint
        slack_connection: Slack API object
        results: MP results list to pass back to calling function
    Returns:
        List of File objects
    """

    for f in file_list:
        file_info = slack_connection.get_file_info(f.get('id'))
        shares = []
        if file_info.get('shares'):
            for share in file_info.get('shares'):
                if share.get('channel').startswith('D'):
                    team_id = get_enterprise(slack_connection).id
                else:
                    team_id = share.get('team')
                conv = slack_connection.get_conversation_info(share.get('channel'), team_id)[0]
                shares.append(conversation.create_from_dict(conv))
            file_info['shares'] = shares
            results.append(post.create_file_from_dict(file_info))

    return results


def _mp_find_messages_worker(sig: signature.Signature,
                             slack_connection: SlackAPI,
                             users_list: [user.User],
                             message_list: [dict],
                             workspaces_list: [workspace.Workspace],
                             results):
    """ MULTIPROCESSING WORKER - Iterates through lists of messages to find matches against a signature

    Args:
        sig: Signature objects
        users_list: List of User objects from the Enterprise
        message_list: List of Message objects
        workspaces_list: List of Workspaces objects from the Enterprise
        results: MP results list to pass back to calling function
    Returns:
        List of Message objects that match the signature
    """

    for query in sig.search_strings:
        message_list = [message for message in message_list if _message_block_search(message, query)]
        for message in message_list:
            r = re.compile(sig.pattern)
            workspace = next(
                (item for item in workspaces_list if item.id == message.get('team')), None)

            match_string = _regex_search_message(message, r)
            if match_string:
                conv_info = slack_connection.get_conversation_info(message.get('conv_id'),
                                                                   message.get('conv_team'))[0]

                shared = []
                if conv_info.get('shared').get('shared_team_ids'):
                    for wrk_id in conv_info.get('shared').get('shared_team_ids'):
                        shared.append(slack_connection.get_team_info(wrk_id))
                conv_info['shared'] = shared
                conv_info = conversation.create_from_dict(conv_info)
                message['conversation'] = conv_info
                message = post.create_message_from_dict(message)
                post_user = next(
                    (item for item in users_list if item.id == message.user), None)
                post_user.workspaces = []

                if workspace:
                    url = f'https://{workspace.domain}.slack.com/archives/{message.conversation.id}' \
                          f'/p{message.timestamp}'
                else:
                    url = None
                if _location_verification(message.conversation, sig):
                    results.append({
                        'match_string': match_string,
                        'message': message,
                        'url': url,
                        'user': post_user,
                        'workspace': workspace
                    })

    return results


def _mp_find_files_worker(sig: signature.Signature,
                          users_list: [user.User],
                          file_list: [post.File],
                          results):
    """ MULTIPROCESSING WORKER - Iterates through lists of files to find matches against a signature

    Args:
        sig: Signature objects
        users_list: List of User objects from the Enterprise
        file_list: List of File objects
        results: MP results list to pass back to calling function
    Returns:
        List of files that have matched the given signature

    """

    for query in sig.search_strings:
        for target_file in file_list:
            if sig.file_types:
                for file_type in sig.file_types:
                    if file_type.lower() in target_file.filetype.lower() \
                            and str(query.lower()) in target_file.title.lower():
                        for conv in target_file.shares:
                            if _location_verification(conv, sig):
                                file_user = next((item for item in users_list if item.id == target_file.user),
                                                 None)
                                file_user.workspaces = []
                                results_dict = {
                                    'file': target_file,
                                    'conversation': conv,
                                    'user': file_user
                                }

                                results.append(results_dict)
            else:
                if str(query.lower()) in target_file.title.lower():
                    for conv in target_file.shares:
                        if _location_verification(conv, sig):
                            file_user = next((item for item in users_list if item.id == target_file.user),
                                             None)
                            file_user.workspaces = []
                            results_dict = {
                                'file': target_file,
                                'conversation': conv,
                                'user': file_user
                            }

                            results.append(results_dict)

    return results
