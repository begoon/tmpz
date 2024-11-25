use std::{collections::HashMap, env};

use serde::Serialize;
use warp::Filter;

#[derive(Serialize)]
struct VersionInfo {
    version: String,
}

#[tokio::main]
async fn main() {
    let version = warp::path("version").and(warp::get()).map(|| {
        warp::reply::json(&VersionInfo {
            version: "1.0.0".to_string(),
        })
    });
    let env = warp::path("env").and(warp::get()).map(|| {
        let mut env_vars = HashMap::new();
        for (key, value) in env::vars() {
            env_vars.insert(key, value);
        }
        warp::reply::json(&env_vars)
    });
    let routes = version.or(env);
    warp::serve(routes).run(([127, 0, 0, 1], 8000)).await;
}
