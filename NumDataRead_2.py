'''
-------------------------- ver 1 ------------------------------
created date: 25/9/2020 16:10
author: Wenyu Qiu
email address: wenyuqiu1997@qq.com
description: 
        1. this is a data read file for all labels data
        2. modify the No.129 line, the wrong logic for correcting
--------------------------- ver 2 -----------------------------
update time: 2/11/2020 16:30
author：Wenyu Qiu
description:
        1. add the prevent flying-point algorithm named as "def pre_fly"
        2. regarding the tracks begin with status '1' and end with '3' and the first point is equal to the last one,
        this kind of points we treat it as 'trash point' and delete it
*attention: when it will be published, need to modify the processing of empty chars like 
No.69 No.129 and No.148 line, can take the "dataread.py" stable v1.0 as reference
'''

import math
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import random
import os
import re
from copy import deepcopy

HEIGHT = 160

class BaseData:
    def __init__(self):
        self.words = []
        self.labels = []

class Word:
    def __init__(self):
        self.label = ''
        self.tracks = []
        self.filename = ''

    def show(self):
        for track in self.tracks:
            x = [point[0] for point in track]
            y = [point[1] for point in track]
            plt.plot(x, y)
        plt.show()

class baseWord:
    def __init__(self, label, matrix, tracks, rawTracks, filename):
        self.label = label
        self.matrix = matrix
        self.tracks = tracks
        self.rawTracks = rawTracks
        self.filename = filename

