import json

with open("output.json") as f:
    data = json.load(f)

results = []

for item in data["Items"]:
    if "UserID" in item and "PasswordHash" in item:
        username = item["UserID"]["S"]
        password_hash = item["PasswordHash"]["S"]
        results.append(f"{username}:{password_hash}")

with open("user_hash", "w") as f:
    f.write("\n".join(results) + "\n")

print(f"[+] Extracted {len(results)} username/hash pairs")
print("[+] Saved to user_hash")
