from setuptools import setup, find_packages

setup(
    name="ai_werewolf",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'python-dotenv',
        'pytest',
        'pytest-asyncio'
    ]
) 