# Migrating Applications

## Table of contents


## ACT1



### Upgrade application
Once the codespace has initialized succesfuly
1. Open a PS terminal
2. Run the ```upgrade-assistant``` command to make sure the tool is intalled
![](images/upgrade-assistant-01.jpg)
3. Run the ```upgrade-assistant migrate``` command and follow the wizard steps to perform the upgrade.

4. Once the process finishes run ```dotnet build .``` to build the solution.

    > **NOTE** The build will fail. A few manual steps are needed to compile  

    - **Changes at .csproj**

      Remove the nuget package references at the csproj file to only have

      ```
      <Project Sdk="Microsoft.NET.Sdk.Web">
        <PropertyGroup>
          <TargetFramework>net9.0</TargetFramework>
        </PropertyGroup>
        <ItemGrou>
          <PackageReference Include="Microsoft.EntityFrameworkCore.SqlServer" Version="9.0.0" />
          <PackageReference Include="Microsoft.VisualStudio.Web.CodeGeneration.Design" Version="9.0.0" />
        </ItemGroup>
      </Project>
      ```
    - **Changes at ``startup.cs``**
    
      Change signature of configure method to use ``IWebHostEnvironment`` instead of ``IHostingEnvironment`` which is obsolete.

      Add endpoint routing
    
      `` services.AddMvc(services => services.EnableEndpointRouting = false); ``

      Remove the compatibility mode.

      ``services.AddMvc().SetCompatibilityVersion(CompatibilityVersion.Version_2_1);``

      Remove httpsRedirection

      ``app.UseHttpsRedirection();``

    - **Changes at ``sampledbContext.cs``**

      Replace all instances of ``HasName()`` function with ``HasDatabaseName()``

5. Select ``startup.cs`` and go to the debug pane and create a ``launch.json`` file to start the application.

```json
{
    // Use IntelliSense to learn about possible attributes.
    // Hover to view descriptions of existing attributes.
    // For more information, visit: https://go.microsoft.com/fwlink/?linkid=830387
    "version": "0.2.0",
    "configurations": [
        {
            "name": ".NET Core Launch (web)",
            "type": "coreclr",
            "request": "launch",
            "preLaunchTask": "build",
            "program": "${workspaceFolder}/bin/Debug/net9.0/AdventureWorks.Web.dll",
            "args": [],
            "cwd": "${workspaceFolder}",
            "stopAtEntry": false,
            "serverReadyAction": {
                "action": "openExternally",
                "pattern": "\\bNow listening on:\\s+(https?://\\S+)"
            },
            "env": {
                "ASPNETCORE_ENVIRONMENT": "Development"
            },
            "sourceFileMap": {
                "/Views": "${workspaceFolder}/Views"
            }
        },
        {
            "name": ".NET Core Attach",
            "type": "coreclr",
            "request": "attach"
        }
    ]
}
```

you can now start the application in debug mode. GitHub will establish a tunnel to allow the communication of the browser with the codespace running the application.

>**NOTE** the application will crash (throw an exception) as no database connection string has been specified.

### Code level assesment
1. Create a solution file for the project as it's needed by appcat by running the following commands at the terminal
    ```
    dotnet new sln -n AdventureWorks
    dotnet sln AdventureWorks.sln add AdventureWorks.Web.csproj
    ```
2. Create a new action from the GitHub repository named appcat.yml
2. Paste the following code to run a code level assesment for the application

    ```
    on:
      workflow_dispatch:
      push:
      
    jobs:
      test_appcat_action:
        runs-on: windows-latest
        name: A job to test the appcat action
        steps:
          - uses: actions/checkout@v4
          - id: foo
            uses: kpantos/dotnet-appcat-action@v5
            with:
              source: 'Solution'
              path: 'AdventureWorks.Web.csproj'
              target: 'ACA'
              privacyMode: 'Unrestricted'
              serializer: 'html'
    ```
  >**NOTE** If you use multiple branches you will have to copy the workflow to your working branch

### Containerization

