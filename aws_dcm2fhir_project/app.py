#!/usr/bin/env python3
from aws_cdk import App
from master_stack import MasterStack

app = App()
MasterStack(app, "DCM2FHIRStack-Final")
app.synth()