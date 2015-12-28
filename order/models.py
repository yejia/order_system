#-*- coding: utf-8 -*

import sys
import time
import random
import hashlib
import copy

from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.conf import settings
from django.core.files.storage import FileSystemStorage    



import snapshot

OPERATOR_ROLE_CHOICES = (
        ('P', 'Platform'),('A', 'Admin'),('B', 'Buyer'),('S', 'Seller'),
    )

#TODO:better regex
#To support comma separated states. So far the maximum number of states supported is 5 comma separated states string
def state_machine_match_regex(st):
    return r'^\*$|^'+st+'$|^'+st+',|,'+st+'$|,'+st+',|^'+st+'$'






ORDER_STATE_CHOICES = (
        ('WP', _('Waiting for Payment')),('FP', _('Finished Payment')),('FS', _('Finished Shipping')), ('HS', _('Hold Shipping')), 
        ('ST', _('Successful Transatcion')), ('CT', _('Closed Transatcion')), 
        ('WA', _('Waiting for Accounting')), ('FA', _('Finished Accounting')),
    )

#state for Service_Order
# ORDER_STATE_CHOICES = (
#         ('WP', _('Waiting for Payment')),('FP', _('Finished Payment')),
#         ('ST', _('Successful Transatcion')), ('CT', _('Closed Transatcion')), 
#         #('WA', _('Waiting for Accounting')), ('FA', _('Finished Accounting')),
#     )



#'WSA' is added. The product design document will add this too.
# 'CSA' is added. Before return and after return of the item, the "force refund" action will cause different results for refund with return item 
REFUND_STATE_CHOICES = (
        ('WSR', _('Waiting For Seller Response')),('WSA', _('Waiting For Seller Response After Return')),('PPR', _('Platform Processing Refund')), ('SRR', _('Seller Rejected Refund')), 
        ('CSI', _('Customer Service Involved')), ('WBS', _('Waiting For Buyer Shipping Back')), #WBS only used for refund with return type of refund
        ('CSA', _('Customer Service Involved After Return')),
        ('PFR', _('Platform Finished Refund')), ('CCR', _('Clustomer Closed Refund')), ('PCR', _('Platform Closed Refund')),
    ) #if a refund is closed, the corresponding item cannot be requested refund again.
#TODO:change Finished Refund to Successful Refund


#state for SO_Refund_Sheet
# REFUND_STATE_CHOICES = (
#        ('PPR', _('Platform Processing Refund')),        
#        ('PFR', _('Platform Finished Refund')), 
#     )




class State_Machine(models.Model):
    operator_role = models.CharField(max_length=1, choices=OPERATOR_ROLE_CHOICES)
    action = models.CharField('action to do', max_length=256)  
    current_state = models.CharField(max_length=128) 
    next_state = models.CharField(max_length=3)
    post_action = models.CharField('action to do afterwards by the platform', max_length=64) 

    class Meta:
        abstract = True



    @classmethod
    def get_initial_state(cls):
        return ''


    @classmethod
    def get_next(cls, role, action, c_state):
        try:
            osm = cls.objects.get(operator_role=role, action=action, current_state__regex=state_machine_match_regex(c_state))
            return osm.next_state, osm.post_action
        except MultipleObjectsReturned, mor:
            #TODO:make a custom exception
            raise Exception('Multiple states returned!') 
        #TODO:
        except ObjectDoesNotExist, dne:
            return None, None    

    
    


    @classmethod
    def get_role_actions(cls, c_state):
        '''Get which roles can do what actions when the order is in a certain state
        '''      
        osms = cls.objects.filter(current_state__regex=state_machine_match_regex(c_state)).values_list('operator_role','action')   
        roles = list(set([osm[0] for osm in osms]))        
        role_actions = {}
        for r in roles:
            role_actions[r] = []
            for s in osms:
                if s[0]==r:
                    role_actions[r].append(s[1])
        return role_actions   


    


    #TODO:remove
    @classmethod
    def get_initials(cls):
        osms = cls.objects.filter(current_state=self.get_initial_state())   
        return osms   

   
    @classmethod
    def get_initial_role_actions(cls):
        ras = cls.get_role_actions(cls.get_initial_state())
        return ras      






#actually exactly the same as order state machine TODO:use abstract table
class Refund_State_Machine(State_Machine):
  
    class Meta:
        abstract = True



    @classmethod
    def get_initial_state(cls):
        return 'WSR'



def remove_no_display_actions(role_actions, no_display_actions):
    #need to be deep copy here. Otherwise it only copies the reference (to the list inside in this case)
    #modifying a list in one will also change the other
    ras = copy.deepcopy(role_actions) 
    for role in ras.keys():
        for action in ras[role]:
            if action in no_display_actions:
                role_actions[role].remove(action)
        if not role_actions[role]:
            role_actions.pop(role)
    return role_actions        

   
class Work_Flow(models.Model): 
    '''State machine controlled work flow
    '''  
    #id =  models.CharField(max_length=64, primary_key=True) 
    state = models.CharField(max_length=3)

    class Meta:
        abstract = True



    @classmethod
    def get_state_machine(cls): 
        pass 


    def get_role_actions(self):
        '''Get which roles can do what actions when the refund sheet is in a certain state
        '''             
        ras = self.__class__.get_state_machine().get_role_actions(self.state)    
        return self.remove_actions(ras)
        
    
    def remove_actions(self, ras):
        pass


    def goto_next(self, role, action, **kwargs):        
        next_state, post_action = self.__class__.get_state_machine().get_next(role, action, self.state)        
        if next_state:
            self.state = next_state
            self.save()
            if post_action:
                getattr(sys.modules[self.__class__.__module__], post_action)(self.id)
        self.common_post_action(role, action, **kwargs)    
        return next_state, post_action    
          

    def common_post_action(self, role, action, **kwargs):
        pass      
    
    def get_state_display(self):
        pass


