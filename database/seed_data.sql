-- Mectro AI Customer Support System
-- Sample data
-- Run with: mysql -u root -p < database/seed_data.sql

USE mectro_support;

-- ---------------------------------------------------------------
-- Policies
-- ---------------------------------------------------------------
INSERT INTO policies (policy_type, title, content) VALUES
('refund_policy', 'Refund Policy',
 'Mectro offers a full refund within 30 days of delivery for unused items in their original packaging. Refunds are processed to the original payment method within 5-7 business days after we receive the returned item.'),
('return_policy', 'Return Policy',
 'Items can be returned within 30 days of delivery if they are unused, undamaged, and in their original packaging. To start a return, contact support with your order ID and reason for the return. Return shipping is free for defective or incorrect items.'),
('cancellation_policy', 'Order Cancellation Policy',
 'Orders can be cancelled free of charge as long as they have not yet been shipped. Once an order status changes to "Shipped", it can no longer be cancelled, but it can be returned after delivery under our return policy.'),
('shipping_policy', 'Shipping Policy',
 'Standard shipping takes 3-5 business days and is free on orders over 999 INR. Express shipping (1-2 business days) is available at checkout for an additional fee. Once an order ships, a tracking number and carrier are provided by email.')
ON DUPLICATE KEY UPDATE
    title = VALUES(title),
    content = VALUES(content);

-- ---------------------------------------------------------------
-- Orders
-- ---------------------------------------------------------------
INSERT INTO orders
(order_id, customer_name, order_status, payment_status, tracking_number, carrier, expected_delivery, order_amount)
VALUES
('ORD1001', 'Aditi Sharma',  'Shipped',          'Paid',     'TRK9988771', 'BlueDart',  '2026-07-20', 2499.00),
('ORD1002', 'Rohan Mehta',   'Placed',           'Paid',     NULL,         NULL,        '2026-07-25', 1299.00),
('ORD1003', 'Kavya Iyer',    'Out for Delivery', 'Paid',     'TRK1122334', 'Delhivery', '2026-07-19', 899.00),
('ORD1004', 'Sanya Kapoor',  'Delivered',        'Paid',     'TRK5566778', 'DTDC',      '2026-07-10', 3599.00),
('ORD1005', 'Arjun Verma',   'Cancelled',        'Refunded', NULL,         NULL,        NULL,          1999.00),
('ORD1006', 'Priya Nair',    'Placed',           'Failed',   NULL,         NULL,        '2026-07-28', 749.00)
ON DUPLICATE KEY UPDATE
    customer_name     = VALUES(customer_name),
    order_status       = VALUES(order_status),
    payment_status     = VALUES(payment_status),
    tracking_number    = VALUES(tracking_number),
    carrier            = VALUES(carrier),
    expected_delivery  = VALUES(expected_delivery),
    order_amount       = VALUES(order_amount);
