import os

SKILL_DIR = "skills"

def list_skills():
    return [
        f[:-3]
        for f in os.listdir(SKILL_DIR)
        if f.endswith(".py") and f != "__init__.py"
    ]