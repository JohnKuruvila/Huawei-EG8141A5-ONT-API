import requests
import base64


def get_elements_from_javascript_array(input_text, array_name, array_number):

    # We use this function a lot. This splits the values from a javascript array (or similar looking things like a constructor) and returns an array of the elements
    # The router web pages store a lot of important data as javascript arrays
    # input_text param is the whole text from which we want to search an array
    # array_name param is the name of the array (or function or constructor) for which we need the values
    # array_number param is the index of the array in the text. For example if an array named 'stOpticInfo' occurs twice in the text and we need the values from its second occurance, the array_number would be 2
    # Ex: input : .... arrayName(aa, bb, cc, dd, ee, ff) ....
    #    output: [aa, bb, cc, dd, ee, ff]

    array_elements = (
        input_text.split(array_name + "(")[array_number].split(")")[0].split(",")
    )

    # Cleaning up the output
    for i in range(len(array_elements)):
        array_elements[i] = (
            array_elements[i].encode("utf-8").decode("unicode-escape").replace('"', "")
        )

    return array_elements


def parse_eth_info(input_text, array_number):

    # This function sets the details about a LAN Port
    # input_text param is the eth_info page
    # array_number param is the index of the LAN Port in the input_text. For example, for LAN Port 1, the index in eth_info page will be 2, for LAN Port 2 its 3 and so on

    LANStats = get_elements_from_javascript_array(input_text, "LANStats", array_number)
    LANInfo = get_elements_from_javascript_array(input_text, "GEInfo", array_number)

    ETHStats = {}

    if LANInfo[1] == "0":
        ETHStats["Mode"] = "Half Duplex"
    elif LANInfo[1] == "1":
        ETHStats["Mode"] = "Full Duplex"

    if LANInfo[2] == "0":
        ETHStats["Speed"] = "10M"
    elif LANInfo[2] == "1":
        ETHStats["Speed"] = "100M"
    elif LANInfo[2] == "2":
        ETHStats["Speed"] = "1000M"

    if LANInfo[3] == "1":
        ETHStats["Status"] = True
    elif LANInfo[3] == "0":
        ETHStats["Status"] = False

    ETHStats["txPackets"] = int(LANStats[1])
    ETHStats["txBytes"] = int(LANStats[2])
    ETHStats["rxPackets"] = int(LANStats[3])
    ETHStats["rxBytes"] = int(LANStats[4])

    return ETHStats


