import setuptools

setuptools.setup(
    name="sidekik",
    version="1.0.0",
    description="",
    license="",

    author="Mitchell Murphy",
    author_email="",
    
    packages=setuptools.find_packages(),
    include_package_data=True,
    
    install_requires=[
        "email-validator",
        "Flask",
        "Flask-Admin",
        "Flask-Login",
        "Flask-Migrate",
        "Flask-SQLAlchemy",
        "Flask-WTF",
        "inflect",
        "networkx",
        "pandas",
        "psycopg2-binary",
        "python-dotenv"
    ],
    zip_safe=False
)
