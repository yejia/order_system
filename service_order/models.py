#-*- coding: utf-8 -*

import pdb
import sys, random, copy, json
from datetime import *

from django.db import models
from django.core.exceptions import MultipleObjectsReturned
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.conf import settings


from order.models import State_Machine, Refund_State_Machine, Refund_Sheet, Refund_Log, Order, \
    state_machine_match_regex, save_snapshot, ORDER_STATE_CHOICES, create_attendance_code, get_order_id, Work_Flow, \
    remove_no_display_actions as rm_no_display_actions

#TODO: for now, import this here and accomplish mobile msg sending here
from sms_api.sms_api import Mobile_Msg_Client
import snapshot


#TODO: separate P and A in state machine
OPERATOR_ROLE_CHOICES = (
        ('P', 'Platform'),('A', 'Admin'),('B', 'Buyer'),('S', 'Seller'),
    )






no_display_actions = ['used service finished refund', 'unused service finished refund']

platform_controlled_actions = [] #(action, check_func)


input_actions = ['payment successful', 'finished refund', 'used service finished refund',
                 'unused service finished refund', 'all used', 'attendance code expired']





#TODO: consider making order.Order_State_Machine abstract, and inherit it here
class Order_State_Machine(State_Machine): 
    pass   
    
   







   

class Service_Refund_State_Machine(Refund_State_Machine):
    
    @classmethod
    def get_initial_state(cls):
        return 'PPR'



if settings.ORDER_SYSTEM_DEMO == True:    
    PAYMENT_WAITING_PERIOD = settings.INTERVAL_FOR_DEMO
else:
    PAYMENT_WAITING_PERIOD = settings.PAYMENT_WAITING_PERIOD




class Service_Commodity(models.Model):
    commodity_id = models.CharField(max_length=18,  primary_key=True)
    title =  models.CharField(max_length=64)
    desc =  models.CharField(max_length=2000, blank=True)
    seller = models.CharField(max_length=10) #TODO
    service_times = models.IntegerField(null=True, verbose_name='number of times for this service')
    sale_num = models.IntegerField(null=True, verbose_name='total number for sales')
    #Category
    init_time = models.DateTimeField('time created', auto_now_add=True)
    update_time = models.DateTimeField('time last modified', auto_now=True)


#TODO:move tasks out of here
#task_module = 'order.tasks'
task_module = __name__
#from .models import Order, Order_Item_Rel, Refund_Sheet



#post actions to take after the state change  

def order_created(order_id):    
    no_payment.apply_async((order_id,), countdown=PAYMENT_WAITING_PERIOD)

import inspect

#TODO:make http request instead, get the deployed host and port
def make_payment(order_id):  
    frm = inspect.stack()[3]
    mod = inspect.getmodule(frm[0])
    print '[%s] %s' % (mod.__name__, order_id)
    getattr(mod, 'make_payment')(order_id)


def payment_successful(order_id, **kwargs):
    order = get_object_or_404(Service_Order, id=order_id) 
    ocr = order.order_item_rel_set.all()[0]    
    #create the attendance code
    code_to_send = ''
    if not ocr.get_item().service_times:#get_sku_value('service_times'):
        return 
    for i in range(int(ocr.get_item().service_times)):#get_sku_value('service_times'))):   
        #pdb.set_trace()   
        #TODO:change the name in  Mobile_Msg_Sender         
        # c = Mobile_Msg_Sender.create_attendance_code(user_id=kwargs.get('buyer_id'), 
        #     product_id=kwargs.get('commodity_id', ''), business_id=kwargs.get('service_supplier_id'))
        #pdb.set_trace()
        c = create_attendance_code(buyer_id=order.buyer_id, 
            commodity_id=ocr.get_item().commodity_id, seller_id=getattr(ocr.get_item(), 'seller_id', '0')) #incase there is no seller_id
        ac = Attendance_Code(item=ocr, state='Un', code=c)
        #pdb.set_trace()
        ac.save()
        #only send the first code
        # if i < 3:
        #     code_to_send.append(c)
        if i == 0:
            code_to_send = c
    mobile = order.mobile#kwargs.get('mobile', '')
    #print    'mobile:', mobile             
    if code_to_send and mobile:
        #TODO:testing
        #need import service here. so maybe not very good design here
        snapshot = ocr.get_item(eval(settings.SERVICE_COMMODITY_SNAPSHOT_CLASS))
        name = snapshot.name
        valid_date_end = snapshot.valid_date_end
        if snapshot.service_times == 1:
            content = settings.SMS_CONTENT_FOR_SINGLE_SERVICE.decode('utf8') % (name, code_to_send, valid_date_end)
        else:
            content = settings.SMS_CONTENT_FOR_MULTIPLE_SERVICE.decode('utf8') % (name, code_to_send, valid_date_end, snapshot.service_times-1)    
        sms_sender = Mobile_Msg_Client()  
        #print 'sending msg to mobile:', mobile, ' with content:', content.encode('utf-8')             
        sms_sender.sendXSms(mobile, content=content.encode('utf-8')) 
        #TODO:record whether sms is sent successfully    






