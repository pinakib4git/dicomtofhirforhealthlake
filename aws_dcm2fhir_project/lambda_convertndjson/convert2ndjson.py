import json
import os
import logging
import boto3
from botocore.exceptions import ClientError
import io

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize S3 client
s3 = boto3.client('s3')

def convert_json_to_ndjson(json_data):
    """
    Convert JSON data to NDJSON format.
    
    Args:
        json_data: Loaded JSON data (dict or list)
        
    Returns:
        str: NDJSON formatted string
    """
    # Determine the type of JSON data
    if isinstance(json_data, list):
        # If it's a list, each item becomes a line in NDJSON
        items = json_data
    elif isinstance(json_data, dict):
        # If it's a dictionary, convert to a single-item list
        items = [json_data]
    else:
        raise ValueError(f"Unexpected JSON structure: {type(json_data)}")
    
    # Convert each item to NDJSON format
    ndjson_lines = []
    for item in items:
        line = json.dumps(item, ensure_ascii=False)
        ndjson_lines.append(line)
    
    # Join lines with newline character
    return '\n'.join(ndjson_lines)

def lambda_handler(event, context):
    """
    AWS Lambda function handler to convert JSON files from S3 to NDJSON format.
    """
    try:
        # Log the full event for debugging
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Extract source and destination information from the event
        if 'Records' in event:
            # S3 event trigger
            source_bucket = event['Records'][0]['s3']['bucket']['name']
            source_key = event['Records'][0]['s3']['object']['key']
            
            # For S3 events, we'll use the same bucket for destination
            # or use the environment variable if set
            destination_bucket = os.environ.get('DESTINATION_BUCKET', source_bucket)
            destination_key = os.path.splitext(source_key)[0] + '.ndjson'
        else:
            # Direct invocation
            source_bucket = event.get('source_bucket', os.environ.get('SOURCE_BUCKET'))
            source_key = event.get('source_key')
            destination_bucket = event.get('destination_bucket', os.environ.get('DESTINATION_BUCKET', source_bucket))
            destination_key = event.get('destination_key', os.path.splitext(source_key)[0] + '.ndjson')
        
        if not source_bucket or not source_key:
            logger.error("Source bucket and key must be provided")
            return {
                'statusCode': 400,
                'body': json.dumps("Source bucket and key must be provided")
            }
            
        logger.info(f"Processing file s3://{source_bucket}/{source_key}")
        logger.info(f"Will write to s3://{destination_bucket}/{destination_key}")
        
        # Check if the source bucket exists
        try:
            s3.head_bucket(Bucket=source_bucket)
            logger.info(f"Successfully verified source bucket exists: {source_bucket}")
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            if error_code == '403':
                logger.error(f"Access denied to source bucket: {source_bucket}. Check IAM permissions.")
            elif error_code == '404':
                logger.error(f"Source bucket not found: {source_bucket}")
            else:
                logger.error(f"Error accessing source bucket: {e}")
            return {
                'statusCode': 500,
                'body': json.dumps(f"Error accessing source bucket: {str(e)}")
            }
        
        # Check if the source object exists
        try:
            s3.head_object(Bucket=source_bucket, Key=source_key)
            logger.info(f"Successfully verified source object exists: {source_key}")
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            if error_code == '403':
                logger.error(f"Access denied to object: {source_key}. Check IAM permissions.")
            elif error_code == '404':
                logger.error(f"Object not found: {source_key}")
                # List objects with similar prefix to help debugging
                try:
                    prefix = '/'.join(source_key.split('/')[:-1]) + '/'
                    response = s3.list_objects_v2(Bucket=source_bucket, Prefix=prefix, MaxKeys=10)
                    if 'Contents' in response:
                        logger.info(f"Found similar objects with prefix '{prefix}':")
                        for obj in response['Contents']:
                            logger.info(f"  - {obj['Key']}")
                    else:
                        logger.info(f"No objects found with prefix '{prefix}'")
                except Exception as list_err:
                    logger.warning(f"Could not list similar objects: {list_err}")
            else:
                logger.error(f"Error accessing object: {e}")
            return {
                'statusCode': 500,
                'body': json.dumps(f"Error accessing object: {str(e)}")
            }
        
        # Read the JSON file directly from S3 into memory
        try:
            logger.info(f"Reading object content from s3://{source_bucket}/{source_key}")
            response = s3.get_object(Bucket=source_bucket, Key=source_key)
            content = response['Body'].read().decode('utf-8')
            logger.info(f"Successfully read object content, size: {len(content)} bytes")
            
            # Parse JSON
            json_data = json.loads(content)
            logger.info(f"Successfully parsed JSON data")
        except ClientError as e:
            logger.error(f"Error reading object from S3: {e}")
            return {
                'statusCode': 500,
                'body': json.dumps(f"Error reading object from S3: {str(e)}")
            }
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in input file: {e}")
            return {
                'statusCode': 400,
                'body': json.dumps(f"Invalid JSON format: {str(e)}")
            }
        
        # Convert to NDJSON
        try:
            ndjson_content = convert_json_to_ndjson(json_data)
            logger.info(f"Successfully converted to NDJSON format")
        except Exception as e:
            logger.error(f"Error converting to NDJSON: {e}")
            return {
                'statusCode': 500,
                'body': json.dumps(f"Error converting to NDJSON: {str(e)}")
            }
        
        # Check if the destination bucket exists
        try:
            s3.head_bucket(Bucket=destination_bucket)
            logger.info(f"Successfully verified destination bucket exists: {destination_bucket}")
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            if error_code == '403':
                logger.error(f"Access denied to destination bucket: {destination_bucket}. Check IAM permissions.")
            elif error_code == '404':
                logger.error(f"Destination bucket not found: {destination_bucket}")
            else:
                logger.error(f"Error accessing destination bucket: {e}")
            return {
                'statusCode': 500,
                'body': json.dumps(f"Error accessing destination bucket: {str(e)}")
            }
        
        # Upload the NDJSON content directly to S3
        try:
            logger.info(f"Uploading NDJSON content to s3://{destination_bucket}/{destination_key}")
            # Ensure the content ends with a newline
            if not ndjson_content.endswith('\n'):
                ndjson_content += '\n'
                
            # Upload the content directly without using a temporary file
            s3.put_object(
                Bucket=destination_bucket,
                Key=destination_key,
                Body=ndjson_content.encode('utf-8'),
                ContentType='application/x-ndjson'
            )
            logger.info(f"Successfully uploaded NDJSON file to s3://{destination_bucket}/{destination_key}")
        except ClientError as e:
            logger.error(f"Error uploading to S3: {e}")
            return {
                'statusCode': 500,
                'body': json.dumps(f"Error uploading to S3: {str(e)}")
            }
        
        # Return success response
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Successfully converted JSON to NDJSON',
                'source': f"s3://{source_bucket}/{source_key}",
                'destination': f"s3://{destination_bucket}/{destination_key}"
            })
        }
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Unexpected error: {str(e)}")
        }
