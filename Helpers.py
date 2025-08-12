import re

def remove_country_flags(pair):
    """
    Удаляет эмодзи флагов стран из строки валютной пары.
    """
    emoji_pattern = re.compile(r"[\U0001F1E6-\U0001F1FF\s]+")  # Соответствует эмодзи флагов стран и пробелам
    return emoji_pattern.sub("", pair).strip()

def format_indicators(indicators):
    """
    Форматирует объект индикаторов в удобочитаемую строку с эмодзи и табуляцией.
    """
    lines = []

    # Основной заголовок
    lines.append("📊 **Анализ Индикаторов**\n")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━")

    # Добавление отдельных индикаторов
    if 'RSI' in indicators:
        lines.append(f"📈 **RSI**: {indicators['RSI']:.2f} 🎯")

    if 'EMA' in indicators:
        lines.append(f"📊 **EMA**: {indicators['EMA']:.5f}")

    if 'MACD' in indicators:
        lines.append("📊 **MACD**:")
        lines.append(f"   ├─ MACD: {indicators['MACD']['MACD']:.5f}")
        lines.append(f"   └─ Сигнал: {indicators['MACD']['Signal']:.5f}")

    if 'Bollinger Bands' in indicators:
        bb = indicators['Bollinger Bands']
        lines.append("📊 **Полосы Боллинджера**:")
        lines.append(f"   ├─ Верхняя Полоса: {bb['Upper Band']:.5f}")
        lines.append(f"   ├─ Нижняя Полоса: {bb['Lower Band']:.5f}")
        lines.append(f"   └─ Средняя Полоса: {bb['Middle Band']:.5f}")

    if 'Stochastic Oscillator' in indicators:
        so = indicators['Stochastic Oscillator']
        lines.append("📊 **Стохастический Осциллятор**:")
        lines.append(f"   ├─ %K: {so['%K']:.2f}")
        lines.append(f"   └─ %D: {so['%D']:.2f}")

    if 'Support and Resistance' in indicators:
        sr = indicators['Support and Resistance']
        lines.append("📊 **Уровни Поддержки и Сопротивления**:")
        lines.append(f"   ├─ Поддержка: {sr['Support']:.5f}")
        lines.append(f"   └─ Сопротивление: {sr['Resistance']:.5f}")

    if 'Keltner Channels' in indicators:
        kc = indicators['Keltner Channels']
        lines.append("📊 **Каналы Келтнера**:")
        lines.append(f"   ├─ Верхняя Полоса: {kc['Upper Band']:.5f}")
        lines.append(f"   ├─ Нижняя Полоса: {kc['Lower Band']:.5f}")
        lines.append(f"   └─ Средняя Линия: {kc['Middle Line']:.5f}")

    if 'Parabolic SAR' in indicators:
        lines.append(f"📊 **Параболический SAR**: {indicators['Parabolic SAR']:.5f}")

    if 'Fibonacci Retracement' in indicators:
        fr = indicators['Fibonacci Retracement']
        lines.append("📊 **Уровни Фибоначчи**:")
        for level, value in fr.items():
            lines.append(f"   └─ {level}: {value:.5f}")

    # Финальный разделитель
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━")

    # Объединение строк в форматированную строку
    return "\n".join(lines)

def format_summary(summary):
    """
    Форматирует объект сводки в удобочитаемую строку с эмодзи и табуляцией.
    """
    lines = []

    # Основной заголовок
    lines.append("📊 **Сводка**\n")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━")

    # Добавление деталей сводки
    if 'Open' in summary:
        lines.append(f"📈 **Открытие**: {summary['Open']:.5f}")
    if 'High' in summary:
        lines.append(f"📈 **Максимум**: {summary['High']:.5f}")
    if 'Low' in summary:
        lines.append(f"📉 **Минимум**: {summary['Low']:.5f}")
    if 'Close' in summary:
        lines.append(f"📉 **Закрытие**: {summary['Close']:.5f}")
    if 'Volume' in summary:
        lines.append(f"📊 **Объем**: {summary['Volume']}")
    if 'Start Time' in summary:
        lines.append(f"⏲️ **Начальное Время**: {summary['Start Time']}")
    if 'End Time' in summary:
        lines.append(f"⏲️ **Конечное Время**: {summary['End Time']}")
    if 'Top Value Time' in summary:
        lines.append(f"⭐ **Время Максимального Значения**: {summary['Top Value Time']}")
    if 'Bottom Value Time' in summary:
        lines.append(f"⭐ **Время Минимального Значения**: {summary['Bottom Value Time']}")

    # Финальный разделитель
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━")

    # Объединение строк в форматированную строку
    return "\n".join(lines)

def print_indicators(results):
    """
    Выводит индикаторы и сводку.
    """
    if not results:
        print("Нет результатов для отображения.")
        return

    print("\n📊 **Сводка**:")
    for key, value in results["Summary"].items():
        print(f"{key}: {value}")

    print("\n📊 **Индикаторы**:")
    for indicator, value in results["Indicators"].items():
        print(f"{indicator}: {value}")
