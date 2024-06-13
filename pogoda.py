import requests
from bs4 import BeautifulSoup

def send_telegram_message(chat_id, text, token):
    """Функция для отправки сообщений в Telegram."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    response = requests.post(url, data=payload)
    return response.json()

def get_weather_data(url, headers, token):
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Извлечение всех данных
    data = {
        'times': [tag.text for tag in soup.select('.widget-row-time span')],
        'weather_conditions': [tag['data-text'] for tag in soup.select('.widget-row-icon .weather-icon.tooltip')],
        'temperatures': [tag.text for tag in soup.select('.widget-row-chart[data-row="temperature-air"] .unit_temperature_c')],
        'feels_like_temperatures': [tag.text for tag in soup.select('.widget-row-chart[data-row="temperature-heat-index"] .unit_temperature_c')],
        'gusts': [tag.text.strip() for tag in soup.select('.widget-row-wind-gust .unit_wind_m_s')],
        'pressure': [tag.text.strip() for tag in soup.select('.widget-row-chart[data-row="pressure"] .unit_pressure_mm_hg')],
        'humidity': [int(tag.text.strip().replace('%', '')) for tag in soup.select('.widget-row-humidity .row-item')]
    }

    # Извлечение данных о рассвете и закате
    sunrise = soup.select_one('.astro-times div:nth-of-type(2)').text.split('— ')[1]
    sunset = soup.select_one('.astro-times div:nth-of-type(3)').text.split('— ')[1]

    # Маппинг временных интервалов к нужным заголовкам и вывод данных
    time_map = {'8:00': 'Утро', '14:00': 'День', '20:00': 'Вечер'}
    selected_humidities = []
    report_part1 = ""
    report_part2 = ""

    for i, time in enumerate(data['times']):
        if time in time_map:
            report = (f"{time_map[time]}: Погода: {data['weather_conditions'][i]}, Температура: {data['temperatures'][i+1]}°, "
                      f"Ощущается как: {data['feels_like_temperatures'][i+1]}°, Порывы: {data['gusts'][i+1]} м/с, "
                      f"Давление: {data['pressure'][i+1]} мм. рт. ст., Влажность: {data['humidity'][i]}%")
            report_part1 += report + "\n"
            selected_humidities.append(data['humidity'][i])

    # Расчет средней влажности
    average_humidity = sum(selected_humidities) / len(selected_humidities) if selected_humidities else 0

    for i, time in enumerate(data['times']):
        if time in time_map:
            temp = data['temperatures'][i+1]
            condition = data['weather_conditions'][i]
            report_part2 += f"{time_map[time]} {temp}° {condition.lower()}\n"

    report_part2 += (f"Влажность {average_humidity:.0f}%\n"
                     f"Рассвет {sunrise}\n"
                     f"Закат {sunset}\n\n")

    # Отправка отчетов в Telegram
    send_telegram_message(-867700741, report_part1.strip(), token)
    future_forecasts = fetch_weather_forecast(forecast_urls, headers, token)
    send_telegram_message(-867700741, report_part2.strip() + future_forecasts, token)

def fetch_weather_forecast(urls, headers, token):
    weekdays = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    future_forecasts = ""

    for url in urls:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Находим базовый день и сдвигаем его
        current_day = soup.select_one('.date').text.split(',')[0]
        current_index = weekdays.index(current_day)
        next_day_index = (current_index + 1) % 7
        next_day = weekdays[next_day_index]

        # Извлечение данных о времени, температуре и погодных условиях
        time_slots = soup.select('.widget-row-time span')
        temperature_values = soup.select('.widget-row-chart[data-row="temperature-air"] .unit_temperature_c')
        
        desired_time = "14:00"
        temperature_at_14 = "N/A"  # Начальное значение на случай, если нет данных в 14:00

        for i, time in enumerate(time_slots):
            if time.text == desired_time:
                temperature_at_14 = temperature_values[i+1].text
                break
        
        weather_description = soup.select_one('.weathertab.weathertab-block.tooltip')['data-text']
        future_forecasts += f"\n{next_day} {temperature_at_14}° {weather_description}"

    return future_forecasts

# Заголовки для имитации запроса от браузера
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'ru-RU,ru;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive'
}

# Токен вашего бота в Telegram
token = '7464681990:AAHAi3htak1tJwqqN4M39pPYHq9M0rXdcPI'

# URL страницы с прогнозом и страницы с прогнозами на несколько дней
url = "https://www.gismeteo.ru/weather-toulouse-1880/tomorrow/"
forecast_urls = [
    "https://www.gismeteo.ru/weather-toulouse-1880/3-day/",
    "https://www.gismeteo.ru/weather-toulouse-1880/4-day/",
    "https://www.gismeteo.ru/weather-toulouse-1880/5-day/"
]

# Вызов функции для получения и отправки данных
get_weather_data(url, headers, token)
