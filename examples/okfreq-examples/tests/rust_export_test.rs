#[path = "../src/rust_export.rs"]
mod rust_export;

use rust_export::export_rust_row;

// @tests_req SwRS-CORE-002
#[test]
fn exports_a_rust_csv_row() {
    assert_eq!(export_rust_row("Ada", "uses CSV"), "Ada,uses CSV\n");
}

#[test]
fn exports_an_empty_rust_row() {
    assert_eq!(export_rust_row("", ""), ",\n");
}
