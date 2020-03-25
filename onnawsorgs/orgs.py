import boto3
import sys
from botocore.exceptions import ClientError
from pprint import pformat


class Orgs:
    def __init__(self, logger):
        """Description:
            Convenience Python module for AWS Organisations

        Args:
            logger (onnlogger.Loggers): An instance of `onnlogger.Loggers`

        Example:
            Example usage:

                from onnlogger import Loggers

                logger = Loggers(logger_name='Orgs', console_logger=True, log_level='INFO', log_file_path='/tmp/log')
                orgs = Orgs(logger)
        """
        self.logger = logger
        self.org = boto3.client('organizations')
        self.sts = boto3.client('sts')

    def get_aws_accounts(self) -> list:
        """Description:
            List of all AWS Organization accounts

            Automatically paginates through all AWS accounts and returns the results as a list

        Example:
            Example usage:

                orgs.get_aws_accounts()
                [{'Arn': 'arn:aws:organizations::098765432109:account/o-345jk6d2fa/6834032126350',
                 'Email': 'example@example.com',
                 'Id': '123456789012',
                 'JoinedMethod': 'CREATED',
                 'JoinedTimestamp': datetime.datetime(2020, 1, 13, 13, 59, 46, 540000, tzinfo=tzlocal()),
                 'Name': 'John Doe',
                 'Status': 'ACTIVE'}]

        Returns:
            [List of all AWS Organization accounts](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/organizations.html#Organizations.Client.list_accounts)
        """
        next_token = dict()
        account_info = []

        self.logger.entry('info', 'Getting AWS Organization account numbers...')
        while True:
            accounts = self.org.list_accounts(**next_token)
            found_accounts = accounts['Accounts']
            account_info = account_info + found_accounts
            get_token = accounts.get('NextToken')

            if get_token:
                next_token['NextToken'] = get_token

            else:
                break

        return account_info

    def assume_role(self, account_id, role_session_name, account_role='OrganizationAccountAccessRole') -> dict:
        """Description:
            Assumes a role in an another account

        Args:
            account_id (str): ID of the account assuming into
            role_session_name (str): Name of the assume session
            account_role (str): Account to assume in `account_id`

        Example:
            Example usage:

                orgs.assume_role('098765432109', 'demo')
                {'AccessKeyId': 'ASIATWQY7MABPWBJYKGX',
                 'Expiration': datetime.datetime(2020, 3, 25, 12, 30, 57, tzinfo=tzutc()),
                 'SecretAccessKey': 'kKJ(324kljd,sfs.sl32423489/dakwu423nsdf',
                 'SessionToken': 'FwoGZf35YXdzEI3//////////wEaDBQJZuRBd0ja6UFC'}


        Returns:
            [Temporary API credentials](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sts.html#STS.Client.assume_role)
        """
        role_arn = f'arn:aws:iam::{account_id}:role/{account_role}'
        self.logger.entry('info', f'Assuming role ARN: {role_arn}...')

        try:
            assumed_role_object = self.sts.assume_role(
                RoleArn=role_arn,
                RoleSessionName=role_session_name,
            )

            assumed_credentials = assumed_role_object['Credentials']
            self.logger.entry('debug', f'Assumed credentials:\n{pformat(assumed_credentials)}')

            return assumed_credentials

        except ClientError as e:
            self._aws_exception_msg(e)

    @staticmethod
    def _aws_exception_msg(e):
        msg = e.response['Error']['Message']
        sys.exit(f'Error: {msg}')