"""Convenience Python module for AWS Organisations & STS

## Example

    from onnlogger import Loggers

    # Create a `Loggers` object and pass it into `Orgs`
    logger = Loggers(logger_name='Orgs', console_logger=True, log_level='INFO', log_file_path='/tmp/log')
    orgs = Orgs(logger)

    # Get a list of AWS accounts
    account_list = orgs.get_aws_accounts()
    print(account_list)
    [{'Arn': 'arn:aws:organizations::098765432109:account/o-345jk6d2fa/6834032126350',
     'Email': 'example@example.com',
     'Id': '123456789012',
     'JoinedMethod': 'CREATED',
     'JoinedTimestamp': datetime.datetime(2020, 1, 13, 13, 59, 46, 540000, tzinfo=tzlocal()),
     'Name': 'John Doe',
     'Status': 'ACTIVE'}]

     # Assume a role
     assumed_credentials = orgs.assume_role('098765432109', 'demo')

     # Use the assumed credentials to create a Boto3 resource
     assumed_s3 = orgs.get_assumed_client('s3', assumed_credentials)

     # Use the resource to list S3 buckets in the assumed account
     bucket_list = assumed_s3.buckets.all()
     for bucket in bucket_list:
         print(bucket_object)

## Installation

    pip3 install onnawsorgs

## Contact

* Code: [onnawsorgs](https://github.com/OzNetNerd/onnawsorgs)
* Blog: [oznetnerd.com](https://oznetnerd.com)
* Email: [will@oznetnerd.com](mailto:will@oznetnerd.com)


"""

from .orgs import Orgs