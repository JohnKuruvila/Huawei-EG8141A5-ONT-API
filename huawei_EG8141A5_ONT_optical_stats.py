import requests
import time
import csv

token = requests.post("http://192.168.18.1/asp/GetRandCount.asp").text[3:]

data = {"UserName" : "",
        "PassWord" : "", '''Hashed password. You can get it by checking network tab in developer options while logging in to the router page'''
        "Language" : "english",
        "x.X_HW_Token" : str(token) }

cookies = {"Cookie" : "body:Language:english:id=-1" }

cookie = str(requests.post("http://192.168.18.1/login.cgi", data = data, cookies = cookies).headers).split("Cookie=")[1].split(";")[0]

cookies = {"Cookie" : str(cookie) }

optic_info = requests.get("http://192.168.18.1/html/amp/opticinfo/opticinfo.asp", cookies = cookies).text

value_types = optic_info.split("stOpticInfo(")[2].split(")")[0]
values = optic_info.split("stOpticInfo(")[3].split(")")[0]

dict_values = {}

for i in range(len(values.split(","))):
    dict_values[str(value_types.split(",")[i])] = str(values.split(",")[i].encode("utf-8").decode("unicode-escape")).replace('"','')

data = { "RequestFile" : "html/logout.html" }

requests.post("http://192.168.18.1/logout.cgi?RequestFile=html/logout.html", data = data, cookies = cookies)
requests.get("http://192.168.18.1/html/logout.html", cookies = cookies)

file = open("router_stats.csv","a", newline = "")
writer = csv.writer(file)
writer.writerow([str(int(time.time())),dict_values["transOpticPower"],dict_values["revOpticPower"],dict_values["voltage"],dict_values["temperature"],dict_values["bias"],dict_values[" LosStatus"]])
file.close()
