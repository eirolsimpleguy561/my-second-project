import asyncio
import random
import time


async def producer(queue: asyncio.Queue, sensor_id: int, total: int):
    """Simulates a sensor generating data."""
    for i in range(total):
        value = round(random.uniform(20.0, 80.0), 2)
        timestamp = time.strftime("%H:%M:%S")
        item = {"sensor": sensor_id, "value": value, "time": timestamp}
        await queue.put(item)
        await asyncio.sleep(random.uniform(0.1, 0.5))
    await queue.put(None)  # Sentinel to signal done


async def consumer(queue: asyncio.Queue, results: list):
    """Processes data from the queue."""
    while True:
        item = await queue.get()
        if item is None:
            queue.task_done()
            break
        processed = {**item, "normalized": round(item["value"] / 100, 4)}
        results.append(processed)
        print(f"[{processed['time']}] Sensor {processed['sensor']}: "
              f"{processed['value']} -> {processed['normalized']}")
        queue.task_done()


async def main():
    queue = asyncio.Queue(maxsize=50)
    results = []
    num_sensors = 3
    readings_each = 5

    producers = [asyncio.create_task(producer(queue, i+1, readings_each))
                 for i in range(num_sensors)]
    consumers = [asyncio.create_task(consumer(queue, results))
                 for _ in range(num_sensors)]

    await asyncio.gather(*producers)
    await queue.join()
    for c in consumers:
        c.cancel()

    values = [r["value"] for r in results]
    print(f"\nProcessed {len(results)} readings.")
    print(f"Average: {sum(values)/len(values):.2f}")
    print(f"Min: {min(values)} | Max: {max(values)}")


if __name__ == "__main__":
    asyncio.run(main())
