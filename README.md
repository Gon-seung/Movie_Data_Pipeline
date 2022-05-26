# movie dataset을 이용한 데이터 처리 및 영화 추천
이 프로젝트의 목적은 movie 데이터셋을 이용해서 airflow의 dag를 만들어보고, 하는 과정입니다.

# Prerequisites
Python 3.8.10

Apache Airflow 2.2.5

Apache Spark 3.2.1

Kaggle API 1.5.12

# Installation
Python, Airflow, Spark, Kaggle을 설치한다.

-portfolio.py : pipeline을 구축한 파일

https://www.kaggle.com/ 에서 account -> kaggle api를 다운받은 후에 kaggle.json 파일을 root/.kaggle/에 이동한다.
airflow scheduler, airflow webserver를 실행시키면 portfolio.py을 실행할 수가 있다. 

-data_analysis.py : movie_dataset을 데이터 분석한 파일

colab에서 실행하면 된다.

# Pipeline

![화면 캡처 2022-05-26 140723](https://user-images.githubusercontent.com/70638465/170420023-bb61b51a-1a76-44e7-ba86-9fac082dca30.jpg)


다음과 같은 과정으로 이루어져 있다.

1. download_movie에서는 kaggle에서 movie 데이터를 다운받는 과정을,

2. download_rating에서는 kaggle에서 rating 데이터를 다운받는 과정을,

3. print_time에서는 다운받는 시간을 출력하는 과정을,

4. processing_movie은 movie 데이터를 가공해서 새롭게 저장하는 과정을,

5. processing_rating은 rating 데이터를 가공해서 새롭게 저장하는 과정을,

6. end는 과정이 끝났음을 확인하기 위해서 print문을 넣은 과정이다.


데이터 원본 : https://www.kaggle.com/datasets/rounakbanik/the-movies-dataset

download 이후의 dataframe : 
![캡처](https://user-images.githubusercontent.com/70638465/165229806-ead688ba-c8f4-4e5e-9a95-06fbb741332a.jpg)
processing 이후의 dataframe : 
![캡처](https://user-images.githubusercontent.com/70638465/165229941-1b730e81-68a6-4f11-b83f-c29c9a91c8f0.jpg)


# 영화 추천 알고리즘

가공된 데이터를 통해서 영화 데이터셋을 분석하고 추천 알고리즘을 작성한 방식이다.

colab/data_analysis.ipynb 참고 
