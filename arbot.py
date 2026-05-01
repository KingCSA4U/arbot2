import ccxt.pro as ccxt  # Use the async-supported version
import logging
from dotenv import load_dotenv

load_dotenv()


class ARbot:
    FEE = 0.0005
    PROFIT_THRESHOLD_PCT = 0.2

    @classmethod
    async def create(cls, key: str, secret: str) -> "ARbot":
        self = cls.__new__(cls)
        self.exchange = ccxt.mexc(
            {
                "apiKey": key,
                "secret": secret,
                "enableRateLimit": True,
                "options": {
                    "adjustForTimeDifference": True,
                    "fetchMarkets": ["spot"],
                },
                "timeout": 30000,
            }
        )

        logging.basicConfig(
            filename="main.log",
            filemode="a",
            format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            level=logging.INFO,
        )
        self.logger = logging.getLogger("ARbot")
        self.markets = await self.exchange.load_markets()
        await self.exchange.load_time_difference()
        self.tickers = {}
        # self.symbols = []
        balance = await self.get_balance()
        self.logger.info("BOT initialised")
        self.logger.info(f"Starting balance: {balance} USDT")
        return self

    # ------------------------------------------------------------------
    # Market helpers
    # ------------------------------------------------------------------

    async def get_balance(self) -> float:
        balance = await self.exchange.fetch_balance()
        return balance["free"].get("USDT", 0.0)

    # async def run_loop(self):
    #     """Fetch all tickers and cache them. Returns True on success."""
    #     while True:
    #         try:
    #             new_tickers = await self.exchange.watch_tickers(self.symbols)
    #             self.tickers.update(new_tickers)
    #             return True
    #         except Exception as e:
    #             self.logger.exception("Error fetching tickers: %s", e)
    #             # return False

    # ------------------------------------------------------------------
    # Path generation
    # ------------------------------------------------------------------

    async def generate_triangular_paths(self, coins: list[str], base: str) -> tuple[list[dict], list[str]]:
            paths = []
            symbols = set()

            for a in coins:
                for b in coins:
                    if a == b:
                        continue

                    pair1 = f"{a}/{base}"  # BUY a with base   (ask)
                    pair2 = f"{a}/{b}"  # SELL a for b       (bid)
                    pair2b = f"{b}/{a}"  # SELL b for a       (bid)
                    pair3 = f"{b}/{base}"  # SELL b for base    (bid)
                    pair3b = f"{b}/{base}"  # SELL b for base    (bid)

                    if (
                        pair1 in self.markets
                        and pair2 in self.markets
                        and pair3 in self.markets
                    ):
                        paths.append(
                            {
                                "legs": (pair1, pair2, pair3),
                                "directions": ("buy", "sell", "sell"),
                            })
                        symbols.update([pair1, pair2, pair3])
                    elif (
                        pair1 in self.markets
                        and pair2b in self.markets
                        and pair3b in self.markets
                    ):
                        paths.append(
                            {
                                "legs": (pair1, pair2b, pair3b),
                                "directions": ("buy", "sell", "sell"),
                            }
                        )
                        symbols.update([pair1, pair2b, pair3b])


            self.logger.info(f"{len(paths)} triangular paths and {len(symbols)} symbols generated")
            return paths,list(symbols)
    # ------------------------------------------------------------------
    # Opportunity detection
    # ------------------------------------------------------------------

    def _leg_rate(self, symbol: str, direction: str) -> float | None:
        """
        Return the effective exchange rate for one leg.
        buying  → we pay the ask  → rate = 1 / ask  (base units per quote)
        selling → we receive bid  → rate = bid
        """
        ticker = self.tickers.get(symbol)
        if not ticker:
            return None

        if direction == "buy":
            price = ticker.get("ask")
            if not price:
                return None
            return 1.0 / price
        else:  # sell
            price = ticker.get("bid")
            if not price:
                return None
            return price

    async def opportunity_checker(self, paths: list[dict], base: str) -> list[dict]:
        # if not await self.update_tickers():
        #     return []

        opportunities = []

        for path in paths:
            legs = path["legs"]
            directions = path["directions"]

            # Skip if any symbol is missing from tickers
            if any(sym not in self.tickers for sym in legs):
                continue

            amount = 1.0
            valid = True
            for symbol, direction in zip(legs, directions):
                rate = self._leg_rate(symbol, direction)
                if rate is None:
                    valid = False
                    break
                amount *= rate * (1 - self.FEE)

            if not valid:
                continue

            profit_pct = (amount - 1.0) * 100

            print(f"\n--- {legs[0]} -> {legs[1]} -> {legs[2]} ---")
            print(f"directions: {directions}")
            for symbol, direction in zip(legs, directions):
                ticker = self.tickers.get(symbol, {})
                ask = ticker.get("ask")
                bid = ticker.get("bid")
                rate = self._leg_rate(symbol, direction)
                print(f"  {symbol} [{direction}] | ask={ask} bid={bid} | rate={rate}")
            print(f"  final={amount:.8f} | profit={profit_pct:.4f}%")

            if profit_pct > self.PROFIT_THRESHOLD_PCT:
                path_str = "->".join(legs)
                self.logger.info(f"{path_str} | Profit: {profit_pct:.4f}%")
                opportunities.append(
                    {
                        "path": legs,
                        "directions": directions,
                        "profit_pct": profit_pct,
                        "final_ratio": amount,
                    }
                )

        return sorted(opportunities, key=lambda o: o["profit_pct"], reverse=True)

    # ------------------------------------------------------------------
    # Execution (scaffold — fill in once you're ready to go live)
    # ------------------------------------------------------------------

    async def execute_cycle(self, opportunities: list[dict]) -> None:
        """
        Execute the best opportunity found.
        Currently a dry-run scaffold — log only, no real orders.
        """
        if not opportunities:
            return

        best = opportunities[0]
        path_str = "->".join(best["path"])
        self.logger.info(
            f"[DRY RUN] Would execute: {path_str} | "
            f"Profit: {best['profit_pct']:.4f}%"
        )
        # TODO:
        # balance = self.get_balance()
        # trade_amount = balance * 0.95   # leave some buffer
        # place limit/market orders for each leg in sequence
        # handle partial fills, timeouts, and rollback
