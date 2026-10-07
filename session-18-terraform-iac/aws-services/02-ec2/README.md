# 02 - EC2 (Elastic Compute Cloud) - Compute

## What is EC2?
EC2 gives you virtual machines (called **instances**) in the AWS cloud. You choose the OS, CPU, memory,
disk and network, start it in minutes, and pay only while it runs (per second for Linux).
It is IaaS - AWS manages the hardware, I manage the OS and everything above it.

```text
   AMI (OS image) + Instance type (size) + Key pair + Security Group + EBS disk
                                   |
                                   v
                          Running EC2 instance
                       (in a subnet inside a VPC)
```

## AMI (Amazon Machine Image)
- A template used to launch an instance: OS + pre-installed software + disk layout.
- Examples: Amazon Linux 2023, Ubuntu 24.04, Windows Server.
- AMIs are **region specific** (same Ubuntu has different AMI IDs in us-east-1 and ap-south-1).
- You can create your own AMI from a configured instance (a "golden image").

## Instance types
Name format: `family` + `generation` + `size`, e.g. `t3.micro`, `m7g.large`.

| Family | Optimised for | Example use |
|---|---|---|
| t (t3, t4g) | Burstable, general purpose, cheap | dev/test, small websites |
| m (m6i, m7g) | Balanced general purpose | app servers |
| c (c6i, c7g) | Compute (CPU) | batch jobs, gaming servers |
| r / x | Memory | in-memory caches, big databases |
| i / d | Storage (fast local disks) | NoSQL, data warehousing |
| p / g | GPU | ML training, video |

`g` at the end (like `t4g`) means ARM Graviton processor.

## Key pairs
- Used for SSH login to Linux instances (RDP password decryption for Windows).
- AWS keeps the **public key** and puts it into the instance; I download the **private key** (`.pem`) once.
- Login: `ssh -i mykey.pem ec2-user@<public-ip>`
- If the private key is lost you can't SSH in with it (alternative: SSM Session Manager).

## Security Groups
- A virtual firewall attached to the instance (actually to its network interface).
- Only **allow** rules, no deny rules.
- **Stateful** - if inbound traffic is allowed, the reply goes out automatically.
- By default: all inbound blocked, all outbound allowed.
- Example: allow 22 from my IP only, allow 80/443 from `0.0.0.0/0`.

## EBS (Elastic Block Store)
- Network-attached disk for an instance (like a virtual hard drive).
- The root volume is usually EBS. Data stays even if the instance is stopped.
- Lives in **one AZ** - can only attach to instances in the same AZ.
- Types: `gp3` (general SSD), `io2` (high IOPS SSD), `st1`/`sc1` (HDD).
- **Snapshots** back up a volume to S3 and can be copied to other regions.
- Different from **instance store** - local disk that is lost when the instance stops.

## Public vs private IP
| | Private IP | Public IP |
|---|---|---|
| Reachable from | inside the VPC | the internet |
| Comes from | subnet CIDR, e.g. 10.0.1.25 | AWS pool |
| On stop/start | stays the same | **changes** (unless Elastic IP) |
| Always present? | yes | only in a public subnet with auto-assign or Elastic IP |

**Elastic IP** = a static public IP that you own until you release it.

## Instance lifecycle
```text
 launch
   |
   v
 pending ──> running ──(stop)──> stopping ──> stopped ──(start)──> pending
                │                                   │
              (reboot: stays running)            (terminate)
                │                                   │
                └──(terminate)──> shutting-down ──> terminated
```
- **running** - you are billed for compute.
- **stopped** - no compute bill, but EBS storage is still billed. Public IP is released.
- **terminated** - instance deleted (root EBS deleted too by default). Cannot be started again.
- **reboot** - same host, same IPs.

## Common use cases
- Hosting web servers / APIs (often behind a Load Balancer with Auto Scaling).
- Jenkins or other CI build servers, bastion hosts.
- Running Docker or self-managed Kubernetes nodes.
- Batch processing, ML training on GPU instances.
- Lift-and-shift of on-prem servers to the cloud.

## What I learned
To launch an EC2 instance you need an AMI, an instance type, a key pair, a security group and a
subnet. Stopping is not the same as terminating, and the public IP changes on stop/start unless you use an Elastic IP.
