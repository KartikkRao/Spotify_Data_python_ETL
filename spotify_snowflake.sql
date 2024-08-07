-- creating table to store data cleaned and transformed in s3
CREATE OR REPLACE TABLE spotify_top_songs(
    album_id text,
    album_name varchar(100),
    album_release_date timestamp,
    song_name varchar(100),
    song_popularity_rating int,
    artist_name array,
    album_total_tracks int,
    album_link text,
    song_link text,
    id NUMBER AUTOINCREMENT PRIMARY KEY  -- created a suroget key to identify duplicates in future 
);


-- creating a storage integration
CREATE storage INTEGRATION spotify_init
    type = external_stage
    storage_provider = s3
    storage_aws_role_arn = 'your_user'
    enabled = true
    storage_allowed_locations = ( 'Your_s3_location' );

DESC INTEGRATION spotify_init;  -- This is to get the info which needs to be put in IAM user of aws (external_id and aws_iam_arn)

-- file format to descride how to read csv 
CREATE OR REPLACE FILE FORMAT csv_format
    type = csv
    field_delimiter = ','
    skip_header = 1
    null_if = ('NULL','null')
    empty_field_as_null = True
    field_optionally_enclosed_by = '"'
    error_on_column_count_mismatch = False ;


-- stage to communicate with s3    
CREATE OR REPLACE STAGE spotify_stage  
    url = 'your_specific_location'
    storage_integration = spotify_init
    file_format = csv_format;

-- copying initial data already in s3 to table   
COPY INTO spotify_top_songs (
    album_id,
    album_name,
    album_release_date,
    song_name,
    song_popularity_rating,
    artist_name,
    album_total_tracks,
    album_link,
    song_link
)
FROM @spotify_stage;


-- stage for pipeline for new data to come
CREATE OR REPLACE STAGE spotify_stage1
    url = 'your_specific_location'
    storage_integration = spotify_init
    file_format = csv_format;


-- pipe created to communicate with s3 location when notified automatically will add new data from new csv files
CREATE OR REPLACE PIPE spotify_pipe
    auto_ingest = True
    AS
    COPY INTO spotify_top_songs (
    album_id,
    album_name,
    album_release_date,
    song_name,
    song_popularity_rating,
    artist_name,
    album_total_tracks,
    album_link,
    song_link
)
FROM @spotify_stage1;

DESC PIPE spotify_pipe;  --This is to copy the sqs url to put in the event trigger of  aws s3
    
select * from spotify_top_songs; -- to check pipe once when a new csv file is put in my s3 


-- deleting duplicates if any 
DELETE FROM spotify_top_songs
WHERE id IN (
    SELECT id FROM (
        SELECT 
            id,
            ROW_NUMBER() OVER (PARTITION BY song_name ORDER BY id) as row_num
        FROM 
            spotify_top_songs
    ) cte
    WHERE row_num > 1
);
