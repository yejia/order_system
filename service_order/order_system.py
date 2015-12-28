

from datetime import datetime, timedelta
from django.shortcuts import get_object_or_404
from service_order.models import Order_State_Machine, Service_Order as Order, SO_Refund_Sheet as Refund_Sheet, \
   input_actions, SO_Refund_Log as Refund_Log


#service order has no item action

class Order_System: 
     

    @classmethod
    def get_initial(cls):
        return {'order': None, 'role_actions':Order_State_Machine.get_initial_role_actions(),
                   'current_state':Order_State_Machine.get_initial_state(), 'item_list':None} 

    @classmethod
    def goto_next(cls, order_id, role, order_action, **kwargs):
        if order_action:
            #if there is no order yet, and the action is from Buyer 'create order', then create the order
            #TODO: if not order_id, ask the state machine whether to create an order. e.g. make create_order a 
            #method of state machine instead of order
            if not order_id and role == 'B' and order_action == 'create order': 
                order_id = Order.create_order() 
                order =  get_object_or_404(Order, id=order_id)
            else:
                order =  get_object_or_404(Order, id=order_id)
                order.goto_next(role, order_action, **kwargs)  
                      
            

        #TODO:move this to view. Just return order_id here.
        return {'order': order, 'input_actions':input_actions}        


    @classmethod
    def get_status(cls, order_id):
        order = get_object_or_404(Order, id=order_id)
        
        return {'order': order, 'input_actions':input_actions}   


    #TODO:only keep on create_order, also it is better to pass default values here
    @classmethod
    def create_order(cls, order_id=None, buyer_id='877673433', item_list=['56899023', '83768385'], **kwargs):
        return Order.create_order(order_id, buyer_id, item_list, **kwargs)


    

  
                    








    
          
            