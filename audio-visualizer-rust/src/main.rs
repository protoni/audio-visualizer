use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use rustfft::{FftPlanner, num_complex::Complex};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::Duration;
use std::collections::VecDeque;
use std::io::{self, Write};

fn main() {
    // Setup CPAL audio capture
    let host = cpal::default_host();
    let devices: Vec<_> = host.input_devices().unwrap().collect();

    // List available devices
    println!("Available input devices:");
    for (index, device) in devices.iter().enumerate() {
        println!("{}: {}", index, device.name().unwrap_or_else(|_| "Unknown Device".to_string()));
    }

    // Select device by index
    print!("Select device index: ");
    io::stdout().flush().unwrap();

    let mut input = String::new();
    io::stdin().read_line(&mut input).unwrap();
    let device_index: usize = input.trim().parse().expect("Invalid index");

    let device = devices.get(device_index).expect("Failed to get device");

    println!("Selected device: {}", device.name().unwrap_or_else(|_| "Unknown Device".to_string()));

    print!("\x1B[H");

    let config = device.default_input_config().expect("Failed to get default input format").config();

    let audio_data = Arc::new(Mutex::new(VecDeque::new()));
    let audio_data_clone = audio_data.clone();

    let stream = device.build_input_stream(
        &config,
        move |data: &[f32], _: &cpal::InputCallbackInfo| {
            let mut audio_data = audio_data_clone.lock().unwrap();
            audio_data.extend(data.iter().cloned());
            while audio_data.len() > 2048 {
                audio_data.pop_front();
            }
        },
        move |err| {
            eprintln!("Stream error: {}", err);
        },
    ).expect("Failed to build input stream");

    stream.play().expect("Failed to play stream");

    // Print ASCII graph in a separate thread
    let audio_data_clone = audio_data.clone();
    thread::spawn(move || {
        // Setup FFT
        let mut planner = FftPlanner::new();
        let fft = planner.plan_fft_forward(1024);

        loop {
            thread::sleep(Duration::from_millis(100));

            let mut audio_data = audio_data_clone.lock().unwrap();
            if audio_data.len() < 1024 {
                continue;
            }

            // Perform FFT
            let mut buffer: Vec<Complex<f32>> = audio_data.drain(..1024).map(|x| Complex { re: x, im: 0.0 }).collect();
            fft.process(&mut buffer);

            // Compute the magnitude of each frequency bin
            let magnitudes: Vec<f32> = buffer.iter().map(|c| c.norm()).collect();

            // Move cursor to top-left
            print!("\x1B[H");

            // Determine the maximum magnitude for dynamic scaling, ensure it's non-zero
            let max_magnitude = magnitudes.iter().cloned().fold(0.0, f32::max).max(1.0);

            // Display the magnitudes as a bar graph
            for (i, &magnitude) in magnitudes.iter().take(50).enumerate() {
                // Apply a threshold to reduce the effect of very low magnitudes
                let thresholded_magnitude = magnitude; //if magnitude > 0.02 { magnitude } else { 0.0 };

                // Dynamically scale the bar height based on the maximum magnitude
                let bar_height = ((thresholded_magnitude / max_magnitude) * 100.0).round() as usize;
                let bar: String = (0..bar_height).map(|_| '#').collect();
                println!("{:4}Hz: {:<50}", i * (config.sample_rate.0 as usize / 1024), bar); // Adjusting frequency labels based on sample rate and FFT size
            }

            // Print blank lines to clear any remaining part of the previous graph
            for _ in magnitudes.iter().take(50).len()..50 {
                println!("{:<60}", " ");
            }

            // Flush stdout to ensure immediate display update
            io::stdout().flush().unwrap();
        }
    });

    // Prevent the main thread from exiting
    loop {
        thread::sleep(Duration::from_secs(1));
    }
}
