import json
import boto3
import pandas as  pd
from datetime import datetime
from io import StringIO

def album_store(data):
    album_list=[]
    for row in data['items']:
        album_id = row['track']['album']['id']
        album_name = row['track']['album']['name']
        album_release_date = row['track']['album']['release_date']
        song_name = row['track']['name']
        song_popularity_rating = row['track']['popularity']
        name = []
        for item in row['track']['album']['artists']:
            name.append(item['name'])
        artist_name = name
        album_total_tracks = row['track']['album']['total_tracks']
        album_link = row['track']['album']['external_urls']['spotify']
        song_link = row['track']['external_urls']['spotify']
        
        album = {'album_id': album_id , 'album_name': album_name , 'album_release_date': album_release_date , 'song_name': song_name ,
                'song_popularity_rating': song_popularity_rating ,'artist_name': artist_name , 'album_total_tracks': album_total_tracks ,
                'album_link': album_link , 'song_link': song_link} 
        album_list.append(album)
    return album_list


def lambda_handler(event, context):
    
    s3 = boto3.client("s3")
    Bucket = "spotify-etl-kartik203"
    Key = "raw_data/to_processed/"
    
    #print(s3.list_objects(Bucket = Bucket, Prefix = Key)['Contents'])
    
    spotify_key = []
    spotify_data = []
    for file in s3.list_objects(Bucket = Bucket, Prefix = Key)['Contents']:
        file_key = file['Key']
        
        if file_key.split('.')[-1] == "json":
            response = s3.get_object(Bucket = Bucket , Key = file_key)
            content = response['Body']
            obj_data = json.loads(content.read())
            spotify_data.append(obj_data)
            spotify_key.append(file_key)
            
     # After finding all data object we need to transfer the data to transformed data after transforming data    
    for data in spotify_data:
        album_list = album_store(data)
        
        df = pd.DataFrame.from_dict(album_list)
        df = df.drop_duplicates(subset = ['album_id'])
        df.loc[:, 'album_release_date'] = pd.to_datetime(df['album_release_date'])
        
        album_key = "transformed_data/spotify_transformed" + str(datetime.now()) + ".csv"
        
        album_buffer = StringIO()
        df.to_csv(album_buffer, index = False)
        album_content = album_buffer.getvalue()
        s3.put_object(Bucket = Bucket, Key = album_key , Body = album_content)
        
    # This code is to delete files from to_processed data and send it to processed data file in s3 bucket
    s3_resource = boto3.resource('s3')
    for key in spotify_key:
        copy_source={
            "Bucket": Bucket,
            "Key": key
        }
        s3_resource.meta.client.copy(copy_source , Bucket , "raw_data/processed/" + key.split('/')[-1])
        s3_resource.Object(Bucket , key).delete()
        
            
            
            
   