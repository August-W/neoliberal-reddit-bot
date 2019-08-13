import praw
import datetime
import numpy
import pandas
import os
import time
import matplotlib.pyplot as plt
from dotenv_config import Config
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType
from pyspark.sql.types import StructField
from pyspark.sql.types import StringType
from pyspark.sql.types import IntegerType
from pyspark.sql.types import TimestampType
from pyspark.sql.types import FloatType
from pyspark.sql.types import StringType
from pyspark.sql.types import BooleanType
from pyspark.sql.functions import udf
from pyspark.sql.functions import desc
from pandas.plotting import table

#NEED THIS TO GET TO REDDIT
config = Config('.env')

#SET UP THE REDDIT CONNECTION
r = praw.Reddit(user_agent='reddit-neoliberal-bot-py',
                client_id=os.environ['CLIENT_ID'],
                client_secret=os.environ['CLIENT_SECRET'],
                password=os.environ['REDDIT_PASS'],
                username=os.environ['REDDIT_USER'])

#FOR SOME REASON THIS ISN'T WORKING...
#r = praw.Reddit(user_agent='reddit-neoliberal-bot-py',
#                client_id=config('NEOLIBERAL_CLIENT_ID'),
#                client_secret=config('NEOLIBERAL_CLIENT_SECRET'),
#                password=config('NEOLIBERAL_REDDIT_PASS'),
#                username=config('NEOLIBERAL_REDDIT_USER'))

#READ COMMENTS FROM DISCUSSION THREAD
def handle_post(submission, post_date):
    spark = start_spark()
    comment_list = submission.comments.replace_more(limit=None)
    schema_1 = gen_schema_1()
    schema_2 = gen_schema_2()
    rdd = spark.sparkContext.parallelize(comment_list)
    comment_data_frame_1 = spark.createDataFrame(rdd,schema_1)
    comment_data_frame_2 = spark.createDataFrame(rdd,schema_2)
    graph_most_upvoted_comments(comment_data_frame_2)
    graph_comment_count_per_time(comment_data_frame_1)
    file_path = os.path.join(ROOT_DIR, 'discussion_thread_data/'+str(post_date)+'_neolib_dt_analytics.pdf')
    plt.savefig(file_path)
    create_post(file_path, post_date)
    spark.stop()

#GENERATE SCHEMA 1
def gen_schema_1():
    return StructType([
        StructField('body', StringType(), True),
        StructField('created_utc', FloatType(), True)
    ])

#GENERATE SCHEMA 2
def gen_schema_2():
    return StructType([
        StructField('body', StringType(), True),
        StructField('score', IntegerType(), True),
        StructField('author', StructType([
            StructField('name', StringType(), True)
        ]), True)
    ])

#START SPARK
def start_spark():
    return SparkSession\
        .builder\
        .appName('DiscussionThreadAnalyzer')\
        .getOrCreate()

#CREATE POST WITH IMAGE
def create_post(file_path, post_date):
    submission = r.subreddit('neoliberal').submit_image(str(post_date)+' DT Analysis', file_path)
    submission.reply(POST_DESCRIPTION)
    return

#GRAPH NUMBER OF COMMENTS OVER TIME
def graph_comment_count_per_time(comments_date_time_data_frame):
    udf_as_time_str = udf(as_time_str, StringType())
    comments_date_time_data_frame_converted = comments_date_time_data_frame.withColumn('datetime', udf_as_time_str('created_utc'))
    comments_time = comments_date_time_data_frame_converted.groupBy('datetime')
    pandas_comments_time = comments_time.count().orderBy('datetime').toPandas()
    ax0 = plt.subplot2grid((8,3), (0,0), rowspan=1, colspan=3)
    pandas_comments_time.plot(ax=ax0, kind='line', x='datetime', y='count')
    ax0.set_xlabel('time (EST)')
    ax0.set_ylabel('comments')
    ax0.set_title('DT Comments per Hour')
    find_real_neolib_hours(comments_date_time_data_frame_converted, pandas_comments_time, udf_as_time_str)

#DOES THE COMMENT CONTAIN A "REAL NEOLIBERAL HOURS" KEY WORD?
def contains_rnh(comment):
    rnh_root_words = ['alcohol', 'depress', 'whiskey', 'sad', 'wine', 'suicid', 'beer', 'alone', 'tequila', 'lonely', 'vodka', 'antisocial', 'drugs', 'cry', 'weed', 'anxiety', 'gin', 'unhappy', 'cocktail', 'stress']
    for word in rnh_root_words:
        if word in str(comment):
            return True
    return False

