"""
 Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 SPDX-License-Identifier: MIT-0
"""
import os
from constructs import Construct
import aws_cdk as cdk

from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_iam as iam
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_rds as rds
from aws_cdk import aws_secretsmanager as secretsmanager
from aws_cdk import aws_ssm as ssm

import aws_cdk.aws_ecs_patterns as ecsp

import constants

#########################################
# In this section we need to create new #
# infra resrouces used to deploy tools  #
#########################################

# Class defined to deploy new ECS infra and Security Tools
class SecTools(cdk.Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        #########################################
        #           Shared components           #
        #########################################

        vpc = ec2.Vpc.from_lookup(self, "VPC",
            vpc_id=ssm.StringParameter.value_from_lookup(
                self, constants.CORE_VPC_PARAMETER_NAME)
        )

        # Create IAM Role using AWS managed policies with permissions to deploy ECS Tasks
        ecs_task_role = iam.Role(
            self,
            id="ECSTaskRole",
            role_name="ECSTaskRole",
            assumed_by=iam.ServicePrincipal(service="ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonECSTaskExecutionRolePolicy")
            ]
        )

        cluster = ecs.Cluster(self, "SecurityToolsECSCluster",
            capacity=ecs.AddCapacityOptions(
            instance_type=ec2.InstanceType('m5.large')),
            vpc=vpc
        )

        asg = cluster.autoscaling_group
        asg.add_user_data(
            'sudo sysctl -w vm.max_map_count=524288',
            'sudo sysctl -w fs.file-max=131072',
            'sudo ulimit -n 131072',
            'sudo ulimit -u 8192'
            'sudo echo "vm.max_map_count=524288" >> /etc/sysctl.conf',
            'sudo sysctl -p'
        )

        #########################################
        #               SonarQube               #
        #########################################

        # Create SG for RDS PostGres to be used by Sonarqube allowing all outbound traffic
        self.sg = ec2.SecurityGroup(
            self, 'RDSSecurityGroup',
            vpc=vpc,
            allow_all_outbound=True,
            description="RDS Instance Security Group"
        )

        # Create Sonarqube Postgres DB for Sonarqube service connect
        self.database = rds.DatabaseInstance(self, 'SonarqubeDB',
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_14_2),
            database_name="sonarqube",
            credentials=rds.Credentials.from_generated_secret(
                "sonar_creds"),
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.MEDIUM),
            vpc=vpc,
            multi_az=True,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
            ),
            publicly_accessible=False,
            security_groups=[self.sg]
        )

        rds_url = 'jdbc:postgresql://{}/sonarqube'.format(
            self.database.db_instance_endpoint_address)

        # Addins SG rule allowing access to DB from VPC
        self.sg.add_ingress_rule(
            ec2.Peer.ipv4('10.0.0.0/16'), ec2.Port.tcp(5432), "AccessToDB"
        )

        sonarqube_ecs_service = ecsp.ApplicationLoadBalancedEc2Service(self, "SonarquebEcsTask",
            task_image_options=ecsp.ApplicationLoadBalancedTaskImageOptions(
                environment={
                    'sonar.jdbc.url': rds_url,
                    },
                image=ecs.ContainerImage.from_registry(
                    "public.ecr.aws/docker/library/sonarqube:latest"),
                container_port=9000,
                secrets={
                    "sonar.jdbc.username": ecs.Secret.from_secrets_manager(self.database.secret, field="username"),
                    "sonar.jdbc.password": ecs.Secret.from_secrets_manager(self.database.secret, field="password")
                },
                task_role=ecs_task_role,
            ),
            public_load_balancer=True,
            cluster=cluster,
            cpu=512,
            memory_limit_mib=2048,
        )

        sonarqube_secret = secretsmanager.Secret(self, "SonarQubeSecret",
            secret_object_value={
                "host": cdk.SecretValue.unsafe_plain_text(f'http://{sonarqube_ecs_service.load_balancer.load_balancer_dns_name}')
            }
        )

        #########################################
        #                Outputs                #
        #########################################

        cdk.CfnOutput(self, 'SonarQubeSecretArnOutput',
            value=sonarqube_secret.secret_full_arn,
            export_name=constants.SONARQUBE_SECRET_ARN_EXPORT_NAME
        )
