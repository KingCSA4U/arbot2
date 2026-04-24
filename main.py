import os
import asyncio
from arbot import ARbot

COINS = ["BTC", "ETH", "SOL", "DOGE", "TON", "XRP", "BNB", "SUI"]
BASE = "USDT"
POLL_INTERVAL = 0.5
MAX_BACKOFF_SECONDS = 8.0


async def main() -> None:
    api_key = os.getenv("API_KEY")
    api_secret = os.getenv("API_SECRET")
    if not api_key or not api_secret:
        raise RuntimeError("Missing API_KEY or API_SECRET in environment.")

    bot = None
    consecutive_failures = 0

    try:
        bot = await ARbot.create(api_key, api_secret)
        paths = await bot.generate_triangular_paths(COINS, BASE)
        print(f"Monitoring {len(paths)} paths. Press Ctrl+C to stop.\n")

        while True:
            try:
                opps = await bot.opportunity_checker(paths, BASE)
                consecutive_failures = 0

                if opps:
                    for opp in opps:
                        path_str = "->".join(opp["path"])
                        print(f"  {path_str} | {opp['profit_pct']:.4f}%")
                    await bot.execute_cycle(opps)
                else:
                    print("No opportunities found.")

                await asyncio.sleep(POLL_INTERVAL)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                consecutive_failures += 1
                backoff = min(POLL_INTERVAL * (2 ** consecutive_failures), MAX_BACKOFF_SECONDS)
                print(
                    f"Loop error: {exc}. "
                    f"Retrying in {backoff:.1f}s (failure #{consecutive_failures})."
                )
                if bot is not None:
                    bot.logger.exception("Main loop error")
                await asyncio.sleep(backoff)

    except KeyboardInterrupt:
        print("\nShutting down gracefully.")
        if bot is not None:
            bot.logger.info("BOT shut down by user")
    except asyncio.CancelledError:
        print("\nAsync task cancelled. Shutting down gracefully.")
        if bot is not None:
            bot.logger.info("BOT cancelled")
    finally:
        if bot is not None:
            print("\nReleasing MEXC resources...")
            bot.logger.info("Releasing MEXC resources")
            await bot.exchange.close()


if __name__ == "__main__":
    # asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
