    async def __init__(self, key: str, secret: str):

        
        self.logger = logging.getLogger("ARbot")

        self.markets = await self.exchange.load_markets()
        self.tickers: dict = {}

        balance = await self.get_balance()
        self.logger.info(f"Starting balance: {balance} USDT")
