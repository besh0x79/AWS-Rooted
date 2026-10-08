# Discover AWS Organization ID via S3 Bucket

![Discover AWS Organization ID via S3 Bucket - Cybr.com Lab](https://images.cybr.com/labs/cmpyliej60000mt07jha7m0p1/71ed01d3002d0f8ea8b07ebdf1ea32f98f80e11c5531261be7045f998a75b9c2.webp)

Hello pwners, this is Beshoy again, and today we have a new lab from Cybr.com. In today's lab, we will learn how to discover AWS Organization IDs by exploiting limited S3 bucket access. Using an automated approach, this lab demonstrates how to efficiently identify org IDs in just 360 attempts instead of brute-forcing 3.66 quadrillion combinations.

> **Ready to try it yourself?** Launch the lab here: [**Start the Lab on Cybr.com**](https://cybr.com/hands-on-labs/lab/discover-aws-organization-id-via-s3-bucket/)

---

## What exactly will we learn?

- Install and set up the `conditional-love` tool in a Python virtual environment.
- Enumerate an IAM role and read its policy to find the target S3 bucket.
- Assume the role and run `conditional-love` to guess an AWS Organization ID one character at a time.
- Read the CloudTrail log entries this technique leaves behind.
- Explain why testing one character at a time makes guessing the Organization ID practical.

## What is an AWS Organization ID?

An **AWS Organization ID** is the unique identifier assigned to an AWS Organization when you create it. It looks like `o-` followed by lowercase letters or digits, for example `o-a1b2c3d4e5`.

**What is it for?**

AWS Organizations lets you centrally manage multiple AWS accounts (consolidated billing, policies, account grouping). The Organization ID identifies that whole group of accounts, as opposed to a single account.

## Why is it important for an attacker?

Discovering the Organization ID during a pentest matters because it shows you the **trust boundaries** of the environment and what an attacker could reach from a foothold.

In short, the org ID isn't a vulnerability by itself. It's a map key that shows how far access can spread, and that's what makes it useful for a pentester and worth defending against.

---

# Install conditional-love

`conditional-love` is an AWS metadata enumeration tool by [Daniel Grzelak](https://www.linkedin.com/in/danielgrzelak/) of [Plerion](https://plerion.com/). You can use it to enumerate resource tags, account IDs, org IDs, organization management account IDs, and more. Its GitHub repository is [here](https://github.com/plerionhq/conditional-love/tree/main).

It is inspired by [S3 Account Search](https://github.com/WeAreCloudar/s3-account-search) by [Cloudar](https://cloudar.be/).

To get started, let's download the tool we'll be using for this lab:

```shell
git clone https://github.com/plerionhq/conditional-love.git
```

After cloning the repository, just `cd` into the directory.

<img width="1061" height="145" alt="image" src="https://github.com/user-attachments/assets/d83078b9-f729-4254-8ec5-7aa5d6b447cd" />

Let's now install the requirements for this tool to run.

**Note:** You may encounter an `externally-managed-environment` error when installing the requirements with `pip3`. To avoid it, create and use a Python virtual environment:

```shell
python3 -m venv .venv
```

Activate the virtual environment:

```shell
source .venv/bin/activate
```

Then install the requirements:

```shell
pip install -r requirements.txt
```

<img width="1553" height="376" alt="image" src="https://github.com/user-attachments/assets/8468740a-2369-4508-a897-349e9be3cfe6" />

Then make the script executable:

```shell
chmod +x ./conditional-love.py
```

---

# Configuration

First of all, let's authenticate ourselves on the AWS CLI with the credentials that the lab provides.

<img width="781" height="488" alt="image" src="https://github.com/user-attachments/assets/e40a9cd1-b04b-478d-8476-ac8a381819b4" />

You can find them here.

You can think of the `ACCESS KEY ID` and the `SECRET ACCESS KEY` as a username and a password.

To configure them, run the following command:

```shell
aws configure --profile enum
```

You can either configure the credentials in a named profile or go without one, but if you skip the profile, the credentials will overwrite your default ones if they already exist.

By the way, the name `enum` isn't fixed; you can set whatever name you want.

<img width="1433" height="120" alt="image" src="https://github.com/user-attachments/assets/f9313da5-8747-448e-ad5a-61117de9ae94" />

Make sure to use `us-east-1` as the region, because the labs on Cybr.com always use this region unless otherwise specified.

---

# Enumerate IAM Roles

An **IAM role** is a secure identity that you create. It does not have permanent credentials attached; instead, it provides temporary permissions to trusted users, applications, or services.

Let's see how we can enumerate information about these roles:

```shell
aws iam list-roles --profile enum
```

It's pretty common for an AWS account to be packed with roles. They serve many different purposes, and one person may need a handful of them to get their work done, so running into dozens, or even hundreds, is nothing unusual. Out of the box, an account is capped at 1,000 roles, though you can ask AWS to raise that ceiling to 5,000.

So while this command is handy, the results can quickly turn into a wall of text. If your terminal freezes on a lone `:`, don't worry; it's just paging the output so you can read it bit by bit. Use the up and down arrow keys to scroll, and press `q` when you want to exit.

Let's cut the noise. When you already know the exact name of the role, you can filter the results down to just that one:

```shell
aws iam list-roles --query "Roles[?RoleName=='S3AccessImages']" --profile enum
```

**Note:** I already knew that the role `S3AccessImages` existed from the initial stages of enumeration. In a real engagement, you have to do your own enumeration and find it.

<img width="1920" height="589" alt="image" src="https://github.com/user-attachments/assets/04aafc25-a4b0-4f83-987b-380d8f7675df" />

Copy the ARN value and save it in your notes, since we'll need it again in just a moment.

---

## Retrieve the role's policy

Let's now see which policies this role has:

```shell
aws iam list-role-policies --role-name S3AccessImages --profile enum
```

<img width="1877" height="147" alt="image" src="https://github.com/user-attachments/assets/a0578aa3-d1df-419f-ab37-4278b6bc663a" />

As you can see, this role has an inline policy named `AccessS3BucketObjects`. Let's retrieve this policy:

```shell
aws iam get-role-policy --role-name S3AccessImages --policy-name AccessS3BucketObjects --profile enum
```

<img width="1920" height="522" alt="image" src="https://github.com/user-attachments/assets/b52e5b0d-6054-4d97-b222-7aa41ba76e2e" />

As you can see here, this role has access to an S3 bucket called `img.cybrlabs.io`.

---

# Running conditional-love

Now that we know the role ARN and the bucket name, we have all the information we need to run the tool:

```shell
./conditional-love.py --role arn:aws:iam::337405469824:role/S3AccessImages --target s3://img.cybrlabs.io/ --action=s3:HeadObject --condition=aws:ResourceOrgID --alphabet="0123456789abcdefghijklmnopqrstuvwxyz-" --profile enum
```

<img width="503" height="276" alt="image" src="https://github.com/user-attachments/assets/3180be3b-fc47-4292-bf77-d81d4aa29ed7" />


And there it is: the full ID has been revealed. That's the flag.

<img width="708" height="855" alt="image" src="https://github.com/user-attachments/assets/9e67e6f5-cde2-4139-a100-78328a8298e7" />

---

# Conclusion

In this lab, we discovered the AWS Organization ID that owns an S3 bucket using nothing but a low-privileged IAM role. We started by installing `conditional-love` in a Python virtual environment and configuring a named AWS profile with the lab's credentials. Then we enumerated the IAM role `S3AccessImages`, read its inline policy, `AccessS3BucketObjects`, and found the target bucket, `img.cybrlabs.io`.

With the role ARN and the bucket name, we ran `conditional-love` with the `aws:ResourceOrgID` condition key and the `s3:HeadObject` action. The technique works because condition keys such as `aws:ResourceOrgID` support wildcard matching, so the tool can test the ID one character at a time instead of guessing it all at once. An Organization ID is `o-` followed by 10 characters, and each position has 36 possible values (`a-z` and `0-9`), so the worst case is 10 × 36 = 360 attempts instead of 36¹⁰ (about 3.66 quadrillion) for a blind brute force.

The key takeaway is that identifiers such as account IDs and organization IDs are not secrets, and they can be recovered with very little access. They are still valuable reconnaissance information, because they reveal how far trust and access can spread across an environment. For defenders, this means three things: don't rely on the secrecy of these IDs as a security control, limit who can assume roles like this one, and watch CloudTrail for bursts of failed S3 requests, since a technique that makes hundreds of guesses leaves a clear trail behind.