def refund_requested(order_id, **kwargs):
    order = get_object_or_404(Service_Order, id=order_id) 
    ocr = order.order_item_rel_set.all()[0]
    if not SO_Refund_Sheet.objects.filter(item_id=ocr.id).exists():
        rs = SO_Refund_Sheet.create_refund_sheet(ocr.id, rs_type='AR')
        rl = SO_Refund_Log(refund_sheet_id=rs.id, action='request refund', #TODO:remove hard coding here
                        memo=kwargs.get('memo', ''), operator=kwargs.get('operator',''),
                        refund_fee=kwargs.get('refund_fee', None))
        rl.save()


def attendance_code_expired(order_id, **kwargs):
    order = get_object_or_404(Service_Order, id=order_id) 
    ocr = order.order_item_rel_set.all()[0]
    if not SO_Refund_Sheet.objects.filter(item_id=ocr.id).exists():
        rs = SO_Refund_Sheet.create_refund_sheet(ocr.id, rs_type='ER') 
        rl = SO_Refund_Log(refund_sheet_id=rs.id, action='attendance code expired', #TODO:remove hard coding here
                        memo=kwargs.get('memo', ''), operator=kwargs.get('operator','Platform'),
                        refund_fee=kwargs.get('refund_fee', None)) #
        rl.save()      


def refund_sheet_finished(order_id):        
    order = get_object_or_404(Service_Order, id=order_id)
    #for now, one service order has only one refund sheet
    #TODO:below has redundant code, just use the item directly
    
    #pdb.set_trace()
    if order.order_item_rel_set.all()[0].attendance_code_set.filter(state='Us').exists():
        order.goto_next('P', 'used service finished refund')
    else:
        order.goto_next('P', 'unused service finished refund')
    #TODO:use state machine to change the state
    # rs.state = 'PFR'    
    # rs.save()

import celery

@celery.task(name="tasks.service_no_payment")
def no_payment(order_id):
    order = get_object_or_404(Service_Order, id=order_id)
    if order.state == 'WP':
        order.goto_next('P', 'no payment')
        return True
    else:
        return False  


 
