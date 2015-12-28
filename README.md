Easy Order System for ECommerce
================

-----------------------------------------------------------
## environment setup

1. install [Git](http://en.wikipedia.org/wiki/Git_%28software%29 "Git")， MySQL, virtualenv, pip 

2. set up your project directory and activate your virtualenv

		mkdir /path/to/yourproject
		cd /path/to/yourproject
		virtualenv your_venv_name
		cd your_venv_name 
		source bin/activate

3. login your github account, and fork this project to your repository

4. get the source code

		git clone https://your_github_account@github.com/your_github_account/easy_order.git

5. install dependency package

		pip install -r pip_requirements.txt 

6. initialize database, login into your db shell

		create database order_system character set = 'utf8';
		use order_system;
		#run django's syncdb	

7. set up local settings

		copy order_system/env_settings.tmpl content into order_system/env_settings.py, and change the values to your local environment settings

8. run tests (TODO:)

		python rununittests.py 

9. install [rabbitmq-server](http://www.rabbitmq.com/install-debian.html "install rabbitmq-server on ubuntu")

10. start [celery](http://www.celeryproject.org/ "celery")
  
                
		./start_celery.sh 

11. start easy_order server

		./runserver.sh 
            
12. start [flower](https://github.com/mher/flower "flower"), web monitoring tool for celery
                
		celery flower --port=9998 #default port is 5555


13. view the demo, for product order demo:
                
		http://localhost:8080/demo/


13. and for service order demo:
                
		http://localhost:8080/service_order_demo/




