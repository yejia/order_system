#-*- coding: utf-8 -*

import pdb
from decimal import Decimal
import sys, copy, json, random

from django.db import models
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from order.models import Order, State_Machine, Refund_Sheet, Refund_Log, OPERATOR_ROLE_CHOICES, REFUND_STATE_CHOICES,\
     Refund_State_Machine, state_machine_match_regex, save_snapshot, ORDER_STATE_CHOICES, get_order_id, Work_Flow, remove_no_display_actions as rm_no_display_actions
import snapshot

#TODO: hold the auto ack of shipping if the buyer requested refund of all items in the order
#TODO: after requesting refund, the maximum wait time for the response
#TODO: record of operation. For example, for refund sheet, the reasons for each operation
#TODO: hold the 7 days refund time check if refund is requested, resume it after that refund is finished/closed. Might implement this way: for 
#each refund time check task, put the order id, the start time and time left into db, when need to hold, just mark the old one as void, when resume, just update it.
#when the task executes, it needs to check if it is voided

#If some items in the order is requested refund and the seller agreed refund (before shipping), if the item is the only item in the order (or all items are agreed refund),
# if the item's refund is still in processing (waiting for the success input from the refund system), then there shall not be "ship the order" action available for the seller.
# if only some items in the order is in such a state, it can still be shipped (better not to allow, just hold the whole order). But for the item that is agreed refund, it should still be in "Waiting for Refund" state. Suggested
#way of implementing this: add another state: "Hold Shipping"--"HS" to the order. So when in this state, there is no action for the seller. But we don't display this state
#on the page. (Currently this approach is used.) Another way should be holding the order so no other action can be done on the order to change its state except the success input from refund system


#From PRD: buyer delete closed order from his order center (still present in seller order center and platform admin order center). This should be implemented by the external
# order center that uses this order system module.

#TODO:for closed refund, be able to display the type of "closed"

#TODO: add shipping back address after the seller agreed refund (for "refund with return" item)

#TODO:provide a mechanism to sort actions in role_actions, so when it get displayed for a role
#on the webpage, certain action can appear before others. Might be better to implement this in the view

#TODO:implement machanism to match '*', so when if an action can be applied to all states, just put '*'. 


#From PRD: when change refund request, the buyer can change the amount of refund and type of refund


#TODO:PI(Platform Input), PS(Platform Scheduled), PA(Platform Admin)


#four types of platform actions: 
#1. timed event, such as no response within 72 hours; 
#2. triggered event, such as order stated changed to 'FD', trigger item state change
#3. input from other system, such as payment successful signal from payment system;
#4. manual operations from customer service people

#only manual operations will show in customer service page. 
#For demo, triggered event by order state change will not be displayed at the front

#From PRD: for confirming reception of order, on the front pages, the buyer needs to pick which item to confirm. If the buyer has requested refund of some items,
#we just treat "confirming reception of an item" as "cancel the refund request" action 






#TODO:think of storing the info below in the db
no_display_actions = ['order state changed to FS', 'order state changed to FP', 'refund sheet closed', 
             'all items refunded', 'all refund closed or finished', 'processing refund', 'item finished refund', 'item closed refund',
             'no more open refund', 'all items done with refund' ]
#some actions, although available to a role, its displaying or not is dependent on some other factors, such as time.
#For example, 7 days after shipping, the order's auto confirm days can be extended to 3 more days. TODO: need to retrieve previously scheduled task and modify it
#TODO: move these into db as well
platform_controlled_actions = [('extend auto ack shipping days', 'enable_auto_ack_extension')] #(action, check_func)

#For now, admin actions are a type of platform actions. We list it here 
admin_actions = ['reject refund', 'force refund']
#input from other systems, such as payment system, accounting system
input_actions = ['payment successful', 'finished accounting', 'finished refund']






class Order_State_Machine(State_Machine):    
    pass
 




ORDER_ITEM_STATE_CHOICES = (
        ('FP', _('Finished Payment')),('WR', _('Waiting for Refund')),('FR', _('Finished Refund')), ('CR', _('Closed Refund'))
    )

