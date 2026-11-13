export type OrderLine = { id: string; description: string; amountPence: number };

export type Order = { number: string; lines: OrderLine[] };
