#!/usr/bin/env python3
import os
import aws_cdk as cdk
from cdk.yolov8_sagemaker import YOLOv8SageMakerStack

app = cdk.App()
YOLOv8SageMakerStack(app, "YOLOv8SageMakerStack",)

app.synth()
