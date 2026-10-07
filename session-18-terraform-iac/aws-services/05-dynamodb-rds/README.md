# 05 - DynamoDB & RDS - Database Services

AWS has two main managed database styles:

```text
                AWS Databases
               /             \
       DynamoDB               RDS
   NoSQL (key-value)     Relational (SQL)
   serverless            managed DB server
   flexible schema       fixed schema, joins
```

---

# DynamoDB

## NoSQL
DynamoDB is a fully managed, serverless **NoSQL key-value and document** database.
- No servers to manage, no patching. Scales automatically.
- Single-digit millisecond latency at almost any scale.
- No fixed schema - every item can have different attributes (only the key is required).
- No joins; you design tables around your access patterns.
- Capacity modes: **On-Demand** (pay per request) or **Provisioned** (set read/write capacity units, can autoscale).

## Tables
A table is a collection of items (like a table in SQL but without fixed columns).

## Items
An item is one record (like a row), max 400 KB.

## Attributes
An attribute is a name/value pair in an item (like a column), e.g. `name = "Shubham"`.
Types: String, Number, Binary, Boolean, Null, List, Map, Set.

```text
Table: Orders
┌──────────────┬─────────────────────┬─────────┬──────────────────────┐
│ customer_id  │ order_date          │ amount  │ items                │
│ (partition)  │ (sort key)          │         │                      │
├──────────────┼─────────────────────┼─────────┼──────────────────────┤
│ C101         │ 2026-10-01T10:00    │ 499     │ ["book"]             │
│ C101         │ 2026-10-05T18:30    │ 1299    │ ["shoes","socks"]    │
│ C202         │ 2026-10-02T09:15    │ 89      │ (attribute missing)  │
└──────────────┴─────────────────────┴─────────┴──────────────────────┘
   each row = item, each column = attribute
```

## Partition key
- The required part of the primary key. DynamoDB hashes it to decide which physical partition stores the item.
- If the table has only a partition key, it must be unique for each item.
- Choose a key with many distinct values (like `user_id`) so load spreads evenly - avoid "hot" partitions.

## Sort key
- Optional second part of the primary key (composite key = partition key + sort key).
- Items with the same partition key are stored sorted by the sort key.
- Allows range queries like "all orders of C101 between 1 Oct and 5 Oct".
- Extra query patterns can use **GSI** (Global Secondary Index) / **LSI** (Local Secondary Index).

## DynamoDB use cases
- User sessions, shopping carts, user profiles.
- Gaming leaderboards and player state.
- IoT and event data with huge write volume.
- Serverless apps with Lambda + API Gateway.
- Terraform state locking (older setups used a DynamoDB lock table).

---

# RDS (Relational Database Service)

## Relational database
RDS is a managed service to run a **relational (SQL)** database. Data is in tables with fixed columns,
relationships with foreign keys, SQL queries, joins and ACID transactions.
AWS handles hardware, OS, DB installation, patching, backups and failover; I handle schema, queries and tuning.

## Supported engines
- MySQL
- PostgreSQL
- MariaDB
- Oracle
- Microsoft SQL Server
- IBM Db2
- Amazon Aurora (AWS's own MySQL/PostgreSQL-compatible engine, faster and with shared distributed storage)

## DB instances
- A DB instance is the database server, with an instance class like `db.t3.micro`, `db.m6g.large`, `db.r6g.xlarge`.
- Storage is EBS-based (gp3, io1/io2) and can auto-scale.
- It lives in a **DB subnet group** (subnets in at least 2 AZs inside my VPC).
- I connect using the endpoint DNS name, e.g. `mydb.abc123.us-east-1.rds.amazonaws.com:5432`. No SSH access to the OS.

## Security
- Put RDS in **private subnets**, `publicly_accessible = false`.
- **Security group** allowing the DB port (3306/5432) only from the app servers' security group.
- **Encryption at rest** with KMS (must be chosen at creation), **in transit** with SSL/TLS.
- Store the master password in **Secrets Manager** (RDS can manage and rotate it).
- **IAM database authentication** for MySQL/PostgreSQL.

## Backups
- **Automated backups**: daily snapshot + transaction logs, retention 1-35 days, allows **point-in-time restore** (to any second in the window).
- **Manual snapshots**: taken by you, kept until you delete them, can be copied to other regions/accounts.
- Restoring always creates a **new** DB instance.

## Multi-AZ
- RDS keeps a **standby** copy in another AZ with **synchronous** replication.
- If the primary fails (or during maintenance), RDS automatically fails over to the standby and the endpoint DNS points to it (about 1-2 minutes).
- The standby is for **high availability only** - you can't read from it (in the classic Multi-AZ instance setup).

## Read replicas
- Copies of the DB with **asynchronous** replication, used to **scale reads**.
- Have their own endpoint; the app sends SELECT queries to them.
- Can be in the same region or cross-region; a replica can be promoted to a standalone DB (for DR).

```text
          writes + reads                 reads only
App ─────────────> Primary (AZ-a) ──async──> Read replica
                      │
                      │ sync
                      v
                  Standby (AZ-b)   <- Multi-AZ, takes over on failure
```

## RDS use cases
- Web and mobile app backends that need SQL (users, orders, payments).
- E-commerce and banking apps that need transactions and consistency.
- ERP / CRM systems, WordPress and other CMS.
- Migrating existing on-prem MySQL/PostgreSQL/Oracle databases to the cloud.

---

## DynamoDB vs RDS (quick comparison)
| | DynamoDB | RDS |
|---|---|---|
| Type | NoSQL key-value / document | Relational SQL |
| Schema | flexible | fixed tables and columns |
| Scaling | automatic, horizontal | bigger instance + read replicas |
| Servers | serverless | managed DB instance |
| Joins / complex queries | no | yes |
| Best for | huge scale, simple known access patterns | complex queries, relations, transactions |

## What I learned
DynamoDB is great when I know my access pattern and need massive scale without managing servers -
the key design (partition + sort key) is everything. RDS is for normal SQL apps where I need joins and
transactions; Multi-AZ gives availability and read replicas give read scaling.
