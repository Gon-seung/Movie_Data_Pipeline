#airflow 관련 라이브러리
from datetime import datetime, timedelta
from textwrap import dedent
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

#데이터 처리 관련 라이브러리
import pandas as pd
from ast import literal_eval
import numpy as np
from pyspark.sql.functions import *
from pyspark.sql import SparkSession

#유사 영화 찾기 관련 라이브러리
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer

#데이터 생성 관련 라이브러리
import kaggle.api as kaggle
from tempfile import gettempdir
from pathlib import Path

#데이터 이동 관련 라이브러리
from google.cloud import storage
import os

#기타
import time

def _download_movie_data(**context):

    start = time.time()
    #kaggle로부터 데이터 다운받기
    data_path = Path(gettempdir()) / 'movies_metadata' / 'movies_metadata.csv'

    kaggle.authenticate()
    kaggle.dataset_download_files('rounakbanik/the-movies-dataset', data_path.parent, unzip=True)
    df = pd.read_csv(data_path, index_col=0)
    print(df.size)
    print(df.head(3))
    df.to_csv('movies_metadata.csv', index=False)
    context['task_instance'].xcom_push(key='down_movie_time', value= time.time() - start)

def _download_rating_data(**context):

    start = time.time()
    #kaggle로부터 데이터 다운받기
    data_path = Path(gettempdir()) / 'movies_metadata' / 'ratings_small.csv'

    kaggle.authenticate()
    kaggle.dataset_download_files('rounakbanik/the-movies-dataset', data_path.parent, unzip=True)
    df = pd.read_csv(data_path, index_col=0)
    print(df.size)
    print(df.head(3))
    df.to_csv('ratings.csv', index=False)
    context['task_instance'].xcom_push(key='down_rating_time', value= time.time() - start)

def print_time(**context):
    print("check_time")
    down_time1 = context["task_instance"].xcom_pull(key='down_movie_time')
    down_time2 = context["task_instance"].xcom_pull(key='down_rating_time')
    print("download time : ",down_time1 + down_time2)

def del_not_require():
    #csv 파일을 spark dataframe 형태로 불러오기
    sc = SparkSession.builder.master('local[*]').appName('hello').getOrCreate()
    file_df = sc.read.csv('./movies_metadata.csv', header = True)
    print(file_df.head(5))
    print((file_df.count(), len(file_df.columns)))
    
    #각 데이터 형태에 맞게 변환
    file_df = file_df.withColumn("vote_average", file_df["vote_average"].cast("float"))
    file_df = file_df.withColumn("vote_count", file_df["vote_count"].cast("int"))
    file_df = file_df.withColumn("id", file_df["id"].cast("int"))
    file_df = file_df.withColumn("release_date", to_date(file_df["release_date"]))

    #null 값은 filter을 통해서 제거
    file_df = file_df.filter(col("vote_average").isNotNull())
    file_df = file_df.filter(col("vote_count").isNotNull())
    file_df = file_df.filter(col("id").isNotNull())
    file_df = file_df.filter(col("release_date").isNotNull())

    #사용할 column 값들만 선택
    file_df = file_df.select('belongs_to_collection', 'genres', 'id' , 'release_date','tagline','title','vote_average','vote_count')

    print((file_df.count(), len(file_df.columns)))

    #genres, collection, tag을 dict, string 형태에서 list형태로 변환해주는 함수 생성
    def get_genres(x):
        x = literal_eval(x)
        answer = []
        for i in x:
            genre_name = i['name']
            genre_name = genre_name.replace(' ','_')
            answer.append('\'' + genre_name + '\'')
        return answer

    def get_collection(x):
        try:
            x = literal_eval(x)
            return x['name']
        except:
            return None

    def get_tag(x):
        if x is None:
            return([])
        x = x.split(' ')
        answer = []
        for i in x:
            i = i.replace('\'','_')
            answer.append('\'' + i + '\'')
        return answer

    #각 함수를 적용
    from pyspark.sql.types import StringType

    func_udf = udf(get_genres, StringType())
    file_df = file_df.withColumn("genres", func_udf(file_df["genres"]))

    func_udf = udf(get_collection, StringType())
    file_df = file_df.withColumn("belongs_to_collection", func_udf(file_df["belongs_to_collection"]))

    func_udf = udf(get_tag, StringType())
    file_df = file_df.withColumn("tagline", func_udf(file_df["tagline"]))

    #dataframe을 csv 파일로 저장
    file_df = file_df.select("*").toPandas()
    file_df.to_csv('./movies_processing1.csv', index = False)
    
    #rating 파일을 불러오는 과정
    sc = SparkSession.builder.master('local[*]').appName('hello').getOrCreate()
    rating_df = sc.read.csv('./ratings.csv', header = True)
    print(rating_df.head(10))
    print((rating_df.count(), len(rating_df.columns)))

    #필요 없는 속성값은 timestamp 제거
    rating_df = rating_df.drop('timestamp')
    rating_df = rating_df.select("*").toPandas()
    rating_df.to_csv('./ratings_processing1.csv', index = False)
    
