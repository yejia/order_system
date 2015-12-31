"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _

from product_order.models import Product_Order
from product_order.order_system import Order_System


class Product_Order_Test(TestCase):
    """
    Below is doctest for Order_System, which is moved here since we haven't found a way to run it automatically through
    python manage.py test if it is put there. (TODO:) 



    >>> o_id = Order_System.create_order()
    >>> o = get_object_or_404(Product_Order, id=o_id)
    >>> int(o.id) == int(o_id)
    True
    >>> o.shipping_fee
    >>> 
    >>> o.get_role_actions()
    {u'P': [u'no payment', u'payment successful'], u'S': [u'change shipping fee'], u'B': [u'cancel order', u'make payment']}
    >>> o.state
    u'WP'
    >>> o.buyer_can_extend_shipping_ack
    False
    >>> o.auto_confirm_reception_ended
    False
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

    >>> #test interacting with each specific object directly

    >>> #test interacting through Order_System

    """


    fixtures = ['product_order_init.json']

    def setUp(self):
        pass


    def test_state_machine(self):
        initials = Order_System.get_initial()
        self.assertDictEqual(initials, {'role_actions': {u'B': [u'create order']}, 'current_state': '', 'order': None})


    def test_work_flow1(self):
        """create product order -> cancel this order
        """
        o_id = Order_System.create_order()
        o = get_object_or_404(Product_Order, id=o_id)  
        status = o.state
        self.assertEqual(status,  u'WP')                     
        status = o.get_state_display()
        self.assertEqual(status, u'Waiting for Payment') 

        o.goto_next(u'B', u'cancel order')                   
        status = o.state
        self.assertEqual(status, u'CT')                      
        actions =  o.get_role_actions()
        self.assertDictEqual(actions, {})
        status = o.get_state_display()    
        self.assertEqual(status, u'Closed Transatcion')


    def test_work_flow2(self):  
        """create product order -> pay the order -> provider ships the product -> auto confirm       
        """
        o_id = Order_System.create_order()
        o = get_object_or_404(Product_Order, id=o_id) 
        status = o.state
        self.assertEqual(status,  u'WP')                    
        status = o.get_state_display()
        self.assertEqual(status, u'Waiting for Payment') 

        o.goto_next(u'p', u'payment successful')            
        status = o.state
        self.assertEqual(status,  u'FP')  

        o.goto_next(u'S',u'ship the order')                 
        status = o.state
        self.assertEqual(status,  u'FS')

        o.goto_next(u'P',u'auto ack reception of order')    
        status = o.state
        self.assertEqual(status,  u'ST')

        o.goto_next(u'P',u'no refund request')              
        status = o.state
        self.assertEqual(status,  u'WA')

        o.goto_next(u'P',u'finished accounting')            
        status = o.state
        self.assertEqual(status,  u'FA')



    def test_work_flow3(self): 
        """create product order -> pay the order -> provider ships the product -> buyer confirms
        """
        o_id = Order_System.create_order()
        o = get_object_or_404(Product_Order, id=o_id)  
        status = o.state
        self.assertEqual(status,  u'WP')                     
        status = o.get_state_display()
        self.assertEqual(status, u'Waiting for Payment')     

        o.goto_next(u'p', u'payment successful')             
        status = o.state
        self.assertEqual(status,  u'FP')  

        o.goto_next(u'S',u'ship the order')                  
        status = o.state
        self.assertEqual(status,  u'FS')

        o.goto_next(u'B',u'confirm reception of order')     
        status = o.state
        self.assertEqual(status,  u'ST')

        o.goto_next(u'P',u'no refund request')              
        status = o.state
        self.assertEqual(status,  u'WA')

        o.goto_next(u'P',u'finished accounting')            
        status = o.state
        self.assertEqual(status,  u'FA')




    def test_work_flow4(self):  
        """refund before shipping the product: create product order -> pay -> request refund -> cancel refund -> provider ships the product -> buyer confirms

        """
        pass
        

    def test_work_flow4(self):  
        """refund before shipping the product: create product order -> pay -> request refund -> provider agrees to refund 

        """
        pass
        

    def test_work_flow5(self):  
        """refund before shipping the product: create product order -> pay -> request refund -> provider ships the product (no refund) -buyer confirms

        """
        pass      


    def test_work_flow6(self):  
        """refund before shipping products(more than two product items): create product order -> pay -> refund one item -> provider agrees to refund
        -> ship the product - buyer confirms
        """
        pass       


    def test_work_flow7(self):  
        """only refund payment: create product order -> pay -> ship the product -> request refund -> cancel refund -> provider ships the product -> buyer confirms

        """
        pass 
    

    def test_work_flow8(self):  
        """only refund payment: create product order -> pay -> ship product -> request refund -> agree to refund 

        """
        pass 
    

    def test_work_flow9(self):  
        """only refund payment (more than one product items) : create product order -> pay -> ship product -> request refund -> agree to refund 
        -> confirm (the other product)
        """
        pass 


    def test_work_flow10(self):  
        """only refund charge : create product order - pay - send product - refund - disagree - cancel refund

        """
        pass 


            



class PO_With_Scheduled_Tasks_Test(TestCase):

    def setUp(self):
        pass
        


    
    def test_work_flow1(self):  
        """

        """
        pass



class State_Machine_Test(TestCase):
    pass
