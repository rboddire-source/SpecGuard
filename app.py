def compare_requirements(old_requirement, new_requirement):
    if old_requirement == new_requirement:
        return "SAME"
    else:
        return "CHANGED"


result = compare_requirements(
    "Users can upload files up to 10 MB",
    "Users can upload files up to 25 MB"
)

print(result)
requirement_changed = True
conflict_detected = False

print(requirement_changed)
print(conflict_detected)