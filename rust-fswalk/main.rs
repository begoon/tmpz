use ansi_term::Colour::{Blue, Cyan, Red};
use clap::Parser;
use regex::Regex;
use std::io::Write;
use std::path::Path;
use std::path::PathBuf;
use std::time::Instant;
use std::{env, vec};
use walkdir::{DirEntry, WalkDir};

enum Colored {
    Yes,
    No,
}

fn human_readable_size(bytes: u64, colored: Colored) -> String {
    const KB: u64 = 1024;
    const MB: u64 = KB * 1024;
    const GB: u64 = MB * 1024;

    if bytes >= GB {
        let v = format!("{:.2} GB", bytes as f64 / GB as f64);
        match colored {
            Colored::Yes => Red.bold().paint(v).to_string(),
            Colored::No => v,
        }
    } else if bytes >= MB {
        let v = format!("{:.2} MB", bytes as f64 / MB as f64);
        match colored {
            Colored::Yes => Cyan.bold().paint(v).to_string(),
            Colored::No => v,
        }
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
        println!(
            "{} - {}",
            folder_name,
            human_readable_size(*size, Colored::Yes)
        );
    }
    println!(
        "total size: {} / {} folder(s)",
        human_readable_size(total_size, Colored::Yes),
        results.len(),
    );
    println!("scanned: {} folder(s)", scanned);

    let seconds = started.elapsed().as_secs_f64();
    println!("elapsed time: {:.3} seconds", seconds);

    if !cli.command.is_empty() {
        let mut script_file =
            std::fs::File::create(&cli.script).expect("error creating script file");
        for (folder_name, size) in results.iter() {
            let command = cli.command.replace("{}", folder_name);
            let line = format!(
                "{} # {}\n",
                command,
                human_readable_size(*size, Colored::No)
            );
            script_file
                .write(line.as_bytes())
                .expect("error writing to script file");
            if cli.verbose {
                print!(
                    "{} # {}\n",
                    command.replace("{}", folder_name),
                    human_readable_size(*size, Colored::Yes)
                );
            }
        }
        println!("script written to {}", cli.script.display());
        let cmd = "source ".to_string() + cli.script.display().to_string().as_str();
        println!("run it with: {}", Blue.underline().paint(cmd));
    }
}
