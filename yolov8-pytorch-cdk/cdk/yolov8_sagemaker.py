import os
from constructs import Construct
from aws_cdk import (
    Aws,
    Stack,
    aws_s3 as s3,
    aws_iam as iam,
    aws_sagemaker as sagemaker,
    aws_ec2 as ec2,
)
import aws_cdk as cdk

region = Aws.REGION
account = Aws.ACCOUNT_ID

# CDK Stack for
# 1. Create S3
# 2. Create SageMaker Notebook and use GitHub as Source

class YOLOv8SageMakerStack(Stack):
    """
    The SageMaker Notebook is used to deploy the custom model on a SageMaker endpoint and test it.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ## Create S3 bucket
        self.bucket = s3.Bucket(
            self, "yolov8-s3",
            auto_delete_objects=True,
            removal_policy=cdk.RemovalPolicy.DESTROY)

        ## IAM Roles
        # Create role for Notebook instance
        nRole = iam.Role(
            self,
            "yolov8-notebookAccessRole",
            assumed_by=iam.ServicePrincipal('sagemaker'))

        # Attach the right policies for SageMaker Notebook instance
        nPolicy = iam.Policy(
            self,
            "yolov8-notebookAccessPolicy",
            policy_name="yolov8-notebookAccessPolicy",
            statements=[
                iam.PolicyStatement(actions=['sagemaker:*'], resources=['*']), 
                iam.PolicyStatement(actions=['s3:ListAllMyBuckets'], resources=['arn:aws:s3:::*']),
                iam.PolicyStatement(actions=['iam:PassRole', 'ecr:*', "logs:*"], resources=['*', '*', '*']),
                iam.PolicyStatement(actions=['s3:*'], resources=[self.bucket.bucket_arn, self.bucket.bucket_arn+'/*']),
                ]).attach_to_role(nRole)

        ## Create SageMaker Notebook instances cluster
        nid = 'yolov8-sm-notebook'
        notebook = sagemaker.CfnNotebookInstance(
            self,
            nid,
            instance_type='ml.m5.4xlarge',
            volume_size_in_gb=5,
            notebook_instance_name=nid,
            role_arn=nRole.role_arn,
            additional_code_repositories=["https://github.com/aws-samples/host-yolov8-on-sagemaker-endpoint"],
        )
