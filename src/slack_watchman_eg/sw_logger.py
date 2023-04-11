import json
import dataclasses
import logging
import sys
import logging.handlers
import re
import traceback
from logging import Logger
from typing import Any, Dict
from colorama import Fore, Back, Style, init


class StdoutLogger:
    def __init__(self, **kwargs):
        self.debug = kwargs.get('debug')
        self.print_header()
        init()

    def log(self,
            mes_type: str,
            message: Any,
            **kwargs) -> None:

        notify_type = kwargs.get('notify_type')

        if not self.debug and mes_type == 'DEBUG':
            return

        if dataclasses.is_dataclass(message):
            message = dataclasses.asdict(message)

        if notify_type == 'enterprise':
            message = f'ENTERPRISE: \n' \
                      f'    ID: {message.get("id")}  ' \
                      f'NAME: {message.get("name")}  ' \
                      f'DOMAIN: {message.get("domain")}  ' \
                      f'URL: {message.get("url")}'
            mes_type = 'ENTERPRISE'
        if notify_type == "workspace":
            message = f'WORKSPACE: \n' \
                      f'    ID: {message.get("id")}  ' \
                      f'NAME: {message.get("name")}  ' \
                      f'DOMAIN: {message.get("domain")}  ' \
                      f'URL: {message.get("url")}'
            mes_type = 'WORKSPACE'
        if notify_type == "result":
            if message.get('message'):
                if message.get('message').get('conversation').get('is_im'):
                    conversation_type = 'Direct Message'
                elif message.get('message').get('conversation').get('is_private'):
                    conversation_type = 'Private Channel'
                else:
                    conversation_type = 'Public Channel'

                message = 'POST_TYPE: Message ' \
                          f'POTENTIAL_SECRET: {message.get("match_string")} ' \
                          f'POSTED_BY: {message.get("user").get("email")} ' \
                          f'POSTED_ON: {message.get("message").get("created")} ' \
                          f'WORKSPACE: {message.get("workspace").get("name")} ' \
                          f'CONVERSATION: {message.get("message").get("conversation").get("name")} ' \
                          f'CONVERSATION_TYPE: {conversation_type} ' \
                          f'URL: {message.get("url")}'
            elif message.get('file'):
                if message.get('conversation').get('is_im'):
                    conversation_type = 'Direct Message'
                elif message.get('conversation').get('is_private'):
                    conversation_type = 'Private Channel'
                else:
                    conversation_type = 'Public Channel'

                message = 'POST_TYPE: File ' \
                          f'FILE_NAME: {message.get("file").get("name")} ' \
                          f'POSTED_BY: {message.get("user").get("email")} ' \
                          f'CREATED: {message.get("file").get("created")} ' \
                          f'CONVERSATION: {message.get("conversation").get("name")} ' \
                          f'CONVERSATION_TYPE: {conversation_type} ' \
                          f'URL: {message.get("file").get("url_private_download")} '
            elif message.get('draft'):
                message = 'POST_TYPE: Draft ' \
                          f'POTENTIAL_SECRET: {message.get("match_string")} ' \
                          f'CREATED_BY: {message.get("user").get("email")} ' \
                          f'CREATED_ON: {message.get("draft").get("created")} '
            mes_type = 'RESULT'
        if notify_type == "user":
            return

        try:
            self.log_to_stdout(message, mes_type)
        except Exception as e:
            print(e)
            print('Cannot print certain characters to command line - see log file for full unicode encoded log line')
            self.log_to_stdout(message, mes_type)

    def log_to_stdout(self,
                      message: Any,
                      mes_type: str) -> None:

        try:

            reset_all = Style.NORMAL + Fore.RESET + Back.RESET
            key_color = Fore.WHITE
            base_color = Fore.WHITE
            high_color = Fore.WHITE
            style = Style.NORMAL

            if mes_type == "NOTIFY":
                base_color = Fore.CYAN
                high_color = Fore.CYAN
                key_color = Fore.CYAN
                style = Style.NORMAL
            elif mes_type == "INFO" or mes_type == 'USER':
                base_color = Fore.WHITE
                high_color = Fore.WHITE
                key_color = Fore.WHITE
                style = Style.DIM
                mes_type = '-'
            elif mes_type == "ENTERPRISE" or mes_type == 'WORKSPACE':
                base_color = Fore.LIGHTBLUE_EX
                high_color = Fore.LIGHTBLUE_EX
                key_color = Fore.LIGHTBLUE_EX
                style = Style.NORMAL
                mes_type = '+'
            elif mes_type == "WARNING":
                base_color = Fore.YELLOW
                high_color = Fore.YELLOW
                key_color = Fore.YELLOW
                style = Style.NORMAL
            elif mes_type == "SUCCESS":
                base_color = Fore.LIGHTGREEN_EX
                high_color = Fore.LIGHTGREEN_EX
                key_color = Fore.LIGHTGREEN_EX
                style = Style.NORMAL
                mes_type = '>>'
            elif mes_type == "DEBUG":
                base_color = Fore.WHITE
                high_color = Fore.WHITE
                key_color = Fore.WHITE
                style = Style.DIM
                mes_type = '#'
            elif mes_type == "ERROR":
                base_color = Fore.MAGENTA
                high_color = Fore.MAGENTA
                key_color = Fore.MAGENTA
                style = Style.NORMAL
            elif mes_type == "CRITICAL":
                base_color = Fore.RED
                high_color = Fore.RED
                key_color = Fore.RED
                style = Style.NORMAL
            elif mes_type == "RESULT":
                base_color = Fore.LIGHTGREEN_EX
                high_color = Fore.LIGHTGREEN_EX
                key_color = Fore.LIGHTGREEN_EX
                style = Style.NORMAL
                mes_type = '!'

            # Make log level word/symbol coloured
            type_colorer = re.compile(r'([A-Z]{3,})', re.VERBOSE)
            mes_type = type_colorer.sub(high_color + r'\1' + base_color, mes_type.lower())
            # Make header words coloured
            header_words = re.compile('([A-Z_0-9]{2,}:)\s', re.VERBOSE)
            message = header_words.sub(key_color + Style.BRIGHT + r'\1 ' + Fore.WHITE + Style.NORMAL, str(message))
            sys.stdout.write(
                f"{reset_all}{style}[{base_color}{mes_type}{Fore.WHITE}]{style} {message}{Fore.WHITE}{Style.NORMAL}\n")
        except Exception:
            if self.debug:
                traceback.print_exc()
                sys.exit(1)
            print('Formatting error')

    def print_header(self) -> None:
        print(" ".ljust(79) + Style.BRIGHT)

        print(
            """
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣀⣀⣀⣀⡀⠀⠀⠀⠀⠀⠀⠀
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⠾⠛⢉⣉⣉⣉⡉⠛⠷⣦⣄⠀⠀⠀⠀
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⠋⣠⣴⣿⣿⣿⣿⣿⡿⣿⣶⣌⠹⣷⡀⠀⠀
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣼⠁⣴⣿⣿⣿⣿⣿⣿⣿⣿⣆⠉⠻⣧⠘⣷⠀⠀
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⡇⢰⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠀⠀⠈⠀⢹⡇⠀
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡇⢸⣿⠛⣿⣿⣿⣿⣿⣿⡿⠃⠀⠀⠀⠀⢸⡇⠀
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⣷⠀⢿⡆⠈⠛⠻⠟⠛⠉⠀⠀⠀⠀⠀⠀⣾⠃⠀
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⣧⡀⠻⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣼⠃⠀⠀
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢼⠿⣦⣄⠀⠀⠀⠀⠀⠀⠀⣀⣴⠟⠁⠀⠀⠀
        ⠀⠀⠀⠀⠀⠀⠀⠀⣠⣾⣿⣦⠀⠀⠈⠉⠛⠓⠲⠶⠖⠚⠋⠉⠀⠀⠀⠀⠀⠀
        ⠀⠀⠀⠀⠀⠀⣠⣾⣿⣿⠟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠀⠀⠀⠀⣠⣾⣿⣿⠟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠀⠀⠀⣾⣿⣿⠟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠀ ⠈⠛⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        """
        )
        print('   Slack Watchman for Enterprise Grid     ')
        print(Style.DIM + '   Detect exposed secrets in Slack Enterprise Grid      ' + Style.RESET_ALL)
        print('  ')
        print(Style.BRIGHT + '   by PaperMtn - GNU General Public License')
        print(' '.ljust(79) + Fore.GREEN)


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


