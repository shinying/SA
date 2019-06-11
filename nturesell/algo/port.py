"""interface for access existing data
"""

import os
import pandas as pd
from typing import Tuple

file_dir = os.path.dirname(__file__)

# port to pier distance
df_port_to_pier = pd.read_excel(os.path.join(file_dir, "data/complete_dis.xlsx"), index_col="代號")

# pier to pier distance
df_pier_to_pier = pd.read_excel(os.path.join(file_dir, "data/complete_dis_meter.xlsx"), index_col=1)

# reverse: if 'L' then 0 順 1 逆
df_reverse1 = pd.read_excel(os.path.join(file_dir, "data/左靠逆靠.xlsx"))


def get_portToPier_dist(port, pier):
    portnum = 9001 if port == 1 else 9002
    return (df_port_to_pier.loc[int(portnum), int(pier)])


def get_pierToPier_dist(pier1, pier2):
    return df_pier_to_pier.loc[int(pier1), int(pier2)]


def get_pier_latlng(pier) -> Tuple[float, float]:
    if pier == 9001: # port 1
        return (22.616677, 120.265942)
    elif pier == 9002: # port 2
        return (22.552638, 120.316716)

    return tuple([float(i) for i in df_port_to_pier.loc[int(pier), "經緯度"].split(',')])


def get_reverse(task):
    reverse = 0
    if task.ship_state == 'I':
        if task.start == 9001:
            if task.side == 'L':
                reverse = bool(df_reverse1.loc[int(task.to), 9001])
            else:
                reverse = not(bool(df_reverse1.loc[int(task.to), 9001]))
        elif task.start == 9002:
            if task.side == 'L':
                reverse = bool(df_reverse1.loc[int(task.to), 9002])
            else:
                reverse = not(bool(df_reverse1.loc[int(task.to), 9002]))
    elif task.ship_state == 'T':
        reverse = 0
    return reverse


def get_closest_pier(pier):
    if pier >= 1501 and pier <= 1513 or pier == 1814:
        return(1047)
    elif pier == 1801 or pier == 1802 or pier == 1813:
        return(1046)
    elif pier == 1803 or pier == 1804:
        return(1057)
    elif (pier >= 1805 and pier <= 1807) or pier == 1809 or pier == 1821:
        return(1060)
    elif pier >= 1808:
        return(1033)
    elif pier == 1816:
        return(1063)
    elif pier >= 1817 and pier <= 1819:
        return(1056)
    elif pier == 1823:
        return(1061)
    elif pier == 1825:
        return(1043)
    elif pier == 1829:
        return(1036)
    elif pier == 4020 or pier == 4021:
        return(1001)
    elif pier == 4022:
        return(1002)
    elif pier == 4023:
        return(1003)
    elif pier == 4024:
        return(1004)
    elif pier == 4025:
        return(1006)
    elif pier == 4031:
        return(1035)
    elif pier == 4032:
        return(1033)
    elif pier == 4033:
        return(1032)
    elif pier == 4081:
        return(1109)
    elif pier == 4082:
        return(1108)
    elif pier == 4044:
        return(1044)
    elif pier == 4045:
        return(1045)
    elif pier == 4046:
        return(1046)
    elif pier == 4050:
        return(1048)
    elif pier == 4051:
        return(1049)
    elif pier == 4052:
        return(1050)
    elif pier == 4053:
        return(1051)
    elif pier == 4054:
        return(1052)
    elif pier == 4061:
        return(1062)
    elif pier == 4062:
        return(1064)
    elif pier == 4081:
        return(1109)
    elif pier == 4082:
        return(1108)
    elif pier == 8801:
        return(1086)
    elif pier == 8804:
        return(1089)
    elif pier == 8807:
        return(1119)
    elif pier == 8861:
        return(1085)
    else:
        return(1001)


