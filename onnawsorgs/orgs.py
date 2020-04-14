import boto3
import sys
import csv
import re
from botocore.exceptions import ClientError
from pprint import pformat
from onnmisc import csv_to_list
from time import sleep


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
        self.root_account_id = boto3.client('sts').get_caller_identity().get('Account')

    def get_accounts(self) -> list:
        """Description:
            List of all AWS Organization accounts

            Automatically paginates through all AWS accounts and returns the results as a list

        Example:
            Example usage:

                account_list = orgs.get_accounts()
                print(account_list)
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

                assumed_credentials = orgs.assume_role('098765432109', 'demo')
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

    def get_assumed_client(self, service_name, assumed_credentials, **kwargs):
        """Description:
            Creates a client object using an assumed role

        Args:
            service_name (str): AWS service name
            assumed_credentials (dict): `assume_role` dict
            kwargs (dict): [Session parameters](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/core/session.html)

        Example:
            Example usage:

                assumed_credentials = orgs.assume_role('098765432109', 'demo')
                assumed_s3 = orgs.get_assumed_client('s3', assumed_credentials)
                bucket_list = assumed_s3.list_buckets()

        Returns:
            Boto3 client
        """

        self.logger.entry('info', f'Creating "{service_name}" client object...')

        assumed_client = boto3.client(
            service_name,
            aws_access_key_id=assumed_credentials['AccessKeyId'],
            aws_secret_access_key=assumed_credentials['SecretAccessKey'],
            aws_session_token=assumed_credentials['SessionToken'],
            **kwargs,
        )

        return assumed_client

    def get_assumed_resource(self, service_name, assumed_credentials, **kwargs):
        """Description:
            Creates a resource object using an assumed role

        Args:
            service_name (str): AWS service name
            assumed_credentials (dict): `assume_role` dict
            kwargs (dict): [Session parameters](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/core/session.html)

        Example:
            Example usage:

                assumed_credentials = orgs.assume_role('098765432109', 'demo')
                assumed_s3 = orgs.get_assumed_client('s3', assumed_credentials)
                bucket_list = assumed_s3.buckets.all()
                for bucket in bucket_list:
                    print(bucket_object)

        Returns:
            Boto3 resource
        """

        self.logger.entry('info', f'Creating "{service_name}" resource object...')

        assumed_resource = boto3.resource(
            service_name,
            aws_access_key_id=assumed_credentials['AccessKeyId'],
            aws_secret_access_key=assumed_credentials['SecretAccessKey'],
            aws_session_token=assumed_credentials['SessionToken'],
            **kwargs,
        )

        return assumed_resource

    def accounts_to_csv(self, account_ids, output_file_path='aws_accounts.csv') -> None:
        """Description:
            Outputs AWS accounts in a CSV file

        Args:
            account_ids (list): `List` of account `dicts` (see `get_accounts`)
            output_file_path (str): Path and filename of where to output the CSV

        Example:
            Example usage:

                orgs.accounts_to_csv()

                # CSV file contents
                Id,Arn,Email,Name,Status,JoinedMethod,JoinedTimestamp
                123456789012,arn:aws:organizations::0987654321009:account/o-753jk6teq2/123456789012,john@example.com,John Doe,ACTIVE,CREATED,2020-01-13 13:58:39.542000+11:00

        Returns:
            None
        """
        self.logger.entry('info', 'Exporting accounts to CSV file...')
        headers = account_ids[0].keys()

        with open(output_file_path, 'w') as f:
            dict_writer = csv.DictWriter(f, headers)
            dict_writer.writeheader()
            dict_writer.writerows(account_ids)

    def create_accounts(self, input_file_path, sleep_time=5) -> list:
        """Description:
            Creates AWS accounts using information contained in a CSV file

            `RoleName` defaults to `OrganizationAccountAccessRole` and `IamUserAccessToBilling` defaults to `DENY`

        Args:
            input_file_path (str): Path to CSV file
            sleep_time (int):

        Example:
            Example CSV file:

                Email,AccountName,RoleName,IamUserAccessToBilling
                demo@example.com,demo,,
                demo2@example.com,demo2,,

            Example usage:

                from pprint import pprint
                create_statuses = orgs.create_accounts('new_accounts.csv')
                pprint(create_statuses)
                [{'CreateAccountStatus': {'AccountName': 'demo',
                                          'CompletedTimestamp': datetime.datetime(2020, 4, 14, 10, 49, 40, 484000, tzinfo=tzlocal()),
                                          'FailureReason': 'EMAIL_ALREADY_EXISTS',
                                          'Id': 'fse-jmh342kjdsf9231jhsakdi127rh210la',
                                          'RequestedTimestamp': datetime.datetime(2020, 4, 14, 10, 49, 40, 112000, tzinfo=tzlocal()),
                                          'State': 'FAILED'},
                  'ResponseMetadata': {'HTTPHeaders': {'content-length': '222',
                                                       'content-type': 'application/x-amz-json-1.1',
                                                       'date': 'Tue, 14 Apr 2020 00:49:51 GMT',
                                                       'x-amzn-requestid': 'sadjk3-kjdhasjkdh231-asjdhaskdh1'},
                                       'HTTPStatusCode': 200,
                                       'RequestId': 'sadjk3-kjdhasjkdh231-asjdhaskdh1',
                                       'RetryAttempts': 0}},
                 {'CreateAccountStatus': {'AccountId': '123456789012',
                                          'AccountName': 'demo2',
                                          'CompletedTimestamp': datetime.datetime(2020, 4, 14, 10, 49, 50, 59000, tzinfo=tzlocal()),
                                          'Id': 's42-kj342ufsdjfhsa87sdfj234821jhi3fd',
                                          'RequestedTimestamp': datetime.datetime(2020, 4, 14, 10, 49, 45, 901000, tzinfo=tzlocal()),
                                          'State': 'SUCCEEDED'},
                  'ResponseMetadata': {'HTTPHeaders': {'content-length': '213',
                                                       'content-type': 'application/x-amz-json-1.1',
                                                       'date': 'Tue, 14 Apr 2020 00:49:51 GMT',
                                                       'x-amzn-requestid': '3245df-dsfe54-435gd-324fds-fswdr4352'},
                                       'HTTPStatusCode': 200,
                                       'RequestId': '3245df-dsfe54-435gd-324fds-fswdr4352',
                                       'RetryAttempts': 0}}]

        Returns:
            list
        """
        status_ids = []

        self.logger.entry('info', f'Creating new accounts as per {input_file_path}...')
        new_accounts = csv_to_list(input_file_path)

        for account in new_accounts:
            email = account['Email']
            account_name = account['AccountName']
            role_name = account.get('RoleName') if account.get('RoleName') else 'OrganizationAccountAccessRole'
            access_billing = account.get('IamUserAccessToBilling') if account.get('IamUserAccessToBilling') else 'DENY'

            while True:
                self.logger.entry('debug', f'Creating role - Account name: {account_name}, Email: {email}, '
                                           f'Role: {role_name}, Access to billing: {access_billing}')

                try:
                    create_status = self.org.create_account(
                        Email=email,
                        AccountName=account_name,
                        RoleName=role_name,
                        IamUserAccessToBilling=access_billing
                    )

                    break

                except ClientError as e:
                    if e.response['Error']['Code'] == 'ConcurrentModificationException':
                        self.logger.entry('debug', f'Sleeping {sleep_time} seconds to avoid account creation '
                                                   f'conflicts...')
                        sleep(sleep_time)

            status_id = create_status['CreateAccountStatus']['Id']
            status_ids.append(status_id)

        create_statuses = self._get_account_statuses(status_ids)

        self.logger.entry('debug', f'Finished creating accounts:\n{pformat(create_statuses)}')

        return create_statuses

    def _get_account_statuses(self, status_ids, sleep_time=5) -> list:
        """Description:
            Ensures that the account creation process finishes

            See `create_accounts` for more information

        Args:
            status_ids: Output from `create_accounts`
            sleep_time (int): Seconds to sleep between checks

        Returns:
            list
        """
        results = []

        self.logger.entry('info', 'Checking the status of the account creations...')

        for status_id in status_ids:
            while True:
                get_status = self.org.describe_create_account_status(CreateAccountRequestId=status_id)
                creation_state = get_status['CreateAccountStatus']['State']
                account_name = get_status['CreateAccountStatus']['AccountName']

                if creation_state == 'IN_PROGRESS':
                    self.logger.entry('debug', f'Creation state for account name "{account_name}" is "IN_PROGRESS". '
                                               f'Sleeping for {sleep_time} seconds then will try again...')
                    sleep(sleep_time)
                    continue

                elif creation_state == 'SUCCEEDED':
                    self.logger.entry('debug', f'Successfully created account name "{account_name}"')
                    results.append(get_status)
                    break

                elif creation_state == 'FAILED':
                    failure_reason = get_status['CreateAccountStatus']['FailureReason']
                    self.logger.entry('warning', f'Failed to create account name "{account_name}": {failure_reason}')
                    results.append(get_status)
                    break

        return results

    def get_filtered_accounts(self, regex):
        """Description:
            Provides a filtered list of AWS accounts

            Args:
                regex (str): Regular expression to match the `Name` field

            Example:
                Example usage:

                    from pprint import pprint
                    regex = r'(^lab\\d*)'
                    matched_accounts = orgs.get_filtered_accounts(regex)
                    pprint(matched_accounts)
                    [{'Arn': 'arn:aws:organizations::123456789012:account/o-4235gfds3w1/098765432109',
                      'Email': 'lab44@example.com',
                      'Id': '789012345678',
                      'JoinedMethod': 'CREATED',
                      'JoinedTimestamp': datetime.datetime(2020, 4, 14, 12, 38, 58, 342000, tzinfo=tzlocal()),
                      'Name': 'lab44',
                      'Status': 'ACTIVE'}]

            Returns:
                dict
        """

        self.logger.entry('info', 'Getting filtered accounts...')

        matched_accounts = []
        all_accounts = self.get_accounts()

        for account in all_accounts:
            account_name = account['Name']

            try:
                re.search(regex, account_name).group(1)
                self.logger.entry('debug', f'Found match: {account_name}')
                matched_accounts.append(account)

            except AttributeError:
                pass

        self.logger.entry('debug', f'Matching accounts:\n{pformat(matched_accounts)}')

        return matched_accounts

    def extract_account_statuses(self, create_statuses) -> dict:
        """Description:
            Simplified account creation information

        Args:
            create_statuses: Output from `create_accounts`

        Example:
            Example usage:

                from pprint import pprint
                create_statuses = orgs.create_accounts('new_accounts.csv')
                statuses = orgs.extract_account_statuses(create_statuses)
                pprint(statuses)
                {'Failed': {'demo': 'EMAIL_ALREADY_EXISTS'}, 'Succeeded': ['demo2']}

        Returns:
            dict
        """
        self.logger.entry('info', f'Extracting account creation statuses...')

        statuses = {
            'Succeeded': [],
            'Failed': {},
        }

        for entry in create_statuses:
            account_name = entry['CreateAccountStatus']['AccountName']
            state = entry['CreateAccountStatus']['State']

            if state == 'SUCCEEDED':
                statuses['Succeeded'].append(account_name)

            elif state == 'FAILED':
                failure_reason = entry['CreateAccountStatus']['FailureReason']
                statuses['Failed'][account_name] = failure_reason

        self.logger.entry('debug', f'Account statuses:\n{pformat(statuses)}')
        return statuses

