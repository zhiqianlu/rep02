# Code level assesment
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
              path: 'app/AdventureWorks.sln'
              target: 'ACA'
              privacyMode: 'Unrestricted'
              serializer: 'html'
    ```
  >**NOTE** If you use multiple branches you will have to copy the workflow to your working branch