#TODO: add a state machine attribute to bind it to a state machine
class Service_Order(Order):
    """
    >>> so_id = Service_Order.create_order(**{'items_json':'[{"service_times": 3, "price": 500.00, "commodity_id": "686932423", "name": "yoga fighting"}]', "buyer_id": "76968984"})    
    >>> so = get_object_or_404(Service_Order, id=so_id)
    >>> so.state
    u'WP'
    >>> so.get_role_actions()
    {u'P': [u'no payment', u'payment successful'], u'B': [u'cancel order', u'make payment']}
    >>> so.goto_next('P', 'payment successful')
    (u'FP', u'payment_successful')
    >>> so.state
    u'FP'
    >>> so.get_role_actions()
    {u'P': [u'attendance code expired', u'finished refund', u'all used'], u'B': [u'request refund']}
    >>> so.goto_next('S', 'request refund') #passed a wrong role!
    (None, None)
    >>> so.goto_next('B', 'request refund')
    (u'FP', u'refund_requested')
    >>> so.state
    u'FP'
    >>> so.get_role_actions()
    {u'P': [u'attendance code expired', u'finished refund', u'all used'], u'B': []}
    >>> item0 = so.order_item_rel_set.all()[0]
    >>> len(so.order_item_rel_set.all())
    1
    >>> item0.item_id
    u'686932423'
    >>> item0.get_item().commodity_id
    u'686932423'
    >>> item0.refund_sheet.state
    u'PPR'
    >>> len(item0.refund_sheet.refund_log_set.all())
    1
    >>> rls = item0.refund_sheet.refund_log_set.all()    
    >>> rls[0].action
    u'request refund'
    >>> 
    >>> so.state
    u'FP'
    >>> so.get_role_actions()
    {u'P': [u'attendance code expired', u'finished refund', u'all used'], u'B': []}
    >>> so.goto_next('P', 'finished refund')    
    (u'FP', u'refund_sheet_finished')
    >>> so.state
    u'CT'
    >>> 
    >>> so.get_role_actions()
    {}




    """
    #below commented out, but its actual choice is different from Product_Order. Not sure this will
    #cause inconvenience in the future. TODO:
    #state = models.CharField(max_length=2, choices=ORDER_STATE_CHOICES) 
    mobile = models.CharField(max_length=18, blank=True, verbose_name='mobiel phone')
    



    @classmethod
    def get_state_machine(cls): 
        return Order_State_Machine
        


    #TODO:pass item_ids
    #TODO:give a default mobile? So if no mobile provided, someone in the company still get the sms and thus know something 
    #needs to be fixed.
    @classmethod
    def create_order(cls, id=None, buyer_id='877673433', item_list=['92399069', '83768385'], mobile='', **kwargs):
        # if not order_id:
        #     order_id = get_order_id()        
        # o = cls(order_id=order_id, buyer_id=buyer_id, state=Order_State_Machine.get_initial_state()) 
        # o.save()
       
        # for item_id in item_list:
        #     ocr = Order_Item_Rel(order=o, item_id=item_id)
        #     ocr.save()    
        # #TODO:change the state directly?
        # o.goto_next('B', 'create order') 

        #TODO:improve below
        items_json = kwargs.get('items_json', '')
        if items_json:
            item_list = json.loads(items_json)
            #pdb.set_trace()
            #item_list = items_dict['items']
            #order_id = item_list.get('order_id', None)
            #TODO:default
            #buyer_id = items_dict.get('buyer_id', '') #TODO:php pass buyer_username?  
            #mobile =  item_list.get('mobile', '')        
        if not buyer_id:
            buyer_id = kwargs.get('buyer_id', '877673433')
        if not mobile:
            mobile = kwargs.get('mobile', '')
        if not id:
            id = kwargs.get('id', None) 
        if not id:
            id = get_order_id()        
        o = Service_Order(id=id, buyer_id=buyer_id, state=cls.get_state_machine().get_initial_state(), mobile=mobile) 
        #pdb.set_trace()
        o.save()        
        for it in item_list:
            
            if type(it) == str: #not passing snapshot by json
                item_id = it
            else:
                item_id = it['commodity_id']  

            ocr = Order_Item_Rel(order=o, item_id=item_id)
            ocr.save()  
        o.goto_next('B', 'create order')         

        #save the snapshot
        save_snapshot(id, item_list, 
            default_snapshot_class=settings.SERVICE_COMMODITY_SNAPSHOT_CLASS, **kwargs)

        return id  
        

    def remove_actions(self, ras):        
        remove_no_display_actions(ras)

        ocr = self.order_item_rel_set.all()[0]
        #TODO:might make "refund requested" as a state
        if SO_Refund_Sheet.objects.filter(item_id=ocr.id).exists():   
            if 'request refund' in ras.get('B', []):
                ras['B'].remove('request refund')

        return ras

        

    def common_post_action(self, role, action, **kwargs):
        #sometimes some post_actions will change the order state further in the system, so refresh the state
        #TODO: make a refresh_state() method in the parent? This way, at least in the console it is easy to get the current real state
        another_o = Service_Order.objects.get(id=self.id)
        self.state = another_o.state        

        ocr = self.order_item_rel_set.all()[0]              
        #when the action is  'request refund' or 'attendance code expired', there are post actions that will
        #create refund_log as well. TODO:simplify design of this
        if action not in ['request refund', 'attendance code expired'] and SO_Refund_Sheet.objects.filter(item_id=ocr.id).exists(): #TODO:                 
            rs = ocr.refund_sheet #get_object_or_404(SO_Refund_Sheet, item_id=ocr.id)
            rs.goto_next(role, action)
            #whether to log ineffective action (actions that didn't change the state) too  TODO:
            rl = SO_Refund_Log(refund_sheet_id=rs.id, action=action, 
                    memo=kwargs.get('memo', ''), operator=kwargs.get('operator',''),
                    refund_fee=kwargs.get('refund_fee', None))
            rl.save()


    def get_order_type(self):
        return 'service' 


    def get_items(self):
        return self.order_item_rel_set.all()    


   
    
def remove_no_display_actions(role_actions):
    return rm_no_display_actions(role_actions, no_display_actions=no_display_actions)




