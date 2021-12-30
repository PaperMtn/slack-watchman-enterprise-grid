import pathlib
import yaml
from dataclasses import dataclass


@dataclass
class Signature(object):
    """ Class that handles loaded signature objects. Signatures
    define what to search for in Slack and where to search for it.
    They also contain regex patterns to validate data that is found"""

    __slots__ = [
        'filename',
        'enabled',
        'meta',
        'tombstone',
        'scope',
        'file_types',
        'locations',
        'test_cases',
        'search_strings',
        'pattern'
    ]

    filename: str
    enabled: bool
    meta: dataclass
    tombstone: bool
    scope: list
    file_types: list
    locations: list
    test_cases: dataclass
    search_strings: str
    pattern: str

    def __repr__(self):
        return f'{self.__class__.__name__}({self.__dict__!r})'

    def __str__(self):
        return ' '.join(f'{k}: {v!s}' for k, v in self.__dict__.items())


@dataclass
class Meta(object):
    __slots__ = [
        'name',
        'author',
        'date',
        'version',
        'description',
        'severity'
    ]

    name: str
    author: str
    date: str
    version: str
    description: str
    severity: int


@dataclass
class TestCases(object):
    __slots__ = [
        'match_cases',
        'fail_cases',
    ]

    match_cases: list
    fail_cases: list


def load_from_yaml(sig_path: pathlib.PosixPath) -> Signature:
    """Load YAML file and return a Signature object

    Args:
        sig_path: Path of YAML file
    Returns:
        Signature object with fields populated from the YAML
        signature file
    """

    with open(sig_path) as yaml_file:
        yaml_import = yaml.safe_load(yaml_file)

        meta = Meta(
            name=yaml_import.get('meta').get('name'),
            author=yaml_import.get('meta').get('author'),
            date=yaml_import.get('meta').get('date'),
            version=yaml_import.get('meta').get('version'),
            description=yaml_import.get('meta').get('description'),
            severity=yaml_import.get('meta').get('severity')
        )

        test_cases = TestCases(
            match_cases=yaml_import.get('test_cases').get('match_cases'),
            fail_cases=yaml_import.get('test_cases').get('fail_cases')
        )

        rule = Signature(filename=yaml_import.get('filename'),
                         enabled=yaml_import.get('enabled'),
                         meta=meta,
                         tombstone=yaml_import.get('tombstone'),
                         scope=yaml_import.get('scope'),
                         file_types=yaml_import.get('file_types'),
                         locations=yaml_import.get('locations'),
                         test_cases=test_cases,
                         search_strings=yaml_import.get('search_strings'),
                         pattern=yaml_import.get('pattern'))
    return rule