#TODO:make this into another type of state_machine, or make the orginal State_Machine able to accept some external entities' states as well
class Order_Item_State_Machine(State_Machine):      
    
    order_current_state = models.CharField(max_length=128, choices=ORDER_STATE_CHOICES) 
    

    @classmethod
    def get_initial_state(cls):
        return 'FP'


    @classmethod
    def get_next(cls, role, action, order_c_state, c_state):
        try:
            order_state_to_match = state_machine_match_regex(order_c_state)
            osm = cls.objects.get(operator_role=role, action=action, 
                order_current_state__regex=order_state_to_match, current_state=c_state)                
            return osm.next_state, osm.post_action
        except MultipleObjectsReturned, mor:
            #TODO:make a custom exception
            raise Exception('Multiple states returned!')  
        except Order_Item_State_Machine.DoesNotExist, dne:
            #it is quite possible that the order action won't affect the items' action. So, just pass
            return None, None 


    @classmethod
    def get_role_actions(cls, order_c_state, c_state):
        '''Get which roles can do what actions when the order and item are in certain states
        '''   
        order_state_to_match = state_machine_match_regex(order_c_state)
        osms = cls.objects.filter(order_current_state__regex=order_state_to_match, current_state=c_state).values_list('operator_role','action')   
        roles = list(set([osm[0] for osm in osms]))        
        role_actions = {}
        for r in roles:
            role_actions[r] = []
            for s in osms:
                if s[0]==r:
                    if s[1] not in role_actions[r]:
                        role_actions[r].append(s[1])
        return role_actions        



# REFUND_WITH_RETURN_STATE_CHOICES = (
#         ('WSR', _('Waiting For Seller Response')),('PPR', _('Platform Processing Refund')), ('SRR', _('Seller Rejected Refund')), 
#         ('CSI', _('Customer Service Involved')), ('WBS', _('Waiting For Buyer Shipping Back')), 
#         ('PFR', _('Platform Finished Refund')), ('CCR', _('Clustomer Closed Refund')), ('PCR', _('Platform Closed Refund')),
#     )






class Refund_Only_State_Machine(Refund_State_Machine):
    pass

class Refund_With_Return_State_Machine(Refund_State_Machine):
    pass
    






#Since the refund processing is quite unique when the order is not shipped, we use a unique state machine for it 
#to keep the rest clean.
#the refund state machine used before shipping, e.g. just for order state 'FP'. Thus quite the same as Refund_State_Machine
class Pre_Shipping_Refund_State_Machine(Refund_State_Machine):
   pass






class Commodity(models.Model):
    commodity_id = models.CharField(max_length=18,  primary_key=True)
    title =  models.CharField(max_length=64)
    desc =  models.CharField(max_length=2000, blank=True)
    seller = models.CharField(max_length=10) #TODO
    #Category
    init_time = models.DateTimeField('time created', auto_now_add=True)
    update_time = models.DateTimeField('time last modified', auto_now=True)


#TODO:move tasks out of here
task_module = __name__





if settings.ORDER_SYSTEM_DEMO == True:    
    PAYMENT_WAITING_PERIOD = SELLER_NO_RESPONSE_WAITING_PERIOD = BUYER_NO_RESPONSE_WAITING_PERIOD= NO_REFUND_REQUST_AFTER_ST_WAITING_PERIOD = AUTO_ACK_SHIPPING_WAITING_PERIOD = settings.INTERVAL_FOR_DEMO
    LENGTH_OF_EXTENDING_AUTO_ACK_SHIPPING = settings.INTERVAL_OF_EXTENDING_FOR_DEMO
    WAIT_FOR_EXTENDING_INTERVAL_WAITING_PERIOD = settings.WAIT_FOR_EXTENDING_INTERVAL_FOR_DEMO
