import time
from dataclasses import dataclass
from typing import Optional, Dict


def _convert_timestamp(timestamp: str or int) -> str or None:
    """ Converts epoch timestamp into human-readable time

    Args:
        timestamp: epoch timestamp in seconds
    Returns:
        String time in the format YYYY-mm-dd hh:mm:ss
    """

    if timestamp:
        if isinstance(timestamp, str):
            timestamp = timestamp.split('.', 1)[0]

        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(timestamp)))
    else:
        return None


@dataclass(slots=True)
class Workspace(object):
    """ Class that defines Workspaces objects. Workspaces are collections
    of conversations in a Slack Enterprise Organisation"""

    id: str
    name: str
    domain: str
    email_domain: str
    archived: bool
    created: int or float or str
    description: str
    url: str
    is_verified: Optional[bool] = None
    deleted: Optional[bool] = None
    discoverable: Optional[bool] = None
    enterprise_id: Optional[str] = None
    enterprise_domain: Optional[str] = None
    enterprise_name: Optional[str] = None
    is_enterprise: Optional[int] = None


@dataclass(slots=True)
class WorkspaceSuccinct(object):
    """ Class that defines Workspaces objects. Workspaces are collections
    of conversations in a Slack Enterprise Organisation"""

    id: str
    name: str
    domain: str
    email_domain: str
    archived: bool
    created: int or float or str
    description: str
    url: str


def create_from_dict(workspace_dict: Dict, verbose: bool) -> Workspace or WorkspaceSuccinct:
    """ Return a Workspace object based off an input dictionary

    Args:
        workspace_dict: dictionary/JSON formatted representation of the
            workspace.
        verbose: Whether verbose logging has been selected or not
    Returns:
        Workspace object representing the workspace
    """

    if verbose:
        return Workspace(
            id=workspace_dict.get('id'),
            name=workspace_dict.get('name'),
            domain=workspace_dict.get('domain'),
            email_domain=workspace_dict.get('email_domain'),
            is_verified=workspace_dict.get('is_verified'),
            archived=workspace_dict.get('archived'),
            deleted=workspace_dict.get('deleted'),
            discoverable=workspace_dict.get('discoverable'),
            enterprise_id=workspace_dict.get('enterprise_id'),
            enterprise_domain=workspace_dict.get('enterprise_domain'),
            enterprise_name=workspace_dict.get('enterprise_name'),
            is_enterprise=workspace_dict.get('is_enterprise'),
            created=_convert_timestamp(workspace_dict.get('created')),
            description=workspace_dict.get('description'),
            url=f'https://{workspace_dict.get("enterprise_domain")}'
                f'.enterprise.slack.com/workspace/{workspace_dict.get("id")} '
        )
    else:
        return WorkspaceSuccinct(
            id=workspace_dict.get('id'),
            name=workspace_dict.get('name'),
            domain=workspace_dict.get('domain'),
            email_domain=workspace_dict.get('email_domain'),
            archived=workspace_dict.get('archived'),
            created=_convert_timestamp(workspace_dict.get('created')),
            description=workspace_dict.get('description'),
            url=f'https://{workspace_dict.get("enterprise_domain")}'
                f'.enterprise.slack.com/workspace/{workspace_dict.get("id")} '
        )
