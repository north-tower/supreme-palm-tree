import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
from datetime import datetime
from matplotlib import rcParams

# Configure matplotlib to use a font with better Unicode support
rcParams["font.family"] = "DejaVu Sans"

class TradingChartPlotter:
    def __init__(self, history_data, currency_pair, time_frame):
        self.history_df = pd.DataFrame(history_data, columns=["Время", "Значение"])
        self.currency_pair = currency_pair
        self.time_frame = time_frame

    def filter_recent_data(self):
        try:
            if not self.history_df.empty:
                self.history_df["Время"] = pd.to_datetime(self.history_df["Время"], unit='s')
        except Exception as e:
            print(f"Ошибка фильтрации данных: {e}")

    def plot_trading_chart(self, outlier_threshold=1.5):
        try:
            self.filter_recent_data()

            if self.history_df.empty:
                print("Нет данных для построения графика.")
                return None

            mean_value = self.history_df["Значение"].mean()
            std_dev = self.history_df["Значение"].std()
            upper_bound = mean_value + outlier_threshold * std_dev
            lower_bound = mean_value - outlier_threshold * std_dev

            self.history_df["Выброс"] = (self.history_df["Значение"] > upper_bound) | (self.history_df["Значение"] < lower_bound)

            # Set the background and line styles
            plt.figure(figsize=(12, 6))
            plt.style.use('dark_background')  # Dark background style

            plt.plot(self.history_df["Время"], self.history_df["Значение"], label="Значение", color="#00BFFF", alpha=0.8)
            outliers = self.history_df[self.history_df["Выброс"]]
            plt.scatter(outliers["Время"], outliers["Значение"], color="red", label="Выбросы", zorder=5)

            # Add average and boundaries
            plt.axhline(mean_value, color="green", linestyle="--", label="Среднее", linewidth=2)
            plt.axhline(upper_bound, color="orange", linestyle="--", label="Верхняя граница", linewidth=2)
            plt.axhline(lower_bound, color="orange", linestyle="--", label="Нижняя граница", linewidth=2)

            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            plt.title(f"График торгов для {self.currency_pair} ({self.time_frame})\nСоздано {current_time}", fontsize=16, color="white")
            plt.xlabel("Время", fontsize=12, color="white")
            plt.ylabel("Значение", fontsize=12, color="white")

            plt.legend(loc="upper left", fontsize=10)
            plt.grid(alpha=0.3)
            plt.tight_layout()

            # Save to BytesIO
            image_data = io.BytesIO()
            plt.savefig(image_data, format="png", dpi=300)
            image_data.seek(0)
            plt.close()

            return image_data

        except Exception as e:
            print(f"Ошибка построения графика: {e}")
            return None


# import pandas as pd
# import numpy as np
# import matplotlib.pyplot as plt
# import io
# from datetime import datetime

# class TradingChartPlotter:
#     def __init__(self, history_data, currency_pair, time_frame):
#         """
#         Initializes the TradingChartPlotter with history data, currency pair, and time frame.

#         Parameters:
#         - history_data: List of [timestamp, value] data points.
#         - currency_pair: Name of the currency pair (e.g., "EUR/USD").
#         - time_frame: Time frame of the data (e.g., "5 minutes").
#         """
#         self.history_df = pd.DataFrame(history_data, columns=["Timestamp", "Value"])
#         self.currency_pair = currency_pair
#         self.time_frame = time_frame

#     def filter_recent_data(self):
#         """Filters the data to include only the most recent values."""
#         try:
#             if not self.history_df.empty:
#                 self.history_df["Timestamp"] = pd.to_datetime(self.history_df["Timestamp"], unit='s')
#         except Exception as e:
#             print(f"Error filtering recent data: {e}")

#     def plot_trading_chart(self, outlier_threshold=1.5):
#         """
#         Plots a trading chart with timestamp on the x-axis and value on the y-axis,
#         highlights outliers, and returns the image data.

#         Parameters:
#         - outlier_threshold: Multiplier for standard deviation to detect outliers.

#         Returns:
#         - BytesIO object containing the image data.
#         """
#         try:
#             self.filter_recent_data()

#             if self.history_df.empty:
#                 print("No data to plot.")
#                 return None

#             # Identify outliers
#             mean_value = self.history_df["Value"].mean()
#             std_dev = self.history_df["Value"].std()
#             upper_bound = mean_value + outlier_threshold * std_dev
#             lower_bound = mean_value - outlier_threshold * std_dev

#             self.history_df["Outlier"] = (self.history_df["Value"] > upper_bound) | (self.history_df["Value"] < lower_bound)

#             # Plot the trading chart
#             plt.figure(figsize=(12, 6))
#             plt.plot(self.history_df["Timestamp"], self.history_df["Value"], label="Value", color="blue", alpha=0.7)
            
#             # Highlight outliers
#             outliers = self.history_df[self.history_df["Outlier"]]
#             plt.scatter(outliers["Timestamp"], outliers["Value"], color="red", label="Outliers", zorder=5)

#             # Add mean and bounds as horizontal lines
#             plt.axhline(mean_value, color="green", linestyle="--", label="Mean")
#             plt.axhline(upper_bound, color="orange", linestyle="--", label="Upper Bound")
#             plt.axhline(lower_bound, color="orange", linestyle="--", label="Lower Bound")

#             # Customize the chart
#             current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#             plt.title(
#                 f"Trading Chart for {self.currency_pair} ({self.time_frame})\nGenerated at {current_time}",
#                 fontsize=16
#             )
#             plt.xlabel("Timestamp", fontsize=12)
#             plt.ylabel("Value", fontsize=12)
#             plt.legend(loc="upper left", fontsize=10)
#             plt.grid(alpha=0.3)
#             plt.tight_layout()

#             # Save the plot to a BytesIO object
#             image_data = io.BytesIO()
#             plt.savefig(image_data, format="png")
#             image_data.seek(0)

#             plt.close()

#             return image_data

#         except Exception as e:
#             print(f"Error plotting trading chart: {e}")
#             return None
