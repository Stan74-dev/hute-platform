import React, { useEffect, useState } from "react";
import axios from "axios";

const API = "http://127.0.0.1:8000/api";

function App() {
  const [products, setProducts] = useState([]);
  const [cart, setCart] = useState([]);

  useEffect(() => {
    axios.get(`${API}/inventory/warehouse-products/1/`)
      .then(res => setProducts(res.data));
  }, []);

  const add = (p) => {
    setCart([...cart, { ...p, quantity: 1 }]);
  };

  const checkout = async () => {
    const res = await axios.post(`${API}/sales/checkout/`, {
      cart,
      warehouse_id: 1
    });

    alert(`Total £${res.data.total}`);
    setCart([]);
  };

  return (
    <div>
      <h1>HUTE POS</h1>

      {products.map(p => (
        <button key={p.id} onClick={() => add(p)}>
          {p.name} £{p.selling_price}
        </button>
      ))}

      <h2>Cart</h2>
      {cart.map((c, i) => (
        <div key={i}>{c.name}</div>
      ))}

      <button onClick={checkout}>Checkout</button>
    </div>
  );
}

export default App;