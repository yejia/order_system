Easy Order System for ECommerce
================

### This order system is implemented with state machine based workflow. The workflow controls the states of the order and the items in the order, what actions can be applied by what roles when the order is in a certain action, the next state and available roles and actions. Two type of orders, product order and service order, are implemented as examples. This order system can be used as middleware in various order centers in ecommerce platforms. For details, please read the [wiki](https://github.com/yejia/order_system/wiki). 

### For a quick try, here is the live demo:

[product order demo](http://easy_order.yugonger.com:9999/demo/)

[service order demo](http://easy_order.yugonger.com:9999/service_order_demo/)

[task monitoring](http://easy_order.yugonger.com:9998/tasks?limit=100)

### To run it locally

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

6. initialize database 

		#login into your mysql db shell, then run the following 
		create database order_system character set = 'utf8';
		use order_system;
		#run the following django's command, it creates the tables and loads database data from your fixtures (json files in fixtures folder)
		python manage.py migrate	

7. set up local settings

		copy order_system/env_settings.tmpl content into order_system/env_settings.py, and change the values to your local environment settings

8. run tests

		python manage.py test 

9. install [rabbitmq-server](http://www.rabbitmq.com/install-debian.html "install rabbitmq-server on ubuntu")

10. start [celery](http://www.celeryproject.org/ "celery")
  
                
		./start_celery.sh 

11. start easy_order server

		./runserver.sh 
            
12. start [flower](https://github.com/mher/flower "flower"), web monitoring tool for celery
                
		celery flower --port=9998 #default port is 5555


13. view the demo, for product order demo:
                
		http://localhost:8000/demo/


14. and for service order demo:
                
		http://localhost:8000/service_order_demo/


15. you can try the following in your django shell (run: python manage.py shell) to play with objects in the easy order system:

	
	    >>> o_id = Order_System.create_order()
	    >>> o = get_object_or_404(Product_Order, id=o_id)
	    >>> int(o.id) == int(o_id)
	    True
	    >>> o.get_role_actions()
	    {u'P': [u'no payment', u'payment successful'], u'S': [u'change shipping fee'], u'B': [u'cancel order', u'make payment']}
	    >>> o.state
	    u'WP'
	    >>> o.get_role_actions()
	    {u'P': [u'no payment', u'payment successful'], u'S': [u'change shipping fee'], u'B': [u'cancel order', u'make payment']}
	    >>> o.goto_next('B', 'make payement')
	    (None, None)
	    >>> o.state
	    u'WP'
	    >>> o.get_role_actions()
	    {u'P': [u'no payment', u'payment successful'], u'S': [u'change shipping fee'], u'B': [u'cancel order', u'make payment']}
	    >>> o.goto_next('P', 'payment successful')
	    (u'FP', u'order_paid')
	    >>> o.state
	    u'FP'
	    >>> o.get_role_actions()
	    {u'S': [u'ship the order', u'change shipping addr']}
	    >>> o.goto_next('s', 'ship the order') #role doesn't distinguish btw upper case or lower case
	    (u'FS', u'order_shipped')
	    >>> o.state
	    u'FS'
	    >>> o.get_role_actions()
	    {u'P': [u'auto ack reception of order'], u'S': [], u'B': [u'confirm reception of order']}
	    >>> o.goto_next('B', 'confirm')
	    (None, None)
	    >>> o.state
	    u'FS'
	    >>> o.goto_next('B', 'confirm reception of order')
	    (u'ST', u'transaction_successful')
	    >>> o.state
	    u'ST'
	    >>> o.get_role_actions()
	    {u'P': [u'no refund request']}
	    >>> 
	    >>> o.goto_next('P', 'no refund request')
	    (u'WA', u'')
	    >>> o.state
	    u'WA'
	    >>> 
	    >>> o.get_role_actions()
	    {u'P': [u'finished accounting']}
	    >>> o.goto_next('U', 'finished accounting') #unknown role have no effect
	    (None, None)
	    >>> o.state
	    u'WA'
	    >>> 
	    >>> o.goto_next('P', 'finished accounting')
	    (u'FA', u'')
	    >>> o.state
	    u'FA'
	    >>> o.get_role_actions()
	    {}

		 
16. for more example usages, you can view the doctest in the source code.


	