else:
    PAYMENT_WAITING_PERIOD =  settings.PAYMENT_WAITING_PERIOD
    SELLER_NO_RESPONSE_WAITING_PERIOD = settings.SELLER_NO_RESPONSE_WAITING_PERIOD
    BUYER_NO_RESPONSE_WAITING_PERIOD = settings.BUYER_NO_RESPONSE_WAITING_PERIOD
    NO_REFUND_REQUST_AFTER_ST_WAITING_PERIOD = settings.NO_REFUND_REQUST_AFTER_ST_WAITING_PERIOD
    AUTO_ACK_SHIPPING_WAITING_PERIOD = settings.AUTO_ACK_SHIPPING_WAITING_PERIOD  
    WAIT_FOR_EXTENDING_INTERVAL_WAITING_PERIOD = settings.WAIT_FOR_EXTENDING_INTERVAL_WAITING_PERIOD
    LENGTH_OF_EXTENDING_AUTO_ACK_SHIPPING = settings.LENGTH_OF_EXTENDING_AUTO_ACK_SHIPPING






#post actions to take after the state change  

def order_created(order_id):
    #TODO: use interval instead of countdown
    #interval = datetime.utcnow() + timedelta(days=1)
    #no_payment.apply_async((order.order_id,), eta=interval)
    #below is for testing, wait for 60 seconds
    no_payment.apply_async((order_id,), countdown=PAYMENT_WAITING_PERIOD)

import inspect

#TODO:make http request instead, get the deployed host and port
def make_payment(order_id):  
    frm = inspect.stack()[3]
    mod = inspect.getmodule(frm[0])
    print '[%s] %s' % (mod.__name__, order_id)
    getattr(mod, 'make_payment')(order_id)


                       
def order_shipped(order_id):
    order = get_object_or_404(Product_Order, id=order_id)
    for item_rel in order.order_item_rel_set.all():
        item_rel.goto_next('P', 'order state changed to FS')
        if PO_Refund_Sheet.objects.filter(item_id=item_rel.id).exists():
            rs = get_object_or_404(PO_Refund_Sheet, item_id=item_rel.id)
            rs.soft_delete()
    result = auto_ack_shipping.apply_async((order_id,), countdown=AUTO_ACK_SHIPPING_WAITING_PERIOD) #15days
    st = Scheduled_Task(task_id=result.id, order_id=order_id)
    st.save()
    enable_extend_shipping_ack.apply_async((order_id,), countdown=WAIT_FOR_EXTENDING_INTERVAL_WAITING_PERIOD) #7days
    

def buyer_extend_shipping_ack(order_id):
    order = get_object_or_404(Product_Order, id=order_id)
    if Scheduled_Task.objects.filter(order_id=order_id).exists():
        t = Scheduled_Task.objects.get(order_id=order_id)
        t.buyer_extending = True
        t.save()
        order.buyer_can_extend_shipping_ack = False
        order.save()
        

def seller_extend_shipping_ack(order_id):
    order = get_object_or_404(Product_Order, id=order_id)
    if Scheduled_Task.objects.filter(order_id=order_id).exists():
        t = Scheduled_Task.objects.get(order_id=order_id)
        t.seller_extending = True
        t.save()
        order.seller_can_extend_shipping_ack = False
        order.save()



def order_paid(order_id):
    order = get_object_or_404(Product_Order, id=order_id)
    for item_rel in order.order_item_rel_set.all():
        item_rel.goto_next('P', 'order state changed to FP')


def transaction_successful(order_id):
    order = get_object_or_404(Product_Order, id=order_id)    
    if all_items_done_with_refund(order.id):
        order.goto_next('P', 'all items done with refund')
    else:            
        #TODO:only for seller who supports 7 days refund
        no_refund_request_after_st.apply_async((order_id,), countdown=NO_REFUND_REQUST_AFTER_ST_WAITING_PERIOD)  


