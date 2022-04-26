from datetime import datetime, timedelta
from textwrap import dedent

from airflow import DAG

from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

import pandas as pd
import kaggle.api as kaggle
from tempfile import gettempdir
from pathlib import Path
from pyspark.sql.functions import *
from pyspark.sql import SparkSession
from ast import literal_eval

def _download_data():
    #kaggle로부터 데이터 다운받기
    data_path = Path(gettempdir()) / 'movies_metadata' / 'movies_metadata.csv'

    kaggle.authenticate()
    kaggle.dataset_download_files('rounakbanik/the-movies-dataset', data_path.parent, unzip=True)
    df = pd.read_csv(data_path, index_col=0)
    print(df.size)
    print(df.head(3))
    df.to_csv('movies_metadata.csv', index=False)

def data_processing():
    #csv 파일을 spark dataframe 형태로 불러오기
    sc = SparkSession.builder.master('local[*]').appName('hello').getOrCreate()
    file_df = sc.read.csv('./movies_metadata.csv', header = True)
    print(file_df.head(10))
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

    #필요없는 col 값들은 제거
    file_df = file_df.select('belongs_to_collection', 'genres', 'id' , 'release_date','tagline','title','vote_average','vote_count')

    print((file_df.count(), len(file_df.columns)))

    #genres, collection을 dict 형태에서 list형태로 변환, 데이터 처리 후 Dataframe 확인

    def get_genres(x):
        x = literal_eval(x)
        answer = []
        for i in x:
            answer.append(i['name'])
        return answer

    def get_collection(x):
        try:
            x = literal_eval(x)
            return x['name']
        except:
            return None

    from pyspark.sql.types import StringType

    func_udf = udf(get_genres, StringType())
    file_df = file_df.withColumn("genres", func_udf(file_df["genres"]))

    func_udf = udf(get_collection, StringType())
    file_df = file_df.withColumn("belongs_to_collection", func_udf(file_df["belongs_to_collection"]))
    print(file_df.orderBy(col("id").asc()).show(10))
    file_df.coalesce(1).write.csv("movie_metadata_process")
    

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

    t1 = PythonOperator(
        task_id='download',
        python_callable = _download_data,
    )

    t2 = PythonOperator(
        task_id='processing',
        python_callable = data_processing,
        retries=3,
    )


    templated_command = dedent(
        """
    {% for i in range(5) %}
        echo "end"
    {% endfor %}
    """
    )

    t3 = BashOperator(
        task_id='end',
        depends_on_past=False,
        bash_command=templated_command,
    )

    t1 >> t2 >> t3
