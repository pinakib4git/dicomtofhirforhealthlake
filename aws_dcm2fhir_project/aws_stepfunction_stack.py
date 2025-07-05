from aws_cdk import (
    App,
    Stack,
    NestedStack,
    aws_stepfunctions as sfn,
    aws_iam as iam,
    aws_s3_assets as s3_assets,
    CfnOutput
)
from constructs import Construct
import json
import os
import uuid

class StepFunctionStack(NestedStack):
    def __init__(self, scope: Construct, id: str, resource_prefix: str = None, **kwargs) -> None:
        # Remove resource_prefix from kwargs before passing to parent
        filtered_kwargs = {k: v for k, v in kwargs.items() if k != 'resource_prefix'}
        super().__init__(scope, id, **filtered_kwargs)
        
        # Create IAM Role with dynamic name for Step Function
        step_function_role = iam.Role(
            self, "StepFunctionExecutionRole",
            role_name=f"{resource_prefix}-StepFunctionRole",
            assumed_by=iam.ServicePrincipal("states.amazonaws.com"),
            description="Role for Step Function accessing S3, Health Imaging, and HealthLake"
        )

        # Attach required managed policies
        step_function_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess")
        )
        step_function_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AWSHealthImagingFullAccess")
        )
        step_function_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonHealthLakeFullAccess")
        )
        step_function_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AWSLambda_FullAccess")
        )

        # Get the path to the stepfunction.json file using relative path
        stepfunction_path = os.path.join(os.path.dirname(__file__), "stepfunction.json")
        
        # Create an asset from your existing Step Functions JSON file
        state_machine_json = s3_assets.Asset(
            self, 
            "StateMachineJson", 
            path=stepfunction_path
        )

        # Create a proper CDK StateMachine construct instead of CfnStateMachine
        with open(stepfunction_path, "r") as f:
            definition_json = json.load(f)

        # Create the Step Function using the high-level construct with dynamic name
        self.state_machine = sfn.StateMachine(
            self, "MyHealthStateMachine",
            state_machine_name=f"{resource_prefix}-ProcessDICOMFilesConvertFHIR",
            definition_body=sfn.DefinitionBody.from_string(json.dumps(definition_json)),
            role=step_function_role,
            state_machine_type=sfn.StateMachineType.STANDARD
        )

        # Output the state machine ARN
        CfnOutput(self, "StateMachineARN", value=self.state_machine.state_machine_arn)
        CfnOutput(self, "StateMachineName", value=self.state_machine.state_machine_name)
