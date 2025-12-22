from setuptools import setup, find_packages

setup(
    name="text-augmentation-api",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Flask==2.3.3',
        'Flask-CORS==4.0.0',
        'Flask-Limiter==3.3.2',
        'flasgger==0.9.5',
        'textblob==0.17.1',
        'nltk==3.8.1',
        'python-dotenv==1.0.0',
    ],
    entry_points={
        'console_scripts': [
            'text-augmentor=run:main',
        ],
    },
)