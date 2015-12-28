

/*TODO: think of changing action into a set of short choices*/
INSERT INTO `product_order_order_state_machine` (`operator_role`,`action`,`current_state`, `next_state`, `post_action`) VALUES 
('B', 'create order', '', 'WP', 'order_created'),
('B', 'cancel order', 'WP', 'CT', ''),
('B', 'make payment', 'WP', 'WP', ''),
('S', 'change shipping fee', 'WP', 'WP', ''),
#above is just for showing the available actions on the page. If no need to get the actions automatically, then can remove this from state machine
('P', 'no payment', 'WP', 'CT', ''), # within 24 hours
('P', 'payment successful', 'WP', 'FP', 'order_paid'),
('S', 'ship the order', 'FP', 'FS', 'order_shipped'),
('S', 'change shipping addr', 'FP', 'FP', ''),
('B', 'confirm reception of order', 'FS', 'ST', 'transaction_successful'),
('P', 'auto ack reception of order', 'FS', 'ST', 'transaction_successful'), # within 15 days
('B', 'extend auto acking reception of order', 'FS', 'FS', 'buyer_extend_shipping_ack'),
('S', 'extend auto acking reception of order', 'FS', 'FS', 'seller_extend_shipping_ack'),
('P', 'all items done with refund', 'ST', 'WA', ''),
('P', 'no refund request', 'ST', 'WA', ''), # within 7 days
('P', 'finished accounting', 'WA', 'FA', ''),
('P', 'all items refunded', 'ST,FS,FP', 'CT', ''),
('P', 'processing refund', 'FP', 'HS', ''),
('P', 'no more open refund', 'FS', 'ST', 'transaction_successful'),
('P', 'no more open refund', 'ST', 'WA', ''),
('P', 'item finished refund', 'HS', 'FP', '')
;
/*The above three states can also have all items refunded action?? need to involve item state to decide order available action?? e.g. when all items
are in FR state. or make another small state machine for the platform to use?? or since this is platform auto triggered event, so it is unlike manual 
actions, no need to worry about it. TODO:*/


/*for display at front (buyer, seller??), 'WA' and 'FA' is displayed as 'ST'*/
/*There should be a state called 'Buyer Made Payment' (may not be successful yet). But don't display this state at front*/
/*payment failed, should be a platform action as well, and the state go back to WP. But since the state doesn't change, there
is no need to make one*/
/* order state probably should also be affected by the item in it. For example, when the buyer requested refund on an item, the
order should also be in a state of refund requested. Then there will be no action for 'no refund request within 7 days' from the system. 
Also after 7 days, the buyer cannot request refund anymore. But this can be achieved by the WA state */


/*actions on the item can be viewed as on both the item and its refund sheet. If it only changes state of one, no need to store it in the other*/
INSERT INTO `product_order_order_item_state_machine` (`operator_role`, `action`, `order_current_state`, `current_state`, `next_state`, `post_action`) VALUES 
('P', 'order state changed to FP', 'FP', '', 'FP', ''),
#('B', 'request refund', 'FP', 'FP', 'WR', 'seller_no_response'),
('P', 'order state changed to FS', 'FS', 'WR', 'FP', ''),
#merged the second one into below and added HS 
('B', 'request refund', 'FP,HS,FS,ST','FP', 'WR', 'seller_no_response'), #this can only be in order_item_rel because no refund sheet is created yet
('B', 'request refund with return', 'FS,ST','FP', 'WR', 'seller_no_response'), 
('P', 'item finished refund', 'FP,FS,HS,ST', 'WR', 'FR', 'refund_finished'),
('P', 'item closed refund', 'FP,FS,ST','WR', 'CR', 'refund_closed');

#added
#('P', 'refund sheet closed', 'FP','WR', 'CR', ''),
#('P', 'refund sheet closed', 'FS','WR', 'CR', ''),
#('P', 'refund sheet closed', 'ST','WR', 'CR', '');
/*distinguish btw customer service forced refund and seller agreed refund?*/
/*TODO:platform force refund need to interface with the payment system??*/
/* when in successful transaction state, how is the the refund process? still waiting for the seller response and so on? Yes, the same
as the refund process after FD. Also only some sellers support refund after ST within 7 days. TODO:*/





/*seller reject refund is different when order is in 'FP' or after 'FP'. For now, just treat this as a special  case, and don't include order state in the refund
sheet state machine*/
#TODO:remove 72 hours and other numbers so it is more extendable
INSERT INTO `product_order_refund_only_state_machine` (`operator_role`,`action`,`current_state`, `next_state`, `post_action`) VALUES 
('S', 'reject refund', 'WSR', 'SRR', 'buyer_no_response'),
('S', 'agree refund', 'WSR', 'PPR', ''),
('B', 'cancel refund request', 'WSR,SRR', 'CCR', 'refund_sheet_closed'),
('P', 'seller no response', 'WSR', 'CSI', ''),
('P', 'reject refund', 'CSI', 'PCR', 'refund_sheet_closed'),
('P', 'force refund', 'CSI', 'PPR', ''),
('B', 'change refund request', 'SRR', 'WSR', ''),
('B', 'request customer service involvement', 'SRR', 'CSI', ''),
('P', 'buyer no response', 'SRR', 'CCR', 'refund_sheet_closed'),
('P', 'finished refund', 'PPR', 'PFR', 'refund_sheet_finished');



INSERT INTO `product_order_refund_with_return_state_machine` (`operator_role`,`action`,`current_state`, `next_state`, `post_action`) VALUES 
('S', 'reject refund', 'WSR', 'SRR', 'buyer_no_response'),
('S', 'agree refund', 'WSR', 'WBS', 'buyer_no_response'),
('B', 'cancel refund request', 'WBS', 'CCR', 'refund_sheet_closed'),
('B', 'ship back', 'WBS', 'WSA', 'refund_seller_no_response'), #think of moving this into order_item_state_machine TODO:
('B', 'cancel refund request', 'WSR,SRR', 'CCR', 'refund_sheet_closed'),
('P', 'seller no response', 'WSR', 'CSI', ''),
('S', 'reject refund', 'WSA', 'CSA', ''),
('S', 'agree refund', 'WSA', 'PPR', ''),
('P', 'seller no response', 'WSA', 'PPR', ''),
('P', 'reject refund', 'CSI,CSA', 'PCR', 'refund_sheet_closed'),
('P', 'force refund', 'CSI', 'WBS', 'buyer_no_response'),
('P', 'force refund', 'CSA', 'PPR', ''),
('B', 'change refund request', 'SRR', 'WSR', ''),
('B', 'request customer service involvement', 'SRR', 'CSI', ''),
('P', 'buyer no response', 'SRR,WBS', 'CCR', 'refund_sheet_closed'),
('P', 'finished refund', 'PPR', 'PFR', 'refund_sheet_finished');


INSERT INTO `product_order_pre_shipping_refund_state_machine` (`operator_role`, `action`, `current_state`, `next_state`, `post_action`) VALUES 
('S', 'agree refund', 'WSR', 'PPR', 'seller_agree_refund'),
('P', 'seller no response', 'WSR', 'PPR', ''),
('B', 'cancel refund request', 'WSR', 'CCR', 'refund_sheet_closed'),
('P', 'finished refund', 'PPR', 'PFR', 'refund_sheet_finished');





COMMIT;