class Order(Work_Flow):    
    buyer_id = models.CharField(max_length=10) #TODO:move to order center?
    #state = models.CharField(max_length=2, choices=ORDER_STATE_CHOICES, null=True) 
    

    def __unicode__(self):
        return unicode(self.id)


    #TODO: implement this by adding one extra parameter: order_type, so it is more convenient for usage
    @classmethod
    def create_order(cls, id=None, buyer_id='877673433', item_list=['92399069', '83768385'], **kwargs):     
        pass

  


    def get_state_display(self):
        return dict(ORDER_STATE_CHOICES).get(self.state)


    #calling order center using this order_system might want to hide WA and FA states, then they can use this mentod to display the state
    def get_custom_state_display(self):
        if self.state in ['WA', 'FA']:
            return _('Successful Transatcion') #testing translation TODO:
        elif self.state == 'HS':
            return _('Finished Payment')
        else:
            return self.get_state_display() 
            
    

    
    def get_order_type(self):    
        return 'order'

    #TODO:test
    #TODO: to be used in order center
    def get_items(self):
        """


        """
        pass
        # if self.get_order_type() == 'product':
        #     return self.product_order.order_item_rel_set.all()
        # else:#assume service
        #     return self.service_order.order_item_rel_set.all()    
               

 
 

class Refund_Sheet(Work_Flow):       
    #state = models.CharField(max_length=3, choices=REFUND_STATE_CHOICES, null=True)  
    #so far, read refund_fee from refund_log
    #refund_fee = models.DecimalField(null=True, max_digits=9, decimal_places=2, verbose_name='refund fee')     
  

    
    def get_refund_type(self):
        """
     

        """                    
        log.info('No refund type detected!')
        return 'order' 

    
    def get_pics(self):
        """get the first three pics of the refund_sheet if available


        """
        return self.refund_sheet_pic_set.all().order_by('-pk')[:3]
    

    def get_main_log(self):
        pass


    #TODO:get the order_item_rel so it is convenient to go back
    def get_item(self):
        pass

class Refund_Log(models.Model):
    action = models.CharField('action done', max_length=256)     
    memo = models.TextField(blank=True)
    operator = models.CharField(max_length=30)
    refund_fee = models.DecimalField(null=True, max_digits=9, decimal_places=2, verbose_name='refund fee') 
    init_time = models.DateTimeField('time created', auto_now_add=True)        






fs = FileSystemStorage(location=settings.MEDIA_ROOT)


def get_storage_loc(instance, filename):        
    return 'refund_pics/'+str(instance.refund_sheet.id)+'_'+str(time.time()).replace('.', '')
    

class Refund_Sheet_Pic(models.Model):
     refund_sheet = models.ForeignKey(Refund_Sheet)
     pic = models.ImageField(upload_to=get_storage_loc, blank=True, storage=fs, verbose_name=_('refund pictures'))
    



def save_snapshot(order_id, item_list, default_snapshot_class, **kwargs):
    ''' item_list accept two types of data, one is a list of str (commodity_id), 
        the other is a list of dict, which contains other fields of each item to 
        be saved in snapshot. For the first case, the other fieldnames need to be 
        obtained from kwargs, where you might use some method depending on the convention
        set up (for example, prefix each field with item1_ to denote that this field belongs
        to item1)
    '''
    item_class = kwargs.pop('item_class', '')
    if not item_class:
        item_class = eval(default_snapshot_class)
    else:
        item_class = eval(item_class)
    sku_cls = item_class.get_sku_class()
    for it in item_list:
        if type(it) == str: #not passing snapshot by json
            item_id = it
        else:
            item_id = it['commodity_id']    

        item = item_class()                      
        item.order_id = order_id
        item.commodity_id = item_id            

        if type(it) == str:            
            for field_name in kwargs.keys():
                if not field_name.startswith('sku_'):
                    #TODO: if getattr  check if attr exists
                    setattr(item, field_name, kwargs[field_name])
                else:     
                    save_sku_field(sku_cls, order_id, item_id, field_name[4:], kwargs[field_name])                                        
        else:
            it.pop('commodity_id')
            for field_name in it.keys():
                if not field_name.startswith('sku_'):
                    #TODO: if getattr  check if attr exists
                    setattr(item, field_name, it[field_name])
                else:  
                    save_sku_field(sku_cls, order_id, item_id, field_name[4:], it[field_name])                              
        item.save()


def save_sku_field(sku_cls, order_id, commodity_id, field_name, field_value):
    sku = sku_cls() 
    sku.order_id = order_id
    sku.commodity_id = commodity_id                                    
    sku.field_name = field_name
    sku.field_value = field_value
    sku.save() 


def create_attendance_code(buyer_id, commodity_id, seller_id):
    """
    Generate an attendance code
    """
    s_str = list(buyer_id + commodity_id + seller_id + str(int(time.time())))
    random.shuffle(s_str)
    s_str = ''.join(s_str)
    h = hashlib.md5()
    h.update(s_str)
    d_str = h.hexdigest()
    dd_num = ''
    for i in d_str:
        if i.isalpha():
            i = str(ord(i))
        dd_num += i
    attendance_code = ''.join(random.sample(dd_num, settings.DEFAULT_LENGTH_OF_ATTENDANCE_CODE))
    return attendance_code        


#so far, just get a random number. TODO:
def get_order_id():
    return str(random.randint(10000000, 99999999))    