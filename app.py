with open("requirements_v1.txt", "r") as file:
    v1_content = file.read().strip().splitlines()

with open("requirements_v2.txt", "r") as file:
    v2_content = file.read().strip().splitlines()

for old_requirement, new_requirement in zip(v1_content, v2_content):

    if old_requirement == new_requirement:
        print("NO CHANGE:", old_requirement)

    else:
        print("CHANGED")
        print("Old:", old_requirement)
        print("New:", new_requirement)