# AWS Ghost Account Deployment Issue

## Summary

The nshm-hazard-graphql-api service was deployed to an unintended AWS account (a recently created account) instead of the expected account `461564345538`.

## Background

### Deployment Configuration

- **Framework**: Serverless Framework v4
- **CI/CD**: GitHub Actions using reusable workflows from `GNS-Science/nshm-github-actions`
- **Target Account**: `461564345538` (referenced in serverless.yml IAM policies for DynamoDB, S3, ECR access)
- **Authentication**: GitHub Secrets (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)

### GitHub Secrets

| Secret | Purpose | Age |
|--------|---------|-----|
| `AWS_ACCESS_KEY_ID` | AWS authentication | ~3 years |
| `AWS_SECRET_ACCESS_KEY` | AWS authentication | ~3 years |
| `SERVERLESS_ACCESS_KEY` | Serverless Framework Dashboard metrics | 3 years |

## Analysis

### How AWS Credentials Work

AWS access keys are **tied to exactly one AWS account**. When keys are created, they are generated within a specific AWS account and can only authenticate to that account. Therefore:

- If deployment landed in a different account, **the credentials must belong to that account**
- Credentials cannot "accidentally" authenticate to a different account

### Possible Causes

1. **Silent Credential Rotation**
   - The GitHub secrets may have been updated with credentials from the new account
   - This could have happened during key rotation without clear documentation

2. **Key Regeneration in Wrong Account**
   - During a scheduled key rotation, new keys were created in the new account
   - The old keys from `461564345538` were deactivated or deleted

3. **Multiple Maintainers**
   - Another team member may have updated secrets without communication

### What We Know

- GitHub secrets have existed for ~3 years (claimed)
- Deployment landed in a recently created AWS account
- The service was expected to deploy to account `461564345538`
- No explicit OIDC configuration exists in this repository (using static access keys)

## Diagnostic Steps

To confirm which account the current GitHub secrets belong to:

```bash
# Run locally or in GitHub Actions:
AWS_ACCESS_KEY_ID=<secret_value> \
AWS_SECRET_ACCESS_KEY=<secret_value> \
aws sts get-caller-identity
```

Expected output:
```json
{
  "UserId": "AIDAI...",
  "Account": "123456789012",  // <-- This will reveal the actual account
  "Arn": "arn:aws:iam::123456789012:user/..."
}
```

## Fix Options

### Option A: Restore Credentials from Target Account

**Quick fix using existing access key pattern.**

#### Steps

1. Log into AWS Account `461564345538` (expected target)
2. Navigate to IAM → Users → Find the deployment user
3. Create new access keys if needed, or locate existing active keys
4. Update GitHub repository secrets:
   - `AWS_ACCESS_KEY_ID` → new key ID from account `461564345538`
   - `AWS_SECRET_ACCESS_KEY` → new secret from account `461564345538`
5. Re-run deployment workflow
6. Verify deployment lands in correct account

#### Pros
- Quick to implement
- No infrastructure changes required
- Familiar pattern for team

#### Cons
- Long-lived credentials remain a security risk
- Keys can be leaked via logs, code, or credential exposure
- Requires periodic rotation
- No audit trail for which GitHub workflow used credentials

---

### Option B: Migrate to OIDC Authentication (Recommended)

**Secure, credential-less authentication using GitHub OIDC.**

#### Steps

1. **Create IAM OIDC Provider in Account `461564345538`**
   ```bash
   # If not already exists
   aws iam create-open-id-connect-provider \
     --url https://token.actions.githubusercontent.com \
     --client-id-list sts.amazonaws.com \
     --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
   ```

2. **Create IAM Role for GitHub Actions**
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Principal": {
           "Federated": "arn:aws:iam::461564345538:oidc-provider/token.actions.githubusercontent.com"
         },
         "Action": "sts:AssumeRoleWithWebIdentity",
         "Condition": {
           "StringEquals": {
             "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
           },
           "StringLike": {
             "token.actions.githubusercontent.com:sub": "repo:GNS-Science/nshm-hazard-graphql-api:*"
           }
         }
       }
     ]
   }
   ```

3. **Attach Required Policies to the Role**
   - Include all permissions from `.github/old_policy.json`
   - Include Serverless Framework deployment permissions

4. **Update GitHub Secrets**
   - Remove `AWS_ACCESS_KEY_ID`
   - Remove `AWS_SECRET_ACCESS_KEY`
   - Add `AWS_ROLE_ARN` = `arn:aws:iam::461564345538:role/GitHubActionsDeployRole`

5. **Update Reusable Workflow** (in `nshm-github-actions` repository)
   ```yaml
   - name: Configure AWS credentials
     uses: aws-actions/configure-aws-credentials@v4
     with:
       role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
       aws-region: us-east-1
   ```

6. **Test and Deploy**
   - Re-run workflow
   - Verify deployment lands in correct account

#### Pros
- No long-lived credentials in GitHub
- Automatic credential expiration (1 hour tokens)
- Fine-grained access control per repository/branch
- Full audit trail in AWS CloudTrail
- Cannot be leaked via code or logs

#### Cons
- More complex initial setup
- Requires changes to shared workflow repository
- May need coordination with other teams using the reusable workflow

---

### Option C: Verify and Rotate Existing Keys

**If credentials haven't changed, verify they're correct.**

#### Steps

1. Run diagnostic command to identify account for current secrets
2. If secrets belong to wrong account → proceed to Option A
3. If secrets belong to correct account → investigate other causes:
   - Serverless Framework Dashboard settings
   - `--stage` or `--region` overrides
   - Multiple CloudFormation stacks with similar names

## Recommendation

1. **Immediate**: Run diagnostic to confirm which account the secrets belong to
2. **Short-term**: If wrong account, restore correct credentials (Option A)
3. **Long-term**: Migrate to OIDC (Option B) to prevent future credential-related issues

## Prevention Measures

- Add deployment account verification step to CI/CD workflow:
  ```yaml
  - name: Verify target account
    run: |
      ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
      if [ "$ACCOUNT_ID" != "461564345538" ]; then
        echo "ERROR: Deploying to wrong account: $ACCOUNT_ID"
        exit 1
      fi
  ```

- Document credential ownership and rotation schedule
- Consider migrating all repositories to OIDC for consistency

## References

- [GitHub Actions OIDC with AWS](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services)
- [Serverless Framework AWS Credentials](https://www.serverless.com/framework/docs/providers/aws/guide/credentials)
- `.github/old_policy.json` - IAM policy for deployment permissions
- `serverless.yml:110-111` - DynamoDB references to account `461564345538`