class Data:
    def __init__(self, data_path, size, HEIGHT, fly_dis=30):
        self.data = []
        self.total = 0
        self.data_path = data_path
        self.size = size
        self.HEIGHT = HEIGHT
        self.fly_dis = fly_dis

    def read_data_set(self):
        words = self.readWordFromCompany()
        for word in words:
            if word.tracks == []:
                continue
            rawTracks = deepcopy(word.tracks)
            tracks = self.scale(word.tracks)
            if word.tracks == []:
                continue
            matrix = self.word_matrix(word)
            base = baseWord(word.label, matrix, tracks,
                            rawTracks, word.filename)
            self.data.append(base)
        return self.data

    def word_matrix(self, word):
        matrix = np.zeros((self.size, self.size))
        for track in word.tracks:
            for i in range(len(track)-1):
                ps = self.dda(track[i], track[i+1])
            ########################## bug #########################
            try:
                for p in ps:
                    matrix[p[0]][p[1]] = 1
            except UnboundLocalError:
                print('file_name  ', word.filename)
                print('bug ps No.89  ', track)
                print('tracks  ', word.tracks)
                print('bug ps No.89')
                raise
            except Exception as e:
                print(e)
                raise
        return np.array(matrix).reshape(self.size, self.size, 1)

    def scale(self, tracks):
        size = self.size - 1
        vertex = [tracks[0][0][0], tracks[0][0]
                  [1], tracks[0][0][0], tracks[0][0][1]]
        for track in tracks:
            for point in track:
                vertex[0] = min(vertex[0], point[0])
                vertex[1] = min(vertex[1], point[1])
                vertex[2] = max(vertex[2], point[0])
                vertex[3] = max(vertex[3], point[1])
        for track in tracks:
            for point in track:
                point[0] -= vertex[0]
                point[1] -= vertex[1]
        vertex[2] -= vertex[0]
        vertex[3] -= vertex[1]
        vertex[0] = vertex[1] = 0
        if vertex[2] == 0 or vertex[3] == 0:
            return []
        r1 = size / vertex[2]
        r2 = size / vertex[3]
        ratio = min(r1, r2)
        for track in tracks:
            for point in track:
                point[0] = int(point[0] * ratio)
                point[1] = int(point[1] * ratio)
        return tracks

    def readFromFile(self, fpath):
        tracks = []
        fdata = ''
        with open(fpath, 'r', encoding='UTF-8') as f:
            lines = f.readlines()
        for line in lines:
            fdata += line
        lines = fdata.split('_')
        for line in lines:
            point = re.findall('.*{(.*)}.*', line)
            if len(point) == 0:
                continue
            ps = point[0].split(',')
            ps = [int(p) for p in ps]
            if ps[4] == 2:
                tracks.append([[ps[0], -ps[1], ps[4]]])
                continue
            elif ps[4] == 3:
                if len(tracks) == 0:
                    continue
                else:
                    y = list(p[1] for p in tracks[-1])
                    y_max = max(y)
                    y_min = min(y)
                    y_final = ps[1]
                    del_1 = abs(y_max - y_min)
                    del_2 = abs(y_max - y_final)
                    del_3 = abs(y_final - y_max)
                    if del_1 >= self.HEIGHT or del_2 >= self.HEIGHT or del_3 >= self.HEIGHT:
                        tracks = []
                        continue
                    else:
                        tracks[-1].append([ps[0], -ps[1], ps[4]])
            elif ps[4] == 1:
                if len(tracks) == 0:
                    continue
                elif tracks[-1][-1][2] == 3:
                    tracks.append([[ps[0], -ps[1], ps[4]]])
                else:
                    tracks[-1].append([ps[0], -ps[1], ps[4]])
            # check whether exist repeat points
            tracks = Data.che_rep(self, tracks)
            # print(tracks)
            # check whether it is the flying point
            # get the former point and this point in this tracks as input parms
            if tracks[-1][-1][2] == 3:
                answer = Data.pre_fly(self, tracks[-1][-2], tracks[-1][-1])
                if answer == 1:
                    tracks[-1].pop(-1)
                    tracks[-1][-1][2] = 3
                elif answer == 2:
                    tracks.pop(-1)

        return tracks

    def readWordFromCompany(self):
        words = []
        setspath = os.listdir(self.data_path)
        for setpath in setspath:
            fpath = os.path.join(self.data_path, setpath)
            files = os.listdir(fpath)
            for f in files:
                if f is None:
                    continue
                word = Word()
                word.label = f.split('-')[0]
                word.tracks = self.readFromFile(os.path.join(fpath, f))
                word.filename = os.path.join(fpath, f)
                words.append(word)
                self.total += 1
        return words

    def dda(self, p1, p2):
        length = int(max(abs(p2[0]-p1[0]), abs(p2[1]-p1[1])))
        x = p1[0] + 0.5
        y = p1[1] + 0.5
        delta_x = 0
        delta_y = 0
        ps = []
        if length != 0:
            delta_x = (p2[0]-p1[0]) / length
            delta_y = (p2[1]-p1[1]) / length
        for i in range(length+1):
            nx = int(x)
            ny = int(y)
            if nx == self.size:
                nx = self.size - 1
            if ny == self.size:
                ny = self.size - 1
            ps.append((nx, ny))
            x += delta_x
            y += delta_y
        return ps
    
    def pre_fly(self, p0, p1):
        """
        params p0 [x, y, status] (the former point), p1 [x, y, status] (the current point)
        output the three type value, if return 0, continue like usual; if return 1, 
        discard p1; if return 2, discard p0 and p1
        """
        # get the Euclid distance
        if abs(p0[0]-p1[0])>=self.fly_dis and abs(p0[1]-p1[1])>=self.fly_dis:
            if p0[2] == 2:
                return 2
            elif p0[2] == 1:
                return 1
        return 0
    
    def che_rep(self, tracks):
        """
        check whether the last adjacent points is repetitive
        input:  tracks
        output: tracks
                tracks(it may be changed after this func), 
                answer(0: change nothing and enter the next step , 
                       -1: meet the repetitive points and change the tracks
        """
        if len(tracks) == 0:
            return tracks
        elif len(tracks[-1]) <= 2:
            return tracks
        else:
            # case repetitive point
            if tracks[-1][-2][0] == tracks[-1][-1][0] and tracks[-1][-2][1] == tracks[-1][-1][1]:
                # case 1 last two status == 3
                if tracks[-1][-2][2] == 3 and tracks[-1][-1][2] == 3:
                    tracks[-1].pop(-1)
                # case 2 the last one status == 1
                elif tracks[-1][-1][2] == 1:
                    tracks[-1].pop(-1)
                # case 3 the last one status == 3, and the former one != 3
                elif tracks[-1][-1][2] == 3 and tracks[-1][-2][2] != 3:
                    tracks[-1].pop(-2)
        return tracks

    # def che_tra(self, tracks, ps):
    #     """
    #     check trash ps and discard them
    #     """
    #     if len(tracks) == 0:
    #         if ps[4] == 1 or ps[4] == 3:
    #             ps = -1
    #     else:
    #         # in this version consider single point as noise 
    #         if tracks[-1][-1][2] == 3 and ps[4] == 3:
    #             ps = -1
    #     return (tracks, ps)
        


    # def de_tick(self)