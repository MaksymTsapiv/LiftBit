use anyhow::{Context, Result};
use aws_sdk_s3::primitives::ByteStream;
use aws_sdk_s3::{config, config::Region, Client, config::Credentials};
use std::env;
use tide::Request;
use tide::prelude::*;

const ENV_CRED_KEY_ID: &str = "S3_KEY_ID";
const ENV_CRED_KEY_SECRET: &str = "S3_KEY_SECRET";
const BUCKET_NAME: &str = "liftbit";
const REGION: &str = "eu-north-1";

#[derive(Deserialize)]
struct File {
    name: String,
    content: String,
}

async fn upload_file(mut req: Request<()>) -> tide::Result<String> {
    let client = get_aws_client(REGION)?;
    let bucket_name = BUCKET_NAME;

	let File {name, content} = req.body_json().await?;
	// let bytes: &'static [u8] = content.as_bytes();
	let bytes = content.as_bytes().to_vec();
	let stream: ByteStream = ByteStream::from(bytes);
    
	s3_service::upload_object(&client, &bucket_name, stream, &name).await?;
	Ok(format!("Uploaded file: {}", name))
}

async fn delete_file(mut req: Request<()>) -> tide::Result<String> {
    let client = get_aws_client(REGION)?;
    let bucket_name = BUCKET_NAME;

	let File {name, .. } = req.body_json().await?;

    s3_service::remove_object(&client, &bucket_name, &name).await?;
	Ok(format!("Deleted file: {}", name))
}


async fn list_files(mut req: Request<()>) -> tide::Result<String> {
    let client = get_aws_client(REGION)?;
    let bucket_name = BUCKET_NAME;

	let File {..} = req.body_json().await?;

    let list = s3_service::list_objects(&client, &bucket_name).await?;

	Ok(list)
}

async fn test(mut req: Request<()>) -> tide::Result<String> {
	let File {name, content } = req.body_json().await?;
	Ok(format!("name: {}, content: {}", name, content))
}

#[async_std::main]
async fn main() -> Result<(), anyhow::Error> {

	let mut app = tide::new();
	app.at("/storage/upload").post(upload_file);
	app.at("/storage/delete").post(delete_file);
	app.at("/storage/list").post(list_files);

    app.at("/storage/test").post(test);

	app.listen("127.0.0.1:8080").await?;


    Ok(())
}

fn get_aws_client(region: &str) -> Result<Client, anyhow::Error> {
	let key_id = env::var(ENV_CRED_KEY_ID).context("Missing S3_KEY_ID")?;
	let key_secret = env::var(ENV_CRED_KEY_SECRET).context("Missing S3_KEY_SECRET")?;

	let cred = Credentials::new(key_id,
		 key_secret, None, None, "loaded-from-custom-env");

	let region = Region::new(region.to_string());
	let conf_builder = config::Builder::new().region(region).credentials_provider(cred);
	let conf = conf_builder.build();

	let client = Client::from_conf(conf);
	Ok(client)
}
