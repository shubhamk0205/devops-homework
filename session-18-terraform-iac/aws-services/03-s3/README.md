# 03 - S3 (Simple Storage Service) - Storage

## What is S3?
S3 is object storage. You store files (objects) in containers (buckets) and access them over HTTPS.
It is practically unlimited, very durable (designed for 99.999999999% - "11 nines"), and you pay for what you store and transfer.
S3 is **not** a file system or a disk - you can't mount it like EBS; you PUT and GET whole objects.

```text
S3
└── Bucket: shubham-app-logs   (region: us-east-1)
    ├── 2026/10/08/app.log        <- object (key = "2026/10/08/app.log")
    ├── images/logo.png
    └── backup.tar.gz
```

## Buckets
- Top-level container for objects. Created in one region.
- Bucket name must be **globally unique** across all AWS accounts, 3-63 chars, lowercase, no underscores.
- Settings live at the bucket level: versioning, encryption, lifecycle, policy, Block Public Access.

## Objects
- An object = **key** (full name, like a path) + **data** + **metadata** (+ version ID if versioning is on).
- Max object size 5 TB (multipart upload is used for big files).
- There are no real folders - `images/logo.png` is one key, the console just shows `/` like folders.

## Storage classes
| Class | For | Notes |
|---|---|---|
| S3 Standard | frequently accessed data | default, low latency |
| S3 Intelligent-Tiering | unknown/changing access | moves objects between tiers automatically |
| S3 Standard-IA | infrequent access | cheaper storage, retrieval fee |
| S3 One Zone-IA | infrequent, re-creatable data | only 1 AZ |
| S3 Glacier Instant Retrieval | archive, accessed rarely but fast | ms retrieval |
| S3 Glacier Flexible Retrieval | archive | minutes to hours |
| S3 Glacier Deep Archive | long-term compliance archive | cheapest, up to 12-48 hours |

## Versioning
- When enabled, S3 keeps every version of an object. Overwrite = new version, delete = "delete marker".
- Protects from accidental delete/overwrite - you can restore an older version.
- Once enabled it can only be **suspended**, not fully disabled.
- Old versions also cost money, so usually combined with lifecycle rules.

## Lifecycle policies
Rules that automatically move or delete objects after some days.

```text
day 0           day 30              day 90               day 365
Standard ──> Standard-IA ──> Glacier Flexible ──> delete (expire)
```
- Transition actions (change storage class) and expiration actions (delete).
- Can target a prefix (`logs/`) or tags, and can clean up old non-current versions or incomplete multipart uploads.

## Encryption
- **In transit:** HTTPS (TLS). Can be forced with a bucket policy (`aws:SecureTransport`).
- **At rest (server-side):**
  - SSE-S3 - keys managed by S3 (AES-256). **On by default for all new objects since 2023.**
  - SSE-KMS - keys in AWS KMS, gives audit trail and key access control.
  - DSSE-KMS - double-layer KMS encryption.
  - SSE-C - you provide the key with each request.
- **Client-side:** you encrypt before uploading.

## Bucket policies
A resource-based JSON policy attached to the bucket. Example - allow public read of a website bucket:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "PublicRead",
    "Effect": "Allow",
    "Principal": "*",
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::my-website-bucket/*"
  }]
}
```
- Used for cross-account access, forcing HTTPS/encryption, allowing CloudFront, etc.
- **Block Public Access** is ON by default and overrides public policies - it must be turned off on purpose.

## Common use cases
- Backups and archives.
- Static website hosting (HTML/CSS/JS), often with CloudFront.
- Storing user uploads, images, videos.
- Application and access logs, data lake for analytics (Athena, EMR).
- Terraform remote state backend.
- Artifacts from CI/CD pipelines.

## What I learned
S3 = buckets + objects with keys. Bucket names are global, data is encrypted by default, and
versioning + lifecycle rules + the right storage class are how you protect data and control cost.
In Task 1 I created a bucket with Terraform and saw the default AES256 encryption in `terraform show`.
