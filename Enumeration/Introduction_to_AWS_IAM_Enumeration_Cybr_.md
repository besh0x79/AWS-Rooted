# Introduction to AWS IAM Enumeration

Hello pwners! In this lab from cybr.com, we will learn how to enumerate AWS IAM, including users, groups, roles, and permissions. Enumeration is a critical part of security assessments because it gives us the lay of the land and helps us find potential weaknesses.

## What exactly will we learn?

- Configure the AWS CLI with access keys and named profiles.
- Enumerate IAM users and read their inline and managed policies.
- Enumerate IAM groups, their members, and the policies attached to them.
- Enumerate IAM roles, who can assume them, and what they allow.
- Read an IAM policy document to work out which actions it permits.

---

# Configuration

First of all, let's authenticate ourselves on the AWS CLI with the credentials that the lab provides.

<img width="652" height="344" alt="image" src="https://github.com/user-attachments/assets/25e062f6-48df-4165-b1d5-a4c1edfc434c" />

You can find them here.

To configure them, run the following command:

```shell
aws configure --profile enum
```

You can either configure the credentials in a named profile or go without one, but if you skip the profile, the credentials will overwrite your default ones if they already exist.

By the way, the name `enum` isn't fixed; you can set whatever name you want.

<img width="1285" height="135" alt="image" src="https://github.com/user-attachments/assets/1bba748a-8815-44fe-b2c4-c0e9592932ff" />

Make sure to use `us-east-1` as the region, because the labs on Cybr.com always use this region unless otherwise specified.

---

# Enumerate IAM Users

Let's start with a command similar in function to `whoami`:

```shell
aws sts get-caller-identity --profile enum
```

Remember to pass `--profile <name>` if you used a named profile. Otherwise, the command won't work or, worse, it will use different credentials and return wrong results.

<img width="1463" height="177" alt="image" src="https://github.com/user-attachments/assets/c1065aef-d2ad-432a-8070-3a7073c88222" />

Look at this output: it contains some useful information.

The `ARN` stands for Amazon Resource Name, and it includes the Account ID, which is part of how IAM ARNs are kept unique across all of AWS.

Now let's enumerate our current user and the other users in this account using this command:

```shell
aws iam list-users --profile enum
```

<img width="1340" height="814" alt="image" src="https://github.com/user-attachments/assets/a6b811eb-01f2-4c58-b761-604a9a31ef02" />

We have 4 IAM users in this account.

The next step is to enumerate the permissions of each of these 4 users, but to save time, I will go with `Joel` only.

We will start by listing the policies for `Joel`:

```shell
aws iam list-user-policies --user-name Joel --profile enum
```

<img width="1772" height="179" alt="image" src="https://github.com/user-attachments/assets/16c02bd7-2929-4441-975f-507cdaef7f21" />

As you can see, the user `Joel` has an inline policy named `AllowEnumerateRoles`.

Let's dig deeper and get more information about this policy:

```shell
aws iam get-user-policy --user-name Joel --policy-name AllowEnumerateRoles --profile enum
```

<img width="1759" height="548" alt="image" src="https://github.com/user-attachments/assets/3fbee604-2fad-47dd-af96-ce2b28e6a35d" />

Now we can see that this policy permits 4 separate actions:

- `iam:GetRole`
- `iam:GetRolePolicy`
- `iam:ListRoles`
- `iam:ListRolePolicies`

---

# Enumerate IAM Groups

An IAM user group is a collection of IAM users. User groups let you specify permissions for multiple users at once, which makes it easier to manage their permissions.

Let's enumerate the group information:

```shell
aws iam list-groups --profile enum
```

<img width="1362" height="471" alt="image" src="https://github.com/user-attachments/assets/886983f0-16cf-4fe7-81d7-aeb41b6890bf" />

As you can see, there are two groups in this environment:

- `Developers`
- `Infrastructure`

To find out which groups we are part of, we will use the following command:

```shell
aws iam list-groups-for-user --user-name Joel --profile enum
```

<img width="1693" height="316" alt="image" src="https://github.com/user-attachments/assets/155fd249-9c55-4f16-beed-3fc0d53e455d" />

We are part of the `Developers` group. Let's enumerate this group and dig deeper into its information:

```shell
aws iam get-group --group-name Developers --profile enum
```

<img width="1651" height="641" alt="image" src="https://github.com/user-attachments/assets/f2bc54ef-9c4c-43a5-8e85-a0a42ab97ee7" />

As you can see, there are two users in the `Developers` group: our user `Joel` and the user `Mike`.

Now let's list the policies attached to this group:

```shell
aws iam list-group-policies --group-name Developers --profile enum
```

<img width="1786" height="176" alt="image" src="https://github.com/user-attachments/assets/a9cdcecb-05ef-4dc7-9656-7d80b295912d" />

The `Developers` group has a policy named `Developers-policy`. Let's find out more about it:

```shell
aws iam get-group-policy --group-name Developers --policy-name Developers-policy --profile enum
```

The result I got is:

