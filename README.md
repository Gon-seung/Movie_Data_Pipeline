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
3개의 과정으로 이루어져 있다.
![캡처](https://user-images.githubusercontent.com/70638465/165226686-c1049ef6-d1ba-4d27-bd05-49c81c6558cc.jpg)

download에서는 kaggle에서 데이터를 다운받는 과정을,

processing은 데이터를 가공해서 새롭게 저장하는 과정을,

end는 과정이 끝났음을 확인하기 위해서 print문을 넣은 과정이다.

데이터 원본 : https://www.kaggle.com/datasets/rounakbanik/the-movies-dataset

download 이후의 dataframe : 
![캡처](https://user-images.githubusercontent.com/70638465/165229806-ead688ba-c8f4-4e5e-9a95-06fbb741332a.jpg)
processing 이후의 dataframe : 
![캡처](https://user-images.githubusercontent.com/70638465/165229941-1b730e81-68a6-4f11-b83f-c29c9a91c8f0.jpg)


# 영화 추천 알고리즘

colab/data_analysis.ipynb 참고 
