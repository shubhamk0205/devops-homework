# 01 - IAM (Identity and Access Management) - Governance

## What is IAM?
IAM is the AWS service that decides **who** can do **what** on **which** resource in an AWS account.
Every API call to AWS (from the console, CLI, SDK or Terraform) is checked by IAM first.
IAM is global (not tied to a region) and it is free.

```text
   WHO (principal)          WHAT (action)          WHICH (resource)
 user / role / service --> s3:GetObject ------> arn:aws:s3:::my-bucket/*
                                 |
                          IAM policy says Allow or Deny
```

## Users
- An IAM user is a long-term identity for one person or one application.
- A user can have a console password and/or access keys (Access Key ID + Secret Key) for CLI/SDK.
- A new user has **no permissions** until you attach a policy.
- The **root user** (the email used to create the account) has full power - it should only be used for a few account tasks and must have MFA.

## Groups
- A group is a collection of users. Policies attached to the group apply to all users in it.
- Example: group `Developers` with EC2/S3 access, group `Admins` with AdministratorAccess.
- Groups cannot be nested and a group is not an identity itself (you can't log in as a group).

```text
Group: Developers  --(policy: S3 + EC2 access)
   ├── user: rahul
   └── user: priya
```

## Roles
- A role is an identity with permissions but **no permanent password or keys**.
- Someone "assumes" the role and gets **temporary credentials** from STS (valid for a short time).
- Who can assume it is defined in the role's **trust policy**.
- Examples: an EC2 instance role so the app can read S3 without storing keys, a role for a Lambda function, cross-account access, a role for GitHub Actions (OIDC).

## Policies
A policy is a JSON document with statements:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:ListBucket"],
      "Resource": ["arn:aws:s3:::my-bucket", "arn:aws:s3:::my-bucket/*"]
    }
  ]
}
```
- **Effect** - Allow or Deny
- **Action** - API actions like `s3:GetObject`, `ec2:StartInstances`
- **Resource** - ARN of the resource
- **Condition** (optional) - extra rules like source IP, MFA present, tag value

Types:
- **AWS managed policies** - ready made by AWS (e.g. `AmazonS3ReadOnlyAccess`).
- **Customer managed policies** - written by you, reusable.
- **Inline policies** - embedded directly in one user/group/role.
- **Resource-based policies** - attached to the resource itself (e.g. S3 bucket policy).

## Permissions
How IAM decides:
1. By default everything is **denied** (implicit deny).
2. An explicit **Allow** in any attached policy allows the action.
3. An explicit **Deny** always wins over any Allow.

```text
Explicit Deny?  --yes--> DENIED
      | no
Explicit Allow? --yes--> ALLOWED
      | no
             --> DENIED (implicit)
```

## Least privilege
Give only the permissions that are really needed for the job, nothing more.
- Not `s3:*` on `*`, but `s3:GetObject` on one bucket.
- Start small and add permissions when needed (IAM Access Analyzer can suggest policies from real usage).
- If a key leaks, least privilege limits the damage.

## IAM best practices
- Lock away the root user, enable MFA on it, don't create root access keys.
- Enable MFA for all human users.
- Prefer **roles and temporary credentials** over long-term access keys (EC2 roles, SSO / IAM Identity Center, OIDC for CI).
- Give permissions to **groups**, not to individual users.
- Follow least privilege, review unused users/keys/permissions regularly.
- Rotate access keys if you must use them, never commit them to Git.
- Use a strong password policy.
- Turn on CloudTrail to log who did what.

## Common use cases
- Giving each team member their own login with only the access they need.
- EC2 instance role so an app can read from S3 / write to DynamoDB without hard-coded keys.
- Terraform / CI pipeline role with permissions to create infrastructure.
- Cross-account access (dev account can read logs from prod account).
- Bucket policies to allow another account or service to access an S3 bucket.

## What I learned
IAM is the first thing to get right in AWS. Users are for people, roles are for services and temporary
access, and policies are just JSON Allow/Deny rules. Deny always wins, and least privilege is the default mindset.
