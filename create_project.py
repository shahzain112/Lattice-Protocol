import os

base = r"E:\Lattice"
folders = ["core", "blockchain", "adapters", "data_engine", "security", "demos"]

files = {
    "core": ["__init__.py", "protocol.py", "messages.py"],
    "security": ["__init__.py", "crypto.py", "sandbox.py"],
    "blockchain": ["__init__.py", "ethereum.py", "solana.py"],
    "adapters": ["__init__.py", "aws.py", "sql.py"],
    "data_engine": ["__init__.py", "pipeline.py", "transform.py"],
    "demos": ["ai_agent.py", "web_server.py"],
    ".": ["requirements.txt", "README.md", "main.py"]
}

# Create folders
for folder in folders:
    os.makedirs(os.path.join(base, folder), exist_ok=True)
    print(f"📁 Created folder: {folder}")

# Create files
for folder, file_list in files.items():
    path = base if folder == "." else os.path.join(base, folder)
    for file in file_list:
        filepath = os.path.join(path, file)
        open(filepath, 'w').close()
        print(f"📄 Created file: {filepath}")

print("\n✅ Sab kuch ban gaya jani! Lattice project ready hai 🔥")