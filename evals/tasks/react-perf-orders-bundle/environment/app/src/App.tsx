import { OrdersPage } from "./orders/OrdersPage";
import { SAMPLE_ORDERS } from "./orders/sampleOrders";

export function App() {
  return <OrdersPage initialOrders={SAMPLE_ORDERS} />;
}
