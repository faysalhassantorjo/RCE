class ProductCategory:
    def __init__(self, name):
        self.name = name
        self.subcategories = []

    def add_subcategory(self, subcategory):
        self.subcategories.append(subcategory)

    def __repr__(self, level=0):
        ret = "\t" * level + repr(self.name) + "\n"
        for subcategory in self.subcategories:
            ret += subcategory.__repr__(level + 1)
        return ret
def build_product_category_tree():
    # Root category
    root = ProductCategory("All Products")

    # First level categories
    electronics = ProductCategory("Electronics")
    clothing = ProductCategory("Clothing")
    furniture = ProductCategory("Furniture")

    root.add_subcategory(electronics)
    root.add_subcategory(clothing)
    root.add_subcategory(furniture)

    # Subcategories for Electronics
    phones = ProductCategory("Phones")
    laptops = ProductCategory("Laptops")
    electronics.add_subcategory(phones)
    electronics.add_subcategory(laptops)

    # Subcategories for Phones
    smartphones = ProductCategory("Smartphones")
    landline_phones = ProductCategory("Landline Phones")
    phones.add_subcategory(smartphones)
    phones.add_subcategory(landline_phones)

    # Subcategories for Clothing
    mens_clothing = ProductCategory("Men's Clothing")
    womens_clothing = ProductCategory("Women's Clothing")
    clothing.add_subcategory(mens_clothing)
    clothing.add_subcategory(womens_clothing)

    # Subcategories for Furniture
    living_room = ProductCategory("Living Room Furniture")
    bedroom = ProductCategory("Bedroom Furniture")
    furniture.add_subcategory(living_room)
    furniture.add_subcategory(bedroom)

    return root
  
def dfs_product_category(root):
    print(root.name)
    for subcategory in root.subcategories:
        dfs_product_category(subcategory)


root = build_product_category_tree()


#something

print("Product Category Tree Structure:")
print(root)

print("\nDepth First Search (DFS) Traversal:")
dfs_product_category(root)