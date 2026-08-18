# variables & arithmetic
item_name = "server unit"
quantity = 4
unit_cost = 450.00
tax_rate = 0.0825
subtotal = quantity * unit_cost
total = subtotal * (1 + tax_rate)

#formatted string (f-string)
print(f"order: {quantity} x {item_name}")
print(f"subtotal: ${subtotal:,.2f}")
print(f"Subtotal: ${subtotal:,.2f}")
print(f"final Total with Tax: ${total:,.2f}")
