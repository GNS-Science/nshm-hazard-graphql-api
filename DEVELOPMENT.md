# DEVELOPMENT

This application uses  serverless.com.


### Environment setup

 - clone the repo
 - check/install a recent node version >=17.8
 - check/install a recent npm version >=8.11
 - install serverless `npm install --save serverless` [more info]()
 - install `npm install --save serverless-python-requirements`  [more info](https://www.serverless.com/blog/serverless-python-packaging/)
 - install `npm install -save serverless-wsgi` [more info](https://www.serverless.com/plugins/serverless-wsgi)
 - `serverless plugin install -n serverless-python-requirements`
 - `serverless plugin install -n serverless-wsgi`


Now `sls info` should print something like ...

```
chrisbc@tryharder-ubuntu:/GNSDATA/API/kororaa-graphql-api$ sls info
Running "serverless" from node_modules
Environment: linux, node 17.8.0, framework 3.18.2 (local) 3.10.1v (global), plugin 6.2.2, SDK 4.3.2
Credentials: Local, "default" profile
Docs:        docs.serverless.com
Support:     forum.serverless.com
Bugs:        github.com/serverless/serverless/issue

```

You'll problably see an error, if youtr AWS credentials are not thise required for SLS.


### AWS credentials

## TESTING

### Run API locally
`$> ENABLE_METRICS=0 AWS_PROFILE=toshi_batch_devops sls wsgi serve --region ap-southeast-2 --stage PROD`


### API Feature tests
`$>poetry run pytest`