1. Use the following prompt to create the dockerfile using copilot

    ```
    @workspace create a dockerfile for building and running the application. Use different stages for the build and runtime. Use an alpine base image for the runtime. Install the icu-libs
    tiff, libgdiplus, libc-dev, tzdata packages. Set the globalization invariant mode to false. Add the ASPNETCORE_URLS env variable for port 8080 and expose that port from the container.
    ```

    The resulting dockerfile should be 
    ```
    # Stage 1: Build
    FROM mcr.microsoft.com/dotnet/sdk:9.0 AS build
    WORKDIR /source

    # Copy the project files and restore dependencies
    COPY *.sln .
    COPY AdventureWorks.Web.csproj .
    RUN dotnet restore AdventureWorks.Web.csproj

    # Copy the rest of the source code and build the application
    COPY . .
    RUN dotnet publish AdventureWorks.Web.csproj -c Release -o /app

    # Stage 2: Runtime
    FROM mcr.microsoft.com/dotnet/aspnet:9.0-alpine AS runtime
    WORKDIR /app

    # Install required packages
    RUN apk add --no-cache \
        tiff \
        libgdiplus

    # Set the globalization invariant mode to false
    ENV DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=false

    # Set the ASPNETCORE_URLS environment variable
    ENV ASPNETCORE_URLS=http://+:8080

    # Copy the built application from the build stage
    COPY --from=build /app .

    # Expose port 8080
    EXPOSE 8080

    # Run the application
    ENTRYPOINT ["dotnet", "AdventureWorks.Web.dll"]
    ```

2. Build the container image using the dockerfile
    ```
    docker build -t adventureworks-web .
    ```
    Check if the image has been built correctly by running 
    ```
    docker images
    ```

3. Run the container image
    ```
    docker run -d -p 8080:8080 --name adventureworks-web adventureworks-web
    ```
    the container should be running and a tunnel should be created pointing to the running container instance
    use that port to run the application in the browser
    ![](images/container-forward-port.jpg)

    >**NOTE** The application will throw an exception as there's no database connectivity yet. That's expected.
    ![](images/application-exception.jpg)

    ```
    docker run -d -p 8080:8080 --name adventureworks-web -e ConnectionStrings__sampledbContext="Server=tcp:kpdbserver.database.windows.net,1433;Initial Catalog=advworks;Persist Security Info=False;User ID=sqladmin;Password={PASSWORD};MultipleActiveResultSets=False;Encrypt=True;TrustServerCertificate=False;Connection Timeout=30;" adventureworks-web
    ```

## ACT2

### Initial deployment

1. Login to Azure tenant using AZD

```
azd auth login --tenant-id 5c632e18-3086-4bad-938e-5144bc5c69bc
```

>**OPTIONAL** Login to Azure tenant using az cli ```az login --tenant 5c632e18-3086-4bad-938e-5144bc5c69bc```

2. Run ```azd init``` to initialize select use code in current directory.
![](images/azd-init.jpg)

azd will scan the current directory to find the right azure target hosting environment to deploy the application.
![](images/azd-scan.jpg)

once the scan is complete azd will generate the artifacts required to deploy your application to azure.
![](images/azd-prov-complete.jpg)

3. Test out the deployment by running the ``azd up`` command
![](images/azd-dev-deployment.jpg)

Once the deployment has finished navigate to Azure and demonstrate the resources that have been deployed for the application.
![](images/azure-dev-env.jpg)

  >**NOTE** The application will throw an exception as there's no database connectivity yet. That's expected.
    ![](images/application-exception.jpg)

4. Navigate to the deployed container app and add a secret for the database connection string

```
Server=tcp:kpdbserver.database.windows.net,1433;Initial Catalog=advworks;Persist Security Info=False;User ID=sqladmin;Password=<<PASSWORD>>;MultipleActiveResultSets=False;Encrypt=True;TrustServerCertificate=False;Connection Timeout=30;
```

![](images/set-db-secret.jpg)

6. Next navigate to containers and click edit and deploy in order to create a new environment variable and link it to the secret already created
![](images/set-env-variable.jpg)

once the new revision is up and running the application should load up.

### Configure CI/CD using azd
1. Run ``azd pipeline config`` to create a CI/CD pipeline for deploying the application.
![](images/azd-configure-pipeline.jpg) 