#TODO:return?
def refund_finished(order_item_rel_id):
    order_item_rel = get_object_or_404(Order_Item_Rel, id=order_item_rel_id)
    order = order_item_rel.order
    if order.state == 'HS':
        order.goto_next('P', 'item finished refund')
    all_items_refunded = True
    for item_rel in order.order_item_rel_set.all():
        if item_rel.state != 'FR':
            all_items_refunded =  False
            break
    if all_items_refunded:
        order.goto_next('P', 'all items refunded')        
        return True
    else:   
        if not have_open_refund(order.id) and (order.auto_confirm_reception_ended == True or order.refund_wait_time_ended == True):
            order.goto_next('P','no more open refund')
            return True
    return False        


#TODO:no_seller_response duplicate with the one below. #critical!#
def seller_no_response(order_item_rel_id):
    #from celery.task.control import inspect
    #i = inspect()
    #tasks = i.scheduled() #TODO:above code cause problem (server hung up) on 251 server
    #print 'scheduled tasks:', tasks 
    #TODO:wait different time when the refund sheet or item is in a different state
    no_seller_response.apply_async((order_item_rel_id,), countdown=SELLER_NO_RESPONSE_WAITING_PERIOD) 
    #hold the 7 day refund counting if the order state is 'ST'
    # order_item_rel = get_object_or_404(Order_Item_Rel, id=order_item_rel_id)
    # order = order_item_rel.order
    # if order.state == 'ST':


#TODO: think of merge this with the above seller_no_response method
def refund_seller_no_response(refund_sheet_id):
    rs = get_object_or_404(PO_Refund_Sheet, id=refund_sheet_id)
    order_item_rel_id = rs.item.id
    no_seller_response.apply_async((order_item_rel_id,), countdown=SELLER_NO_RESPONSE_WAITING_PERIOD) 


def buyer_no_response(refund_sheet_id):
    result = no_buyer_response.apply_async((refund_sheet_id,), countdown=BUYER_NO_RESPONSE_WAITING_PERIOD) 




def refund_sheet_finished(refund_sheet_id):
    rs = get_object_or_404(PO_Refund_Sheet, id=refund_sheet_id)
    rs.item.goto_next('P', 'item finished refund')

#refund sheet state change to affect item
def refund_sheet_closed(refund_sheet_id):
    rs = get_object_or_404(PO_Refund_Sheet, id=refund_sheet_id)
    rs.item.goto_next('P', 'item closed refund')


#item state change to affect order
def refund_closed(order_item_rel_id):
    # rs = get_object_or_404(Refund_Sheet, id=refund_id)
    # rs.item.goto_next('P', 'refund sheet closed')
    order_item_rel = get_object_or_404(Order_Item_Rel, id=order_item_rel_id)
    order = order_item_rel.order    
    changed_state = False
    if all_items_done_with_refund(order.id):
        order.goto_next('P', 'all items done with refund')
        changed_state = True
    if not have_open_refund(order.id) and (order.auto_confirm_reception_ended == True or order.refund_wait_time_ended == True):
        order.goto_next('P','no more open refund')
        changed_state = True    
    return changed_state
        


#def are_all_refunds_closed_or_finished(order_id):
#all items of the order are in either Closed Refund state or Finsihsed Refund state. Thus there will be no more refund request on items of the order    
def all_items_done_with_refund(order_id):    
    order = get_object_or_404(Product_Order, id=order_id)
    all_refunds_closed_or_finished = True
    for item_rel in order.order_item_rel_set.all():        
        if item_rel.state not in ['CR', 'FR']:
            all_refunds_closed_or_finished = False
            break
    return all_refunds_closed_or_finished        


def have_open_refund(order_id):
    order = get_object_or_404(Product_Order, id=order_id)
    having_open_refund = False
    for item_rel in  order.order_item_rel_set.all():
        #if state in 'FP', 'CR', 'FR', there is no need to wait. If state in 'WR', need to wait for the refund to finish
        if item_rel.state == 'WR': 
            having_open_refund = True
            break    
    return  having_open_refund       

#if the order is before shipping ('FP' state), when some item is in the middle of platform processing refund, hold the shipping (e.g. no shipping) 
#TODO:might move this into state machine as well (add order state into refund sheet state machine)
def seller_agree_refund(refund_sheet_id):
    rs = get_object_or_404(PO_Refund_Sheet, id=refund_sheet_id)
    if rs.item.order.state == 'FP':
        rs.item.order.goto_next('P', 'processing refund')
        