class EG8141A5(object):

    def __init__(self, url):

        if not url.startswith("http://"):
            url = "http://" + url

        if not url.endswith("/"):
            url += "/"

        self.url = url

    def login(self, username, password):

        # Only admin users have access to certain data
        if username == "Epadmin":
            self.is_admin = True

        else:
            self.is_admin = False

        # First we need to get a token which is (as far as I know) randomly generated
        token = requests.post(self.url + "asp/GetRandCount.asp", verify=False).text[3:]

        # Encoding the password to base64
        password_bytes = password.encode("ascii")
        base64_bytes = base64.b64encode(password_bytes)
        base64_password = base64_bytes.decode("ascii")

        data = {
            "UserName": username,
            "PassWord": base64_password,
            "Language": "english",
            "x.X_HW_Token": str(token),
        }

        # Hard coded cookies
        cookies = {"Cookie": "body:Language:english:id=-1"}

        login_result = requests.post(
            self.url + "login.cgi", data=data, cookies=cookies, verify=False
        )

        if "var pageName = 'index.asp'" in login_result.text:
            self.is_logged_in = True

        else:
            self.is_logged_in = False
            raise RuntimeError("Authentication Failure")

        # Cookie needed for the rest of the session
        cookie = str(login_result.headers).split("Cookie=")[1].split(";")[0]
        self.cookies = {"Cookie": str(cookie)}

    def get_device_info(self):

        device_info = requests.get(
            self.url + "html/ssmp/deviceinfo/deviceinfo.asp",
            cookies=self.cookies,
            verify=False,
        ).text

        cpuUsed = device_info.split("var cpuUsed = '")[1].split("%'")[0]
        memUsed = device_info.split("var memUsed = '")[1].split("%'")[0]
        dev_uptime = device_info.split("var dev_uptime = '")[1].split("'")[0]

        ont_infos = get_elements_from_javascript_array(device_info, "ONTInfo", 2)

        ONTID = ont_infos[1]
        ONTStatus = ont_infos[2]

        device_info_dict = {}

        device_info_dict["cpuUsed"] = int(cpuUsed)
        device_info_dict["memUsed"] = int(memUsed)
        device_info_dict["dev_uptime"] = int(dev_uptime)
        device_info_dict["ONTID"] = int(ONTID)
        device_info_dict["ONTStatus"] = ONTStatus

        return device_info_dict

    def get_wan_info(self):

        wan_list = requests.get(
            self.url + "html/bbsp/common/wan_list.asp",
            cookies=self.cookies,
            verify=False,
        ).text

        wan_info_stats = get_elements_from_javascript_array(wan_list, "WaninfoStats", 1)
        wan_ppp_stats = get_elements_from_javascript_array(wan_list, "WanPPP", 1)

        wan_info_dict = {}

        wan_info_dict["BytesSent"] = int(wan_info_stats[1])
        wan_info_dict["BytesReceived"] = int(wan_info_stats[2])
        wan_info_dict["PacketsSent"] = int(wan_info_stats[3])
        wan_info_dict["PacketsReceived"] = int(wan_info_stats[4])
        wan_info_dict["UnicastSent"] = int(wan_info_stats[5])
        wan_info_dict["UnicastReceived"] = int(wan_info_stats[6])
        wan_info_dict["MulticastSent"] = int(wan_info_stats[7])
        wan_info_dict["MulticastReceived"] = int(wan_info_stats[8])
        wan_info_dict["BroadcastSent"] = int(wan_info_stats[9])
        wan_info_dict["BroadcastReceived"] = int(wan_info_stats[10])
        wan_info_dict["Status"] = wan_ppp_stats[3]
        wan_info_dict["IPAddress"] = wan_ppp_stats[12]
        wan_info_dict["Gateway"] = wan_ppp_stats[13]
        wan_info_dict["DNSServers"] = wan_ppp_stats[16].split(",")
        wan_info_dict["VLANID"] = int(wan_ppp_stats[21])
        wan_info_dict["PPPoEACName"] = wan_ppp_stats[36]
        wan_info_dict["Uptime"] = int(wan_ppp_stats[38])
        wan_info_dict["PPPoESessionID"] = int(wan_ppp_stats[41])

        return wan_info_dict

    def get_eth_info(self):

        eth_info = requests.get(
            self.url + "html/amp/ethinfo/ethinfo.asp",
            cookies=self.cookies,
            verify=False,
        ).text

        lan_stats_dict = {}

        lan_stats_dict["LAN1"] = {}
        lan_stats_dict["LAN2"] = {}
        lan_stats_dict["LAN3"] = {}
        lan_stats_dict["LAN4"] = {}

        lan_stats_dict["LAN1"] = parse_eth_info(eth_info, 2)
        lan_stats_dict["LAN2"] = parse_eth_info(eth_info, 3)
        lan_stats_dict["LAN3"] = parse_eth_info(eth_info, 4)
        lan_stats_dict["LAN4"] = parse_eth_info(eth_info, 5)

        return lan_stats_dict

    def get_optic_info(self):

        optic_info = requests.get(
            self.url + "html/amp/opticinfo/opticinfo.asp",
            cookies=self.cookies,
            verify=False,
        ).text

        optic_values = get_elements_from_javascript_array(optic_info, "stOpticInfo", 3)
        link_time = optic_info.split("var LinkTime = '")[1].split("'")[0]
        PONTxPackets = optic_info.split("var PONTxPackets = '")[1].split("'")[0]
        PONRxPackets = optic_info.split("var PONTxPackets = '")[2].split("'")[0]

        optic_info_dict = {}

        optic_info_dict["transOpticPower"] = float(optic_values[1])
        optic_info_dict["revOpticPower"] = float(optic_values[2])
        optic_info_dict["voltage"] = int(optic_values[3])
        optic_info_dict["temperature"] = int(optic_values[4])
        optic_info_dict["bias"] = int(optic_values[5])
        optic_info_dict["LosStatus"] = int(optic_values[14])
        optic_info_dict["LinkTime"] = int(link_time)
        optic_info_dict["PONTxPackets"] = int(PONTxPackets)
        optic_info_dict["PONRxPackets"] = int(PONRxPackets)

        return optic_info_dict

    def get_debug_log(self):

        debug_log_view = requests.get(
            self.url + "html/ssmp/debuglog/debuglogview.asp",
            cookies=self.cookies,
            verify=False,
        ).text

        ont_token = debug_log_view.split('name="onttoken" id="onttoken" value="')[
            1
        ].split('"')[0]

        data = {"logtype": "opt", "x.X_HW_Token": ont_token}

        debug_log = requests.post(
            self.url
            + "html/ssmp/debuglog/debuglogdown.cgi?FileType=debuglog&RequestFile=html/ssmp/debuglog/debuglogview.asp",
            data=data,
            cookies=self.cookies,
            verify=False,
        ).text

        return debug_log

    def logout(self):

        data = {"RequestFile": "html/logout.html"}
        requests.post(
            self.url + "logout.cgi?RequestFile=html/logout.html",
            data=data,
            cookies=self.cookies,
            verify=False,
        )
        requests.get(self.url + "html/logout.html", cookies=self.cookies, verify=False)