### Production Environment
1. Start by deleting all the bicep files under infra folder leaving just the main.bicep one.

2. At the main.bicep replace all the content with

    ```bicep
    targetScope = 'subscription'

    param location string = 'northeurope'
    @secure()
    param password string

    module hostingEnvironment 'br/public:avm/ptn/aca-lza/hosting-environment:0.2.0' = {
      name: 'hostingEnvironmentDeployment'
      params: {
        // Required parameters
        applicationGatewayCertificateKeyName: 'appgwcert'
        deploymentSubnetAddressPrefix: '10.1.4.0/24'
        enableApplicationInsights: true
        enableDaprInstrumentation: false
        spokeApplicationGatewaySubnetAddressPrefix: '10.1.3.0/24'
        spokeInfraSubnetAddressPrefix: '10.1.0.0/23'
        spokePrivateEndpointsSubnetAddressPrefix: '10.1.2.0/27'
        spokeVNetAddressPrefixes: [
          '10.1.0.0/21'
        ]
        vmAdminPassword: password
        vmJumpBoxSubnetAddressPrefix: '10.1.2.32/27'
        vmSize: 'Standard_B1s'
        // Non-required parameters
        deployZoneRedundantResources: true
        enableDdosProtection: true
        environment: 'prod'
        exposeContainerAppsWith: 'applicationGateway'
        location: location
        storageAccountType: 'Premium_LRS'
        tags: {
          environment: 'test'
        }
        vmAuthenticationType: 'sshPublicKey'
        vmJumpboxOSType: 'linux'
        workloadName: 'advworks'
      }
    }

    output AZURE_CONTAINERAPPSENV_RESOURCE_ID string = hostingEnvironment.outputs.containerAppsEnvironmentResourceId
    output AZURE_CONTAINERREGISTRY_RESOURCE_ID string = hostingEnvironment.outputs.containerRegistryResourceId
    output AZURE_KEYVAULT_RESOURCE_ID string = hostingEnvironment.outputs.keyVaultResourceId

    ```

3. Create a new azd env by running `azd env new` and provide a name for it (e.g. prod)

4. Select the defaut environment to use with azd by issueing `azd env select <name>`

5. Provision the production environment by running `azd provision`

    ![](images/azd-prov-prod.jpg)


### Hosted runner deployment
In order to be able to deploy the application in the new production environment we need to run from within the virtual network so that the container registry is accessible and can push new image builds.
To do this we can deploy a job app at the existing container apps environment to run the gh pipelines.

1. Add the following piece of code to the `main.bicep` file

    ```
    module hostedRunner 'br/public:avm/res/app/job:0.5.2' = {
      name: 'hostedRunnerDeployment'
      scope: resourceGroup('rg-advworks-spoke-prod-neu')
      params: {
        name: 'hosted-runner-job'
        location: location
        tags: {
          environment: 'prod'
        }
        environmentResourceId: hostingEnvironment.outputs.containerAppsEnvironmentResourceId
        workloadProfileName: 'general-purpose'
        triggerType: 'Event'
        replicaTimeout: 1800
        replicaRetryLimit: 0
        secrets: [
          {
            name: 'personal-access-token'
            value: githubpat
          }
        ]
        eventTriggerConfig: {
          parallelism: 1
          replicaCompletionCount: 1
          scale: {
            minExecutions: 0
            maxExecutions: 10
            pollingInterval: 30
            rules: [
              {
                name: 'github-runner'
                type: 'github-runner'
                metadata: {
                  githubAPIURL: 'https://api.github.com'
                  owner: 'kpantos'
                  runnerScope : 'repo'
                  repos: 'AdventureWorks.Web'
                  targetWorkflowQueueLength: '1'
                }
                auth: [
                  {
                    secretRef: 'personal-access-token'
                    triggerParameter: 'personalAccessToken'
                  }
                ]
              }
            ]
          }
        }
        containers: [
          {
            name: 'hosted-runner-job'
            image: 'docker.io/kpantos/github-actions-runner:1.5'
            resources: {
              cpu: '2.0'
              memory: '4Gi'
            }
            env: [
              {
                name: 'GITHUB_PAT'
                secretRef: 'personal-access-token'
              }
              {
                name: 'GH_URL'
                value: 'https://github.com/kpantos/AdventureWorks.Web'
              }
              {
                name: 'REGISTRATION_TOKEN_API_URL'
                value: 'https://api.github.com/repos/kpantos/AdventureWorks.Web/actions/runners/registration-token'
              }
            ]
          }
        ]
      }
    }
    ```
    this requires a GitHub personal access token parameter which need to be added at the bicep file. azd will ask for a value next time the `azd provision` command is issued.

    >**NOTE** Don't forget to run azd pipeline config to update github state with the cuurent parameter values.

