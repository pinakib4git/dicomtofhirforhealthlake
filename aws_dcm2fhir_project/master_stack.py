from aws_cdk import (
    Stack,
    aws_cloudformation as cfn
)
from constructs import Construct
from aws_dcm2fhir_project.aws_s3event_bucket_stack import S3BucketStackEvent
from aws_dcm2fhir_project.aws_stepfunction_stack import StepFunctionStack
from aws_dcm2fhir_project.aws_eventbridge_new_stack import EventBridgeStack
from aws_dcm2fhir_project.aws_lambda_stack import LambdaIAMStack
from aws_dcm2fhir_project.aws_kmskey_stack import KMSKeyStack
from aws_dcm2fhir_project.aws_healthlake_stack import HealthLakeStack
from aws_dcm2fhir_project.aws_s3_stack import S3BucketStack
import json
import os
import uuid

class MasterStack(Stack):
    def __init__(self, scope: Construct, id: str, environment: str = None, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        # Get environment from context or use default
        env = environment or "dev"
        
        # Create a unique identifier for resources based on stack ID
        # This ensures resources have unique names across deployments
        stack_name = Stack.of(self).stack_name
        
        # Use provided suffix or generate a short unique identifier (first 3 chars of a UUID)
        unique_id = str(uuid.uuid4())[:3]
        
        # Create resource prefix with environment, stack name and unique ID
        resource_prefix_var = f"{env}-{unique_id}"

        # Create KMS stack first (if other stacks depend on it)
        kms_stack = KMSKeyStack(self, "KMSStack", resource_prefix=resource_prefix_var)

        # Create the S3 bucket which leads the Eventbridge Rule
        s3_event = S3BucketStackEvent(self, "S3BucketEventStack", resource_prefix=resource_prefix_var)

        # Create S3 bucket stack
        s3_stack = S3BucketStack(self, "S3BucketStack", resource_prefix=resource_prefix_var)

        # Create Step Functions stack
        step_functions_stack = StepFunctionStack(self, "StepFunctionsStack" , resource_prefix=resource_prefix_var)

        # Create the HealthLake stack
        healthlake_stack = HealthLakeStack(self, "HealthLakeStack" , resource_prefix=resource_prefix_var)
        
        # Create Lambda stack
        lambda_stack = LambdaIAMStack(
            self, 
            "LambdaIAMStack",
            healthlake_datastore_id=healthlake_stack.healthlake_datastore_id,
            healthlake_datastore_arn=healthlake_stack.healthlake_datastore_arn,
            kms_key=kms_stack.kms_key,
            resource_prefix=resource_prefix_var
        )

        # Create EventBridge stack with dependencies from other stacks
        eventbridge_stack = EventBridgeStack(
            self, 
            "EventBridgeStack", 
            source_bucket=s3_event.event_bucket,
            source_bucket_name= s3_event.bucket_name,
            processing_workflow=step_functions_stack.state_machine,
            resource_prefix=resource_prefix_var,
            env=self.node.try_get_context("env")
        )
