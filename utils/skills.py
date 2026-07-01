skills_db = [
    "python",
    "java",
    "sql",
    "excel",
    "power bi",
    "sap",
    "machine learning",
    "artificial intelligence",
    "javascript",
    "react",
    "flask",
    "django",
    "docker",
    "git",
    "linux",
    "c++",
    "c#",
    "management",
    "leadership",
    "html",
    "css",
    "node.js",
    "mongodb",
    "mysql"
]
def extract_skills(text):

    found = []

    for skill in skills_db:
        if skill.lower() in text.lower():
            found.append(skill)

    return found