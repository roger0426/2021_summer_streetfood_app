# -*- coding: utf-8 -*-
"""資訊專題比賽(測試圖片function)

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1aqN-ouRnE-O_ghu5pEsYAL9jhfyhrI0c

# 進行 test data 測試

install OpenCV
"""
"""
!pip install -i https://pypi.tuna.tsinghua.edu.cn/simple opencv-python==3.4.2.17

!pip install -i https://pypi.tuna.tsinghua.edu.cn/simple opencv-contrib-python==3.4.2.17
"""
import json
import os
import cv2
import numpy as np
from sklearn.cluster import KMeans
import csv
import sqlite3
import pandas as pd
from decoder import decode_64

## search name,feature stored in test.db
def search(longitude,latitude,direction):#接收使用者經緯度跟方向，回傳可能看的到的商店名字跟feature
    # 取得dectect_picture.py的絕對路徑
    path = os.path.abspath(__file__)
    # 改變path對應到test.db的相對路徑
    path = os.path.join(path, "..", "..", "test.db")
    conn = sqlite3.connect(path)
    c = conn.cursor()
    c.execute('SELECT `feature`,`NAME` FROM `table3`;')
    name=[]
    feature=[]
    for row in c.fetchall():
        #a=row[0].split(']')[1][1:].split('.')[:-1]
        a=row[0].split(']')[:-1]
        list_b=[]
        for i in range(len(a)):
                b=a[i][1:].split('.')[:-1]
                list_a=[]
                for j in range(len(b)):
                    list_a.append(float(b[j]))
                list_b.append(list_a)
        name.append(row[1])
        feature.append(list_b)
        #row[1]、list_b
    conn.commit()
    conn.close()
    return name, feature
    
    
def FLANN_Matching(img_base64, tr_name_list ,tr_desc_list):
    #1 測試圖片的base64編碼 #2 訓練圖片的[name,desc](list型態儲存)  
    
    ### apply  sift method on test image ####
    feature_extractor_test = cv2.xfeatures2d.SIFT_create()
    gray_test_list=[]
    rgb_test_list=[]
    kp_test_list=[]
    desc_test_list=[]

    test_image_total=int(0)
    max_correct_index=[]#record the max index for every image

    ### process the SIFT on the test_image
    #---    
    ratio=0.45 #設定image縮放比例
    test_picture = decode_64(img_base64)
    height=int(len(test_picture)*ratio)
    width=int(len(test_picture[0])*ratio)      

    test_picture = cv2.resize(test_picture, (width, height), interpolation=cv2.INTER_AREA)

    #get rgb,gray
    rgb_test = cv2.cvtColor(test_picture , cv2.COLOR_BGR2RGB)
    gray_test = cv2.cvtColor(rgb_test, cv2.COLOR_RGB2GRAY)#transfer RGB to gray
          
    #find the keypoints and descriptors with chosen feature_extractor
    kp_test,  desc_test =  feature_extractor_test.detectAndCompute( gray_test, None)# kp_1 is keypoint, desc_1 is descriptor
    test = cv2.drawKeypoints( rgb_test,  kp_test, None, flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)

    gray_test_list.append(gray_test)
    rgb_test_list.append(rgb_test)
    kp_test_list.append(kp_test)
    desc_test_list.append(desc_test)
        
    ### process FLANN matching ###

    max_tmp=int(0)
    max_tmp_index=int(0)
    max_tmp_list=[]
    max_tmp_index_list=[]

    for s in range(0,len(tr_desc_list)): #每張test_image 與 train_image 做比較 
    
            # FLANN parameters              
            FLANN_INDEX_KDTREE = 1
            index_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 5)
            search_params = dict(checks=20)   # or pass empty dictionary
            flann = cv2.FlannBasedMatcher(index_params,search_params)
            matches = flann.knnMatch(tr_desc_list[s], desc_test,k=2)

            # Need to draw only good matches, so create a mask
            matchesMask = []
            
            
            ### ratio test as per Lowe's paper ###
            if (len(matches)>0): 

                for m in (matches):
                    if m[0].distance/m[1].distance < 0.625: #Lowe's Ratio test
                      #matchesMask[s]=[1,0]
                      matchesMask.append(m)# 小於特定ratio，將m 儲存在matchMask
                      matchesMask_arr = np.asarray(matchesMask)

                    #print("Correctance: ",len(matchesMask)/len(matches),"; Current_max_index: ",max_tmp_index)
                

                if (len(matches)!=0 and (len(matchesMask)>= max_tmp or (len(matchesMask)>= 30)) ):

                    #max_tmp_2d=[]#用2維陣列 [x,y]，才能丟入kmeans()

                    max_tmp=len(matchesMask)                      
                    max_tmp_index=s

                    max_tmp_index_list.append(max_tmp_index)

                    #max_tmp_2d.append(max_tmp)
                    #max_tmp_2d.append(0)

                    max_tmp_list.append(max_tmp)

                    #print("max_match= ",max_tmp,"max_tmp_index= ", max_tmp_index)

                else :
                    max_tmp=max_tmp
                    max_tmp_index=max_tmp_index
 
    if (len(max_tmp_list)>0):

      #kmeans = KMeans(n_clusters=2, random_state=0).fit(max_tmp_list)
      #print(kmeans.labels_)

      max_tmp_correct_index=[]
      length=(len(max_tmp_index_list))       
    
      max_tmp_correct_index.append(max_tmp_index_list[length-1]) 

        
      for i in range(len(max_tmp_list)-1):
      

          if (max_tmp_list[i]>=35):

            max_tmp_correct_index.append(max_tmp_index_list[i])

      #print(max_tmp_correct_index,"\n")
          
    max_correct_index.append(max_tmp_correct_index)
    ### end the SIFT on the test_image
   

    #### find the resemble stores ####

    resemble_store_name_list=[] #儲放每張 test images 相似訓練圖片的名稱

    for i in range(len(max_correct_index)):

      store_name=[]
 
      for j in range(len(max_correct_index[i])):

        s=max_correct_index[i][j]
       
        #print("The resemble stores: ")
        #print("name: ",tr_name_list[s]) #輸出相似店家名稱
        
        store_name.append(tr_name_list[s])


      resemble_store_name_list.append(store_name)  
       
    return resemble_store_name_list # 2d array
    
    
    
    
def main():
  img_base64 = input()
  name_list, feature_list = search(10,10,10)
  b=FLANN_Matching(img_base64.split(',')[1], name_list, feature_list)
  result = {'success':'123'}
  print(json.dumps(result))
  #print(b)
main()