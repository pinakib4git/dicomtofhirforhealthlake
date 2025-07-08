#!/usr/bin/env python3
from aws_cdk import App
from master_stack import MasterStack

app = App()
suffix = app.node.try_get_context("suffix") or ""
stack_name = f"DCM2FHIRStack-Final{'-' + suffix if suffix else ''}"
MasterStack(app, stack_name)
app.synth()