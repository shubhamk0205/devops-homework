# 04 - VPC (Virtual Private Cloud) - Networking

## What is VPC?
A VPC is my own private, isolated network inside an AWS region. I choose the IP range, split it into
subnets, and control routing and firewalls. Resources like EC2 and RDS are launched inside a VPC.
Every region has a **default VPC**, but for real projects we create our own.

```text
Region: us-east-1
+------------------------- VPC 10.0.0.0/16 --------------------------+
|                                                                    |
|   AZ us-east-1a                     AZ us-east-1b                  |
|  +----------------------------+    +----------------------------+  |
|  | Public subnet 10.0.1.0/24  |    | Public subnet 10.0.2.0/24  |  |
|  |   [web EC2]                |    |   [NAT Gateway]            |  |
|  +----------------------------+    +----------------------------+  |
|  +----------------------------+    +----------------------------+  |
|  | Private subnet 10.0.11.0/24|    | Private subnet 10.0.12.0/24|  |
|  |   [app EC2]                |    |   [RDS]                    |  |
|  +----------------------------+    +----------------------------+  |
|                                                                    |
+------------------------- Internet Gateway -------------------------+
                                 |
                              Internet
```

## CIDR
- CIDR (Classless Inter-Domain Routing) is how we write an IP range: `10.0.0.0/16`.
- The number after `/` = how many bits are fixed. Fewer fixed bits = more IPs.
  - `/16` = 65,536 addresses, `/24` = 256 addresses, `/28` = 16 addresses.
- VPC size can be from `/16` to `/28`. Use private ranges: `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`.
- Plan ranges so they don't overlap with other VPCs or the office network (needed for peering/VPN).

## Subnets
- A subnet is a smaller range of the VPC CIDR, and it lives in **exactly one Availability Zone**.
- AWS reserves 5 IPs in every subnet (first 4 and the last), so a `/24` gives 251 usable IPs.
- Use subnets in 2+ AZs for high availability.

## Route tables
- A route table is a list of rules: "traffic for this destination goes to this target".
- Every subnet is associated with one route table (the main one if you don't choose).
- Every route table has a `local` route so all subnets in the VPC can talk to each other.

```text
Public route table              Private route table
Destination   Target            Destination   Target
10.0.0.0/16   local             10.0.0.0/16   local
0.0.0.0/0     igw-xxxx          0.0.0.0/0     nat-xxxx
```

## Internet Gateway (IGW)
- Attached to the VPC, gives two-way internet access.
- A subnet becomes "public" when its route table has `0.0.0.0/0 -> IGW`.
- The instance also needs a public IP or Elastic IP to be reachable.
- One IGW per VPC, highly available, no bandwidth limit, free.

## NAT Gateway
- Lets instances in a **private** subnet go **out** to the internet (to download updates, call APIs) but nobody from the internet can connect in.
- Placed in a public subnet, has an Elastic IP; private route table points `0.0.0.0/0 -> NAT GW`.
- It's per-AZ and costs money per hour + per GB (one of the common surprise bills).

## Security Groups
- Firewall at the **instance / ENI level**.
- Allow rules only, **stateful** (return traffic allowed automatically).
- Can reference other security groups (e.g. DB SG allows 3306 only from App SG).

## Network ACLs
- Firewall at the **subnet level**.
- Has both **allow and deny** rules, processed in order by rule number (lowest first).
- **Stateless** - return traffic must be allowed explicitly (ephemeral ports 1024-65535).
- Default NACL allows everything.

| | Security Group | Network ACL |
|---|---|---|
| Level | instance (ENI) | subnet |
| Rules | allow only | allow + deny |
| State | stateful | stateless |
| Evaluation | all rules together | in number order, first match |

## Public vs private subnet
| | Public subnet | Private subnet |
|---|---|---|
| Route to internet | `0.0.0.0/0 -> Internet Gateway` | none, or `0.0.0.0/0 -> NAT Gateway` |
| Reachable from internet | yes (if the instance has a public IP and SG allows) | no |
| Typical resources | load balancers, bastion host, NAT GW | app servers, databases, caches |

## What I learned
A VPC is just a network I design: CIDR -> subnets per AZ -> route tables decide public or private ->
IGW for internet, NAT for outbound only -> security groups and NACLs as two layers of firewall.
In Session 19 I built a VPC + subnet + IGW + route table + security group with Terraform.
