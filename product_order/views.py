

import json
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, Http404, HttpResponse
from product_order.models import Product_Order as Order, PO_Refund_Sheet as Refund_Sheet, Commodity, Order_State_Machine
from product_order.order_system import Order_System




def index(request, template_name='product_order/index.html'):
    return render_to_response(template_name, {},
        context_instance=RequestContext(request)) 


def order_state_machine(request,  template_name='product_order/order_state_machine.html'):
    role = request.GET.get('role')
    action = request.GET.get('action')
    c_state = request.GET.get('current_state')
    if not (role or action or c_state):
        #initial state
        next_state = Order_State_Machine.get_initial_state()
        ras = Order_State_Machine.get_initial_role_actions()
    else:
        next_state, post_action = Order_State_Machine.get_next(role, action, c_state)
        ras = Order_State_Machine.get_role_actions(next_state)
    return render_to_response(template_name, {'roles':ras.keys(), 'role_actions':ras, 'current_state':next_state},
        context_instance=RequestContext(request))


#TODO: also demo the order item state machine (need to consider order state)
# def item_state_machine(request,  template_name='order/item_state_machine.html'):
#     role = request.GET.get('role')
#     action = request.GET.get('action')
#     c_state = request.GET.get('current_state')
#     if not (role or action or c_state):
#         #initial state
#         next_state = Order_Item_Rel_State_Machine.get_initial_state()
#         ras = Order_Item_Rel_State_Machine.get_initial_role_actions()
#     else:
#         next_state, post_action = Order_Item_Rel_State_Machine.get_next(role, action, c_state)
#         ras = Order_Item_Rel_State_Machine.get_role_actions(next_state)
#     return render_to_response(template_name, {'roles':ras.keys(), 'role_actions':ras, 'current_state':next_state},
#         context_instance=RequestContext(request))    


def make_order(request, template_name='product_order/make_order.html'):
    order_id = request.GET.get('order_id')
    role = request.GET.get('role')
    action = request.GET.get('action')
    if not role:        
        return render_to_response(template_name, {'order': None, 'role_actions':Order_State_Machine.get_initial_role_actions(),
           'current_state':Order_State_Machine.get_initial_state()},
            context_instance=RequestContext(request))
    else:
        if role == 'B' and action == 'create order': 
            order_id = Order.create_order()  
            order = get_object_or_404(Order, id=order_id)        
        else:
            order = get_object_or_404(Order, id=order_id)
            order.goto_next(role, action)           

    return render_to_response(template_name, {'order': order.product_order, 'role_actions':order.product_order.get_role_actions(), 'current_state':order.state},
        context_instance=RequestContext(request))


def make_order2(request, template_name='product_order/make_order2.html'):
    order_id = request.GET.get('order_id')
    role = request.GET.get('role','')
    order_action = request.GET.get('action','')
    item_action = request.GET.get('item_action','')
    item_id = request.GET.get('item_id')
    refresh = request.GET.get('refresh')
    if not order_id:
        order_id = Order_System.create_order() #use the default params
        refresh = 'y'
    print 'order_id:', order_id            
    if refresh == 'y':
        return render_to_response(template_name, Order_System.get_status(order_id) , context_instance=RequestContext(request))
    if not role:        
        return render_to_response(template_name, Order_System.get_initial(), context_instance=RequestContext(request))
    else:
        return render_to_response(template_name, Order_System.goto_next(order_id, role, order_action, item_action, item_id), 
            context_instance=RequestContext(request))



def create_order(request, template_name='product_order/create_order.html'):
    if request.method == 'POST':
        item_id_list = request.POST.getlist('item_id')
        item_name_list = request.POST.getlist('item_name')
        #pdb.set_trace()
        request_params = request.POST.copy()
        request_params = request_params.dict()
        items = []
        for i, item_id in enumerate(item_id_list):
            items.append({'commodity_id':item_id, 'name':item_name_list[i]})
        #items_snapshot = {'order_type':'product', 'items':items}
        items_snapshot = items
        items_json = json.dumps(items_snapshot)  
        request_params['items_json'] = items_json

        o = Order_System.create_order(item_list=item_id_list, **request_params)
        
        return HttpResponseRedirect('/demo/make_order3/?order_id='+o+'&refresh=y') 
    cs = Commodity.objects.all()
    return render_to_response(template_name, {'items':cs}, 
            context_instance=RequestContext(request))



#TODO:add shipping addr; extend shipping; add reasons for refund or reject refund; refund and shipping back commodities; show refund sheets
def make_order3(request, template_name='product_order/make_order3.html'):
    request_params = request.GET.copy()
    request_params = request_params.dict() #TODO:
    #print 'request.GET:', request.GET
    #print 'request_params:', request_params
    order_id = request_params.pop('order_id')
    role = request_params.pop('role','')
    order_action = request_params.pop('action','')
    item_action = request_params.pop('item_action','')
    item_id = request_params.pop('item_id', '')
    #order = None
    refresh = request_params.pop('refresh','')
    #TODO: testing below 
    request_params['operator'] = request.user.username 

    if refresh == 'y':
        return render_to_response(template_name, Order_System.get_status(order_id), context_instance=RequestContext(request))
    if not role:        
        return render_to_response(template_name, Order_System.get_initial(), context_instance=RequestContext(request))
    else:
        return render_to_response(template_name, Order_System.goto_next(order_id, role, order_action, item_action, item_id, **request_params), 
            context_instance=RequestContext(request))


def make_payment(request, order_id):  
    return render_to_response('product_order/make_payment.html', {'order':get_object_or_404(Order, id=order_id)}, 
            context_instance=RequestContext(request))



def view_refund_sheet(request, template_name='product_order/view_refund_sheet.html'):
    refund_sheet_id = request.GET.get('rs_id')
    rs = get_object_or_404(Refund_Sheet, id=refund_sheet_id)
    rl = rs.refund_log_set.filter(action__in=['request refund','request refund with return']).order_by('init_time')
    the_last_request = rl[0]
    rs.refund_fee = the_last_request.refund_fee
    rs.refund_type = the_last_request.refund_type
    rs.reason = the_last_request.reason
    rs.memo = the_last_request.memo
    rs.init_time = the_last_request.init_time

    return render_to_response(template_name, {'refund_sheet':rs}, 
            context_instance=RequestContext(request))
