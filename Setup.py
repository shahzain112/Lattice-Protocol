from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="lattice-protocol",
    version="2.0.0",
    author="Shahzain",
    author_email="your-email@example.com",
    description="The Secure, Stateless Protocol for AI, Data, Blockchain, and Gaming",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/lattice-protocol",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
    install_requires=[
        "pydantic==2.10.4",
        "cryptography==43.0.3",
        "pandas==2.2.3",
        "numpy==1.26.4",
        "fastapi==0.115.6",
        "uvicorn[standard]==0.34.0",
        "web3==7.7.0",
        "pyodbc==5.1.0",
        "pymysql==1.1.1",
        "psycopg2-binary==2.9.10",
        "sqlalchemy==2.0.36",
        "requests==2.32.3",
    ],
    extras_require={
        "dev": ["pytest", "black", "flake8", "mypy"],
        "prod": ["gunicorn==23.0.0", "python-dotenv==1.0.1"],
    },
    entry_points={
        "console_scripts": [
            "lattice-server=server:main",
            "lattice-test=test_lattice:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)