#DETERMINE WHEN REAL NEOLIBERAL HOURS BEGIN
def find_real_neolib_hours(comments_by_time, pandas_comments_time, udf_as_time_str):
    udf_contains_rnh = udf(contains_rnh, BooleanType())
    comments_by_time = comments_by_time.filter(udf_contains_rnh(comments_by_time['body'])).groupBy('datetime').count().orderBy('datetime').toPandas()
    c = ['rnh comment ratio', 'time']
    ratios = numpy.divide(comments_by_time['count'], pandas_comments_time['count'])
    ratios.replace([numpy.inf, -numpy.inf], numpy.nan).dropna()
    pandas_comments_time.replace([numpy.inf, -numpy.inf], numpy.nan).dropna()
    matrix = list(zip(ratios, comments_by_time['datetime']))
    pandas_ratios_time = pandas.DataFrame(data=matrix, columns=c)
    ax1 = plt.subplot2grid((8,3), (2,0), rowspan=1, colspan=3)
    pandas_ratios_time.plot(ax=ax1, kind='line', x='time', y='rnh comment ratio')
    ax1.set_xlabel('time (EST)')
    ax1.set_ylabel('ratio of comments about alcohol or depression per comments per hour')
    ax1.set_title('DT Real Neoliberal Hours')

#CONVERT TIMESTAMP
def as_time_str(x):
    return time.ctime(x)[11:-10]+'00'

#GET NAME FIELD
def get_name(x):
    return str(x)[10:-2]

#GRAPH MOST UPVOTED COMMENTS
def graph_most_upvoted_comments(commentsDataFrame):
    udf_get_name = udf(get_name, StringType())
    comments_data_frame_converted = commentsDataFrame.withColumn('author', udf_get_name('author'))
    comments_by_score = comments_data_frame_converted.orderBy(desc('score')).limit(10).toPandas()
    comments_by_score['body'] = comments_by_score['body'].str.wrap(140)
    comments_by_score.rename(columns={'body': 'comment'})
    comments_by_score.set_index('body')
    ax2 = plt.subplot2grid((8,3), (4,0), rowspan=4, colspan=3, frame_on=False)
    ax2.xaxis.set_visible(False)
    ax2.yaxis.set_visible(False)
    ax2.axis('off')
    tab = table(ax2, comments_by_score, loc='upper center', cellLoc='left')
    tab.auto_set_font_size(False)
    tab.set_fontsize(17)
    cell_dict=tab.get_celld()
    for i in range(11):
        cell_dict[(i,0)].set_width(0.9)
        cell_dict[(i,0)].set_height(0.1)
        cell_dict[(i,1)].set_width(0.06)
        cell_dict[(i,1)].set_height(0.1)
        cell_dict[(i,2)].set_width(0.2)
        cell_dict[(i,2)].set_height(0.1)
    cell_dict[(0,0)].set_height(0.03)
    cell_dict[(0,1)].set_height(0.03)
    cell_dict[(0,2)].set_height(0.03)

#LINK USER TO NEOLIBERAL POSTS
def fetch_discussion_thread():
       for submission in r.subreddit('neoliberal').new(limit=None):
            if 'neoliberal-shill-bot' == submission.author.name:
                return
            post_date = datetime.date.fromtimestamp(submission.created_utc)
            if 'discussion thread' in submission.title.lower() and today-post_date>datetime.timedelta(hours=12):
               handle_post(submission, post_date)
               return


#LETS GET THIS THING STARTED
POST_DESCRIPTION = ('Hi! I\'m a bot. I run daily data analytics on the previous day\'s Discussion Thread. The first graph in my post shows the traffic in the DT over time. \n\n'+
'With the second graph, I am attempting to learn when exactly "real neoliberal hours" begin. The y axis is the ratio of the sum of comments containing alcohol/drugs/depression related words per hour, over the total comments per hour. \n\n'+
'The table at the bottom shows the most upvoted comments.\n I hope you found this informative.' )
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
today = datetime.date.today()
plt.rcParams['figure.figsize'] = (30,100)
plt.rc('font', size=17)
plt.rc('axes', titlesize=17)
plt.rc('axes', labelsize=17)
plt.rc('xtick', labelsize=17)
plt.rc('ytick', labelsize=17)
plt.rc('legend', fontsize=12)
plt.rc('figure', titlesize=24)
fetch_discussion_thread()
