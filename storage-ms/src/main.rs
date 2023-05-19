use anyhow::{Context, Result};
use aws_sdk_s3::config::Credentials;
use aws_sdk_s3::{config, config::Region, Client};
// use s3_service::error::Error;
use std::env;

// -- constants
const ENV_CRED_KEY_ID: &str = "S3_KEY_ID";
const ENV_CRED_KEY_SECRET: &str = "S3_KEY_SECRET";
const BUCKET_NAME: &str = "liftbit";
const REGION: &str = "eu-north-1";


#[tokio::main]
async fn main() -> Result<(), anyhow::Error> {
    let client = get_aws_client(REGION)?;
    let bucket_name = BUCKET_NAME;
    let file_name = "test.txt";
    let key = "test";
    
    s3_service::list_objects(&client, &bucket_name).await?;
    s3_service::upload_object(&client, &bucket_name, &file_name, &key).await?;
    s3_service::list_objects(&client, &bucket_name).await?;
    s3_service::delete_objects(&client, &bucket_name).await?;
    s3_service::list_objects(&client, &bucket_name).await?;

    Ok(())
}

// async fn run_s3_operations(
//     region: Region,
//     client: Client,
//     bucket_name: String,
//     file_name: String,
//     key: String,
//     target_key: String,
// ) -> Result<(), Error> {
//     s3_service::create_bucket(&client, &bucket_name, region.as_ref()).await?;
//     s3_service::upload_object(&client, &bucket_name, &file_name, &key).await?;
//     let _object = s3_service::download_object(&client, &bucket_name, &key).await;
//     s3_service::copy_object(&client, &bucket_name, &key, &target_key).await?;
//     s3_service::list_objects(&client, &bucket_name).await?;
//     s3_service::delete_objects(&client, &bucket_name).await?;
//     s3_service::delete_bucket(&client, &bucket_name).await?;

//     Ok(())
// }

fn get_aws_client(region: &str) -> Result<Client, anyhow::Error> {
	// get the id/secret from env
	let key_id = env::var(ENV_CRED_KEY_ID).context("Missing S3_KEY_ID")?;
	let key_secret = env::var(ENV_CRED_KEY_SECRET).context("Missing S3_KEY_SECRET")?;

	// build the aws cred
	let cred = Credentials::new(key_id, key_secret, None, None, "loaded-from-custom-env");

	// build the aws client
	let region = Region::new(region.to_string());
	let conf_builder = config::Builder::new().region(region).credentials_provider(cred);
	let conf = conf_builder.build();

	// build aws client
	let client = Client::from_conf(conf);
	Ok(client)
}
