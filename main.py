import os
import asyncio
from arbot import ARbot

COINS = ["BTC", "ETH", "SOL", "DOGE", "TON", "XRP", "BNB", "SUI"]
BASE = "USDT"
POLL_INTERVAL = 0.5


async def main() -> None:
    bot = await ARbot.create(os.getenv("API_KEY"), os.getenv("API_SECRET"))
    paths = await bot.generate_triangular_paths(COINS, BASE)

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

    except asyncio.CancelledError:
        print("\nShutting down gracefully.")
        bot.logger.info("BOT shut down by user")
    finally:
        print("\nReleasing MEXC resources...")
        bot.logger.info("Realeasing MEXC resources")
        await bot.exchange.close()


if __name__ == "__main__":
    # asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
