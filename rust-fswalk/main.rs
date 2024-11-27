use clap::Parser;
use regex::Regex;
use std::io::Write;
use std::path::Path;
use std::path::PathBuf;
use std::time::Instant;
use std::{env, vec};
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

fn directory_size(dir: &Path) -> u64 {
    WalkDir::new(dir)
        .into_iter()
        .filter_map(Result::ok)
        .filter(|entry| entry.file_type().is_file())
        .map(|file| file.metadata().map(|m| m.len()).unwrap_or(0))
        .sum()
}

fn is_directory(entry: &DirEntry) -> bool {
    entry.file_type().is_dir()
}

#[derive(Parser)]
#[command(version, about, long_about = None)]
struct Cli {
    start_folder: String,
    regex_pattern: String,

    #[arg(long, default_value = "du -hs {}")]
    command: String,

    #[arg(long, default_value = "./fswalk.sh")]
    script: PathBuf,

    #[arg(long)]
    verbose: bool,
}

fn main() {
    let cli = Cli::parse();
    let args: Vec<String> = env::args().collect();

    let start_folder = cli.start_folder;
    let regex_pattern = cli.regex_pattern;

    if start_folder.is_empty() || regex_pattern.is_empty() {
        eprintln!("usage: {} <start_folder> <regex_pattern>", args[0]);
        std::process::exit(1);
    };

    let script = cli.script;
    println!("script = {}", script.display());
    let command = cli.command;
    println!("command = {}", command);
    let verbose = cli.verbose;
    println!("verbose = {}", verbose);

    let re = match Regex::new(regex_pattern.as_str()) {
        Ok(r) => r,
        Err(e) => {
            eprintln!("invalid regex pattern: {}", e);
            std::process::exit(1);
        }
    };

    if !Path::new(start_folder.as_str()).exists() {
        eprintln!("folder not found: {}", start_folder);
        std::process::exit(1);
    }

    let mut results = vec![];
    let mut scanned = 0;

    let started = Instant::now();

    let mut walker = WalkDir::new(start_folder).into_iter();
    while let Some(entry) = walker.next() {
        match entry {
            Ok(entry) if is_directory(&entry) => {
                let path = entry.path();

                scanned += 1;

                let folder_name = entry.file_name().to_string_lossy();
                if re.is_match(&folder_name) {
                    walker.skip_current_dir();

                    println!("processing {}", path.display());
                    let size = directory_size(&path);
                    results.push((path.display().to_string(), size));
                }
            }
            Err(e) => eprintln!("error reading entry: {}", e),
            _ => {}
        }
    }

    results.sort_by(|a, b| b.1.cmp(&a.1));

    let total_size = results.iter().map(|(_, size)| size).sum::<u64>();
    for (folder_name, size) in results.iter() {
        println!("{} - {}", folder_name, human_readable_size(*size));
    }
    println!(
        "total size: {} / {} folders",
        human_readable_size(total_size),
        results.len(),
    );
    println!("scanned: {} files", scanned);

    let seconds = started.elapsed().as_secs_f64();
    println!("elapsed time: {:.3} seconds", seconds);

    if !command.is_empty() {
        let mut script_file = std::fs::File::create(&script).expect("error creating script file");
        for (folder_name, size) in results.iter() {
            let line = format!(
                "{} # {}\n",
                command.replace("{}", folder_name),
                human_readable_size(*size)
            );
            script_file
                .write(line.as_bytes())
                .expect("error writing to script file");
            if verbose {
                print!("{}", line);
            }
        }
        println!("script written to {}", script.display());
        println!("run it with: source {}", script.display());
    }
}