#from scheduler.celery import celery
import celery

#TODO:also remove the scheduled task if payed
@celery.task(name="tasks.no_payment")
def no_payment(order_id):
    order = get_object_or_404(Product_Order, id=order_id)
    if order.state == 'WP':
        order.goto_next('P', 'no payment')
        #TODO: think of what to return
        return True
    else:
        return False    
    #TODO:leave a msg in the msg queue as well and use decorator to implement that

@celery.task(name="tasks.auto_ack_shipping")
def auto_ack_shipping(order_id):
    order = get_object_or_404(Product_Order, id=order_id)
    #TODO: no hardcoding. use state.FINISH_SHIPPING
    #print 'current task id is:', auto_ack_shipping.request.id
    #or use order_id to query
    if Scheduled_Task.objects.filter(order_id=order_id).exists():
        t = Scheduled_Task.objects.get(order_id=order_id)
        if t.buyer_extending or t.seller_extending:
            #print 't.buyer_extending:', t.buyer_extending
            #print 't.seller_extending:', t.seller_extending
            auto_ack_shipping.apply_async((order_id,), countdown=LENGTH_OF_EXTENDING_AUTO_ACK_SHIPPING*(int(t.buyer_extending)+int(t.seller_extending))) #countdown should be 3 days here  
            t.buyer_extending = t.seller_extending = False              
            t.save()
            #print 'auto_ack_shipping is scheduled'
            return False
    if order.state == 'FS':  
        if not have_open_refund(order_id):  
            order.goto_next('P', 'auto ack reception of order')
            return True
        else:
            order.auto_confirm_reception_ended = True
            order.save()
            return False    
    
    return False


@celery.task(name="tasks.enable_extend_shipping_ack")
def enable_extend_shipping_ack(order_id):
    order = get_object_or_404(Product_Order, id=order_id)
    if order.state == 'FS':
        order.buyer_can_extend_shipping_ack = True
        order.seller_can_extend_shipping_ack = True
        order.save()
        return True
    else:
        return False    





@celery.task(name="tasks.no_refund_request_after_st")
def no_refund_request_after_st(order_id):
    order = get_object_or_404(Product_Order, id=order_id)
    if order.state == 'ST':       
        if not have_open_refund(order_id):
            order.goto_next('P','no refund request')
            return True 
        else:
            order.refund_wait_time_ended = True
            order.save()
            return False      
    return False


@celery.task(name="tasks.no_seller_response")
def no_seller_response(order_item_rel_id):
    #item_rel = get_object_or_404(Order_Item_Rel, id=order_item_rel_id)
    print 'order_item_rel_id', order_item_rel_id
    rs = get_object_or_404(PO_Refund_Sheet, item_id=order_item_rel_id)
    #no need to check state at all?? That is what the state machine should do  TODO: get rid of all state checking in the task. lyl
    #if rs.state == 'WSR':
    rs.goto_next('P', 'seller no response')
    return True
    # else:
    #     return False    


#TODO: #critical#. need to fix this. It should look at the refund log (pass the refund log id) to see if action has been taken
@celery.task(name="tasks.no_buyer_response")
def no_buyer_response(refund_sheet_id):
    #item_rel = get_object_or_404(Order_Item_Rel, id=order_item_rel_id)
    rs = get_object_or_404(PO_Refund_Sheet, id=refund_sheet_id)
    if rs.state in ['SRR','WBS']:
        rs.goto_next('P', 'buyer no response')
        #rs.item.goto_next('P', 'buyer no response')
        return True
    else:
        return False    



def remove_no_display_actions(role_actions):
    return rm_no_display_actions(role_actions, no_display_actions=no_display_actions)



#TODO: make extending waiting time an addon of the order_system instead of a built in, so that the complexity can be
#separated out

