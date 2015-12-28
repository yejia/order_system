/*TODO: think of changing action into a set of short choices*/
INSERT INTO `service_order_order_state_machine` (`operator_role`,`action`,`current_state`, `next_state`, `post_action`) VALUES 
('B', 'create order', '', 'WP', 'order_created'),
('B', 'cancel order', 'WP', 'CT', ''),
('B', 'make payment', 'WP', 'WP', ''),
('B', 'request refund', 'FP', 'FP', 'refund_requested'),
('P', 'no payment', 'WP', 'CT', ''), # within 24 hours
('P', 'payment successful', 'WP', 'FP', 'payment_successful'),
('P', 'attendance code expired', 'FP', 'FP', 'attendance_code_expired'),
#('P', 'all items done with refund', 'ST', 'WA', ''),
#('P', 'finished accounting', 'WA', 'FA', ''),
('P', 'finished refund', 'FP', 'FP', 'refund_sheet_finished'),
('P', 'used service finished refund', 'FP', 'ST', ''),
('P', 'unused service finished refund', 'FP', 'CT', ''),
('P', 'all used', 'FP', 'ST', '')
#('P', 'no more open refund', 'ST', 'WA', '')

;

/*state machine of attendance code. Not used. But put it here to show how it can be done via state machine*/
/*attendance code states: ('Un', _('Unused')),('Us', _('Used')), ('Re', _('Refunded')),('Ex', _('Expired'))*/

#INSERT INTO `service_order_code_state_machine` (`operator_role`,`action`,`current_state`, `next_state`, `post_action`) VALUES 
#('S', 'valide code', 'Un', 'Us', ''),
#('P', 'refund code', 'Un', 'Re', ''),
#('P', 'expired', 'Un', 'Ex', '');
