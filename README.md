# AWS CI/CD Pipeline for DevSecOps

This project is a reference implementation for a CI/CD pipeline integrated with security vulnerability scanning tools.

The pipeline is implemented as code using [AWS CDK](https://aws.amazon.com/cdk/) and the [CDK Pipelines construct](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.pipelines-readme.html). The current implementation performs security vulnerability scanning using SonarQube and Dependency-Check. The pipeline sends to [AWS Security Hub](https://aws.amazon.com/security-hub/) the reports for the security scanning executions. It also contains a sample application implementation for testing purposes.

## Project structure

* `backend/infrastructure.py`: definition of the infrastructure components necessary to run the `backend` component of the sample application.
* `backend/runtime/`: the actual code of the sample application
* `shared/`: definition of the core components that the security tools and components of the sample application share.
* `securityhub/`: implementation of the integration with AWS Security Hub
* `sectools/`: definition of all the security tools the pipeline uses for security vulnerability scanning.
* `pipeline.py`: definition of the CI/CD pipeline as code.
* `deployment.py`: definition of the deployment unit of the sample application that the pipeline will deploy.

## Create development environment
See [Getting Started With the AWS CDK](https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html)
for additional details and prerequisites

### Clone the code
```bash
git clone https://github.com/aws-samples/cdk-devsecops-cicd-pipeline
cd cdk-devsecops-cicd-pipeline
```

### Create Python virtual environment and install the dependencies
```bash
python3.7 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Deploy to a sandbox environment

To deploy the stacks, use CDK commands. If you are new to CDK, see [Getting started with the AWS CDK](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html).

Before proceeding, update the `DEV_ACCOUNT_ID` and `REGION` values on `constants.py` to the AWS account ID of your sandbox environment and your region of choice. After that, run a `cdk ls` command to test if everything is correct with your CDK app. This will list the 4 stacks existing on the CDK app. Note that a file called `cdk.context.json` will also be generated in the root of the project. This is the runtime context file, and it must be commited to your source control. See [Runtime context](https://docs.aws.amazon.com/cdk/v2/guide/context.html) to learn more about that.

#### Push the code to AWS CodeCommit
For this sample CI/CD pipeline, we are using [AWS CodeCommit](https://aws.amazon.com/codecommit/) as a Git repository. For your own projects, you can update `pipeline.py` to use your Git repository of choice.

From the terminal, create a new Git repository on your sandbox environment:
```bash
aws codecommit create-repository --repository-name cdk-devsecops-cicd-pipeline
```

After you created the repository, push the code of this sample pipeline to CodeCommit. If you are new to CodeCommit, see [Getting started with Git and AWS CodeCommit](https://docs.aws.amazon.com/codecommit/latest/userguide/getting-started.html).

#### Bootstrap CDK
```bash
cdk bootstrap aws://<SANDBOX_ACCOUNT_ID/<AWS_REGION>
```

#### Deploy shared components
```bash
cdk deploy SharedInfraStack
```

#### Deploy security tools
```bash
cdk deploy SecToolsStack
```

After deploying the security tools, you'll see output values from CDK on your terminal. Find an output named `SecToolsStack.SonarquebEcsTaskServiceURLABCXYZ`, which is the URL from where your [SonarQube](https://www.sonarqube.org/) instance is responding.

Example output:
```text
 ✅  SecToolsStack

✨  Deployment time: 1018.67s

Outputs:
SecToolsStack.SonarQubeSecretArnOutput = arn:aws:secretsmanager:us-east-1:<MY_SANDBOX_ACCOUNT_UD:secret:SonarQubeSecretABCXYZ
SecToolsStack.SonarquebEcsTaskLoadBalancerABCXYZ = SecTo-Sonar-ABCXYZ.<REGION>.elb.amazonaws.com
SecToolsStack.SonarquebEcsTaskServiceURLE4434029 = http://SecTo-Sonar-ABCXYZ.<REGION>.elb.amazonaws.com
```

To interact with SonarQube's APIs, you need to generate a user token. See [Generating and Using Tokens](https://docs.sonarqube.org/latest/user-guide/user-token/) on SonarQube's documentation to learn how to create yours. You'll also have to create a project on SonarQube to represent the sample application we are using in this reference implementation. The deployment of DB instance associated with SonarQube service can take between 15 to 20 minutes.

As part of the `SecToolsStack`, a secret is created on [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/). Find on the CDK output on your terminal the ARN of this secret, which must be similar to `SecToolsStack.SonarQubeSecretArnOutput`. Update this secret with the SonarQube access data:
```bash
aws secretsmanager put-secret-value \
    --secret-id <MY_SECRET_ARN> \
    --secret-string "{\"access_token\":\"<MY_SONARQUBE_TOKEN>\",\"host\":\"<MY_SONARQUBE_URL\",\"project\":\"<MY_SONARQUBE_PROJECT\"}"
```

The pipeline is sending the findings to [AWS Security Hub](https://aws.amazon.com/security-hub/). For that yo work, you have to enable Security Hub first:
```bash
aws securityhub enable-security-hub
```

In order to activate [AWS CodeGuru Reviewer](https://aws.amazon.com/codeguru/)in your account and associate it to the repository used by the pipeline, just type the following command in the terminal:
```bash
aws codeguru-reviewer associate-repository \
    --repository CodeCommit={Name=cdk-devsecops-cicd-pipeline}
```

#### Deploy CI/CD pipeline
```bash
cdk deploy DevSecOpsPipelineStack
```

Go to the [AWS CodePipeline console to see the pipeline execution](https://console.aws.amazon.com/codesuite/codepipeline/pipelines).

After the pipeline execution, you'll be able to see on [AWS Security Hub](https://aws.amazon.com/security-hub/) the pipeline findings, if there are any.

# Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

# License

This code is licensed under the MIT-0 License. See the [LICENSE](LICENSE) file.
