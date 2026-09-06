-- V2__seed_ai_smart_mart_products.sql: Realistic Indian AI_smart_mart catalog

INSERT INTO products (sku, name, normalized_name, description, unit, is_packaged, cost_price, selling_price, mrp, quantity, reorder_level, gst_rate, hsn_code, active)
VALUES
    -- Loose staples (0% GST)
    ('SKU-SUGAR-LOOSE', 'Sugar Loose', 'sugar loose sugar', 'Refined white crystal sugar loose', 'kg', FALSE, 38.00, 42.00, 45.00, 100.000, 20.000, 0.00, '1701', TRUE),
    ('SKU-RICE-LOOSE', 'Basmati Rice Loose', 'basmati rice loose rice', 'Premium aged loose basmati rice', 'kg', FALSE, 65.00, 75.00, 85.00, 150.000, 30.000, 0.00, '1006', TRUE),
    ('SKU-TOORDAL-LOOSE', 'Toor Dal Loose', 'toor dal loose dal', 'Unpolished yellow toor dal loose', 'kg', FALSE, 130.00, 155.00, 170.00, 80.000, 15.000, 0.00, '0713', TRUE),
    ('SKU-ATTA-LOOSE', 'Chakki Atta Loose', 'chakki atta loose atta', 'Fresh ground whole wheat atta loose', 'kg', FALSE, 30.00, 36.00, 40.00, 120.000, 25.000, 0.00, '1101', TRUE),

    -- Packaged staples (5% GST)
    ('SKU-AASH-ATTA-5KG', 'Aashirvaad Atta 5kg', 'aashirvaad atta 5kg aashirvaad 5kg atta 5kg', 'Aashirvaad Superior MP Sharbati Whole Wheat Atta 5kg', 'packet', TRUE, 235.00, 275.00, 290.00, 40.000, 10.000, 5.00, '1101', TRUE),
    ('SKU-AASH-ATTA-10KG', 'Aashirvaad Atta 10kg', 'aashirvaad atta 10kg aashirvaad 10kg atta 10kg', 'Aashirvaad Superior MP Sharbati Whole Wheat Atta 10kg', 'packet', TRUE, 450.00, 520.00, 560.00, 25.000, 8.000, 5.00, '1101', TRUE),
    ('SKU-TATA-SALT-1KG', 'Tata Salt 1kg', 'tata salt 1kg tata salt salt', 'Tata Vacuum Evaporated Iodised Salt 1kg', 'packet', TRUE, 22.00, 28.00, 28.00, 80.000, 20.000, 5.00, '2501', TRUE),
    ('SKU-FORT-OIL-1L', 'Fortune Sunflower Oil 1L', 'fortune sunflower oil 1l fortune oil sunflower oil', 'Fortune Sunlite Refined Sunflower Oil Pouch 1L', 'packet', TRUE, 122.00, 145.00, 155.00, 50.000, 15.000, 5.00, '1512', TRUE),
    ('SKU-FORT-MUST-1L', 'Fortune Mustard Oil 1L', 'fortune mustard oil 1l mustard oil kachi ghani', 'Fortune Kachi Ghani Pure Mustard Oil 1L', 'packet', TRUE, 132.00, 158.00, 168.00, 30.000, 10.000, 5.00, '1514', TRUE),

    -- Dairy & FMCG Food (12% GST)
    ('SKU-AMUL-BUTTER-100G', 'Amul Butter 100g', 'amul butter 100g amul butter butter', 'Amul Pasteurised Salted Butter 100g', 'packet', TRUE, 51.00, 58.00, 60.00, 45.000, 12.000, 12.00, '0405', TRUE),
    ('SKU-AMUL-BUTTER-500G', 'Amul Butter 500g', 'amul butter 500g amul butter 500gm', 'Amul Pasteurised Salted Butter 500g', 'packet', TRUE, 240.00, 275.00, 285.00, 20.000, 5.000, 12.00, '0405', TRUE),
    ('SKU-MAGGI-70G', 'Maggi 70g', 'maggi 70g maggi 2 minute noodles maggi noodles', 'Nestle Maggi 2-Minute Masala Instant Noodles 70g', 'packet', TRUE, 11.50, 14.00, 14.00, 100.000, 25.000, 12.00, '1902', TRUE),
    ('SKU-PARLE-G-250G', 'Parle-G 250g', 'parle-g 250g parle g biscuit parle g 250gm', 'Parle-G Original Gluco Biscuits 250g', 'packet', TRUE, 24.00, 28.00, 30.00, 60.000, 15.000, 12.00, '1905', TRUE),
    ('SKU-GOOD-DAY-100G', 'Britannia Good Day 100g', 'good day 100g britannia good day butter cookies', 'Britannia Good Day Butter Cookies 100g', 'packet', TRUE, 27.00, 33.00, 35.00, 50.000, 15.000, 12.00, '1905', TRUE),

    -- Personal & Home Care (18% GST)
    ('SKU-SURF-EXCEL-1KG', 'Surf Excel 1kg', 'surf excel 1kg surf excel easy wash surf powder', 'Surf Excel Easy Wash Detergent Powder 1kg', 'packet', TRUE, 112.00, 138.00, 145.00, 35.000, 10.000, 18.00, '3402', TRUE),
    ('SKU-DETTOL-125G', 'Dettol Soap 125g', 'dettol soap 125g dettol original soap dettol', 'Dettol Original Germ Protection Bathing Soap 125g', 'piece', TRUE, 46.00, 56.00, 60.00, 40.000, 12.000, 18.00, '3401', TRUE),
    ('SKU-COLGATE-200G', 'Colgate Strong Teeth 200g', 'colgate strong teeth 200g colgate toothpaste colgate', 'Colgate Strong Teeth Anticavity Toothpaste 200g', 'piece', TRUE, 94.00, 115.00, 124.00, 30.000, 8.000, 18.00, '3306', TRUE);

-- Seed initial seed customers for khata credit testing
INSERT INTO customers (name, normalized_name, phone, current_credit_balance)
VALUES
    ('Ramesh Kumar', 'ramesh kumar ramesh', '+91 98450 11223', 0.00),
    ('Suresh Patel', 'suresh patel suresh', '+91 98450 44556', 250.00),
    ('Priya Sharma', 'priya sharma priya', '+91 98450 77889', 0.00);

-- Initial default owner preferences
INSERT INTO owner_preferences (pref_key, pref_value)
VALUES
    ('default_payment_mode', 'UPI'),
    ('default_atta', 'Aashirvaad Atta 5kg'),
    ('store_name', 'Sri Lakshmi Supermarket'),
    ('store_gstin', '29AAAPL1234C1ZV'),
    ('store_phone', '+91 98765 43210');
