# Discover AWS Account ID via S3 Bucket

![Discover AWS Account ID via S3 Bucket - Cybr.com Lab](https://images.cybr.com/labs/cmpyx230o000dmt07ejo2sdva/f1da2c1db45fb7e72aa585d60d368d5741c2736876a16cd0807196fb113df627.webp)

Hello pwners, this is Beshoy again, and today we have a new lab from Cybr.com. In today's lab, we will learn how to enumerate AWS account IDs with very limited access to S3 buckets. This lab simulates compromised credentials and makes use of a clever automated tool to reduce guesses from 1 trillion possible combinations down to only 120.

> [!tip] Lab Link
> **Ready to try it yourself?** Launch the lab here: [**Start the Lab on Cybr.com**](https://cybr.com/hands-on-labs/lab/discover-aws-account-id-via-s3-bucket/)

---

## What exactly will we learn?

- Configure the AWS CLI with the IAM user credentials the lab gives you.
- Enumerate an IAM role and read its policy to find the S3 bucket it can reach.
- Assume the role and run `s3-account-search` to find the account ID that owns the bucket.
- Explain how the `s3:ResourceAccount` condition key makes this technique work.
- Describe why the tool needs at most 120 attempts instead of 1 trillion.

## What is an AWS Account ID?

Before we get started, a quick word about AWS account IDs: they're not meant to be treated as passwords. Plenty of people argue about this, but the reality is that knowing someone's account ID doesn't, by itself, open any doors.

A better way to picture it is as a street address. Anyone can know where a building is, but that doesn't mean they can walk in. They'd still need a key, or a door someone forgot to lock. In the same way, an attacker who learns your account ID still needs to find an actual weakness, like a misconfigured permission, before they can do any damage.

That doesn't mean the ID is useless, though. It can tell you quite a bit about what's running inside an account, and we'll look at that more closely in the next lesson. For now, this lab zooms in on one specific trick: finding out which AWS account owns an S3 bucket.

---

# Install s3-account-search

`s3-account-search` is a command-line tool used to discover the 12-digit AWS account ID that owns a specific Amazon S3 bucket.

One thing to note before we go further: this technique isn't completely unauthenticated. The tool we'll be using to automate it needs access to an IAM role, so you'll need some level of credentials in hand to make it work.

To get started, let's install the tool we'll be using for this lab:

```shell
pip install s3-account-search
```

![[Pasted image 20261002143931.png]]

**Note:** You may encounter an `externally-managed-environment` error when installing the tool with `pip3` on Kali Linux. You can either create and use a Python virtual environment:

```shell
python3 -m venv venv
source venv/bin/activate
pip install s3-account-search
```

**Or**, if you prefer to install it system-wide, you can bypass the restriction using `--break-system-packages`:

```shell
pip3 install s3-account-search --break-system-packages
```

The `--break-system-packages` option can affect your system Python environment, so using a virtual environment is generally safer.

Once the tool is installed, let's configure ourselves.

---

# Configuration

First of all, let's authenticate ourselves on the AWS CLI with the credentials that the lab provides.

![[Pasted image 20261002145257.png]]

You can find them here.

You can think of the `ACCESS KEY ID` and the `SECRET ACCESS KEY` as a username and a password.

To configure them, run the following command:

```shell
aws configure --profile enum
```

You can either configure the credentials in a named profile or go without one, but if you skip the profile, the credentials will overwrite your default ones if they already exist.

By the way, the name `enum` isn't fixed; you can set whatever name you want.

![[Pasted image 20261002145508.png]]

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

![[Pasted image 20261002152054.png]]

Copy the ARN value and save it in your notes, since we'll need it again in just a moment.

## Retrieve the role's policy

Let's now see which policies this role has:

```shell
aws iam list-role-policies --role-name S3AccessImages --profile enum
```

![[Pasted image 20261002154413.png]]

As you can see, this role has an inline policy named `AccessS3BucketObjects`. Let's retrieve this policy:

```shell
aws iam get-role-policy --role-name S3AccessImages --policy-name AccessS3BucketObjects --profile enum
```

![[Pasted image 20261002154710.png]]

As you can see here, this role has access to an S3 bucket called `img.cybrlabs.io`.

---

# Figure Out the AWS Account ID of This Bucket

With `s3-account-search`, we have two ways to go about it. We can pass in a profile name with `--profile PROFILE`, or we can hand it the role ARN we just retrieved (`arn:aws:iam::069211227012:role/S3AccessImages`).

We'll go with the role ARN approach.

After that, the tool needs to know which bucket to target, either a bucket name or a specific object in it. Since we already have the bucket name, that's what we'll use:

```shell
s3-account-search arn:aws:iam::069211227012:role/S3AccessImages s3://img.cybrlabs.io --profile enum
```

![[Pasted image 20261002160254.png]]

And there it is: the account ID has been revealed. That's the flag.

![[Pasted image 20261002160642.png]]

---

# Conclusion

In this lab, we saw that an AWS account ID can be discovered even when we have almost no direct access to the target. We started by configuring a named profile with the lab's credentials, then enumerated IAM roles and found `S3AccessImages`. By reading its inline policy, `AccessS3BucketObjects`, we learned which bucket it could reach: `img.cybrlabs.io`.

We then used `s3-account-search` with the role's ARN and the bucket name to reveal the 12-digit account ID that owns the bucket. The technique works because the `s3:ResourceAccount` condition key lets a policy match the account ID that owns a bucket, and it supports wildcards. The tool tests the account ID one digit at a time: for each position, at most 10 digits need to be tried, so a 12-digit ID takes at most 12 × 10 = 120 attempts instead of the 1 trillion (10¹²) that a blind brute force would need.

The key takeaway is that an account ID is not a secret on its own, but it is still useful reconnaissance information, since it can help an attacker map the environment and plan the next steps. For defenders, it is a reminder to treat even small pieces of exposed information seriously, to limit which roles can be assumed and what they can access, and to monitor for unusual activity from roles that are rarely used.
