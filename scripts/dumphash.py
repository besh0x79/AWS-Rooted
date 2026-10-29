import json

with open("./output.json","r") as f:
    data = json.load(f)

results = []

for item in data["Items"]:
    if "UserID" in item and "PasswordHash" in item:
        username = item["UserID"]["S"]
        password = item["PasswordHash"]["S"]
        results.append(f"{username}:{password}")

with open('user_hash','w') as f:
    f.write("\n".join(results)+'\n')

print(f"[+] Extracted {len(results)} username/hash pairs")
print("[+] Saved to user_hash")