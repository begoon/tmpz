use regex::Regex;
use std::env;
use std::path::Path;
use std::sync::{Arc, Mutex};
use walkdir::{DirEntry, WalkDir};

fn human_readable_size(bytes: u64) -> String {
    const KB: u64 = 1024;
    const MB: u64 = KB * 1024;
    const GB: u64 = MB * 1024;

    if bytes >= GB {
        format!("{:.2} GB", bytes as f64 / GB as f64)
    } else if bytes >= MB {
        format!("{:.2} MB", bytes as f64 / MB as f64)
    } else if bytes >= KB {
        format!("{:.2} KB", bytes as f64 / KB as f64)
    } else {
        format!("{} bytes", bytes)
    }
}

async fn directory_size(dir: Arc<Path>) -> u64 {
    WalkDir::new(&*dir)
        .into_iter()
        .filter_map(Result::ok)
        .filter(|entry| entry.file_type().is_file())
        .map(|file| file.metadata().map(|m| m.len()).unwrap_or(0))
        .sum()
}

fn is_directory(entry: &DirEntry) -> bool {
    entry.file_type().is_dir()
}

#[tokio::main]
async fn main() {
    let args: Vec<String> = env::args().collect();

    if args.len() != 3 {
        eprintln!("usage: {} <start_folder> <regex_pattern>", args[0]);
        std::process::exit(1);
    }

    let start_folder = &args[1];
    let regex_pattern = &args[2];

    let re = match Regex::new(regex_pattern) {
        Ok(r) => r,
        Err(e) => {
            eprintln!("invalid regex pattern: {}", e);
            std::process::exit(1);
        }
    };

    if !Path::new(start_folder).exists() {
        eprintln!("folder font found: {}", start_folder);
        std::process::exit(1);
    }

    let results = Arc::new(Mutex::new(Vec::new()));

    let mut tasks = vec![];

    let mut walker = WalkDir::new(start_folder).into_iter();
    while let Some(entry) = walker.next() {
        match entry {
            Ok(entry) if is_directory(&entry) => {
                let folder_name = entry.file_name().to_string_lossy();

                if re.is_match(&folder_name) {
                    walker.skip_current_dir();

                    let folder_path = Arc::new(entry.path().to_path_buf());
                    let results = Arc::clone(&results);

                    println!("calculating size of '{}'", folder_path.display());
                    let task = tokio::spawn(async move {
                        let size = directory_size(Arc::from(folder_path.as_path())).await;
                        let mut results = results.lock().unwrap();
                        results.push((folder_path.display().to_string(), size));
                    });

                    tasks.push(task);
                }
            }
            Err(e) => {
                eprintln!("error reading entry: {}", e);
            }
            _ => {}
        }
    }

    for task in tasks {
        if let Err(e) = task.await {
            eprintln!("task failed: {}", e);
        }
    }

    let mut results = results.lock().unwrap();
    results.sort_by(|a, b| b.1.cmp(&a.1));

    let mut total_size = 0;
    let mut total_folders = 0;
    for (folder_name, size) in results.iter() {
        println!("{} - {}", folder_name, human_readable_size(*size));
        total_size += size;
        total_folders += 1;
    }
    println!(
        "total size: {} / {}",
        human_readable_size(total_size),
        total_folders
    );
}