#TODO: add a state machine attribute to bind it to a state machine
class Product_Order(Order): 
    '''
    >>> po_id = Product_Order.create_order()
    >>> po = get_object_or_404(Product_Order,  id=po_id)    
    >>> long(po.id) == long(po_id)
    True
    >>> po.state
    u'WP'


    '''   
 
    shipping_time = models.DateTimeField(null=True, verbose_name='shipping time') #TODO:
    shipping_fee = models.DecimalField(null=True, max_digits=9, decimal_places=2, verbose_name='shipping fee') 
    #shipping_addr = #shipping addr need to use another table, since it contains multiple fields
    #Below is now treated as a special case. If there are many such cases, consider a cleaner implementation.
    #Although they can be treated as states, that would make the state machines sql table difficult to read. So moving them
    #here help keeping the state machine sql table clean.
    #can extend the acknowledge of shipping    
    buyer_can_extend_shipping_ack = models.BooleanField(default=False)  #TODO:make this into an entity state, such as buyer_extended
    seller_can_extend_shipping_ack = models.BooleanField(default=False) 
    auto_confirm_reception_ended =  models.BooleanField(default=False) 
    #7 day refund waiting time after ST
    refund_wait_time_ended = models.BooleanField(default=False) 
    

    

    @classmethod
    def get_state_machine(cls): 
        return Order_State_Machine 


    #TODO:pass item_ids
    #TODO:move this method to parent
    @classmethod
    def create_order(cls, id=None, buyer_id='877673433', item_list=['92399069', '83768385'], **kwargs):
        items_json = kwargs.get('items_json', '')
        if items_json:
            item_list = json.loads(items_json)                    
        if not buyer_id:
            buyer_id = kwargs.get('buyer_id', '877673433')
        if not id:
            id = kwargs.get('id', None)  
        if not id:
            id = get_order_id()        
        o = Product_Order(id=id, buyer_id=buyer_id, state=cls.get_state_machine().get_initial_state()) 
        #pdb.set_trace()
        o.save()
        #pdb.set_trace()
        o.goto_next('B', 'create order')         
       
        for it in item_list:
            if type(it) == str: #not passing snapshot by json
                item_id = it
            else:
                item_id = it['commodity_id']    
            ocr = Order_Item_Rel(order=o, item_id=item_id)
            ocr.save()    
        
        save_snapshot(id, item_list, 
            default_snapshot_class=settings.PRODUCT_COMMODITY_SNAPSHOT_CLASS, **kwargs)

        return o.id  
         


        


    def remove_actions(self, ras):
        remove_no_display_actions(ras)
        #add extend shipping acknowledge action
        if (not self.buyer_can_extend_shipping_ack or self.auto_confirm_reception_ended) and 'extend auto acking reception of order' in ras.get('B',[]):
            ras['B'].remove('extend auto acking reception of order')
        if (not self.seller_can_extend_shipping_ack or self.auto_confirm_reception_ended) and 'extend auto acking reception of order' in ras.get('S',[]):    
            ras['S'].remove('extend auto acking reception of order')
        return ras
       
  
        

    # def finished_payment(self):
    #     self.goto_next('P', 'payment successful')

    def get_order_type(self):
        return 'product' 


    def get_items(self):        
        return self.order_item_rel_set.all()
                







def enable_auto_ack_extension(order_id):
    order = get_object_or_404(Product_Order, id=order_id)
    #TODO:chekc if over 7 days, if so, return True, otherwise return False
    #if order.shipping_time
    return False