def data_processing_rank():

    df = pd.read_csv('./movies_processing1.csv')
    #C : 영화 평점 평균 / m : 상위 10퍼가 받은 영화 평점 개수
    C= df['vote_average'].mean()
    m= df['vote_count'].quantile(0.9)

    df = df.loc[df['vote_count'] >= m]

    #평점, 평점 개수를 통해서 점수를 획득하는 함수 생성
    def weighted_rating(x, m=m, C=C):
        v = x['vote_count']
        R = x['vote_average']
        # IMDB 공식에 따라서 계산한 점수
        answer = float((v/(v+m) * R) + (m/(m+v) * C))
        return answer

    #함수를 적용해 점수 column 생성
    df['score'] = df.apply(weighted_rating, axis=1)
    df = df.sort_values('score', ascending=False)

    #필요한 column 값인 id title score만 뽑아내어서 저장
    df = df[['id', 'title', 'score']]
    print(df.head(5))
    df.to_csv('movies_ranking.csv', index = False)

def data_processing_movie():

    df = pd.read_csv('./movies_processing1.csv')
    #genres_literal에 genres, tagline에 있는 list 정보들을 string 형태로 삽입
    df['genres'] = df['genres'].apply(literal_eval)
    df['tagline'] = df['tagline'].apply(literal_eval)
    df['genres_literal'] = df['genres'].apply(lambda x : (' ').join(x))
    df['tag_literal'] = df['tagline'].apply(lambda x : (' ').join(x))
    df['genres_literal'] = df['genres_literal'] + ' ' + df['tag_literal'] 
    print(df.head(3))

    #TF-IDF를 통해서 각 원소 값들의 벡터 크기를 구해냄
    genres_vect = TfidfVectorizer().fit_transform(df['genres_literal'])
    print(len(df))

    #cosine 유사도를 통해서 i번째 영화는 어떠 영화랑 가장 비슷한지 찾아낸후, id와 title을 list 형태로 저장
    title_info = []
    id_info = []
    for i in range(len(df)):
        answer_index = (i + 1) % len(df)
        genre_sim = cosine_similarity(genres_vect[i], genres_vect)[0]
        for j in range(len(df)):
            #index가 같으면 동일한 영화니 continue 처리
            if i == j:
                continue
            if genre_sim[answer_index] < genre_sim[j]:
                answer_index = j
        
        title_info.append(df.loc[answer_index]['title'])
        id_info.append(df.loc[answer_index]['id'])

    #id와 title로 이루어진 list를 새로운 col 값에 넣음
    print(len(id_info))
    df['similar_movie_id'] = id_info
    df['similar_movie_name'] = title_info

    #필요한 col 값들인 id, title, 비슷한 영화의 id, 비슷한 영화의 이름을 뽑아낸 후 저장
    df = df[['id', 'title', 'similar_movie_id', 'similar_movie_name']]
    df.to_csv('./movies_processing2.csv', index = False)
    return(0)

def upload_data():
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="/root/google_cloud_key.json"

    bucket_name = 'us-west4-first-composer-205a9c14-bucket'    # 서비스 계정 생성한 bucket 이름 입력
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)


    source_file_name = './movies_processing2.csv'    # GCP에 업로드할 파일 절대경로
    destination_blob_name = 'movies_processing2.csv'    # 업로드할 파일을 GCP에 저장할 때의 이름)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)
    
    source_file_name = './movies_ranking.csv'    # GCP에 업로드할 파일 절대경로
    destination_blob_name = 'movies_ranking.csv'    # 업로드할 파일을 GCP에 저장할 때의 이름)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)


with DAG(
    'portfolio',
    default_args={
        'depends_on_past': False,
        'email': ['airflow@example.com'],
        'email_on_failure': False,
        'email_on_retry': False,
        'retries': 1,
        'retry_delay': timedelta(minutes=5),
    },
    description='A simple portfolio DAG',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2022, 1, 1),
    catchup=False,
    tags=['start'],
) as dag:

    step1 = PythonOperator(
        task_id='download_movie',
        python_callable = _download_movie_data,
    )

    step2 = PythonOperator(
        task_id='del_not_require',
        python_callable = del_not_require,
    )


    templated_command = dedent(
        """
    {% for i in range(5) %}
        echo "end"
    {% endfor %}
    """
    )

    step3 = PythonOperator(
        task_id='print_time',
        python_callable = print_time,
    )

    step4 = BashOperator(
        task_id='end',
        depends_on_past=False,
        bash_command=templated_command,
    )

    step5 = PythonOperator(
        task_id='download_rating',
        python_callable=_download_rating_data,
    )

    step6 = PythonOperator(
        task_id='processing_movie_ranking',
        python_callable = data_processing_rank,
    )

    step7 = PythonOperator(
        task_id='processing_movie_similar',
        python_callable = data_processing_movie,
    )

    step8 = PythonOperator(
        task_id='upload_data',
        python_callable = upload_data,
    )

    [step1 , step5] >> step3 >> step2 >> [step6, step7] >> step8 >> step4
