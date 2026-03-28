import importlib

def run_skill(skill_name, **kwargs):
    try:
        module = importlib.import_module(f"skills.{skill_name}")
        return module.run(**kwargs)

    except Exception as e:
        print(f"Error running skill {skill_name}:", e)
        return None