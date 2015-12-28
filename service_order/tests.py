"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.shortcuts import get_object_or_404

from service_order.models import Service_Order
from service_order.order_system import Order_System



class Service_Order_Test(TestCase):
    """
    Below is doctest for Order_System, which is moved here since we haven't found a way to run it automatically through
    python manage.py test if it is put there. (TODO:) 

    >>> o_id = Order_System.create_order() #pass nothing, the system is still able to create an order,\ 
    >>> #but no attendance code (since no service time)
    >>> from order.models import Order
    >>> o = get_object_or_404(Order, id=o_id)
    >>> int(o.id) == int(o_id)
    True
    >>> o.service_order.get_role_actions()
    {u'P': [u'no payment', u'payment successful'], u'B': [u'cancel order', u'make payment']}
    >>> o.state
    u'WP'
    >>> o.service_order.state
    u'WP'
    >>> o.service_order.get_role_actions()
    {u'P': [u'no payment', u'payment successful'], u'B': [u'cancel order', u'make payment']}
    >>> 
    >>> from service_order.models import Service_Order
    >>> so = get_object_or_404(Service_Order, id=o_id)
    >>> int(so.id) == int(o_id)
    True
    >>> so.get_role_actions()
    {u'P': [u'no payment', u'payment successful'], u'B': [u'cancel order', u'make payment']}
    >>> so.goto_next('B', 'make payement')
    (None, None)
    >>> so.state
    u'WP'
    >>> so.goto_next('P', 'payment successful')
    (u'FP', u'payment_successful')
    >>> so.state
    u'FP'
    >>> so.get_role_actions()
    {u'P': [u'attendance code expired', u'finished refund', u'all used'], u'B': [u'request refund']}
    >>> so.goto_next('p', 'attendance code expired')
    (u'FP', u'attendance_code_expired')
    >>> so.state
    u'FP'
    >>> so.get_role_actions()
    {u'P': [u'attendance code expired', u'finished refund', u'all used'], u'B': []}
    >>> so.goto_next('P', 'finished')
    (None, None)
    >>> so.state
    u'FP'
    >>> so.goto_next('P', 'finished refund')
    (u'FP', u'refund_sheet_finished')
    >>> so.state
    u'CT'
    >>> so.get_role_actions()
    {}
    >>> so.goto_next('P', u'finished refund')
    (None, None)
    >>> so.state
    u'CT'    
    >>> item = so.get_items()[0]
    >>> item
    <Order_Item_Rel: Order_Item_Rel object>
    >>> item.refund_sheet
    <SO_Refund_Sheet: SO_Refund_Sheet object>
    >>> rs = item.refund_sheet
    >>> code_list = rs.item.attendance_code_set.all()
    >>> code_list #since when creating the order, there is no service_times passed for the item, so there is no attend_code generated
    []
    >>>
    >>>
    >>>
    >>> #####test cases when service_times is passed including
    >>> #mobile is passed with the order, however, if you want to put it in the item as well, it is fine too. But for the sms sending to work, it needs to be in the order
    >>> o_id2 = Order_System.create_order(**{'items_json': '[{"service_times": 5, "price": 100.0, "commodity_id": "793669834", "name": "yoga meditation"}]', "buyer_id": "6769834", "mobile":"13567783291"})
    >>> so2 = get_object_or_404(Service_Order, id=o_id2)
    >>> so2.goto_next('P', 'payment successful')
    (u'FP', u'payment_successful')
    >>> so2.goto_next('P', 'attendance code expired')
    (u'FP', u'attendance_code_expired')
    >>> so2.goto_next('P', 'finished refund')
    (u'FP', u'refund_sheet_finished')
    >>> so2.state
    u'CT'
    >>> so2.get_role_actions()
    {}
    >>>
    >>>
    >>>
    >>> #####test interacting with each specific object directly
    >>> item1 = so2.get_items()[0]
    >>> item1
    <Order_Item_Rel: Order_Item_Rel object>
    >>> item1.item_id
    u'793669834'
    >>> item1.get_item().commodity_id
    u'793669834'
    >>> item1.get_item().name
    u'yoga meditation'
    >>> so2.buyer_id
    u'6769834'
    >>> rs = item1.refund_sheet
    >>> rs.state
    u'PFR'
    >>> rs.refund_type
    u'ER'
    >>> rs.item
    <Order_Item_Rel: Order_Item_Rel object>
    >>> rs.item.item_id
    u'793669834'
    >>> rs.item.get_item().commodity_id
    u'793669834'
    >>> rls = rs.refund_log_set.all()
    >>> rls
    [<SO_Refund_Log: SO_Refund_Log object>, <SO_Refund_Log: SO_Refund_Log object>, <SO_Refund_Log: SO_Refund_Log object>]
    >>> rls[0].action
    u'attendance code expired'
    >>> rls[0].memo
    u''
    >>> rls[0].operator
    u'Platform'
    >>> rls[0].refund_fee
    >>> 
    >>> codes = item1.attendance_code_set.all()    
    >>> codes[0].state
    u'Un'
    >>> codes[1].state
    u'Un'
    >>> len(codes)
    5

    >>>
    >>>
    >>>
    >>>
    >>> #####test interacting through Order_System       
    >>> so3_id = Order_System.create_order(**{'items_json': '[{"service_times": 5, "price": 100.0, "commodity_id": "686932423", "name": "yoga fighting"}]', "buyer_id": "6769834"})
    >>> len(so3_id) > 0
    True
    >>> result = Order_System.get_status(so3_id)
    >>> o3 = result.get('order')
    >>> o3.state
    u'WP'
    >>> o3.get_role_actions()
    {u'P': [u'no payment', u'payment successful'], u'B': [u'cancel order', u'make payment']}
    >>>     
    >>> result = Order_System.goto_next(o3.id, 'P', 'payment successful')
    >>> result.get('input_actions')
    ['payment successful', 'finished refund', 'used service finished refund', 'unused service finished refund', 'all used', 'attendance code expired']
    >>> 
    >>> o3 = result.get('order')
    >>> o3.state
    u'FP'
    >>> 
    >>> o3.get_role_actions()
    {u'P': [u'attendance code expired', u'finished refund', u'all used'], u'B': [u'request refund']}
    >>> 
    >>> item0 = o3.get_items()[0]
    >>> item0.item_id
    u'686932423'
    >>> item0.get_item().name
    u'yoga fighting'
    >>> codes = item0.attendance_code_set.all()
    >>> len(codes)
    5
    >>> codes[0].state
    u'Un'
    >>> 
    >>> item0.validate(codes[0].code)
    'Validated Successfully!'
    >>> codes[0].state
    u'Un'
    >>> 
    >>> codes2 = item0.attendance_code_set.all()
    >>> codes2[0].state
    u'Us'
    >>> codes2[1].state
    u'Un'
    >>> result = Order_System.get_status(o3.id)
    >>> result.get('input_actions')
    ['payment successful', 'finished refund', 'used service finished refund', 'unused service finished refund', 'all used', 'attendance code expired']
    >>> o4 = result.get('order')
    >>> o4.get_role_actions()
    {u'P': [u'attendance code expired', u'finished refund', u'all used'], u'B': [u'request refund']}
    >>> result = Order_System.goto_next(o4.id, 'P', 'attendance code expired')
    >>> o5 = result.get('order')
    >>> o5.state
    u'FP'
    >>> o5.get_role_actions()
    {u'P': [u'attendance code expired', u'finished refund', u'all used'], u'B': []}
    >>> 
    >>> item0 = o5.get_items()[0]
    >>> item0.refund_sheet.state
    u'PPR'
    >>> item0.refund_sheet.refund_log_set.all()[0].action
    u'attendance code expired'
    >>> len(item0.refund_sheet.refund_log_set.all())
    1
    >>> result = Order_System.goto_next(o5.id, 'P', 'finished refund')    
    >>> 
    >>> o6 = result.get('order')
    >>> o6.state
    u'ST'
    >>> item0 = o6.get_items()[0]
    >>> codes3 = item0.attendance_code_set.all()
    >>> len(codes3)
    5
    >>> codes3[0].state
    u'Us'
    >>> item0.validate(codes3[0].code)
    'Not a valid order!'
    >>> item0.validate(codes3[1].code)
    'Not a valid order!'
    >>> item0.validate(codes3[2].code)
    'Not a valid order!'
    >>> item0.refund_sheet.state
    u'PFR'
    >>> rls = item0.refund_sheet.refund_log_set.all()
    >>> len(rls)
    3
    >>> rls[0].action
    u'attendance code expired'
    >>> rls[1].action
    u'used service finished refund'
    >>> rls[2].action
    u'finished refund'
    >>> 
   


    """  

    def setUp(self):
        pass

    def test_pass_snapshot_by_json_text(self):
        pass

    def test_pass_snapshot_by_params(self):
        pass

    def test_work_flow1(self):
        """no attendance code used, then expired

        """
        o_id2 = Order_System.create_order(
            **{'items_json': '[{"sku_service_times": 5, "price": 100.0, "commodity_id": "793669834", "name": "yoga meditation"}]', "buyer_id": "6769834"})

        so2 = get_object_or_404(Service_Order, id=o_id2)
        current_state_post_action = so2.goto_next('P', 'payment successful')
        self.assertTupleEqual(current_state_post_action,
                              (u'FP', u'payment_successful'))
        current_state_post_action = so2.goto_next(
            'P', 'attendance code expired')
        self.assertTupleEqual(current_state_post_action,
                              (u'FP', u'attendance_code_expired'))
        current_state_post_action = so2.goto_next('P', 'finished refund')
        self.assertTupleEqual(current_state_post_action,
                              (u'FP', u'refund_sheet_finished'))
        current_state = so2.state
        self.assertEqual(current_state, u'CT')
        current_state_post_action = so2.get_role_actions()
        self.assertDictEqual(current_state_post_action, {})
        # clean created order
        #Service_Order.objects.delete()


    def test_work_flow2(self):
        """some attendance code used, then expired

        """
        pass

    def test_work_flow3(self):
        """some attendance code used, then request refund

        """
        pass

    def test_work_flow4(self):
        """no attendance code used, then request refund

        """
        pass

    def test_work_flow5(self):
        """all used before expiration and requesting refund

        """
        pass


    def test_work_flow6(self):
        """ create order, then cancel it

        """
        o_id = Order_System.create_order()
        so = get_object_or_404(Service_Order, id=o_id)
        current_state = so.service_order.state
        self.assertEqual(current_state, u'WP') 
        next_actions = so.service_order.get_role_actions()
        self.assertDictEqual(next_actions, {u'P': [u'no payment', u'payment successful'], u'B': [u'cancel order', u'make payment']}) 
        current_state_post_action = so.goto_next('B', u'cancel order') 
        self.assertTupleEqual(current_state_post_action,(u'CT', u'')) 


    def test_attendance_code(self):
        pass


    def test_sending_sms(self):
        """test if sms got sent after payment successful (without really sending sms).
        Just test if the sms content is constructed correctly
        """
        pass




class SO_With_Scheduled_Tasks_Test(TestCase):

    def setUp(self):
        pass

    def test_work_flow1(self):
        """no attendance code used, then expired

        """
        pass


class State_Machine_Test(TestCase):
    pass
