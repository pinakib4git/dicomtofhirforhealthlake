#!/usr/bin/env python3
from aws_cdk import App, Stack
from constructs import Construct
from aws_stepfunction_stack import StepFunctionStack

class MainStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)
        
        # Create a Step Function stack with a custom suffix
        # This allows you to control the resource naming explicitly
        StepFunctionStack(self, "StepFunctionStack", resource_suffix="deployment1")
        
        # You could create another instance with a different suffix if needed
        # StepFunctionStack(self, "StepFunctionStack2", resource_suffix="deployment2")

app = App()
MainStack(app, "DCM2FHIRStack")
app.synth()