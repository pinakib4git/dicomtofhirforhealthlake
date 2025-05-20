import json
import random
import os


def lambda_handler(event, context):
    RandomNum = random.randint(100,999)
    S3_LandingBucketName = event.get('S3BucketName')   
    S3_DICOMFileKey = event.get('S3BucketKey')
    S3_FHIROutPutBucketName = "s3://my-fhir-bucket"
    S3_CustomFHIRFileName = f"Custom-FHIR-Files/CustomFHIRFile{RandomNum}.json"
    S3_HealthLakeImportBucketName = "s3://my-fhir-bucket/Custom-FHIR-Files/"
    S3_HealthLakeOutputBucketName = "s3://my-fhir-bucket/HealthLake-Output-Import/"
    HealthLake_ImportExecutionRoleArn = os.environ['JobProcessingIAMRole'] #"arn:aws:iam::229055855186:role/service-role/AWSHealthLake-Import-HealthLakeImportJobManagerIAMRole"
    KMSKeyID_HealthLakeImportJob = os.environ['KMS_KEY_ID']
    ImageStore_CreateImportRoleArn = os.environ['JobProcessingIAMRole'] #"arn:aws:iam::229055855186:role/service-role/MedicalImagingDatastores-20240129T131964"
    ImageStoreID_ImportJob = f"AHIStore{RandomNum}"
    ImageImportJob_InputS3Bucket = "s3://dicom-image-lake/inputfile/"
    ImageImportJob_OutputS3Bucket = "s3://dicom-job-output-lake/outputfiles/"
    HealthLakeStoreID_ImportJob = os.environ['HEALTHLAKE_DATASTORE_ID']
    
    # Return all parameters to drive the process end to end
    return {
        'statusCode': 200,
        'S3_LandingBucketName': S3_LandingBucketName,
        'S3_DICOMFileKey': S3_DICOMFileKey,
        'S3_FHIROutPutBucketName': S3_FHIROutPutBucketName,
        'S3_CustomFHIRFileName' :  S3_CustomFHIRFileName,
        'S3_HealthLakeImportBucketName': S3_HealthLakeImportBucketName,
        'S3_HealthLakeOutputBucketName': S3_HealthLakeOutputBucketName,
        'HealthLake_ImportExecutionRoleArn':HealthLake_ImportExecutionRoleArn,
        'ImageStore_CreateImportRoleArn':ImageStore_CreateImportRoleArn,
        'ImageStoreID_ImportJob' : ImageStoreID_ImportJob,
        'ImageImportJob_OutputS3Bucket':ImageImportJob_OutputS3Bucket,
        'ImageImportJob_InputS3Bucket':ImageImportJob_InputS3Bucket,
        'KMSKeyID_HealthLakeImportJob':KMSKeyID_HealthLakeImportJob
    }
