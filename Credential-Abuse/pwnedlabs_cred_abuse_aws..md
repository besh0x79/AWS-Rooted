hello pwners today we have a great lab form PWNED LABS, this lab brings together two critical perspectives in cybersecurity:

- Red Team: How an individual who has obtained AWS credentials can discover the permissions available to them and exploit excessive privileges to access other services and data.
- Blue Team: How to detect account misuse through logs, identify a compromised account, and contain the incident.

## Let’s understand the first scenario.

Imagine a company that uses AWS, with an employee named `'rstead'`. This employee has an IAM account, which allows them to interact with certain company resources.

A security incident occurs: an attacker manages to obtain the credentials for an account within the AWS environment and begins exploring the permissions available to it.

## Attack Chain

Public S3 bucket -> Extracting encrypted passwords -> IAM permissions & DynamoDB -> Credential reuse -> Access to sensitive data

---
# Enumeration

Since the lab provied us with an s3 bucket so it will be our entry point

![[Pasted image 20261028182433.png]]

Lets paly with it.

first i will try to list that bucket with no credentials, maybe there is files set to the public, who knows ?

```bash
aws s3 ls hl-storage-general --no-sign-request
```

![[Pasted image 20261028185842.png]]

as you can see here this bucket has a folder called `migration`.
lets see what is inside this folder

```bash
aws s3 ls hl-storage-general/migration/ --no-sign-request
```

![[Pasted image 20261028185916.png]]

as you can see that folder contines a file named `asana-cloud-migration-backup.json`

##  What is Asana?

Teams use Asana, a cloud-based platform, to keep their tasks organized and on track. Just keep in mind that the information inside can be confidential.

lets download this file and see whit it hides

```bash
aws s3 cp s3://hl-storage-general/migration/asana-cloud-migration-backup.json . --no-sign-request
```

The file is an export of an Asana project, and its `notes` field contains project details along with sensitive data. Keeping secrets inside a project file and then making that file publicly accessible is the first security mistake in the attack chain.

![[Pasted image 20261028191404.png]]

so lets grep all the `notes` fileds

```bash
cat asana-cloud-migration-backup.json | grep '"notes"'
```

![[Pasted image 20261028191840.png]]

here we go bro, i find AWS credentials!

now lets configure our self with aws cli, but before that we need to know the the region that the company uses to deploy infrastructre 

We can find this out by sending a HEAD HTTP request to the S3 bucket. The response returns the region in the `x-amz-bucket-region` header.

```bash
crul -I hl-storage-general.s3.amazonaws.com
```

`-i` (or `--include`) ells `curl` to nclude the HTTP response headers in the output, along with the response body.

![[Pasted image 20261028192613.png]]

as you can see  the region is `us-east-1`

lets now configure

```bash
aws configure
```

![[Pasted image 20261028194859.png]]

now lets see who are we

```bash
aws sts get-caller-identity
```

![[Pasted image 20261028195217.png]]

From the output, we can see that we are authenticated as the IAM user `migration-test` in AWS account `243687662613`.

---
# Exploring IAM permissions using `Pacu`

## What is Pacu?

Pacu is an open-source framework for testing the security of AWS environments, and it makes enumerating our permissions much easier.

you can find and install it here https://github.com/RhinoSecurityLabs/pacu

after install it make sure to create a virutal enviroment to install the requirments

![[Pasted image 20261028203138.png]]

lets fire it!

when it asks you to create a new seession, set `0`

![[Pasted image 20261028203623.png]]

after that use `set_keys` to enter the creds the we found

![[Pasted image 20261028203901.png]]

We can list the available modules in Pacu with `ls`

to understand what we can do we will use a module called i`am__bruteforce_permissions`

```
run iam__bruteforce_permissions
```

![[Pasted image 20261029000855.png]]

It finds multiple DynamoDB permissions!

---
#  Lateral Movement to DynamoDB

