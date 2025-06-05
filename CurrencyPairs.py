class CurrencyPairs:
    def __init__(self):
        # Map of country codes to flag emojis
        self.country_flags = {
            "AED": "🇦🇪", "CNY": "🇨🇳", "AUD": "🇦🇺", "USD": "🇺🇸", "BHD": "🇧🇭", 
            "CAD": "🇨🇦", "JPY": "🇯🇵", "EUR": "🇪🇺", "NZD": "🇳🇿", "GBP": "🇬🇧", 
            "OMR": "🇴🇲", "SAR": "🇸🇦", "ARS": "🇦🇷", "BRL": "🇧🇷", "DZD": "🇩🇿", 
            "RUB": "🇷🇺", "VND": "🇻🇳", "SGD": "🇸🇬", "CHF": "🇨🇭", "TRY": "🇹🇷", 
            "PKR": "🇵🇰", "INR": "🇮🇳", "THB": "🇹🇭", "MXN": "🇲🇽", "HKD": "🇭🇰", 
            "CLP": "🇨🇱", "COP": "🇨🇴", "HUF": "🇭🇺", "JOD": "🇯🇴", "MAD": "🇲🇦", 
            "QAR": "🇶🇦", "TND": "🇹🇳", "BDT": "🇧🇩", "EGP": "🇪🇬", "IDR": "🇮🇩", 
            "MYR": "🇲🇾", "PHP": "🇵🇭"
        }

        # Currency pairs for OTC and Regular Assets
        self.otc_pairs = [
            "AED/CNY OTC", "AUD/USD OTC", "BHD/CNY OTC", "CAD/JPY OTC", "EUR/JPY OTC",
            "EUR/NZD OTC", "EUR/USD OTC", "GBP/USD OTC", "NZD/USD OTC", "OMR/CNY OTC",
            "SAR/CNY OTC", "USD/ARS OTC", "USD/BRL OTC", "USD/DZD OTC", "USD/JPY OTC",
            "USD/RUB OTC", "USD/VND OTC", "USD/SGD OTC", "AUD/CHF OTC", "AUD/CAD OTC",
            "USD/THB OTC", "USD/MXN OTC", "CHF/JPY OTC", "GBP/AUD OTC", "USD/PKR OTC",
            "USD/CAD OTC", "EUR/TRY OTC", "AUD/NZD OTC", "USD/INR OTC", 
            "AUD/ARS OTC", "CAD/CHF OTC", "CHF/NOK OTC", "GBP/CAD OTC", "GBP/JPY OTC",
            "JOD/USD OTC", "MAD/USD OTC", "NZD/JPY OTC", "QAR/CNY OTC", "TND/USD OTC",
            "USD/BDT OTC", "USD/CNY OTC", "USD/EGP OTC", "USD/IDR OTC", "USD/MYR OTC", "USD/PHP OTC"
        ]

        self.regular_pairs = [
            "EUR/GBP", "USD/CHF", "GBP/JPY", "AUD/JPY", "EUR/JPY", "USD/CNY",
            "USD/HKD", "AUD/USD", "NZD/USD", "GBP/USD", "USD/CAD", "EUR/USD",
            "EUR/CHF", "USD/SGD", "USD/INR", "USD/MXN", "USD/ARS", "USD/BRL",
            "USD/CLP", "USD/COP", "USD/THB", "USD/VND", "USD/DZD", "EUR/HUF"
        ]

    def add_flags(self, pairs):
        """
        Adds flag emojis to the currency pairs.
        """
        with_flags = []
        for pair in pairs:
            parts = pair.split("/")
            base = parts[0]
            quote = parts[1].split()[0]  # Handle cases like "USD/ARS OTC"
            flags = f"{self.country_flags.get(base, '')}{self.country_flags.get(quote, '')}"
            with_flags.append(f"{flags} {pair}")
        return with_flags

    async def fetch_pairs(self, asset_type):
        """
        Fetch currency pairs based on the asset type.
        :param asset_type: "otc" or "regular_assets"
        :return: List of currency pairs with flags for the given asset type.
        """
        if asset_type == "otc":
            return self.add_flags(self.otc_pairs)
        elif asset_type == "regular_assets":
            return self.add_flags(self.regular_pairs)
        return []
