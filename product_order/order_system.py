
import pdb

from datetime import datetime, timedelta
from django.shortcuts import get_object_or_404
from product_order.models import Order_State_Machine, Product_Order as Order, admin_actions, input_actions, Refund_Only_State_Machine, \
    Refund_With_Return_State_Machine, PO_Refund_Log as Refund_Log, PO_Refund_Sheet as Refund_Sheet

#TODO: change to Order_Sys
class Order_System:  
    """ Order_System is the interface for the whole order system, including the objects that are closely related to the system'state
    state, in the case of product order system, order, order_item, refund_sheet (including refund_log). The Order_System.get_status()
    will give you the current state of the order system.  The Order_System.goto_next() provides the mechanism for the operators to move
    the system to the next state. It is also ok to use Order directly, if you just want to see how the order's state change. But in that 
    case, you might not see the state change of other objects (such as order_item and refund_sheet). (Design might be changed here to use
        order's state change to affect the whole system objects' state change (TODO:). So as the doctest shown below, you can view and 
        change order's state directly. Or you can use Order_System to view and change the whole system's state.
        )

    The Order_System is for one order, so there is no query method provided to get orders using Order_System. Such a query should be provided
    by the system (order center) that uses this Order_System. 


    


    """  

    @classmethod
    def get_initial(cls):
        return {'order': None, 'role_actions':Order_State_Machine.get_initial_role_actions(),
                   'current_state':Order_State_Machine.get_initial_state()} 

    @classmethod
    def goto_next(cls, order_id, role, order_action, item_action, item_id, **kwargs):
        if order_action:
            #if there is no order yet, and the action is from Buyer 'create order', then create the order
            if not order_id and role == 'B' and order_action == 'create order': 
                #TODO: remove below?
                order_id = Order.create_order() 
                order =  get_object_or_404(Order, id=order_id)
            else:
                order =  get_object_or_404(Order, id=order_id)
                order.goto_next(role, order_action)  
        if item_action:
            #if item_action, this will only affect the item that is acted on
            order =  get_object_or_404(Order, id=order_id)            
            ocr = order.order_item_rel_set.get(item_id=item_id)
            ocr.goto_next(role, item_action)

            if not Refund_Sheet.objects.filter(item_id=ocr.id).exists():#not ocr.refund_sheet:
                if ocr.state == 'WR':
                    rs_type = ''
                    if item_action == 'request refund':
                        rs_type = 'RO'
                    if item_action == 'request refund with return':
                        rs_type = 'RR'    
                    rs = Refund_Sheet.create_refund_sheet(ocr.id, rs_type) 
                    rl = Refund_Log(refund_sheet_id=rs.id, refund_type=rs.refund_type, action=item_action, 
                        reason=kwargs.get('reason',''), memo=kwargs.get('memo', ''), operator=kwargs.get('operator',''),
                        refund_fee=kwargs.get('refund_fee', None))
                    rl.save()                    
            else:
                rs = get_object_or_404(Refund_Sheet, item_id=ocr.id)
                next_state, post_action = rs.goto_next(role, item_action)  
                #TODO:make below into post_action
                if item_action == "ship back":
                    rs.express_company = kwargs.get("express_company", "")
                    rs.express_tracking_no = kwargs.get("express_tracking_no", "")
                    rs.save()
                if item_action == "change refund request":
                    rs_type = kwargs.get('refund_type', '') 
                    if rs_type: 
                        rs.refund_type = rs_type   
                        rs.save()
                if next_state:
                    rl = Refund_Log(refund_sheet_id=rs.id, refund_type=kwargs.get('refund_type', ''), action=item_action, 
                            reason=kwargs.get('reason', ''), memo=kwargs.get('memo', ''), operator=kwargs.get('operator', ''),
                            refund_fee=kwargs.get('refund_fee', None))
                    rl.save()
                
      
        return {'order': order, 'admin_actions':admin_actions, 'input_actions':input_actions}        


    @classmethod
    def get_status(cls, order_id):
        order = get_object_or_404(Order, id=order_id)        
        return {'order': order, 'admin_actions':admin_actions, 'input_actions':input_actions}  


    #TODO:only keep on create_order, also it is better to pass default values here
    @classmethod
    def create_order(cls, order_id=None, buyer_id='877673433', item_list=['56899023', '83768385'],  **kwargs):
        return Order.create_order(order_id, buyer_id, item_list, **kwargs)


    




    
          
            