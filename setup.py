from setuptools import setup, find_packages

setup(
    name='order_system',
    version='1.0',
    long_description=__doc__,
    author='Yejia',
    author_email='',
    url='http://',    
    packages=find_packages(exclude=[]),
    include_package_data=True,
    #package_dir={'.':'data'},
    #package_data={'data':['static', 'templates', 'locale']},
    #data_files=[('data',['config.py', 'manage.py', 'runserver.sh', 'pip_requirements.txt', 'start_celery.sh'])],
    zip_safe=False,
    install_requires=[
        'Django==1.8.1',
        #'South>=0.8.4',
        'celery>=3.1.8',
        'flower>=0.6.0',
        'MySQL-python>=1.2.5',
        #'django-debug-toolbar',               
        #'werkzeug', #this order_system will get db from its host's settings file. So don't need to get from env variable       
        ],
    dependency_links = []   
)
