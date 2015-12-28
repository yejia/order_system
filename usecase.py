#use cases


# o1 = Order.create()
# o2 = Order.create(order_id='7889908238', buyer_id='67894309', item_list=['784389434', '743983432'])
# items = o1.get_items()
# o1.get_role_actions()
# o1.state
# o1.finished_payment()
# o1.shipped()
# o1.state
# items[0].state
# items[0].get_role_actions()
# o1.ack_shipping()
# o1.get_state_display()
# o1.get_role_actions_sorted()
# o1.make_payment()

o1 = Order_System.create_order()
o2 = Order_System.create_order(order_id='7889908238', buyer_id='67894309', item_list=['784389434', '743983432'])
Order_System.goto_next(order_id=o2.order_id, role='S', order_action='ship the order', item_action='', item_id=o2.item_rel_set.all()[0])
o2.get_state_display()
o2.state
items = o2.item_rel_set.all()
items[0].state

