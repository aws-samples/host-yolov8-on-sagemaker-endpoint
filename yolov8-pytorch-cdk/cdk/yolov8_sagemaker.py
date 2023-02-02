import os
from constructs import Construct
from aws_cdk import (
    Aws,
    Stack,
    aws_s3 as s3,
    aws_iam as iam,
    aws_sagemaker as sagemaker,
    aws_ec2 as ec2,
    aws_codecommit as codecommit,
)
import aws_cdk as cdk

region = Aws.REGION
account = Aws.ACCOUNT_ID

# CDK Stack for
# 1. Create CodeCommit
# 2. Push Custom Model Code to CodeCommit
# 3. Create SageMaker Notebook and use CodeCommit as Source


class YOLOv8SageMakerStack(Stack):
    """
    This stack creates a CodeCommit repository and a SageMaker Notebook.
    The CodeCommit respository is used to store the custom model code. 
    The SageMaker Notebook is used to deploy the custom model on a SageMaker endpoint and test it.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ## Create S3 bucket
        self.bucket = s3.Bucket(
            self, "yolov8-s3",
            auto_delete_objects=True,
            removal_policy=cdk.RemovalPolicy.DESTROY)

        ## Create CodeCommit repository
        self.repo = codecommit.Repository(self, "yolov8-repo",
                                          repository_name="yolov8-repo",
                                          code=codecommit.Code.from_directory(
                                              os.path.join(os.getcwd(), "sm-notebook"))
                                          )

        ## Create VPC
        self.vpc = ec2.Vpc(self, "yolov8-VPC",
                           max_azs=2,
                           cidr="10.10.0.0/16",
                           subnet_configuration=[ec2.SubnetConfiguration(
                               subnet_type=ec2.SubnetType.PUBLIC,
                               name="Public",
                               cidr_mask=24
                           ), ec2.SubnetConfiguration(
                               subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT,
                               name="Private",
                               cidr_mask=24
                           )
                           ],
                           nat_gateways=1
                           )

        ## Create Security group
        self.sg = ec2.SecurityGroup.from_security_group_id(
            self, "yolov8-securityGroup", self.vpc.vpc_default_security_group, mutable=False)

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
                iam.PolicyStatement(actions=['codecommit:*'], resources=[self.repo.repository_arn]),
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
            security_group_ids=[self.sg.security_group_id],
            subnet_id=self.vpc.private_subnets[0].subnet_id,
            notebook_instance_name=nid,
            role_arn=nRole.role_arn,
            additional_code_repositories=[self.repo.repository_clone_url_http],
        )