#TODO:think of if creating a shared parent class 
class Order_Item_Rel(Work_Flow):
    order = models.ForeignKey(Product_Order)
    #item = models.ForeignKey(Commodity)    
    item_id = models.CharField(max_length=18) 
    #state = models.CharField(max_length=2, choices=ORDER_ITEM_STATE_CHOICES)
    update_time = models.DateTimeField('time last modified', auto_now=True)
    #TODO:init_time

    class Meta:
       unique_together = (("order", "item_id"),)  

    

    @classmethod
    def get_state_machine(cls): 
        return Order_Item_State_Machine 
   

    def get_item(self, item_class=None):
        if not item_class:
            item_class = eval(settings.PRODUCT_COMMODITY_SNAPSHOT_CLASS)
        return item_class.objects.get(order_id=self.order_id, commodity_id=self.item_id)


    #put here for convenience now. TODO:    
    def get_role_actions(self):
        '''Get which roles can do what actions when the order item is in a certain state
        '''      
        item_ras = self.__class__.get_state_machine().get_role_actions(self.order.product_order.state, self.state) 
        remove_no_display_actions(item_ras)
        
        have_rs = PO_Refund_Sheet.objects.filter(item_id=self.id).exists()
        #pdb.set_trace()
        if not have_rs:
            return item_ras 
        else:
            all_refund_actions = list(Refund_Only_State_Machine.objects.values_list('action', flat=True))
            all_refund_actions.extend(list(Refund_With_Return_State_Machine.objects.values_list('action', flat=True)))
            rs_ras = self.refund_sheet.get_role_actions()

            #item_ras = _merge_role_actions(item_ras, )
            ras = {}
            keys = item_ras.keys()
            keys.extend(rs_ras.keys())
            for r in set(keys):
                acs = list(set(item_ras.get(r, [])))
                acs2 = rs_ras.get(r,[])
                if acs:
                    for ac in list(acs): #make a copy of acs
                        #if the action is a refund action (e.g. related to the refund sheet), but it is not in the actions available
                        # to the current refund sheet state, then it should be removed, since refund sheet state is a finer state 
                        if (ac in all_refund_actions) and (ac not in acs2):
                            acs.remove(ac)
                acs.extend(acs2)
                ras[r] = list(set(acs))
            return ras        


    #TODO:user a more universal base State_Machine class to cover both cases so this method can be removed here and 
    #just using that from the parent will be ok
    def goto_next(self, role, item_action):
        next_state, post_action = self.__class__.get_state_machine().get_next(role, 
               item_action, self.order.state, self.state)
        if next_state:
            self.state = next_state
            self.save()
            if post_action:
                #TODO:rule on which id to pass
                getattr(sys.modules[task_module], post_action)(self.id)
        return  next_state, post_action       


    #TODO:test
    def get_distributor_gain(self):
        """ get distributor gain for one item in the order
            item_id: order_item_rel's item_id, e.g. commodity_id
        """
        # order_item_rel = self.get_order_core().product_order.order_item_rel_set.get(item_id=item_id)
        price = self.get_item().price
        purchase_num = self.get_item().purchase_num
        distributor_percentage = self.get_item().distributor_percentage
        #TOOD:should get default value here??
        if not price:
            price = Decimal(0.00)
        if not purchase_num:
            purchase_num = 1
        if not  distributor_percentage:
            distributor_percentage = 0
        #for py2.6 need to use str instead of float in Decimal()
        return price * purchase_num * distributor_percentage / Decimal('100.00')
        # if self.get_item().price is not None and self.get_item().purchase_num is not None and self.get_item().distributor_percentage is not None:
        #     return self.get_item().price * self.get_item().purchase_num * self.get_item().distributor_percentage / 100.0
        # else:
        #     return Decimal('0.00') #TODO:    
            
            
       



REFUND_CHOICES = (
        ('RO', _('Refund Only')),('RR', _('Refund and Return'))
    )





