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
    name: String,
}

#[derive(Deserialize)]
struct File {
    username: String,
    filename: String,
    path: String
}

async fn upload_file(mut req: Request<()>) -> tide::Result<String> {
    let client = get_aws_client(REGION)?;

    let bytes: Vec<u8> = req.body_bytes().await.unwrap();
    let username_len = usize::from(bytes[0]);
    let (buf, mix) = bytes.split_at(username_len + 1);
    let (_, username_b) = buf.split_at(1);

    let filename_len = usize::from(mix[0]);
    let (buf, mix) = mix.split_at(filename_len + 1);
    let (_, filename_b) = buf.split_at(1);

    let path_len = usize::from(mix[0]);
    let (buf, content) = mix.split_at(path_len + 1);
    let (_, path_b) = buf.split_at(1);

    let username = std::str::from_utf8(username_b).unwrap();
    let filename = String::from_utf8(filename_b.to_vec()).unwrap();
    let mut path = String::from_utf8(path_b.to_vec()).unwrap();
    
    if path.is_empty() || path == "." {
        path = filename;
    } else {
        path.push_str(format!("/{}", filename).as_str());        
    }

    let stream: ByteStream = ByteStream::from(content.to_vec());

    s3_service::upload_object(&client, &username, stream, &path).await?;
    Ok(format!("Uploaded file: {}", path))
}

async fn delete_file(mut req: Request<()>) -> tide::Result<String> {
    let client = get_aws_client(REGION)?;

    let File {username, filename, mut path } = req.body_json().await?;
    path.push_str(format!("/{}", filename).as_str());
    s3_service::remove_object(&client, &username, &path).await?;
    Ok(format!("Deleted file: {}", filename))
}

async fn list_files(mut req: Request<()>) -> tide::Result<String> {
    let client = get_aws_client(REGION)?;

    let Bucket { name } = req.body_json().await?;
    let list = s3_service::list_objects(&client, &name).await?;

    Ok(list)
}

async fn create_user(mut req: Request<()>) -> tide::Result<String> {
    let client = get_aws_client(REGION)?;

    let Bucket { name, .. } = req.body_json().await?;
    s3_service::create_bucket(&client, &name, REGION).await?;

	Ok(format!("Created bucket: {}", name))
}

async fn delete_user(mut req: Request<()>) -> tide::Result<String> {
    let client = get_aws_client(REGION)?;

    let Bucket { name, .. } = req.body_json().await?;
    s3_service::delete_bucket(&client, &name).await?;

	Ok(format!("Deleted bucket: {}", name))
}

async fn download_files(mut req: Request<()>) -> Result<tide::Response, tide::Error> {
	let client = get_aws_client(REGION)?;
    let File { username, filename, mut path} = req.body_json().await?;
    if path.is_empty() || path == "." {
        path = filename;
    } else {
        path.push_str(format!("/{}", filename).as_str());        
    }
	
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

    app.listen("127.0.0.1:8080").await?;

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