DynamoDB is a fully managed, serverless NoSQL database service from AWS. It stores data as key-value/document items in tables, scales automatically, and delivers fast, low-latency performance even at large scale.

since we have the permission to list the tables, so why not list it?

```bash
aws dynamodb list-tables
```

![[Pasted image 20261029002610.png]]

we get two tables: `analytics_app_users` and `user_order_logs`

lets now see if we can read the two tables, we will use `describe-table` to achive taht

```bash
aws dynamodb describe-table --table-name analytics_app_users
aws dynamodb describe-table --table-name user_order_logs
```

![[Pasted image 20261029003630.png]]

![[Pasted image 20261029003645.png]]

as you can see, we can describe `analytics_app_users` but we can't describe `user_order_logs`

The success of `ListTables` does not mean that you can read all the data. Each operation has its own independent IAM permissions, and these permissions may vary depending on the specific resource name.

This result is what makes us realize that we need to identify another account or different permissions.

---
# Cracking Hashes

lets download the table `analytics_app_users` on our machince and see how we can use it

```bash
aws dynambodb scan --table-name analytics_app_users > output.json
```

![[Pasted image 20261029122717.png]]

the table contains the username and the Password Hash for `51` deffirent users

lets check the hash type

```bash
hashid <hash>
```

![[Pasted image 20261029124154.png]]

is it `SHA-256`
before we start to crack the hashed we need to but them in a `username:hash` format, this format allows `John` to treat each hash as belonging to a specific user, and it can display the discovered password alongside the corresponding username.

there are many way to do that but i will go with python to make a simple script to handle it as that what i know and what i good at. i will attach the script with the writeup

![[Pasted image 20261029131447.png]]

now we have our credentials ready for cracking!

```bash
john ./user_hash --format=Raw-SHA256 --wordlist=../../Wordlists/rockyou.txt
```

![[Pasted image 20261029132550.png]]

great, we cracked the hashes and get the passwords for 18 users!

and we can export that list using:

```bash
john ./user_hash --show --format=Raw-SHA256
```

![[Pasted image 20261029132918.png]]

# Lateral Movement via AWS Console Credential Stuffing

An obvious place to reuse these credentials is the AWS Console. Maybe some of these users have the same username and password for their IAM account?

A good tool to use is [GoAWSConsoleSpray](https://github.com/WhiteOakSecurity/GoAWSConsoleSpray). This script takes an AWS account ID, a user list and a password list as parameters

so we need to have to saperated lists one for the `usernames` and one for the `passwords`

```bash
john ./user_hash --show --format=Raw-SHA256 | awk -F":" '{print $1}' > users.txt

john ./user_hash --show --format=Raw-SHA256 | awk -F":" '{print $2}' > passwords.txt
```

don't forget to remove thejohn artifact from bottom of user list.

install GoAWSConsoleSpray

```bash
go install github.com/WhiteOakSecurity/GoAWSConsoleSpray@latest
```

after install it you can find it in `~/go/bin`

lets fire it!!

![[Pasted image 20261029135519.png]]

here we go, we find a valid password for the user `rstead` and the Multi-factor authentication is not enabled for this user.

so lets sign in!

![[Pasted image 20261029135928.png]]

and we are in.

![[Pasted image 20261029140134.png]]

if you remember, you have found two tables in DynamoDB, one we was able to read wich is `analytics_app_users` and one we couldn't wich is `user_order_logs`, so lets check if now we are able to access it

we can do that by navigating to the DynamoDB service.

![[Pasted image 20261029141106.png]]

then we will se the table 

![[Pasted image 20261029144928.png]]

slect it and then `Explore items` .

![[Pasted image 20261029145202.png]]

and here we go!

![[Pasted image 20261029145637.png]]

The dataset exposes users’ personally identifiable information (PII). PWNED! The flag is sitting right there in the table too.

i hope you enjoied with me , i will get enoght the red side in this writeup but that dose not means that there isn't another one the blue side ;)