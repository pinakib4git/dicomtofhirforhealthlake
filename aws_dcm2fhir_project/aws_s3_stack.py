from aws_cdk import (
    Stack,
    NestedStack,
    aws_s3 as s3,
    aws_iam as iam,
    aws_s3_deployment as s3_deploy,
    RemovalPolicy,
    Duration,
    CfnOutput
)
from constructs import Construct

#get random number integer
from random import randint
import random

#generate the random number
random_number = randint(10, 99)


class S3BucketStack(NestedStack):
    def __init__(self, scope: Construct, id: str, resource_prefix: str = None, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        empty_dir = "C:\\Users\\bpinaki\\Documents\\HCLS\\TFC\\aws-dcm2fhir-project\\aws_dcm2fhir_project\\emptyfolder"
        # Create S3 bucket-1 with configuration matching your existing bucket
        bucket1 = s3.Bucket(
            self, "MyConfiguredBucket1",
            bucket_name= f"{resource_prefix}-new-my-fhir-bucket",  # Remove for auto-generated name
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY
            )

        # Create folder structure using empty files inside bucket-1
        folder_structure = ["Custom-FHIR-Files/", "HealthLake-Output-Import/", "processed/", "logs/", "temp/"]
        s3_deploy.BucketDeployment(
            self, "CreateFolderStructure1",
            destination_bucket=bucket1,
            sources=[s3_deploy.Source.asset(empty_dir)],  # Empty directory
            destination_key_prefix="/".join(folder_structure),
            retain_on_delete=False
        )

        # Output important information
        CfnOutput(self, "BucketARN1", value=bucket1.bucket_arn)
        CfnOutput(self, "BucketURL1", value=bucket1.bucket_website_url)


        # Create S3 bucket-3 with configuration matching your existing bucket
        bucket3 = s3.Bucket(
            self, "MyConfiguredBucket3",
            bucket_name= f"{resource_prefix}-new-dicom-job-output-lake",  # Remove for auto-generated name
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY
            )

        # Create folder structure using empty files inside bucket-3
        folder_structure = ["outputfiles/", "processed/", "logs/", "temp/"]
        s3_deploy.BucketDeployment(
            self, "CreateFolderStructure3",
            destination_bucket=bucket3,
            sources=[s3_deploy.Source.asset(empty_dir)],  # Empty directory
            destination_key_prefix="/".join(folder_structure),
            retain_on_delete=False
        )

        # Output important information
        CfnOutput(self, "BucketARN3", value=bucket3.bucket_arn)
        CfnOutput(self, "BucketURL3", value=bucket3.bucket_website_url)