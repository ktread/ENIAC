import re
import requests
from bs4 import BeautifulSoup
import datetime


response = requests.get('https://14ers.com/routes.php')
html = BeautifulSoup(response.text, 'html.parser')
CONVERT = {1:0,2:12,3:24,4:36,5:48,6:60,7:72,8:84,9:96,10:108}

def get_mountains():
	td = html.find_all('tr')
	mountain_data = ([row.get_text(strip=True) for row in td if row.get_text(strip=True)[:6] != 'Routes'])
	return mountain_data

def clean_mountain_data(mountain_data):
	mountain_detail = []
	reg = "(.+)(14,\d{3})(')(\d+|\*?)(.+)"
	for i in range(0, len(mountain_data)):
		match = re.match(reg,str(mountain_data[i]))
		mountain = []
		mountain.append(match.group(1))
		mountain.append(int(match.group(2).replace(',','')))
		mountain.append(int(match.group(4).replace('*','-1')))
		mountain.append(match.group(5))
		mountain_detail.append(mountain)
	return mountain_detail

def get_route_list(html):
	route_pages = set()
	for divtag in html.find_all('div', {'class': 'niceborder'}):
		for atag in divtag.find_all('a',href=True):
			if atag['href'][0:6] == 'routel':
				route_pages.add(atag['href'])
	return route_pages


def get_routes(route_pages):
	routes = set({})
	for link in route_pages:
		response = requests.get('https://14ers.com/' + link)
		html = BeautifulSoup(response.text, 'html.parser')
		table_body = html.find_all('tr')
		[routes.add(x.get_text(strip=True)) for x in table_body if x.get_text(strip=True)[:4] != 'Trip' and x.get_text(strip=True)[0:12] != 'RoutesRoutes']
	return list(routes)


def get_crowdsize():
	crowd_size = []
	response = requests.get('https://14ers.com/php14ers/peakusage.php')
	html = BeautifulSoup(response.text, 'html.parser')
	for divtag in html.find_all('table', {'class': 'MainText1'}):
		[crowd_size.append(atag.get_text(strip=True)) for atag in divtag.find_all('tr')]
	return crowd_size


def get_status():
	status = []
	response = requests.get('https://14ers.com/php14ers/peakstatus_main.php')
	html = BeautifulSoup(response.text, 'html.parser')
	for div in html.find_all('table', {'class': 'peakTable'}):
		for atag in div.find_all('a', href=True):
			mt = re.search('14ers', atag['href'])
			if mt:
				status.append(atag.get_text(strip=True))
				if len(atag.span['class']) == 1:
					status.append('No Updates')
				else:
					status.append(atag.span['class'][1])
	return status

def get_weather_urls():
	response = requests.get('https://www.14ers.com/php14ers/weather.php')
	html = BeautifulSoup(response.text, 'html.parser')
	name = "(.+)(,)( )(Mt.)"
	urls = dict({})
	for div in html.find_all('optgroup', {'label': 'Colorado 14ers'}):
		for atag in div.find_all('option'):
			url = 'https://www.14ers.com/php14ers/ajax_weather1.php?' + atag['value']
			match = re.search(name, str(atag.text))
			if match:
					mtn_name = re.search(name, str(atag.text)).group(4) + ' ' + re.search(name, str(atag.text)).group(1)
			else:
					mtn_name = atag.text
			urls[mtn_name] = url
	return urls


def get_mountain_weather():
	mtn_url = get_weather_urls()
	reg = "(.+)(:)( \d+)(°F)(\d+-?\d+)(mph)(.+)"
	all_weather = []
	for mtn_name,url in mtn_url.items():
		response = requests.get(url)
		html = BeautifulSoup(response.text, 'html.parser')
		weather = [mtn_name]
		for divtag in html.find_all('table', {'class': 'forecastDays'}):
			for atag in divtag.find_all('td'):
				weather.append(atag.get_text(strip=True))
		all_weather.append(weather)
	return all_weather


def mountain_weather(all_weather):
	weather_data = {}
	for mtn in all_weather:
		weather_data.update(clean_weather(mtn))
	return weather_data


def clean_weather(eachmtn):
	ind = 0
	dttmp = []
	full_weather = {}
	for item in eachmtn:
		full_string = re.search("(.+:) (\d+)°F(\d+)-?(\d+)?(mph)(.+)",item)
		day = re.search("(.+:)",item)
		if day:
			today = datetime.date.today()
			j = datetime.datetime(today.year, today.month, today.day)
			degree = full_string.group(2)
			windslow = full_string.group(3)
			windshigh = full_string.group(4) if full_string.group(4) else full_string.group(3)
			desc = full_string.group(6)
			wdate = (j + datetime.timedelta(hours=CONVERT[ind])).strftime('%m-%d-%Y %H:%M:%S')
			dttmp.append((wdate,degree, windslow, windshigh, desc))
		ind = ind+1
	full_weather[eachmtn[0]] =tuple(dttmp)
	return full_weather


class Mountain():

	def __init__(self, name, elevation):
		self.name = name
		self.elevation = elevation

	def __repr__(self):
		return self.name + ':' + self.elevation


def call_data():
	raw_mountain = get_mountains()
	clean_mountain_data(raw_mountain)
	route_pages = get_route_list(html)
	routes = get_routes(route_pages)
	crowdsize = get_crowdsize()
	status = get_status()
	all_weather = get_mountain_weather()
	weather_data = mountain_weather(all_weather)
	print('ROUTES: ',routes)
	print('--'*50)
	print('CROWD SIZE: ', crowdsize)
	print('--'*50)
	print('STATUS: ', status)
	print('--'*50)
	print('WEATHER DATA: ' ,weather_data)
	print('--'*50)


call_data()

# if __name__ == '__main__':