

import json
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.core.context_processors import csrf
from service_order.models import SO_Refund_Sheet as Refund_Sheet, Service_Commodity
from service_order.order_system import Order_System




def index(request, template_name='service_order/index.html'):
    return render_to_response(template_name, {},
        context_instance=RequestContext(request)) 


def order_state_machine(request,  template_name='service_order/order_state_machine.html'):
    role = request.REQUEST.get('role')
    action = request.REQUEST.get('action')
    c_state = request.REQUEST.get('current_state')
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
#     role = request.REQUEST.get('role')
#     action = request.REQUEST.get('action')
#     c_state = request.REQUEST.get('current_state')
#     if not (role or action or c_state):
#         #initial state
#         next_state = Order_Item_Rel_State_Machine.get_initial_state()
#         ras = Order_Item_Rel_State_Machine.get_initial_role_actions()
#     else:
#         next_state, post_action = Order_Item_Rel_State_Machine.get_next(role, action, c_state)
#         ras = Order_Item_Rel_State_Machine.get_role_actions(next_state)
#     return render_to_response(template_name, {'roles':ras.keys(), 'role_actions':ras, 'current_state':next_state},
#         context_instance=RequestContext(request))    


def make_order(request, template_name='service_order/make_order.html'):
    order_id = request.REQUEST.get('order_id')
    role = request.REQUEST.get('role')
    action = request.REQUEST.get('action')
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

    return render_to_response(template_name, {'order': order, 'role_actions':order.get_role_actions(), 'current_state':order.state},
        context_instance=RequestContext(request))


def make_order2(request, template_name='service_order/make_order2.html'):
    order_id = request.REQUEST.get('order_id')
    role = request.REQUEST.get('role','')
    order_action = request.REQUEST.get('action','')
    item_action = request.REQUEST.get('item_action','')
    item_id = request.REQUEST.get('item_id')
    #order = None
    refresh = request.REQUEST.get('refresh')
    if refresh == 'y':
        return render_to_response(template_name, Order_System.get_status(order_id) , context_instance=RequestContext(request))
    if not role:        
        return render_to_response(template_name, Order_System.get_initial(), context_instance=RequestContext(request))
    else:
        return render_to_response(template_name, Order_System.goto_next(order_id, role, order_action, item_action, item_id), 
            context_instance=RequestContext(request))



def create_order(request, template_name='service_order/create_order.html'):
    if request.method == 'POST':
        # item_list = request.POST.getlist('item')
        # o = Order_System.create_order(item_list=item_list)
        item_id_list = request.POST.getlist('item_id')
        item_name_list = request.POST.getlist('item_name')
        #pdb.set_trace()
        request_params = request.POST.copy()
        request_params = request_params.dict()
        items = []
        for i, item_id in enumerate(item_id_list):
            items.append({'commodity_id':item_id, 'name':item_name_list[i], 'sku_service_times':5}) #pass in a default service_times here
        #items_snapshot = {'order_type':'service', 'items':items}
        items_snapshot = items
        items_json = json.dumps(items_snapshot)  
        request_params['items_json'] = items_json
        print 'items_json:', items_json

        o = Order_System.create_order(item_list=item_id_list, **request_params)
        return HttpResponseRedirect('/service_order_demo/make_order3/?order_id='+o+'&refresh=y') 
    cs = Service_Commodity.objects.all()
    return render_to_response(template_name, {'items':cs[:1]}, #for now one order has only one item
            context_instance=RequestContext(request))



#TODO:add shipping addr; extend shipping; add reasons for refund or reject refund; refund and shipping back commodities; show refund sheets
def make_order3(request, template_name='service_order/make_order3.html'):
    request_params = request.GET.copy()
    #pop out the standard parameters, and the rest are the extra parameters and can be passed to Order_System as well
    request_params = request_params.dict() #TODO:
    #print 'request.REQUEST:', request.REQUEST
    #print 'request_params:', request_params
    order_id = request_params.pop('order_id')
    role = request_params.pop('role','')
    order_action = request_params.pop('action','')
    item_action = request_params.pop('item_action','')
    item_id = request_params.pop('item_id', '')
    #order = None
    refresh = request_params.pop('refresh','')   

    if refresh == 'y':
        context = Order_System.get_status(order_id)
        context.update(csrf(request))
        return render_to_response(template_name, context, context_instance=RequestContext(request))
    if not role:        
        return render_to_response(template_name, Order_System.get_initial(), context_instance=RequestContext(request))
    else:
        context = Order_System.goto_next(order_id, role, order_action, **request_params)
        context.update(csrf(request))
        return render_to_response(template_name, context, 
            context_instance=RequestContext(request))


def make_payment(request, order_id):  
    return render_to_response('service_order/make_payment.html', {'order':get_object_or_404(Order, id=order_id)}, 
            context_instance=RequestContext(request))



def view_refund_sheet(request, template_name='service_order/view_refund_sheet.html'):
    refund_sheet_id = request.GET.get('rs_id')
    rs = get_object_or_404(Refund_Sheet, id=refund_sheet_id)
    rl = rs.refund_log_set.filter(action__in=['request refund','request refund with return', 'attendance code expired']).order_by('init_time')
    the_last_request = rl[0]
    rs.refund_fee = the_last_request.refund_fee
    #rs.refund_type = the_last_request.refund_type
    #rs.reason = the_last_request.reason
    rs.memo = the_last_request.memo
    rs.init_time = the_last_request.init_time

    return render_to_response(template_name, {'refund_sheet':rs}, 
            context_instance=RequestContext(request))