2. Split the `azure-dev.yml` pipeline into 2 parts one for provisioning the infrastructure and one for deploying the application.
Name the one used for deploying the application `azure-app.yml` and copy the environment setting from the original pipeline.
The 2 file should look like:

    **`azure-dev.yml`**
    ```yml
    # Run when commits are pushed to step-2-hostingenv
    on:
      workflow_dispatch:

    # Set up permissions for deploying with secretless Azure federated credentials
    # https://learn.microsoft.com/en-us/azure/developer/github/connect-from-azure?tabs=azure-portal%2Clinux#set-up-azure-login-with-openid-connect-authentication
    permissions:
      id-token: write
      contents: read


    jobs:
      build:
        runs-on: ubuntu-latest
        env:
          AZURE_CLIENT_ID: ${{ vars.AZURE_CLIENT_ID }}
          AZURE_TENANT_ID: ${{ vars.AZURE_TENANT_ID }}
          AZURE_SUBSCRIPTION_ID: ${{ vars.AZURE_SUBSCRIPTION_ID }}
          AZURE_ENV_NAME: ${{ vars.AZURE_ENV_NAME }}
          AZURE_LOCATION: ${{ vars.AZURE_LOCATION }}
        steps:
          - name: Checkout
            uses: actions/checkout@v4
          - name: Install azd
            uses: Azure/setup-azd@v2
          - name: Log in with Azure (Federated Credentials)
            run: |
              azd auth login `
                --client-id "$Env:AZURE_CLIENT_ID" `
                --federated-credential-provider "github" `
                --tenant-id "$Env:AZURE_TENANT_ID"
            shell: pwsh


          - name: Provision Infrastructure
            run: azd provision --no-prompt
            env:
              AZD_INITIAL_ENVIRONMENT_CONFIG: ${{ secrets.AZD_INITIAL_ENVIRONMENT_CONFIG }}

    ```

    **`azure-app.yml`**
    ```yml
    # Run when commits are pushed to step-4-hostingenv
    on:
      workflow_dispatch:

    # Set up permissions for deploying with secretless Azure federated credentials
    # https://learn.microsoft.com/en-us/azure/developer/github/connect-from-azure?tabs=azure-portal%2Clinux#set-up-azure-login-with-openid-connect-authentication
    permissions:
      id-token: write
      contents: read


    jobs:
      build:
        runs-on: self-hosted
        env:
          AZURE_CLIENT_ID: ${{ vars.AZURE_CLIENT_ID }}
          AZURE_TENANT_ID: ${{ vars.AZURE_TENANT_ID }}
          AZURE_SUBSCRIPTION_ID: ${{ vars.AZURE_SUBSCRIPTION_ID }}
          AZURE_ENV_NAME: ${{ vars.AZURE_ENV_NAME }}
          AZURE_LOCATION: ${{ vars.AZURE_LOCATION }}
          REGISTRY : 'cradvworksdbqyjprodneu'
          IMAGE : 'adventureworks-web:v${{ github.run_number }}'
          AZURE_RESOURCE_GROUP : 'rg-advworks-spoke-prod-neu'
        steps:
          - name: Checkout
            uses: actions/checkout@v4
          
          - name: Azure CLI Login
            uses: azure/login@v2.2.0
            with:
              client-id: ${{ vars.AZURE_CLIENT_ID }}
              tenant-id: ${{ vars.AZURE_TENANT_ID }}
              subscription-id: ${{ vars.AZURE_SUBSCRIPTION_ID }}

          - name: Build and Push Container Image
            run: |
              az acr build --registry ${{ env.REGISTRY }} --image ${{ env.IMAGE }} --agent-pool agentpool .
    ```

>**IMPORTANT!**
>
> - acr build task needs to run at a virtual network hosted agent pool in order to has access to the registry.
> The LZA deployment already provides an agent pool named `agentpool` that can be used.
>  To do so you will need to specify it at the az acr build by using the `--agent-pool` parameter
>
> - ACR due to WAF alignement has Quarantine policy enabled by default. 
> You will have to disable the policy otherwise the image is not going to be available when deploying the application.
> Use the following command to disable the policy for the needs of the Demo
>   ```
>   id=$(az acr show --name myregistry --query id -o tsv)
>   az resource update --ids $id --set properties.policies.quarantinePolicy.status=disabled
>   ```

3. Now that the application container image is pushed to ACR we need to define the application deployment manifest.

    Create a new file named `deployApp.bicep` at the root path of the aplication and paste in the following content

    ```bicep
    targetScope = 'resourceGroup'

    param location string = resourceGroup().location
    param image string
    param server string
    param envName string = 'poc'
    param tags object = {
      environment: envName
    }
    param name string
    param containerAppsEnvironmentResourceId string
    param managedIdentityResourceId string
    param workloadProfileName string = 'general-purpose'

    param dbServerName string
    param databaseName string
    param dbServerAdminLogin string
    @secure()
    param dbServerAdminPassword string


    module advworksApplication 'br/public:avm/res/app/container-app:0.12.0' = {
      name: 'application-deployment'
      params: {
        name: name
        location: location
        tags: tags
        environmentResourceId: containerAppsEnvironmentResourceId
        managedIdentities: {
          userAssignedResourceIds: [
            managedIdentityResourceId
          ]
        }
        workloadProfileName: workloadProfileName
        containers: [
          {
            name: name
            image: image
            resources: {
              cpu: json('0.25')
              memory: '0.5Gi'
            }
            env: [
              {
                name: 'ConnectionStrings__sampledbContext'
                secretRef: 'database-connection-string'
              }
            ]
          }
        ]
        registries: [
          {
            identity: managedIdentityResourceId
            server: server
          }
        ]
        scaleMinReplicas: 2
        scaleMaxReplicas: 10
        activeRevisionsMode: 'Single'
        ingressExternal: true
        ingressAllowInsecure: false
        ingressTargetPort: 80
        ingressTransport: 'auto'
        secrets: {
          secureList: [
          {
            name: 'database-connection-string'
            value: 'Server=tcp:${dbServerName}.${environment().suffixes.sqlServerHostname},1433;Initial Catalog=${databaseName};Persist Security Info=False;User ID=${dbServerAdminLogin};Password=${dbServerAdminPassword};MultipleActiveResultSets=False;Encrypt=True;TrustServerCertificate=False;Connection Timeout=30;'
          }
        ]}
      }
    }

    // ------------------
    // OUTPUTS
    // ------------------

    @description('The FQDN of the application deployed.')
    output advworksAppFqdn string = advworksApplication.outputs.fqdn
    
    ```

4. Add the deployment step for the `deployApp.bicep` file at the pipeline created earlier

    ```yml
      - name: Deploy to Azure
        run: |
          az deployment group create \
            --resource-group ${{ env.AZURE_RESOURCE_GROUP }} \
            --template-file deployApp.bicep \
            --parameters deployApp.parameters.json \
            --parameters server='${{ env.REGISTRY }}.azurecr.io' image='${{ env.IMAGE }}' dbServerName='${{ env.DB_SERVER_NAME }}' databaseName='${{ env.DATABASE_NAME }}' dbServerAdminLogin='${{ env.DB_USERNAME }}' dbServerAdminPassword='${{ secrets.DB_PASSWORD }}'
    ```

    >**NOTE!**
    >
    > The deployment task needs a few github variables and a secret containing the sql server password.
    > Add this information before running the pipeline.

    and commit and sync all the changes in order for the pipeline to run.
    Onece finished copy the FQDN created for the application as it's going to be needed at the next step.

