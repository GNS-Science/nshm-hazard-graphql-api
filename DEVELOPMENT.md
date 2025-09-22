# DEVELOPMENT

This application uses serverless.com.

### Environment setup

 - clone the repo
 - check/install a recent node version >=22
   `nvm use 22`

- setup python env
```
pyenv local 3.12
poetry env use 3.12
```

setup yarn 2 ...
```
corepack enable
yarn set version berry
yarn install
```

Now `yarn sls info` should print something like ...

```
chrisbc@tryharder-ubuntu:/GNSDATA/API/kororaa-graphql-api$ sls info
Running "serverless" from node_modules
Environment: linux, node 17.8.0, framework 3.18.2 (local) 3.10.1v (global), plugin 6.2.2, SDK 4.3.2
Credentials: Local, "default" profile
Docs:        docs.serverless.com
Support:     forum.serverless.com
Bugs:        github.com/serverless/serverless/issue

```

You'll problably see an error, if your AWS credentials are not thise required for SLS.

### AWS credentials

## TESTING

### API Feature tests
`poetry run pytest`

### Run API locally
`ENABLE_METRICS=0 poetry run yarn sls wsgi serve`
poetry run yarn serverless wsgi serve