class JSONLogger(Logger):
    def __init__(self, name: str = 'Slack Watchman for Enterprise Grid', **kwargs):
        super().__init__(name)
        self.notify_format = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "NOTIFY", "scope": "%(scope)s", "severity": '
            '"%(severity)s", "detection_type": "%(type)s", "detection_data": %(message)s}')
        self.info_format = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}')
        self.success_format = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "SUCCESS", "message": "%(message)s"}')
        self.logger = logging.getLogger(self.name)
        self.handler = logging.StreamHandler(sys.stdout)
        self.logger.addHandler(self.handler)
        if kwargs.get('debug'):
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)

    def bind(self):
        pass

    def log(self,
            level: str,
            log_data: str or Dict,
            **kwargs):
        if level.upper() == 'NOTIFY':
            self.handler.setFormatter(self.notify_format)
            self.logger.info(
                json.dumps(
                    log_data,
                    cls=EnhancedJSONEncoder),
                extra={
                    'scope': kwargs.get('scope', ''),
                    'type': kwargs.get('detect_type', ''),
                    'severity': kwargs.get('severity', '')})
        elif level.upper() == 'INFO':
            self.handler.setFormatter(self.info_format)
            self.logger.info(log_data)
        elif level.upper() == 'DEBUG':
            self.handler.setFormatter(self.info_format)
            self.logger.debug(log_data)
        elif level.upper() == 'SUCCESS':
            self.handler.setFormatter(self.success_format)
            self.logger.info(log_data)
        else:
            self.handler.setFormatter(self.info_format)
            self.logger.critical(log_data)
