use rand::Rng;
use reqwest::{Client, StatusCode};
use serde::Deserialize;
use serde_json::Value;
use std::collections::HashMap;
use tokio::task;

#[derive(Deserialize, Debug)]
struct Structure {
    #[serde(rename = "user-agent")]
    user_agent: String,
}

const HTTPBIN_API: &str = "https://httpbin.org";

async fn fetch_delay(client: &Client, delay: u8) -> Result<StatusCode, reqwest::Error> {
    let url = format!("{}/delay/{}", HTTPBIN_API, delay);
    println!("dialing {}", url);
    let response = client.get(&url).send().await?;
    let status_code = response.status();
    Ok(status_code)
}

async fn fetch_structure(client: &Client) -> Result<Structure, reqwest::Error> {
    let url = format!("{}/user-agent", HTTPBIN_API);
    println!("dialing {}", url);
    let response = client.get(&url).send().await?;
    let data = response.json::<Structure>().await?;
    Ok(data)
}

async fn fetch_json(client: &Client) -> Result<HashMap<String, Value>, reqwest::Error> {
    let url = format!("{}/json", HTTPBIN_API);
    println!("dialing {}", url);
    let response = client.get(url).send().await?;
    let json = response.json::<HashMap<String, Value>>().await?;
    Ok(json)
}

#[tokio::main]
async fn main() {
    let client = Client::builder().user_agent("teapot/1.0").build().unwrap();

    let mut rng = rand::thread_rng();
    let delays: Vec<u8> = (0..2).map(|_| rng.gen_range(1..=5)).collect();

    let delay_handles: Vec<_> = delays
        .iter()
        .map(|&delay| {
            let client = client.clone();
            task::spawn(async move {
                match fetch_delay(&client, delay).await {
                    Ok(response) => {
                        println!("response from delay/ for {}: {:#?}", delay, response)
                    }
                    Err(e) => eprintln!("error querying delay/ {}: {}", delay, e),
                }
            })
        })
        .collect();

    let user_agent_handle = task::spawn({
        let client = client.clone();
        async move {
            match fetch_structure(&client).await {
                Ok(response) => {
                    println!("response from user-agent/: {:#?}", response);
                    println!("user-agent: {}", response.user_agent)
                }
                Err(e) => eprintln!("error querying user-agent/: {}", e),
            }
        }
    });

    let json_handle = task::spawn({
        let client = client.clone();
        async move {
            match fetch_json(&client).await {
                Ok(response) => println!("response from json/: {:#?}", response),
                Err(e) => eprintln!("error querying json/: {}", e),
            }
        }
    });

    let mut handles = delay_handles;
    handles.push(json_handle);
    handles.push(user_agent_handle);

    for handle in handles {
        let _ = handle.await;
    }
}
