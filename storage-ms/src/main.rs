use anyhow::{Context, Result};
use aws_sdk_s3::primitives::ByteStream;
use aws_sdk_s3::{config, config::Credentials, config::Region, Client};
use std::env;
use tide::prelude::*;
use tide::Request;

const ENV_CRED_KEY_ID: &str = "S3_KEY_ID";
const ENV_CRED_KEY_SECRET: &str = "S3_KEY_SECRET";
const REGION: &str = "eu-north-1";

#[derive(Deserialize)]
struct Bucket {
    username: String,
}

#[derive(Deserialize)]
struct File {
    username: String,
    path: String
}

async fn upload_file(mut req: Request<()>) -> Result<tide::Response, tide::Error> {
    let client = get_aws_client(REGION)?;

    let bytes: Vec<u8> = req.body_bytes().await.unwrap();
    let username_len = usize::from(bytes[0]);
    let (buf, mix) = bytes.split_at(username_len + 1);
    let (_, username_b) = buf.split_at(1);

    let path_len = usize::from(mix[0]);
    let (buf, content) = mix.split_at(path_len + 1);
    let (_, path_b) = buf.split_at(1);

    let username = std::str::from_utf8(username_b).unwrap();
    let path: String = String::from_utf8(path_b.to_vec()).unwrap();

    let stream: ByteStream = ByteStream::from(content.to_vec());

    s3_service::upload_object(&client, &username, stream, &path).await?;
    Ok(tide::Response::new(200))
}

async fn delete_file(mut req: Request<()>) -> tide::Result<String> {
    let client = get_aws_client(REGION)?;

    let File {username, path } = req.body_json().await?;
    s3_service::remove_object(&client, &username, &path).await?;
    Ok(format!("Deleted file: {}", path))
}

async fn list_files(mut req: Request<()>) -> Result<tide::Response, tide::Error> {
    let client = get_aws_client(REGION)?;

    let Bucket { username } = req.body_json().await?;
    let list = s3_service::list_objects(&client, &username).await?;

    let response = tide::Response::builder(200)
        .body(list.as_bytes())
        .build();

	Ok(response)
}

async fn create_user(mut req: Request<()>) -> tide::Result<String> {
    let client = get_aws_client(REGION)?;

    let Bucket { username, .. } = req.body_json().await?;
    s3_service::create_bucket(&client, &username, REGION).await?;

	Ok(format!("Created bucket: {}", username))
}

async fn delete_user(mut req: Request<()>) -> tide::Result<String> {
    let client = get_aws_client(REGION)?;

    let Bucket { username, .. } = req.body_json().await?;

    let list = s3_service::list_objects(&client, &username).await?;

    for obj in list.split('\n') {
        if obj.len() < 3 {
            continue;
        }
        s3_service::remove_object(&client, &username, &obj).await?;
    }
    s3_service::delete_bucket(&client, &username).await?;

	Ok(format!("Deleted bucket: {}", username))
}

async fn download_files(mut req: Request<()>) -> Result<tide::Response, tide::Error> {
	let client = get_aws_client(REGION)?;
    let File { username, path } = req.body_json().await?;
	
    tide::log::info!("{}", path);
    println!("{}", path.as_str());
    let object = s3_service::download_object(&client, &username, &path).await?;
	let bytes = object.body.collect().await?.to_vec();
    
    // let mut file = std::fs::File::create(format!("./data/{}", name))?;
    // file.write_all(&bytes.to_vec())?;

    let response = tide::Response::builder(200)
    .body(bytes)
    .build();

	Ok(response)
}

#[async_std::main]
async fn main() -> Result<(), anyhow::Error> {
    femme::start();
    let mut app = tide::new();

    app.with(
        tide::log::LogMiddleware::new());

    app.at("/storage/upload").post(upload_file);
    app.at("/storage/delete").post(delete_file);
    app.at("/storage/list").post(list_files);
	app.at("/storage/download").post(download_files);
    app.at("/storage/create_user").post(create_user);
    app.at("/storage/delete_user").post(delete_user);

    app.listen("0.0.0.0:8080").await?;

    Ok(())
}

fn get_aws_client(region: &str) -> Result<Client, anyhow::Error> {
    let key_id = env::var(ENV_CRED_KEY_ID).context("Missing S3_KEY_ID")?;
    let key_secret = env::var(ENV_CRED_KEY_SECRET).context("Missing S3_KEY_SECRET")?;

    let cred = Credentials::new(key_id, key_secret, None, None, "loaded-from-custom-env");

    let region = Region::new(region.to_string());
    let conf_builder = config::Builder::new()
        .region(region)
        .credentials_provider(cred);
    let conf = conf_builder.build();

    let client = Client::from_conf(conf);
    Ok(client)
}