#This is not made into a workflow since for service order there is only one item for an order and actions on
#item can be treated as actions on the order
class Order_Item_Rel(models.Model):
    order = models.ForeignKey(Service_Order)
    #item = models.ForeignKey(Service_Commodity)    
    item_id = models.CharField(max_length=18) 
    #state = models.CharField(max_length=2, choices=ORDER_ITEM_STATE_CHOICES)
    update_time = models.DateTimeField('time last modified', auto_now=True)
    #TODO:init_time

    class Meta:
        unique_together = (("order", "item_id"),)  


     
    def get_item(self, item_class=None):
        if not item_class:
            item_class = eval(settings.SERVICE_COMMODITY_SNAPSHOT_CLASS)
        return item_class.objects.get(order_id=self.order_id, commodity_id=self.item_id)


    #code validation is not done through state machine since the logic here is not very complex
    def validate(self, code):
        #Don't validate code for orders that are closed or successful. 
        if self.order.state in ['CT', 'ST']:
            return 'Not a valid order!'    
        try:                       
            attend_code = self.attendance_code_set.get(code=code)    
            if attend_code.state == 'Us':
                return 'Already used!'
            if attend_code.state == 'Re':
                return  'Already refunded!'   
            if attend_code.state == 'Ex':
                return  'Already expired!'  
            #if attend_code.state == 'Un':
            #else, assume Un
            #TODO:test below
            if self.get_item().valid_date_end and self.get_item().valid_date_end < datetime.now().date():
                return 'Already expired!' 

            attend_code.state = 'Us'            
            attend_code.save()
            #TODO:consider whether to use state machine for attendance_code as well so that the logic is not scattered
            if not self.attendance_code_set.filter(state='Un').exists():
                self.order.goto_next('P', 'all used')  
            return 'Validated Successfully!'                     
        except Attendance_Code.DoesNotExist, dne:
            return 'Invalid code!'    


    
    #TODO:test
    def get_refund_fee(self):
        """

        """
        used_count = self.attendance_code_set.filter(state="Us").count()
        return self.get_item().price - self.get_item().unit_price * used_count

    #TODO:testing
    def can_apply_refund(self):
        if self.get_item().support_anytime_refund:
            if self.get_refund_fee() > 0:
                return True            
        return False

    # def can_apply_expiration_refund(self):




    
CODE_STATE_CHOICES =   (
        ('Un', _('Unused')),('Us', _('Used')), ('Re', _('Refunded')),('Ex', _('Expired'))
    )
     


class Attendance_Code(models.Model):
    item = models.ForeignKey(Order_Item_Rel)  
    code = models.CharField(max_length=64,  primary_key=True)
    state = models.CharField(max_length=3, choices=CODE_STATE_CHOICES)
    update_time = models.DateTimeField('time last modified', auto_now=True)


    def __unicode__(self):
        return self.code


    



REFUND_CHOICES = (
        ('AR', _('Anytime Refund')),('ER', _('Expiration Refund'))
    )


#Service Order refund sheet
class SO_Refund_Sheet(Refund_Sheet): 
    '''
    '''
    #TODO:better name it as item_rel or sth. else
    item = models.OneToOneField(Order_Item_Rel, related_name='refund_sheet')    
    #state = models.CharField(max_length=3, choices=REFUND_STATE_CHOICES)
    refund_type = models.CharField(max_length=2, choices=REFUND_CHOICES)


    @classmethod
    def get_state_machine(cls): 
        return  Service_Refund_State_Machine


    @classmethod
    def create_refund_sheet(cls, item_rel_id, rs_type): 
        r = cls(item_id=item_rel_id, state=cls.get_state_machine().get_initial_state(), refund_type=rs_type)         
        r.save()              
        return r  
  


    def get_main_log(self):
        #get the latest request refund log
        rl = self.refund_log_set.filter(action__in=['request refund','request refund with return', 'attendance code expired']).order_by('-init_time')[0]
        return rl


    def get_refund_type(self):
        return 'service'     


# class Refund_Sheet_Pic(models.Model):
#     refund_sheet_id = models.ForeignKey(Refund_Sheet)
    



class SO_Refund_Log(Refund_Log):
    refund_sheet = models.ForeignKey(SO_Refund_Sheet, related_name="refund_log_set") #TODO:get rid of foreign key reference here
    #refund_type = models.CharField(max_length=2, choices=REFUND_CHOICES)
    
    #reason = models.TextField(blank=True)
    
    
    

