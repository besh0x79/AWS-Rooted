# Introduction to Amazon S3 Enumeration

Hello pwners, this is Beshoy again, and today we have a new lab from Cybr.com. In today's lab, we will learn how to enumerate Amazon S3, including how to use the AWS S3 CLI, which has unique quirks compared to other AWS services. You'll learn how to list buckets and objects, as well as how to download objects from S3 to your local computer. Enumeration is a critical part of security assessments because it gives us the lay of the land and can help us find potential weaknesses that can be exploited. This lab gives you a safe environment to do exactly that. Capture the flag by submitting the value in `object.txt`.

> [!tip] 🔗 Lab Link
> **Ready to try it yourself?** Launch the lab here: [**Start the Lab on Cybr.com**](https://labs.cybr.com/launch?token=eyJhbGciOiJIUzI1NiJ9.eyJsYWJJZCI6ImNtb2Rjemt1eDAwMDBwemxkdDZoN2p3eDIiLCJjdXN0b21lciI6ImN5YnIiLCJtZW1iZXJzaGlwIjoiZnJlZSIsIm1lbWJlcklkIjoiMTc4OTAiLCJkaXNwbGF5TmFtZSI6IkJlc2hveSIsImlzcyI6ImN5YnIiLCJhdWQiOiJob3N0ZWQtbGF1bmNoIiwic3ViIjoibXl0aGd1eWJAZ21haWwuY29tIiwianRpIjoiYTAzOTFkOGUtNjQ1YS00ZTliLWFkYjQtMDg0MmMxN2NlM2MzIiwiaWF0IjoxNzkwODcxNDk4LCJleHAiOjE3OTA4Nzg2OTh9.4nTT4QEOG3DjBTgY_wDRZzh9XbhYR6GEWhFTuMAvT94)

---

## What exactly will we learn?

- Set up the AWS CLI with the access keys the lab gives you.
- Read an IAM user policy to find which S3 actions it allows.
- List S3 buckets and the objects inside them with the AWS CLI.
- Download an S3 object and read what is inside it.
- Explain why a bucket policy can block access that an IAM policy allows.

## What is Amazon S3?

Amazon S3, which stands for Simple Storage Service, is AWS's cloud storage offering. You can use it to save and retrieve pretty much any kind of data, whether that's files, documents, images, videos, or anything else you need to keep.

---

# Configuration

First of all, let's authenticate ourselves on the AWS CLI with the credentials that the lab provides.

<img width="658" height="299" alt="image" src="https://github.com/user-attachments/assets/c69c4c4b-9102-4ecb-b998-00fa71250af4" />

You can find them here.

You can think of the `ACCESS KEY ID` and the `SECRET ACCESS KEY` as a username and a password.

To configure them, run the following command:

```shell
aws configure --profile enum
```

You can either configure the credentials in a named profile or go without one, but if you skip the profile, the credentials will overwrite your default ones if they already exist.

By the way, the name `enum` isn't fixed; you can set whatever name you want.

<img width="1347" height="147" alt="image" src="https://github.com/user-attachments/assets/a6b4346f-96c4-4c68-8350-aa0a753211b9" />

Make sure to use `us-east-1` as the region, because the labs on Cybr.com always use this region unless otherwise specified.

---

# IAM Enumeration

This lab is about S3 enumeration rather than IAM, but IAM still decides who gets to do what in AWS. Before we can tell whether we're even allowed to enumerate S3, we have to know which policies apply to us, whether that's our current user or our current role, depending on what we have access to. In this lab, it's a user.

Let's start with a command similar in function to `whoami`:

```shell
aws sts get-caller-identity --profile enum
```

Remember to pass `--profile <name>` if you used a named profile. Otherwise, the command won't work or, worse, it will use different credentials and return wrong results.

<img width="1529" height="169" alt="image" src="https://github.com/user-attachments/assets/5d85d256-e952-4437-87be-b112ca2735a6" />

The `ARN` stands for Amazon Resource Name, and it includes the Account ID, which is part of how IAM ARNs are kept unique across all of AWS.

So we're authenticated as a user named `Derek`. Let's start enumerating this user's permissions by listing the user's policies:

```shell
aws iam list-user-policies --user-name Derek --profile enum
```

<img width="1744" height="167" alt="image" src="https://github.com/user-attachments/assets/54e5f963-ab65-4127-bab1-9b9d36d51e69" />

And here we go: our user `Derek` has an inline policy named `AllowS3Operations`.

### What is `AllowS3Operations`?

**Allow S3 Operations** refers to permission settings in Amazon Web Services (AWS) that grant users, roles, or services the right to perform specific actions on Amazon Simple Storage Service (S3) resources such as buckets and objects.

Let's now retrieve this policy and see exactly what it permits:

```shell
aws iam get-user-policy --user-name Derek --policy-name AllowS3Operations --profile enum
```

The result I got is:

```json
{
    "UserName": "Derek",
    "PolicyName": "AllowS3Operations",
    "PolicyDocument": {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Action": [
                    "iam:ListPolicies",
                    "iam:ListPolicyVersions",
                    "iam:GetPolicy",
                    "iam:GetUser",
                    "iam:GetUserPolicy",
                    "iam:ListUserPolicies"
                ],
                "Effect": "Allow",
                "Resource": "*",
                "Sid": "AllowIAMActions"
            },
            {
                "Action": [
                    "s3:ListBucket",
                    "s3:GetBucketPolicy"
                ],
                "Effect": "Allow",
                "Resource": [
                    "arn:aws:s3:::cybr-data-bucket1-874373490618",
                    "arn:aws:s3:::cybr-data-bucket2-874373490618"
                ],
                "Sid": "AllowS3BucketActions"
            },
            {
                "Action": [
                    "s3:GetObject"
                ],
                "Effect": "Allow",
                "Resource": [
                    "arn:aws:s3:::cybr-data-bucket1-874373490618/*",
                    "arn:aws:s3:::cybr-data-bucket2-874373490618/*"
                ],
                "Sid": "AllowS3ObjectActions"
            },
            {
                "Action": [
                    "s3:ListAllMyBuckets",
                    "s3:GetBucketLocation"
                ],
                "Effect": "Allow",
                "Resource": "*",
                "Sid": "AllowListAllBuckets"
            }
        ]
    }
}
```

As you can see, this policy permits several actions, but we will focus on the S3 ones:

- `s3:ListBucket`
- `s3:GetBucketPolicy`

These apply to two resources:

- `arn:aws:s3:::cybr-data-bucket1-874373490618`
- `arn:aws:s3:::cybr-data-bucket2-874373490618`

Then:

- `s3:GetObject`

Once more we're looking at the same two resources, but this time there's a `/*` on the end. That's because the action applies to objects, and S3 requires object ARNs to include it. Bucket-level actions go the other way and need the ARN without the `/*`. It's a strange S3 quirk, so it's worth keeping in mind.

Finally, we see:

- `s3:ListAllMyBuckets`
- `s3:GetBucketLocation`

These apply to all resources (`"*"`).

---

# Enumerating S3

## Listing buckets and objects

To list the buckets, we will use `s3api`. There is another command set called `s3`, but `s3api` is generally much better.

```shell
aws s3api list-buckets --profile enum
```

<img width="1458" height="473" alt="image" src="https://github.com/user-attachments/assets/a71db71d-4755-4a7a-b4ca-481a33602628" />

As you can see, we have two buckets here:

- `cybr-data-bucket1-874373490618`
- `cybr-data-bucket2-874373490618`

Let's list the objects in the first bucket. To do that, we will use `list-objects-v2`. Again, there is an older version called `list-objects`, but it's recommended that you use `list-objects-v2`.

```shell
aws s3api list-objects-v2 --bucket cybr-data-bucket1-874373490618 --profile enum
```

<img width="1873" height="457" alt="image" src="https://github.com/user-attachments/assets/2600f6a6-b3b9-4732-83c7-09e2d1d142f9" />

We got one object stored in this bucket, named `object.txt`. The `Key` field is the object name.

## Accessing/Downloading objects

We can even go a step further and download this object, since we have the `s3:GetObject` permission:

```shell
aws s3api get-object --bucket cybr-data-bucket1-874373490618 --key object.txt ./Objects/object.txt --profile enum
```

<img width="1883" height="251" alt="image" src="https://github.com/user-attachments/assets/8daa08e0-dea6-4230-a5ad-6236f139b20e" />

Here we have 3 required arguments:

- `--bucket`: the name of the bucket where the object resides
- `--key`: the specific object to download
- `<outfile>`: the path and name of the file on our local computer

Once the file is downloaded, we can open it like a regular `.txt` file.

<img width="1900" height="333" alt="image" src="https://github.com/user-attachments/assets/e603efa0-7a1a-458f-b765-f01f238bbdd0" />

And we got the flag ;)

<img width="659" height="550" alt="image" src="https://github.com/user-attachments/assets/b0d65541-4390-4060-86cd-8874d139afb4" />

---

# Conclusion

In this lab, we practiced enumerating Amazon S3 from the AWS CLI using a single set of low-privileged credentials. We configured a named profile, confirmed our identity as the user `Derek` with `aws sts get-caller-identity`, and then read his inline policy, `AllowS3Operations`, to understand exactly what he is allowed to do before touching S3.

That policy showed us the S3 permissions we had: `s3:ListAllMyBuckets` to discover the buckets, `s3:ListBucket` to list their contents, and `s3:GetObject` to read objects. It also showed us an important S3 quirk: bucket-level actions use the plain bucket ARN, while object-level actions require `/*` at the end of the ARN.

With that knowledge, we used `s3api list-buckets` to find two buckets, `s3api list-objects-v2` to find `object.txt` in the first one, and `s3api get-object` to download it and capture the flag.

The key takeaway is that reading the IAM policy first tells you what to expect and saves you from blind guessing. For defenders, it is a reminder to scope S3 permissions to the specific buckets and actions each identity really needs, and to remember that bucket policies are evaluated alongside IAM policies, so they can still restrict access that an IAM policy appears to allow.
