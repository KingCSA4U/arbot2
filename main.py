import os
import asyncio
from arbot import ARbot

COINS = ["BTC", "ETH", "SOL", "DOGE", "TON", "XRP", "BNB", "SUI"]
BASE = "USDT"
POLL_INTERVAL = 0.5


async def main() -> None:
    bot = await ARbot.create(os.getenv("API_KEY"), os.getenv("API_SECRET"))
    paths = bot.generate_triangular_paths(COINS, BASE)

    print(f"Monitoring {len(paths)} paths. Press Ctrl+C to stop.\n")

    try:
        while True:
            opps = await bot.opportunity_checker(paths, BASE)

            if opps:
                for opp in opps:
                    path_str = "->".join(opp["path"])
                    print(f"  {path_str} | {opp['profit_pct']:.4f}%")
                await bot.execute_cycle(opps)
            else:
                print("No opportunities found.")

            await asyncio.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        print("\nShutting down gracefully.")
        bot.logger.info("BOT shut down by user")
        await bot.exchange.close()


if __name__ == "__main__":
    asyncio.run(main())