#TODO:think whether to merge this into Order_Item_Rel
#TODO: whether to make a refund_id? or use the auto increase id?
#TODO: add refund amount, refund type, refund reason, refund note 
#TODO: make another Refund_Sheet_Log to log info(snapshot of the refund sheet at the moment) and time at each step, also need the operator and action (
# since the display of the refund sheet will also depend the previous log, for example if it canceled by the customer or by the admin)
class PO_Refund_Sheet(Refund_Sheet):#Commodity Order refund sheet
    '''product order refund sheet
    '''
    #TODO:better name it as item_rel or sth. else
    item = models.OneToOneField(Order_Item_Rel, related_name="refund_sheet")  
    
    refund_type = models.CharField(max_length=2, choices=REFUND_CHOICES)

    express_company = models.CharField(verbose_name='express company', help_text='express company that shipped back the commodity', blank=True, max_length=32)  
    express_tracking_no = models.CharField(max_length=64, blank=True, null=True, verbose_name='express tracking number', help_text=_('express tracking number for tracking the shipping'))




    @classmethod
    def create_refund_sheet(cls, item_rel_id, rs_type='RO'): 
        #TODO: rule to create refund sheet id?        
        r = cls(item_id=item_rel_id, state=Refund_State_Machine.get_initial_state(), refund_type=rs_type)         
        r.save()              
        return r  


    def get_role_actions(self):
        '''Get which roles can do what actions when the refund sheet is in a certain state
        '''     
        if self.item.order.state in ['FP', 'HS']:
             return Pre_Shipping_Refund_State_Machine.get_role_actions(self.state) 
        else: 
        #     return Refund_State_Machine.get_role_actions(self.state)  
            if self.refund_type == 'RO':  
                return Refund_Only_State_Machine.get_role_actions(self.state)         
            else:
                return Refund_With_Return_State_Machine.get_role_actions(self.state)    
        


    def goto_next(self, role, item_action):
        if self.item.order.state in ['FP', 'HS']:
             next_state, post_action = Pre_Shipping_Refund_State_Machine.get_next(role, item_action, self.state)
        else:    
        #     next_state, post_action = Refund_State_Machine.get_next(role, item_action, self.state)
            if self.refund_type == 'RO':            
                next_state, post_action = Refund_Only_State_Machine.get_next(role, item_action, self.state)
            else:
                next_state, post_action = Refund_With_Return_State_Machine.get_next(role, item_action, self.state)    
        if next_state:
            self.state = next_state
            self.save()
            if post_action:
                getattr(sys.modules[task_module], post_action)(self.id)
        return next_state, post_action        
            

    #TODO:override delete
    def soft_delete(self, reason=''):
        drs = Deleted_Refund_Sheet(item_id=self.item.id, state=self.state, update_time=self.update_time, 
            reason=reason)
        drs.save()
        self.delete()


    def get_main_log(self):
        #get the latest request refund log
        rl = self.refund_log_set.filter(action__in=['request refund', 'request refund with return', 'change refund request']).order_by('-init_time')[0]
        return rl


    def get_refund_type(self):
        return 'product'    




class PO_Refund_Log(Refund_Log):
    refund_sheet = models.ForeignKey(PO_Refund_Sheet, related_name="refund_log_set") #TODO:get rid of foreign key reference here
    refund_type = models.CharField(max_length=2, choices=REFUND_CHOICES)
    reason = models.TextField(blank=True)
    



#it seems cleaner to use another table for deleted refund sheet than to use deleted marker
class Deleted_Refund_Sheet(models.Model):
    '''
    '''
    item = models.OneToOneField(Order_Item_Rel) #TODO:no foreign key reference. Just use integer   
    state = models.CharField(max_length=3, choices=REFUND_STATE_CHOICES)
    refund_type = models.CharField(max_length=2, choices=REFUND_CHOICES)
    update_time = models.DateTimeField('time last modified', auto_now=False)
    reason = models.TextField(blank=True)
    deleted_time = models.DateTimeField('time deleted', auto_now_add=True)
    #deleted_by


class Scheduled_Task(models.Model):
    '''
    '''
    task_id = models.CharField(max_length=64,  primary_key=True)
    order_id = models.CharField(max_length=64)
    buyer_extending = models.BooleanField('if buyer extended the ack', default=False)  
    seller_extending = models.BooleanField('if seller extended the ack', default=False)    
    init_time = models.DateTimeField('time created', auto_now_add=True)


#TODO:need to log the trace of an order?
# class Order_Log(models.Model):
#     item = models.OneToOneField(Order_Item_Rel)  
#     note = models.TextField(blank=True)
#     #added_by = 
#     init_time =  models.DateTimeField('time created', auto_now_add=True)




