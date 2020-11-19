# AUTOGENERATED! DO NOT EDIT! File to edit: aws_utils.ipynb (unless otherwise specified).

__all__ = ['get_boto_session', 'write_json_to_s3', 'write_df_to_s3', 'read_df_from_s3', 'read_json_from_s3']

# Cell
import os
import json
from io import BytesIO
import pandas as pd
import boto3

# Cell
def get_boto_session():
    session = boto3.Session(
      region_name=os.environ["AWS_REGION"],
      aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
      aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"])
    return session

# Cell
def _read_object_from_s3(bucket: str, key: str) -> BytesIO:
    """ Reads an object from S3 """
    s3_resource = get_boto_session().resource("s3")
    bucket = s3_resource.Bucket(bucket)
    data = BytesIO()
    bucket.download_fileobj(key, data)
    data.seek(0)
    return data

# Cell
def _write_object_to_s3(bucket: str, key: str, buffer: BytesIO):
    """ Writes an object to S3 """
    s3_client = get_boto_session().client("s3")
    s3_client.put_object(Bucket=bucket, Key=key, Body=buffer.getvalue())

# Cell
def write_json_to_s3(json_dict, bucket: str, key: str):
    """ Write a Python Dict to S3 as JSON """
    buffer = BytesIO()
    buffer.write(json.dumps(json_dict).encode("utf-8"))
    buffer.seek(0)
    _write_object_to_s3(bucket=bucket, key=key, buffer=buffer)

# Cell
def write_df_to_s3(
        dataframe: pd.DataFrame, bucket: str, key: str, outputformat: str = "parquet"
):
    """ Write a Pandas dataframe to S3 as Parquet """
    buffer = BytesIO()
    if outputformat == "parquet":
        dataframe.to_parquet(buffer, engine="pyarrow", index=False)
    elif outputformat == "csv":
        dataframe.to_csv(buffer, index=False)
    else:
        raise Exception("Unknown format")
    _write_object_to_s3(bucket=bucket, key=key, buffer=buffer)

# Cell
def read_df_from_s3(
        bucket: str, key: str, inputformat: str = "parquet", **df_kwargs
) -> pd.DataFrame:
    """ Reads a Pandas dataframe from S3 """
    data = _read_object_from_s3(bucket=bucket, key=key)
    if inputformat == "parquet":
        return pd.read_parquet(data, **df_kwargs)
    elif inputformat == "csv":
        return pd.read_csv(data, **df_kwargs)
    return pd.DataFrame()

# Cell
def read_json_from_s3(bucket: str, key: str):
    file_content = _read_object_from_s3(bucket=bucket, key=key)
    return json.loads(file_content.read())