```json
{
    "GroupName": "Developers",
    "PolicyName": "Developers-policy",
    "PolicyDocument": {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Action": [
                    "iam:ListAccessKeys"
                ],
                "Effect": "Allow",
                "Resource": [
                    "arn:aws:iam::525530758771:user/Joel",
                    "arn:aws:iam::525530758771:user/Mike"
                ],
                "Sid": "ListAccessKeysOnDevUsers"
            },
            {
                "Action": [
                    "iam:ListGroupPolicies",
                    "iam:ListAttachedPolicies",
                    "iam:ListPolicyVersions",
                    "iam:ListUserPolicies",
                    "iam:ListAttachedUserPolicies",
                    "iam:ListUsers",
                    "iam:ListGroups",
                    "iam:ListGroupsForUser",
                    "iam:GetPolicy",
                    "iam:GetPolicyVersion",
                    "iam:GetUser",
                    "iam:GetUserPolicy",
                    "iam:GetGroupPolicy",
                    "iam:GetGroup",
                    "iam:ListAttachedGroupPolicies"
                ],
                "Effect": "Allow",
                "Resource": "*",
                "Sid": "IAMReadOnly"
            }
        ]
    }
}
```

This information tells us that the members of this group, `Joel` and `Mike`, have all of these permissions available to them:

- The first statement (`ListAccessKeysOnDevUsers`) allows listing the access keys of `Joel` and `Mike` only.
- The second statement (`IAMReadOnly`) allows read-only IAM enumeration actions on all resources (`"Resource": "*"`).

The `Developers-policy` that we just saw is called an **inline policy**. In AWS, there is another kind of policy called an **attached (managed) policy**. This kind of policy exists as a standalone policy and is then attached to a user, group, or role.

So let's find out if the `Developers` group has any of them:

```shell
aws iam list-attached-group-policies --group-name Developers --profile enum
```

<img width="1599" height="104" alt="image" src="https://github.com/user-attachments/assets/d3bf7e47-3942-4081-afef-4baf1d37ea1c" />

There are none for this group.

If you remember, we have another group called `Infrastructure`. You can apply all of the previous steps to it, but to save time, I will just check whether that group has any attached policies:

```shell
aws iam list-attached-group-policies --group-name Infrastructure --profile enum
```

<img width="1646" height="311" alt="image" src="https://github.com/user-attachments/assets/9287d697-0e08-45e4-ad46-7cf10949fec2" />

Ah! This time we have attached managed policies!

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
aws iam list-roles --query "Roles[?RoleName=='SupportRole']" --profile enum
```

Looking at the output, this role is set up for internal support work, and only the user `Mary` is allowed to assume it. Our user `Joel` isn't on that list.

From an attacker's or pentester's point of view, that's the obvious next question: how could we get access as Mary so we can use the role ourselves? In other words, we would start hunting for a path to escalate privileges from Joel to Mary.

Let's now find out which inline policy is associated with this role:

```shell
aws iam list-role-policies --role-name SupportRole --profile enum
```

<img width="1511" height="157" alt="image" src="https://github.com/user-attachments/assets/7cd66d56-88b9-46ee-b7d7-8cfb26adda8f" />

We have an inline policy named `AllowS3FullAccessForRole`.

Let's get the content of that inline policy:

```shell
aws iam get-role-policy --role-name SupportRole --policy-name AllowS3FullAccessForRole --profile enum
```

<img width="1914" height="424" alt="image" src="https://github.com/user-attachments/assets/a278c74c-98b0-435e-ace1-2fc8adb2f397" />

The permissions attached to this role include full Amazon S3 access, and that's exactly the kind of thing a threat actor would go after. A wildcard like `s3:*` should raise an immediate red flag for anyone reviewing this environment's security, since it lets the role do anything at all with S3. Permissions this sweeping should be the exception, not the norm.

---

# Conclusion

In this lab, we walked through the core steps of enumerating AWS IAM using only the AWS CLI and a low-privileged set of credentials. We started by configuring a named profile and confirming our identity with `aws sts get-caller-identity`. Then we enumerated the users in the account, and we read the inline policy of `Joel` to understand what he is allowed to do.

Next, we moved on to groups. We found that `Joel` belongs to the `Developers` group alongside `Mike`, and we read the group's inline policy to see which IAM read-only actions it grants. We also learned the difference between inline policies and attached (managed) policies, and we discovered that the `Infrastructure` group has attached managed policies worth investigating further.

Finally, we enumerated IAM roles. We found that `SupportRole` can only be assumed by `Mary`, which makes her a natural target for privilege escalation from `Joel`, and that the role carries an overly permissive `s3:*` inline policy.

The key takeaway is that even read-only IAM permissions can reveal a lot: who exists, who belongs to which group, who can assume which role, and where dangerous permissions live. This is exactly why enumeration is the foundation of every AWS security assessment. From a defender's point of view, it is also a reminder to follow the principle of least privilege, avoid wildcard permissions, and limit who can enumerate IAM in the first place.
