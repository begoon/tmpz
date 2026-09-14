// Shared state across islands.
//
// Each island is its own hydration root, so a value passed to two islands would normally be
// serialised twice and become two separate copies. Marking the class with a `wire` codec tells
// ogygia how to (de)serialise it, and every island that receives the same instance shares ONE
// live copy in the browser. Mutate it in one island and the other repaints.
export class Cart {
	items = $state<string[]>([]);

	get count() {
		return this.items.length;
	}

	add(item: string) {
		this.items.push(item);
	}

	clear() {
		this.items = [];
	}

	static wire = import.meta.og.wire<Cart, string[]>({
		encode: (cart) => $state.snapshot(cart.items),
		decode: (items) => {
			const cart = new Cart();
			cart.items = items;
			return cart;
		}
	});
}
