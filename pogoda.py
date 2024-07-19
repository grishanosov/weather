import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# Определение общих заголовков
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
    'Accept-Language': 'ru-RU,ru;q=0.9',
    'Referer': 'https://www.gismeteo.ru/'
}

def make_request(url):
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return BeautifulSoup(response.text, 'html.parser')
    else:
        return f"Failed to fetch data: {response.status_code}"

def fetch_detailed_weather_data(url):
    soup = make_request(url)
    if isinstance(soup, str):
        return soup
    
    # Извлечение данных о погоде
    data = {
        "times": [time.text for time in soup.select('.widget-row-datetime-time .row-item span')],
        "weather_conditions": [row['data-tooltip'] for row in soup.select('.widget-row-icon .row-item') if 'data-tooltip' in row.attrs],
        "temperatures": [temp['value'] for temp in soup.select('.widget-row-chart-temperature-air .value temperature-value')],
        "humidities": [int(humidity.text.strip('%')) for humidity in soup.select('.widget-row-humidity .row-item')],
        "sunrise": soup.select_one('.astro-times div:nth-of-type(2)').text.split('—')[1].strip(),
        "sunset": soup.select_one('.astro-times div:nth-of-type(3)').text.split('—')[1].strip()
    }
    return data

def format_temperature(value):
    temp = int(value)
    return f'+{temp}°' if temp >= 0 else f'{temp}°'

def format_output(detailed_data):
    output = []
    tomorrow = datetime.now() + timedelta(days=1)
    output.append(f"Прогноз погоды на {tomorrow.strftime('%d.%m.%Y')}")

    # Форматирование вывода по времени дня
    time_labels = {'8:00': 'Утро', '14:00': 'День', '20:00': 'Вечер'}
    for key_time, label in time_labels.items():
        if key_time in detailed_data['times']:
            index = detailed_data['times'].index(key_time)
            output.append(f"{label}: {format_temperature(detailed_data['temperatures'][index])} {detailed_data['weather_conditions'][index]}")
    
    avg_humidity = sum(detailed_data['humidities']) / len(detailed_data['humidities'])
    output.append(f"Влажность {avg_humidity:.0f}%")
    output.append(f"Рассвет: {detailed_data['sunrise']}")
    output.append(f"Закат: {detailed_data['sunset']}")
    return "\n".join(output)

def send_telegram_message(chat_id, text, token):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    response = requests.post(url, data=payload)
    return response.json()

def fetch_simple_weather_data(urls):
    simple_weather_data = []
    for url in urls:
        soup = make_request(url)
        if isinstance(soup, str):
            continue
        
        weather_tabs = soup.find_all('div', class_='weathertab')
        for tab in weather_tabs:
            date = tab.find('div', class_='date').text.strip()
            condition = tab.get('data-tooltip')
            max_temps = [int(temp['value']) for temp in tab.find_all('temperature-value', {'from-unit': 'c'})]
            max_temp = max(max_temps) if max_temps else None
            if max_temp is not None:
                simple_weather_data.append({
                    'date': date,
                    'max_temperature': f"+{max_temp}°",
                    'condition': condition
                })
    return simple_weather_data

# Токен вашего бота и ID чата
TOKEN = '7464681990:AAHAi3htak1tJwqqN4M39pPYHq9M0rXdcPI'  # Замените на свой токен
CHAT_ID = -867700741  # Ваш ID чата

# Получение и форматирование данных
url_detailed = 'https://www.gismeteo.ru/weather-toulouse-1880/tomorrow/'
detailed_weather_data = fetch_detailed_weather_data(url_detailed)
formatted_detailed_report = format_output(detailed_weather_data)

urls_simple = [
    'https://www.gismeteo.ru/weather-toulouse-1880/3-day/',
    'https://www.gismeteo.ru/weather-toulouse-1880/4-day/',
    'https://www.gismeteo.ru/weather-toulouse-1880/5-day/'
]
simple_weather_data = fetch_simple_weather_data(urls_simple)
formatted_simple_report = "\nПрогноз на следующие дни:\n" + "\n".join(f"{data['date']}: {data['max_temperature']} {data['condition']}" for data in simple_weather_data)

# Отправка полного отчета в одном сообщении
complete_report = f"{formatted_detailed_report}\n\n{formatted_simple_report}"
send_telegram_message(CHAT_ID, complete_report, TOKEN)
