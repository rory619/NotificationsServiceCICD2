import json
import os
RABBIT_URL = os.getenv("RABBIT_URL")
EXCHANGE_NAME = "events_topic"

async def main():
    conn = await aio_pika.connect_robust(RABBIT_URL)
    ch = await conn.channel()

    ex = await ch.declare_exchange(EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC)

    queue = await ch.declare_queue("payment_events_queue")

    await queue.bind(ex, routing_key="payment.#")

    print("Listening for payment events (routing key: 'payment.#')...")

    async with queue.iterator() as q:
        async for msg in q:
            async with msg.process():
                data = json.loads(msg.body)
                print("Payment Event:", msg.routing_key, data)

if __name__ == "__main__":
    asyncio.run(main())